"""Authentication module for forcepy."""

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

from .exceptions import AuthenticationError
from .utils import parse_error_response

logger = logging.getLogger(__name__)


def soap_login(
    username: str, password: str, login_url: str = "https://login.salesforce.com", version: str = "53.0"
) -> tuple[str, str]:
    """Authenticate using SOAP login.

    Args:
        username: Salesforce username
        password: Salesforce password (with security token appended if required)
        login_url: Login endpoint URL
        version: API version

    Returns:
        Tuple of (session_id, instance_url)

    Raises:
        AuthenticationError: If login fails
    """
    soap_url = f"{login_url}/services/Soap/u/{version}"

    headers = {"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "login"}

    body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:enterprise.soap.sforce.com/2005/09/outbound">
    <soapenv:Body>
        <urn:login>
            <urn:username>{username}</urn:username>
            <urn:password>{password}</urn:password>
        </urn:login>
    </soapenv:Body>
</soapenv:Envelope>"""

    try:
        response = requests.post(soap_url, data=body, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise AuthenticationError(f"SOAP login request failed: {e}")

    # Parse SOAP response
    try:
        root = ET.fromstring(response.content)

        # Check for fault
        fault = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
        if fault is not None:
            faultstring = fault.find(".//faultstring")
            error_msg = faultstring.text if faultstring is not None else "Unknown SOAP error"
            raise AuthenticationError(f"SOAP login failed: {error_msg}")

        # Extract session ID and server URL
        session_id_elem = root.find(".//{urn:enterprise.soap.sforce.com/2005/09/outbound}sessionId")
        server_url_elem = root.find(".//{urn:enterprise.soap.sforce.com/2005/09/outbound}serverUrl")

        if session_id_elem is None or server_url_elem is None:
            raise AuthenticationError("Invalid SOAP response: missing sessionId or serverUrl")

        session_id = session_id_elem.text
        server_url = server_url_elem.text

        # Extract instance URL from server URL
        # server_url format: https://instance.salesforce.com/services/Soap/u/53.0/orgId
        instance_url = "/".join(server_url.split("/")[:3])

        return session_id, instance_url

    except ET.ParseError as e:
        raise AuthenticationError(f"Failed to parse SOAP response: {e}")


def oauth_login(
    username: str, password: str, client_id: str, client_secret: str, login_url: str = "https://login.salesforce.com"
) -> dict[str, Any]:
    """Authenticate using OAuth2 password flow.

    Args:
        username: Salesforce username
        password: Salesforce password
        client_id: Connected app client ID
        client_secret: Connected app client secret
        login_url: Login endpoint URL

    Returns:
        Dict with access_token, instance_url, etc.

    Raises:
        AuthenticationError: If login fails
    """
    token_url = f"{login_url}/services/oauth2/token"

    data = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_msg = parse_error_response(response) if "response" in locals() else str(e)
        raise AuthenticationError(f"OAuth login failed: {error_msg}")


def jwt_login(
    client_id: str, private_key: str, username: str, audience: str = "https://login.salesforce.com"
) -> dict[str, Any]:
    """Authenticate using JWT bearer flow.

    Args:
        client_id: Connected app consumer key
        private_key: Private key content (PEM format) or path to key file
        username: Salesforce username
        audience: Token endpoint (use https://test.salesforce.com for sandbox)

    Returns:
        Dict with access_token, instance_url, etc.

    Raises:
        AuthenticationError: If login fails
        ImportError: If JWT dependencies not installed
    """
    try:
        import jwt as pyjwt
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        raise ImportError("JWT authentication requires PyJWT and cryptography. Install with: pip install forcepy[jwt]")

    # Load private key
    try:
        # Try to load as file path first
        try:
            with open(private_key, "rb") as f:
                key_content = f.read()
        except (FileNotFoundError, OSError):
            # Assume it's the key content itself
            key_content = private_key.encode() if isinstance(private_key, str) else private_key

        private_key_obj = serialization.load_pem_private_key(key_content, password=None, backend=default_backend())
    except Exception as e:
        raise AuthenticationError(f"Failed to load private key: {e}")

    # Build JWT claim set
    now = int(time.time())
    claim_set = {
        "iss": client_id,
        "sub": username,
        "aud": audience,
        "exp": now + 300,  # 5 minutes
    }

    # Sign JWT
    try:
        assertion = pyjwt.encode(claim_set, private_key_obj, algorithm="RS256")
    except Exception as e:
        raise AuthenticationError(f"Failed to sign JWT: {e}")

    # Exchange JWT for access token
    token_url = f"{audience}/services/oauth2/token"
    data = {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}

    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_msg = parse_error_response(response) if "response" in locals() else str(e)
        raise AuthenticationError(f"JWT bearer flow failed: {error_msg}")


def refresh_token(
    refresh_token: str, client_id: str, client_secret: str, login_url: str = "https://login.salesforce.com"
) -> dict[str, Any]:
    """Refresh an access token using a refresh token.

    Args:
        refresh_token: OAuth refresh token
        client_id: Connected app client ID
        client_secret: Connected app client secret
        login_url: Login endpoint URL

    Returns:
        Dict with new access_token and instance_url

    Raises:
        AuthenticationError: If refresh fails
    """
    token_url = f"{login_url}/services/oauth2/token"

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_msg = parse_error_response(response) if "response" in locals() else str(e)
        raise AuthenticationError(f"Token refresh failed: {error_msg}")
