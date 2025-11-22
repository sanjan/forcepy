"""Main Salesforce client for forcepy."""

import logging
import time
from typing import Any, Optional
from urllib.parse import urljoin

import requests

from . import auth
from .composite import CompositeRequest
from .exceptions import APIError, AuthenticationError, QueryError
from .metadata import DescribeCache, ObjectDescribe
from .query_advanced import WorkbenchConfig
from .sobject import Sobject, SobjectSet
from .token_cache import TokenCache, create_cache, get_cache_key
from .utils import build_url, parse_error_response

logger = logging.getLogger(__name__)


class DynamicEndpoint:
    """Dynamic endpoint builder for accessing Salesforce REST API."""

    def __init__(self, client: "Salesforce", path: list[str] = None):
        self.client = client
        self.path = path or []

    def __getattr__(self, name: str) -> "DynamicEndpoint":
        """Chain attributes to build endpoint path."""
        return DynamicEndpoint(self.client, self.path + [name])

    def __getitem__(self, key: str) -> "DynamicEndpoint":
        """Add key to path (for IDs, etc.)."""
        return DynamicEndpoint(self.client, self.path + [str(key)])

    def __call__(self, *args, **kwargs) -> Any:
        """Make request with current path."""
        return self.get(*args, **kwargs)

    def _build_url(self) -> str:
        """Build complete URL from path."""
        base = f"/services/data/v{self.client.version}"
        return build_url(base, *self.path)

    @property
    def url_path(self) -> str:
        """Get REST API URL path for this endpoint.

        Returns:
            URL path string

        Example:
            >>> path = sf.sobjects.Account.url_path
            >>> print(path)
            /services/data/v53.0/sobjects/Account
        """
        return self._build_url()

    def get(self, **params) -> Any:
        """GET request."""
        if self.client._batch_mode:
            # Add to batch queue
            ref_id = f"request_{len(self.client._batch_requests)}"
            self.client._batch_requests.append({"method": "GET", "url": self._build_url(), "referenceId": ref_id})
            return {"referenceId": ref_id}  # Return placeholder
        return self.client.http("GET", self._build_url(), params=params)

    def post(self, **data) -> Any:
        """POST request."""
        if self.client._batch_mode:
            # Add to batch queue
            ref_id = f"request_{len(self.client._batch_requests)}"
            self.client._batch_requests.append(
                {"method": "POST", "url": self._build_url(), "referenceId": ref_id, "body": data}
            )
            return {"referenceId": ref_id}  # Return placeholder
        return self.client.http("POST", self._build_url(), json=data)

    def patch(self, **data) -> Any:
        """PATCH request."""
        if self.client._batch_mode:
            # Add to batch queue
            ref_id = f"request_{len(self.client._batch_requests)}"
            self.client._batch_requests.append(
                {"method": "PATCH", "url": self._build_url(), "referenceId": ref_id, "body": data}
            )
            return {"referenceId": ref_id}  # Return placeholder
        return self.client.http("PATCH", self._build_url(), json=data)

    def delete(self) -> Any:
        """DELETE request."""
        if self.client._batch_mode:
            # Add to batch queue
            ref_id = f"request_{len(self.client._batch_requests)}"
            self.client._batch_requests.append({"method": "DELETE", "url": self._build_url(), "referenceId": ref_id})
            return {"referenceId": ref_id}  # Return placeholder
        return self.client.http("DELETE", self._build_url())


