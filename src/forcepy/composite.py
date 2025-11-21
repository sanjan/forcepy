"""Composite API support for forcepy.

Enables batch operations with up to 25 subrequests in a single API call.
"""

import logging
from typing import Any, Optional

from .exceptions import APIError

logger = logging.getLogger(__name__)


class CompositeError(APIError):
    """Exception raised when composite request fails."""

    def __init__(self, message: str, response: Any = None):
        """Initialize composite error.

        Args:
            message: Error message
            response: Full composite response
        """
        super().__init__(message)
        self.response = response


class CompositeResponse:
    """Wrapper for composite API response with helper methods."""

    def __init__(self, response: dict[str, Any]):
        """Initialize composite response.

        Args:
            response: Raw composite response from Salesforce
        """
        self._response = response
        self.composite_response = response.get("compositeResponse", [])

    def get(self, reference_id: str) -> Optional["CompositeSubResponse"]:
        """Get subrequest response by reference ID.

        Args:
            reference_id: Reference ID of the subrequest

        Returns:
            CompositeSubResponse or None if not found
        """
        for item in self.composite_response:
            if item.get("referenceId") == reference_id:
                return CompositeSubResponse(item)
        return None

    def __getitem__(self, reference_id: str) -> "CompositeSubResponse":
        """Get subrequest response by reference ID (dict-like access).

        Args:
            reference_id: Reference ID of the subrequest

        Returns:
            CompositeSubResponse

        Raises:
            KeyError: If reference ID not found
        """
        result = self.get(reference_id)
        if result is None:
            raise KeyError(f"Reference ID not found: {reference_id}")
        return result

    def all_succeeded(self) -> bool:
        """Check if all subrequests succeeded.

        Returns:
            True if all succeeded, False otherwise
        """
        return all(item.get("httpStatusCode", 0) < 300 for item in self.composite_response)

    def get_errors(self) -> list[dict[str, Any]]:
        """Get all error responses.

        Returns:
            List of error responses
        """
        errors = []
        for item in self.composite_response:
            if item.get("httpStatusCode", 0) >= 300:
                errors.append(
                    {
                        "referenceId": item.get("referenceId"),
                        "httpStatusCode": item.get("httpStatusCode"),
                        "body": item.get("body"),
                    }
                )
        return errors

    def __iter__(self):
        """Iterate over all subrequest responses."""
        return (CompositeSubResponse(item) for item in self.composite_response)

    def __len__(self):
        """Get number of subrequest responses."""
        return len(self.composite_response)

    def __repr__(self):
        return f"<CompositeResponse({len(self)} responses)>"


class CompositeSubResponse:
    """Single subrequest response from composite API."""

    def __init__(self, response: dict[str, Any]):
        """Initialize subrequest response.

        Args:
            response: Raw subrequest response
        """
        self._response = response
        self.reference_id = response.get("referenceId")
        self.http_status_code = response.get("httpStatusCode")
        self.http_headers = response.get("httpHeaders", {})
        self.body = response.get("body")

    def is_success(self) -> bool:
        """Check if subrequest succeeded.

        Returns:
            True if status code < 300
        """
        return self.http_status_code < 300

    def __repr__(self):
        return f"<CompositeSubResponse(ref={self.reference_id}, status={self.http_status_code})>"


