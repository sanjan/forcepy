"""Utility functions for forcepy."""

import base64
import re
from typing import Any, Optional

# Salesforce ID patterns
ID_15_PATTERN = re.compile(r"^[a-zA-Z0-9]{15}$")
ID_18_PATTERN = re.compile(r"^[a-zA-Z0-9]{18}$")


def is_salesforce_id(value: Any) -> bool:
    """Check if value is a valid Salesforce ID (15 or 18 characters).

    Args:
        value: Value to check

    Returns:
        True if value is a valid Salesforce ID
    """
    if not isinstance(value, str):
        return False
    return bool(ID_15_PATTERN.match(value) or ID_18_PATTERN.match(value))


def normalize_id(salesforce_id: str) -> str:
    """Normalize a Salesforce ID to 15 characters.

    Args:
        salesforce_id: 15 or 18 character Salesforce ID

    Returns:
        15 character ID

    Raises:
        ValueError: If ID is invalid
    """
    if not is_salesforce_id(salesforce_id):
        raise ValueError(f"Invalid Salesforce ID: {salesforce_id}")

    return salesforce_id[:15]


def build_url(*parts: str, base: Optional[str] = None) -> str:
    """Build a URL from parts.

    Args:
        *parts: URL path components
        base: Optional base URL

    Returns:
        Complete URL
    """
    if base:
        parts = (base.rstrip("/"),) + parts

    return "/".join(str(part).strip("/") for part in parts if part)


def parse_error_response(response: Any) -> str:
    """Parse error message from Salesforce response.

    Args:
        response: HTTP response object

    Returns:
        Error message string
    """
    try:
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            errors = response.json()
            if isinstance(errors, list) and errors:
                return errors[0].get("message", "Unknown error")
            elif isinstance(errors, dict):
                return errors.get("message", "Unknown error")

        elif "text/xml" in content_type:
            match = re.search(r"<faultstring>(.*?)</faultstring>", response.text, re.DOTALL)
            if match:
                return match.group(1)

        return response.text[:500]  # Limit error message length

    except Exception:
        return f"HTTP {response.status_code}: {response.reason}"


def decode_validfor_bitmap(validfor: str, controlling_index: int) -> bool:
    """Decode Salesforce validFor bitmap for dependent picklists.

    The validFor attribute contains a base64-encoded bitmap that indicates
    which controlling field values make this dependent value valid.

    Args:
        validfor: Base64-encoded validFor string from picklist value
        controlling_index: Index of the controlling picklist value

    Returns:
        True if this dependent value is valid for the controlling value

    Example:
        >>> # Check if dependent value is valid for controlling value at index 2
        >>> decode_validfor_bitmap('gAAA', 2)
        True
    """
    if not validfor:
        return False

    try:
        # Decode base64 to bytes
        decoded = base64.b64decode(validfor)

        # Calculate byte and bit position
        byte_index = controlling_index // 8
        bit_index = controlling_index % 8

        # Check if we have enough bytes
        if byte_index >= len(decoded):
            return False

        # Check if the bit is set (using big-endian bit ordering)
        byte_value = decoded[byte_index]
        return bool(byte_value & (1 << (7 - bit_index)))

    except Exception:
        return False