class Salesforce:
    """Salesforce REST API client.

    Automatically authenticates when username and password are provided to constructor.

    Example:
        >>> # Auto-authenticates on construction
        >>> sf = Salesforce(username='user@example.com', password='password')
        >>> accounts = sf.query("SELECT Id, Name FROM Account LIMIT 10")
        >>> for account in accounts.records:
        ...     print(account.Name)

        >>> # Or authenticate manually later
        >>> sf = Salesforce()
        >>> sf.login(username='user@example.com', password='password')
    """

    BASE_URL: Optional[str] = None
    VERSION: str = "53.0"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        security_token: Optional[str] = None,
        sandbox: bool = False,
        base_url: Optional[str] = None,
        version: Optional[str] = None,
        session_id: Optional[str] = None,
        instance_url: Optional[str] = None,
        cache_backend: Optional[str | TokenCache] = "memory",
        max_retries: int = 3,
        retry_delay: float = 6.0,
        retry_backoff: bool = True,
        **cache_kwargs,
    ):
        """Initialize Salesforce client.

        Automatically authenticates if username and password are provided.
        To defer authentication, omit credentials and call .login() later.

        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Security token (automatically appended to password if provided)
            sandbox: Use sandbox environment (default: False for production)
            base_url: Base URL for authentication (overrides sandbox parameter)
            version: API version (default: 53.0)
            session_id: Pre-existing session ID (skips authentication)
            instance_url: Pre-existing instance URL (required if session_id provided)
            cache_backend: Token cache backend:
                - "memory" (default): In-memory cache, thread-safe
                - "null" or None: Disable caching
                - "redis": Redis-backed cache (requires redis package)
                - TokenCache instance: Custom cache
            max_retries: Maximum number of retries for failed requests (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 6.0)
            retry_backoff: Use exponential backoff for retries (default: True)
            **cache_kwargs: Additional arguments for cache backend
                - maxsize: Max tokens to cache (memory backend, default: 100)
                - redis_url: Redis connection URL (redis backend)
                - prefix: Redis key prefix (redis backend)

        Example:
            >>> # Production org (default)
            >>> sf = Salesforce(username='user@example.com', password='password')

            >>> # With security token (automatically appended to password)
            >>> sf = Salesforce(
            ...     username='user@example.com',
            ...     password='password',
            ...     security_token='yourSecurityToken123'
            ... )

            >>> # Sandbox org
            >>> sf = Salesforce(username='user@example.com', password='password', sandbox=True)

            >>> # Defer authentication
            >>> sf = Salesforce()
            >>> sf.login(username='user@example.com', password='password')

            >>> # Use existing session
            >>> sf = Salesforce(session_id='00D...', instance_url='https://na1.salesforce.com')

            >>> # Configure retry behavior
            >>> sf = Salesforce(
            ...     username='user@example.com',
            ...     password='password',
            ...     max_retries=5,
            ...     retry_delay=10.0,
            ...     retry_backoff=True
            ... )
        """
        self.username = username
        self.security_token = security_token
        # Append security token to password if provided
        if password and security_token:
            self.password = password + security_token
        else:
            self.password = password
        self.sandbox = sandbox
        # Determine base_url: explicit base_url > sandbox flag > default production
        if base_url:
            self.base_url = base_url
        elif sandbox:
            self.base_url = "https://test.salesforce.com"
        else:
            self.base_url = self.BASE_URL or "https://login.salesforce.com"
        self.version = version or self.VERSION
        self.session_id = session_id
        self.instance_url = instance_url
        self.session = requests.Session()
        self._token_cache = create_cache(cache_backend, **cache_kwargs)
        self._describe_cache = DescribeCache()
        self.workbench_config = WorkbenchConfig()

        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff

        # Session info tracking
        self._user_id: Optional[str] = None
        self._session_expires: Optional[float] = None
        self._last_request_time: Optional[float] = None

        # Context manager state for composite batching
        self._batch_mode = False
        self._batch_requests: list[dict[str, Any]] = []

        # Auto-login if credentials provided
        if username and password and not session_id:
            self.login()

    def get_login_url(self) -> str:
        """Get login URL (returns base_url set during initialization)."""
        return self.base_url

    def login(self, **kwargs) -> None:
        """Login to Salesforce using SOAP with token caching.

        Checks cache first for valid token. If found, reuses it.
        Otherwise, performs fresh login and caches the result.

        Args:
            **kwargs: Override username, password, security_token, etc.
        """
        username = kwargs.get("username", self.username)
        password = kwargs.get("password", self.password)
        security_token = kwargs.get("security_token", self.security_token)

        # Append security token to password if provided
        if password and security_token and not password.endswith(security_token):
            password = password + security_token

        if not username or not password:
            raise AuthenticationError("Username and password required for login")

        login_url = self.get_login_url()
        cache_key = get_cache_key(username, login_url)

        # Try cache first
        cached_token = self._token_cache.get(cache_key)
        if cached_token:
            # Check if token is still valid
            if cached_token.get("expires_at", 0) > time.time():
                logger.info(f"Using cached session for {username}")
                self.session_id = cached_token["session_id"]
                self.instance_url = cached_token["instance_url"]
                self.session.headers["Authorization"] = f"Bearer {self.session_id}"
                # Restore session info
                self._user_id = cached_token.get("user_id")
                self._session_expires = cached_token.get("expires_at")
                return

        # Cache miss or expired - perform fresh login
        logger.info(f"Logging in as {username} to {login_url}")

        try:
            session_id, instance_url = auth.soap_login(
                username=username, password=password, login_url=login_url, version=self.version
            )

            self.session_id = session_id
            self.instance_url = instance_url

            # Set session header
            self.session.headers["Authorization"] = f"Bearer {session_id}"

            # Track session expiry (Salesforce tokens typically last 2 hours)
            self._session_expires = time.time() + 7200  # 2 hours from now

            # Get user info to extract user_id
            try:
                user_info_url = "/services/oauth2/userinfo"
                user_info = self.http("GET", user_info_url)
                self._user_id = user_info.get("user_id")
            except Exception:
                # If userinfo fails, try to get from identity endpoint
                logger.debug("Could not fetch user info, user_id will be None")
                self._user_id = None

            # Cache the token
            token_data = {
                "session_id": session_id,
                "instance_url": instance_url,
                "expires_at": self._session_expires,
                "user_id": self._user_id,
            }
            self._token_cache.set(cache_key, token_data, ttl=7200)

            logger.info(f"Successfully logged in. Instance: {instance_url}")

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Login failed: {e}")

    def login_with_jwt(
        self, client_id: str, private_key: str, username: Optional[str] = None, audience: Optional[str] = None
    ) -> None:
        """Login using JWT bearer flow.

        Args:
            client_id: Connected app consumer key
            private_key: Private key content or path
            username: Salesforce username (uses self.username if not provided)
            audience: Token endpoint (auto-detected from base_url if not provided)
        """
        username = username or self.username
        if not username:
            raise AuthenticationError("Username required for JWT login")

        if audience is None:
            audience = self.get_login_url()

        logger.info(f"JWT login as {username} to {audience}")

        try:
            token_response = auth.jwt_login(
                client_id=client_id, private_key=private_key, username=username, audience=audience
            )

            self.session_id = token_response["access_token"]
            self.instance_url = token_response["instance_url"]

            self.session.headers["Authorization"] = f"Bearer {self.session_id}"

            logger.info(f"JWT login successful. Instance: {self.instance_url}")

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"JWT login failed: {e}")

    def _is_retryable_error(self, response: requests.Response) -> bool:
        """Check if error should trigger a retry.

        Args:
            response: HTTP response object

        Returns:
            True if error is retryable
        """
        # Retryable status codes
        if response.status_code in (502, 503):
            return True

        # Check for specific 500 errors
        if response.status_code == 500:
            try:
                error_data = response.json()
                error_msg = str(error_data).lower()
                # Retry on transient 500 errors
                if any(msg in error_msg for msg in ["unable to obtain", "timeout", "temporary"]):
                    return True
            except (ValueError, KeyError):
                pass

        # Check for UNABLE_TO_LOCK_ROW (400)
        if response.status_code == 400:
            try:
                error_data = response.json()
                if isinstance(error_data, list) and error_data:
                    error_code = error_data[0].get("errorCode", "")
                    if error_code == "UNABLE_TO_LOCK_ROW":
                        return True
            except (ValueError, KeyError, IndexError):
                pass

        return False

    def http(self, method: str, url: str, **kwargs) -> Any:
        """Make HTTP request with automatic retry logic.

        Automatically retries on:
        - 503 Service Unavailable
        - 502 Bad Gateway
        - 500 Internal Server Error (specific transient errors)
        - 400 with UNABLE_TO_LOCK_ROW
        - 429 Rate Limiting

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            url: URL path (relative to instance_url or absolute)
            **kwargs: Additional request kwargs (params, json, data, etc.)

        Returns:
            Response JSON or dict

        Raises:
            AuthenticationError: If not authenticated or session expired
            APIError: If request fails after all retries
        """

        if not self.session_id or not self.instance_url:
            raise AuthenticationError("Not authenticated. Call login() first.")

        # Track last request time
        self._last_request_time = time.time()

        # Build full URL
        if not url.startswith("http"):
            url = urljoin(self.instance_url, url)

        # Retry loop
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay
                        if self.retry_backoff:
                            wait_time *= 2**attempt
                        logger.warning(
                            f"Rate limited (429). Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        error_msg = parse_error_response(response)
                        raise APIError(
                            f"Rate limited (429) after {self.max_retries} retries: {error_msg}", status_code=429
                        )

                # Handle unauthorized (401)
                if response.status_code == 401:
                    raise AuthenticationError("Unauthorized (401). Session may have expired.")

                # Success (2xx)
                if 200 <= response.status_code < 300:
                    # Some endpoints return empty response (204 No Content)
                    if response.status_code == 204 or not response.content:
                        return {}

                    try:
                        return response.json()
                    except ValueError:
                        # Return text if not JSON
                        return response.text

                # Check if error is retryable
                if self._is_retryable_error(response) and attempt < self.max_retries:
                    wait_time = self.retry_delay
                    if self.retry_backoff:
                        wait_time *= 2**attempt

                    error_msg = parse_error_response(response)
                    logger.warning(
                        f"Retryable error ({response.status_code}): {error_msg}. "
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    continue

                # Non-retryable error
                error_msg = parse_error_response(response)
                raise APIError(
                    f"HTTP {response.status_code}: {error_msg}",
                    status_code=response.status_code,
                    response=response.json() if response.content else {},
                )

            except requests.RequestException as e:
                # Network errors are retryable
                if attempt < self.max_retries:
                    wait_time = self.retry_delay
                    if self.retry_backoff:
                        wait_time *= 2**attempt
                    logger.warning(
                        f"Request failed: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                raise APIError(f"Request failed after {self.max_retries} retries: {e}")

        # Should not reach here, but just in case
        raise APIError(f"Request failed after {self.max_retries} retries")

    def query(self, soql: str, expand_select_star: bool = False, **kwargs) -> SobjectSet:
        """Execute SOQL query.

        Args:
            soql: SOQL query string
            expand_select_star: Auto-expand SELECT * to all fields (default: False)
            **kwargs: Additional query parameters

        Returns:
            SobjectSet of results with pagination metadata

        Example:
            >>> # Basic query
            >>> results = sf.query("SELECT Id, Name FROM Account LIMIT 10")

            >>> # With SELECT * expansion
            >>> results = sf.query("SELECT * FROM Account LIMIT 5", expand_select_star=True)

            >>> # Access pagination info
            >>> if not results.done:
            ...     print(f"More records available: {results.next_records_url}")
        """
        # Expand SELECT * if requested
        if expand_select_star and "SELECT *" in soql.upper():
            from .query_advanced import expand_select_star as expand_fn

            soql = expand_fn(soql, self.describe)

        url = f"/services/data/v{self.version}/query/"
        params = {"q": soql}
        params.update(kwargs)

        try:
            response = self.http("GET", url, params=params)

            # Convert to Sobject instances
            records = SobjectSet()
            for record_data in response.get("records", []):
                record = Sobject(record_data)
                records.append(record)

            # Store pagination metadata
            records.next_records_url = response.get("nextRecordsUrl")
            records.done = response.get("done", True)
            records.total_size = response.get("totalSize")

            return records

        except APIError as e:
            raise QueryError(f"Query failed: {e}")

    def query_more(self, next_records_url: str) -> SobjectSet:
        """Fetch next page of query results.

        Args:
            next_records_url: URL from previous query's next_records_url

        Returns:
            SobjectSet of results with pagination metadata

        Example:
            >>> results = sf.query("SELECT Id FROM Account LIMIT 2000")
            >>> while not results.done:
            ...     results = sf.query_more(results.next_records_url)
            ...     process(results)
        """
        try:
            # nextRecordsUrl is a full path like /services/data/v53.0/query/01gxx-xxx
            response = self.http("GET", next_records_url)

            # Convert to Sobject instances
            records = SobjectSet()
            for record_data in response.get("records", []):
                record = Sobject(record_data)
                records.append(record)

            # Store pagination metadata
            records.next_records_url = response.get("nextRecordsUrl")
            records.done = response.get("done", True)
            records.total_size = response.get("totalSize")

            return records

        except APIError as e:
            raise QueryError(f"Query pagination failed: {e}")

    def iterquery(self, soql: str, batch_size: int = 2000, threaded: bool = False):
        """Execute SOQL query with pagination, yielding pages of results.

        Yields pages (SobjectSet) instead of individual records for efficient processing.
        Optionally prefetches the next page in background when threaded=True.

        Args:
            soql: SOQL query string
            batch_size: Records per batch (default: 2000)
            threaded: Enable background prefetching of next page (default: False)

        Yields:
            SobjectSet pages of results

        Example:
            >>> # Basic iteration (yields pages)
            >>> for page in sf.iterquery("SELECT Id, Name FROM Account"):
            ...     for record in page:
            ...         print(record.Name)

            >>> # With threading (prefetch next page)
            >>> for page in sf.iterquery("SELECT Id FROM Case", threaded=True):
            ...     process_page(page)  # Next page loads in background
        """
        import queue
        import threading as thread_module

        if not threaded:
            # Simple non-threaded iteration
            url = f"/services/data/v{self.version}/query/"
            params = {"q": soql}

            while url:
                try:
                    response = self.http("GET", url, params=params)

                    # Convert to SobjectSet page
                    page = SobjectSet()
                    for record_data in response.get("records", []):
                        page.append(Sobject(record_data))

                    # Store pagination metadata
                    page.next_records_url = response.get("nextRecordsUrl")
                    page.done = response.get("done", True)
                    page.total_size = response.get("totalSize")

                    yield page

                    # Get next batch URL
                    url = response.get("nextRecordsUrl")
                    params = {}  # Next URL is complete

                except APIError as e:
                    raise QueryError(f"Query iteration failed: {e}")

        else:
            # Threaded iteration with prefetching
            result_queue: queue.Queue = queue.Queue(maxsize=1)
            stop_event = thread_module.Event()
            exception_holder = [None]

            def fetch_worker():
                """Background worker to fetch pages."""
                try:
                    url = f"/services/data/v{self.version}/query/"
                    params = {"q": soql}

                    while url and not stop_event.is_set():
                        response = self.http("GET", url, params=params)

                        # Convert to SobjectSet page
                        page = SobjectSet()
                        for record_data in response.get("records", []):
                            page.append(Sobject(record_data))

                        # Store pagination metadata
                        page.next_records_url = response.get("nextRecordsUrl")
                        page.done = response.get("done", True)
                        page.total_size = response.get("totalSize")

                        # Put page in queue (blocks if full)
                        if not stop_event.is_set():
                            result_queue.put(page)

                        # Get next batch URL
                        url = response.get("nextRecordsUrl")
                        params = {}  # Next URL is complete

                    # Signal completion
                    result_queue.put(None)

                except Exception as e:
                    exception_holder[0] = e
                    result_queue.put(None)

            # Start background thread
            worker = thread_module.Thread(target=fetch_worker, daemon=True)
            worker.start()

            try:
                while True:
                    # Get next page from queue
                    page = result_queue.get()

                    # Check for exception
                    if exception_holder[0]:
                        raise QueryError(f"Query iteration failed: {exception_holder[0]}")

                    # Check for completion
                    if page is None:
                        break

                    yield page

            finally:
                # Signal worker to stop
                stop_event.set()
                # Wait for worker to finish (with timeout)
                worker.join(timeout=5.0)

    def composite(self, all_or_none: bool = False) -> CompositeRequest:
        """Create a composite request for batch operations.

        Args:
            all_or_none: If True, all subrequests must succeed or all fail

        Returns:
            CompositeRequest builder

        Example:
            >>> composite = sf.composite(all_or_none=True)
            >>> composite.post(f'/services/data/v{sf.version}/sobjects/Account',
            ...                'NewAccount', body={'Name': 'Test'})
            >>> composite.get(f'/services/data/v{sf.version}/sobjects/Account/@{{NewAccount.id}}',
            ...               'GetAccount')
            >>> response = composite.execute()
            >>> print(response['GetAccount'].body['Name'])
        """
        return CompositeRequest(self, all_or_none=all_or_none)

    def describe(self, sobject_name: str, use_cache: bool = True) -> ObjectDescribe:
        """Get metadata description for an sobject.

        Args:
            sobject_name: Name of the sobject (e.g., 'Account', 'Contact')
            use_cache: Use cached describe if available (default: True)

        Returns:
            ObjectDescribe with full metadata

        Example:
            >>> describe = sf.describe('Account')
            >>> print(f"Account has {len(describe.fields)} fields")
            >>> name_field = describe.get_field('Name')
            >>> print(f"Name field is required: {name_field.is_required}")
        """
        # Check cache first
        if use_cache and sobject_name in self._describe_cache:
            logger.debug(f"Using cached describe for {sobject_name}")
            return self._describe_cache.get(sobject_name)

        logger.debug(f"Fetching describe for {sobject_name}")
        url = f"/services/data/v{self.version}/sobjects/{sobject_name}/describe"
        response = self.http("GET", url)

        describe = ObjectDescribe(response)
        self._describe_cache.set(sobject_name, describe)

        return describe

    def describe_global(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """Get list of all available sobjects.

        Args:
            use_cache: Use cached result if available (default: True)

        Returns:
            List of sobject metadata (name, label, etc.)

        Example:
            >>> sobjects = sf.describe_global()
            >>> print(f"Found {len(sobjects)} sobjects")
            >>> account = next(s for s in sobjects if s['name'] == 'Account')
            >>> print(f"Account label: {account['label']}")
        """
        if use_cache and "__global__" in self._describe_cache:
            cached = self._describe_cache.get("__global__")
            if cached:
                return cached.get("sobjects", [])

        logger.debug("Fetching global describe")
        url = f"/services/data/v{self.version}/sobjects"
        response = self.http("GET", url)

        # Cache the raw response
        if use_cache:
            self._describe_cache.set("__global__", ObjectDescribe(response))

        return response.get("sobjects", [])

    def get_limits(self) -> dict[str, Any]:
        """Get org limits and usage.

        Returns:
            Dict of org limits (API calls, DML, etc.)

        Example:
            >>> limits = sf.get_limits()
            >>> api_limit = limits['DailyApiRequests']
            >>> print(f"API calls: {api_limit['Remaining']}/{api_limit['Max']}")
        """
        url = f"/services/data/v{self.version}/limits"
        return self.http("GET", url)

    def get_picklist_values(
        self, sobject_name: str, field_name: str, controlling_value: str = None, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get picklist values, optionally filtered by controlling field value.

        For dependent picklists, provide controlling_value to get only valid values.

        Args:
            sobject_name: Name of the sobject (e.g., 'Case', 'Account')
            field_name: Name of the picklist field
            controlling_value: Value of controlling field (for dependent picklists)
            active_only: Only return active values (default: True)

        Returns:
            List of picklist value dicts with 'value', 'label', 'active', etc.

        Example:
            >>> # Simple picklist
            >>> values = sf.get_picklist_values('Account', 'Industry')
            >>> print([v['value'] for v in values])

            >>> # Dependent picklist
            >>> values = sf.get_picklist_values(
            ...     'Case',
            ...     'Sub_Category__c',
            ...     controlling_value='Hardware'
            ... )
        """
        describe = self.describe(sobject_name)

        if controlling_value:
            return describe.get_dependent_picklist_values(
                field_name, controlling_value=controlling_value, active_only=active_only
            )
        else:
            return describe.get_picklist_values(field_name, active_only=active_only)

    def get_workbench_url(self, soql: str) -> str:
        """Generate Workbench URL for a SOQL query.

        Args:
            soql: SOQL query

        Returns:
            Workbench URL with pre-filled query

        Example:
            >>> url = sf.get_workbench_url("SELECT Id, Name FROM Account")
            >>> print(url)
            >>> # Open in browser: webbrowser.open(url)
        """
        return self.workbench_config.generate_url(soql, self.instance_url)

    def set_workbench_url(self, base_url: str) -> None:
        """Set custom Workbench base URL.

        Use this for self-hosted Workbench instances.

        Args:
            base_url: Base Workbench URL (e.g., "https://workbench.company.com")

        Example:
            >>> sf.set_workbench_url("https://workbench.mycompany.com")
            >>> url = sf.get_workbench_url("SELECT Id FROM Account")
        """
        self.workbench_config = WorkbenchConfig(base_url)

    def compile_where_clause(self, **kwargs) -> str:
        """Build WHERE clause from kwargs with __ operators.

        Supports: __in, __gt, __lt, __gte, __lte, __ne, __contains, __startswith, __endswith

        Args:
            **kwargs: Field filters with optional __ operators

        Returns:
            SOQL WHERE clause string

        Example:
            >>> clause = sf.compile_where_clause(
            ...     Status='New',
            ...     Priority__in=['High', 'Critical'],
            ...     CreatedDate__gte='2024-01-01'
            ... )
            >>> query = f"SELECT Id FROM Case WHERE {clause}"
        """
        from .query_helpers import compile_where_clause

        return compile_where_clause(**kwargs)

    def get_object_type_from_id(self, record_id: str) -> Optional[str]:
        """Determine Salesforce object type from a record ID.

        Uses the key prefix (first 3 characters) to identify the object type.
        Requires an API call to fetch global describe on first use (cached thereafter).

        Args:
            record_id: 15 or 18 character Salesforce record ID

        Returns:
            Object API name (e.g., 'Account', 'Contact') or None if not found

        Raises:
            ValueError: If record_id is invalid (not 15 or 18 chars alphanumeric)

        Example:
            >>> obj_type = sf.get_object_type_from_id('001B000001234567')
            >>> print(obj_type)  # 'Account'

            >>> obj_type = sf.get_object_type_from_id('003B000001234567')
            >>> print(obj_type)  # 'Contact'

            >>> obj_type = sf.get_object_type_from_id('a07B000001234567')
            >>> print(obj_type)  # 'WorkItem__c' (custom object)
        """
        # Basic validation: must be 15 or 18 characters, alphanumeric
        if not isinstance(record_id, str) or len(record_id) not in (15, 18):
            raise ValueError(f"Invalid Salesforce ID: {record_id} (must be 15 or 18 characters)")

        if not record_id.isalnum():
            raise ValueError(f"Invalid Salesforce ID: {record_id} (must be alphanumeric)")

        # Extract key prefix (first 3 characters)
        key_prefix = record_id[:3]

        # Get all sobjects (cached after first call)
        sobjects = self.describe_global(use_cache=True)

        # Find object with matching key prefix
        for sobject in sobjects:
            if sobject.get("keyPrefix") == key_prefix:
                return sobject["name"]

        return None

    def list_objects(
        self,
        custom_only: bool = False,
        queryable_only: bool = False,
        createable_only: bool = False,
        pattern: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get a filtered list of Salesforce objects.

        Helper method to make it easier for newcomers to explore available objects.

        Args:
            custom_only: If True, only return custom objects (default: False)
            queryable_only: If True, only return queryable objects (default: False)
            createable_only: If True, only return createable objects (default: False)
            pattern: Optional regex pattern to filter object names (case-insensitive)

        Returns:
            List of object metadata dicts

        Example:
            >>> # Get all queryable objects
            >>> objects = sf.list_objects(queryable_only=True)
            >>> print(f"Found {len(objects)} queryable objects")

            >>> # Get custom objects only
            >>> custom = sf.list_objects(custom_only=True)
            >>> for obj in custom:
            ...     print(f"{obj['name']} - {obj['label']}")

            >>> # Find objects matching pattern
            >>> cases = sf.list_objects(pattern='.*case.*')

            >>> # Combine filters
            >>> custom_queryable = sf.list_objects(custom_only=True, queryable_only=True)
        """
        import re

        sobjects = self.describe_global(use_cache=True)

        # Apply filters
        if custom_only:
            sobjects = [s for s in sobjects if s.get("custom", False)]

        if queryable_only:
            sobjects = [s for s in sobjects if s.get("queryable", False)]

        if createable_only:
            sobjects = [s for s in sobjects if s.get("createable", False)]

        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            sobjects = [s for s in sobjects if regex.search(s["name"])]

        return sobjects

    def print_objects(
        self,
        custom_only: bool = False,
        queryable_only: bool = False,
        createable_only: bool = False,
        pattern: Optional[str] = None,
        limit: int = 50,
    ) -> None:
        """Print a human-readable list of Salesforce objects.

        Convenience method for interactive exploration.

        Args:
            custom_only: If True, only show custom objects
            queryable_only: If True, only show queryable objects
            createable_only: If True, only show createable objects
            pattern: Optional regex pattern to filter object names
            limit: Maximum number of objects to print (default: 50)

        Example:
            >>> # Show first 20 custom objects
            >>> sf.print_objects(custom_only=True, limit=20)

            >>> # Show all queryable standard objects
            >>> sf.print_objects(queryable_only=True, custom_only=False)

            >>> # Find account-related objects
            >>> sf.print_objects(pattern='.*account.*', limit=10)
        """
        objects = self.list_objects(
            custom_only=custom_only,
            queryable_only=queryable_only,
            createable_only=createable_only,
            pattern=pattern,
        )

        total = len(objects)
        displayed = min(total, limit)

        print(f"\n{'Name':<40} {'Label':<40} {'Custom':<8} {'Queryable':<10}")
        print("-" * 100)

        for obj in objects[:limit]:
            name = obj["name"]
            label = obj.get("label", "")
            custom = "Yes" if obj.get("custom", False) else "No"
            queryable = "Yes" if obj.get("queryable", False) else "No"

            print(f"{name:<40} {label:<40} {custom:<8} {queryable:<10}")

        if total > limit:
            print(f"\n... and {total - displayed} more (showing {displayed}/{total})")
        else:
            print(f"\nTotal: {total} object(s)")

    def prettyprint(self, query: str) -> str:
        """Pretty print SOQL query.

        Args:
            query: SOQL query to format

        Returns:
            Formatted SOQL query

        Example:
            >>> formatted = sf.prettyprint("SELECT Id,Name FROM Account WHERE Status='Active'")
            >>> print(formatted)
        """
        from .query_helpers import prettyprint_soql

        return prettyprint_soql(query)

    def equal(self, id1: str, id2: str) -> bool:
        """Compare Salesforce IDs (handles 15 vs 18 character).

        Args:
            id1: First Salesforce ID
            id2: Second Salesforce ID

        Returns:
            True if IDs are equal

        Example:
            >>> sf.equal('005B0000000hMtx', '005B0000000hMtxIAI')
            True
        """
        from .id_utils import compare_ids

        return compare_ids(id1, id2)

    def isin(self, salesforce_id: str, id_list: list[str]) -> bool:
        """Check if ID is in list (handles 15/18 char comparison).

        Args:
            salesforce_id: Salesforce ID to check
            id_list: List of Salesforce IDs

        Returns:
            True if ID is in list

        Example:
            >>> sf.isin('005B0000000hMtx', ['005B0000000hMtxIAI', '005B0000000abc'])
            True
        """
        from .id_utils import id_in_list

        return id_in_list(salesforce_id, id_list)

    @property
    def is_sandbox(self) -> bool:
        """Check if connected to sandbox.

        Returns:
            True if sandbox, False if production

        Example:
            >>> if sf.is_sandbox:
            ...     print("Connected to sandbox")
        """
        if not self.instance_url:
            return False
        # Sandbox URLs contain .sandbox. or cs/gs prefixes for scratch orgs
        return (
            ".sandbox." in self.instance_url
            or self.instance_url.startswith("https://cs")
            or self.instance_url.startswith("https://gs")
        )

    @property
    def user_id(self) -> Optional[str]:
        """Get the current user's Salesforce ID.

        Returns:
            User ID or None if not available

        Example:
            >>> print(f"Logged in as: {sf.user_id}")
        """
        return self._user_id

    @property
    def session_expires(self) -> Optional[float]:
        """Get session expiration timestamp (Unix time).

        Returns:
            Expiration timestamp or None if not available

        Example:
            >>> import datetime
            >>> if sf.session_expires:
            ...     expires = datetime.datetime.fromtimestamp(sf.session_expires)
            ...     print(f"Session expires: {expires}")
        """
        return self._session_expires

    @property
    def last_request_time(self) -> Optional[float]:
        """Get timestamp of last API request (Unix time).

        Returns:
            Last request timestamp or None if no requests made

        Example:
            >>> import datetime
            >>> if sf.last_request_time:
            ...     last = datetime.datetime.fromtimestamp(sf.last_request_time)
            ...     print(f"Last request: {last}")
        """
        return self._last_request_time

    @property
    def sobjects(self) -> DynamicEndpoint:
        """Access sobjects via dynamic endpoint.

        Example:
            >>> sf.sobjects.Account['001xx000003DGbQAAW'].get()
            >>> sf.sobjects.Case.post(Subject='Test', Priority='High')
        """
        return DynamicEndpoint(self, ["sobjects"])

    def __getattr__(self, name: str):
        """Enable dynamic endpoint access from client root.
        
        Automatically routes SObject names (capitalized or ending in __c) 
        to /sobjects/ endpoint for user-friendly access like sf.Account
        instead of sf.sobjects.Account.
        """
        # Special handling for bulk property (lazy initialization)
        if name == "bulk":
            # Avoid infinite recursion by checking __dict__ directly
            if "_bulk_api" not in self.__dict__:
                from .bulk import BulkAPI

                self._bulk_api = BulkAPI(self)
            return self._bulk_api
        
        # Auto-detect SObject names (like sfdcutils and simple-salesforce)
        # - Starts with uppercase letter (e.g., Account, Case, Contact)
        # - OR ends with __c (custom objects)
        if name[0].isupper() or name.endswith('__c'):
            return DynamicEndpoint(self, ["sobjects", name])
        
        # Other attributes go to root
        return DynamicEndpoint(self, [name])

    def __enter__(self) -> "Salesforce":
        """Enter context manager for composite batch operations.

        Example:
            >>> with sf as batch:
            ...     batch.sobjects.Account.post(Name='Account 1')
            ...     batch.sobjects.Account.post(Name='Account 2')
            ...     batch.sobjects.Contact['contact-id'].patch(LastName='Smith')
            >>> # Automatically executes as composite request on exit
        """
        self._batch_mode = True
        self._batch_requests = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and execute batched composite request.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised

        Returns:
            False to propagate exceptions
        """
        try:
            if exc_type is None and self._batch_requests:
                # No exception, execute the composite request
                logger.info(f"Executing composite batch with {len(self._batch_requests)} requests")
                composite_response = self.http(
                    "POST",
                    f"/services/data/v{self.version}/composite",
                    json={"allOrNone": False, "compositeRequest": self._batch_requests},
                )
                return composite_response
        finally:
            # Always reset batch mode
            self._batch_mode = False
            self._batch_requests = []

        return False  # Propagate exceptions

    def __repr__(self) -> str:
        return f"<Salesforce instance_url={self.instance_url} version={self.version}>"