class CompositeRequest:
    """Builder for composite API requests."""

    def __init__(self, client: Any, all_or_none: bool = False):
        """Initialize composite request builder.

        Args:
            client: Salesforce client instance
            all_or_none: If True, all subrequests must succeed or all fail
        """
        self.client = client
        self.all_or_none = all_or_none
        self.subrequests: list[dict[str, Any]] = []

    def add(
        self,
        method: str,
        url: str,
        reference_id: str,
        body: Optional[dict[str, Any]] = None,
        http_headers: Optional[dict[str, str]] = None,
    ) -> "CompositeRequest":
        """Add a subrequest to the composite request.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            url: Request URL (can use @{referenceId.field} for references)
            reference_id: Unique reference ID for this subrequest
            body: Request body (for POST/PATCH)
            http_headers: Optional HTTP headers

        Returns:
            Self for chaining

        Example:
            >>> composite = CompositeRequest(sf)
            >>> composite.add('POST', '/services/data/v53.0/sobjects/Account',
            ...               'NewAccount', body={'Name': 'Test'})
            >>> composite.add('GET', '/services/data/v53.0/sobjects/Account/@{NewAccount.id}',
            ...               'GetAccount')
        """
        subrequest: dict[str, Any] = {"method": method.upper(), "url": url, "referenceId": reference_id}

        if body is not None:
            subrequest["body"] = body

        if http_headers:
            subrequest["httpHeaders"] = http_headers

        self.subrequests.append(subrequest)
        return self

    def post(self, url: str, reference_id: str, body: dict[str, Any]) -> "CompositeRequest":
        """Add POST subrequest.

        Args:
            url: Request URL
            reference_id: Unique reference ID
            body: Request body

        Returns:
            Self for chaining
        """
        return self.add("POST", url, reference_id, body=body)

    def get(self, url: str, reference_id: str) -> "CompositeRequest":
        """Add GET subrequest.

        Args:
            url: Request URL
            reference_id: Unique reference ID

        Returns:
            Self for chaining
        """
        return self.add("GET", url, reference_id)

    def patch(self, url: str, reference_id: str, body: dict[str, Any]) -> "CompositeRequest":
        """Add PATCH subrequest.

        Args:
            url: Request URL
            reference_id: Unique reference ID
            body: Request body

        Returns:
            Self for chaining
        """
        return self.add("PATCH", url, reference_id, body=body)

    def delete(self, url: str, reference_id: str) -> "CompositeRequest":
        """Add DELETE subrequest.

        Args:
            url: Request URL
            reference_id: Unique reference ID

        Returns:
            Self for chaining
        """
        return self.add("DELETE", url, reference_id)

    def execute(self) -> CompositeResponse:
        """Execute the composite request.

        Returns:
            CompositeResponse with all subrequest results

        Raises:
            CompositeError: If allOrNone=True and any subrequest fails
            ValueError: If no subrequests added or too many (max 25)

        Example:
            >>> composite = CompositeRequest(sf, all_or_none=True)
            >>> composite.post('/services/data/v53.0/sobjects/Account', 'NewAccount',
            ...                body={'Name': 'Test'})
            >>> response = composite.execute()
            >>> print(response['NewAccount'].body['id'])
        """
        if not self.subrequests:
            raise ValueError("No subrequests added to composite request")

        if len(self.subrequests) > 25:
            raise ValueError(f"Too many subrequests: {len(self.subrequests)} (max 25)")

        # Count queries (max 5 queries per composite request)
        query_count = sum(1 for req in self.subrequests if req["method"] == "GET" and "/query" in req["url"])
        if query_count > 5:
            logger.warning(f"Composite request has {query_count} queries (max recommended: 5)")

        payload = {"allOrNone": self.all_or_none, "compositeRequest": self.subrequests}

        logger.debug(f"Executing composite request with {len(self.subrequests)} subrequests")

        url = f"/services/data/v{self.client.version}/composite"
        raw_response = self.client.http("POST", url, json=payload)

        response = CompositeResponse(raw_response)

        # If allOrNone=True, check for errors
        if self.all_or_none and not response.all_succeeded():
            errors = response.get_errors()
            error_msg = f"Composite request failed with {len(errors)} error(s)"
            raise CompositeError(error_msg, response=response)

        return response

    def __len__(self):
        """Get number of subrequests."""
        return len(self.subrequests)

    def __repr__(self):
        return f"<CompositeRequest({len(self)} subrequests)>"


def validate_composite_response(response: CompositeResponse, raise_on_error: bool = True) -> bool:
    """Validate composite response and optionally raise on errors.

    Args:
        response: CompositeResponse to validate
        raise_on_error: If True, raise CompositeError on any failures

    Returns:
        True if all succeeded, False otherwise

    Raises:
        CompositeError: If raise_on_error=True and any subrequest failed
    """
    if response.all_succeeded():
        return True

    if raise_on_error:
        errors = response.get_errors()
        error_details = []
        for error in errors:
            ref_id = error["referenceId"]
            status = error["httpStatusCode"]
            body = error.get("body", {})
            error_msg = body if isinstance(body, str) else body.get("message", body)
            error_details.append(f"  - {ref_id}: HTTP {status} - {error_msg}")

        error_message = f"Composite request had {len(errors)} failure(s):\n" + "\n".join(error_details)
        raise CompositeError(error_message, response=response)

    return False
