"""Salesforce ID comparison utilities.

Handles comparison of 15 vs 18 character Salesforce IDs.
"""

import logging

logger = logging.getLogger(__name__)


def normalize_id(salesforce_id: str) -> str:
    """Normalize Salesforce ID to 15 characters for comparison.

    Salesforce IDs can be 15 or 18 characters. The first 15 are
    case-sensitive unique identifier, the last 3 are a checksum.

    Args:
        salesforce_id: 15 or 18 character Salesforce ID

    Returns:
        15 character ID (or original if not valid)

    Example:
        >>> normalize_id('005B0000000hMtxIAI')
        '005B0000000hMtx'
        >>> normalize_id('005B0000000hMtx')
        '005B0000000hMtx'
    """
    if not salesforce_id:
        return salesforce_id

    # If it's 18 characters, take first 15
    if len(salesforce_id) >= 15:
        return salesforce_id[:15]

    return salesforce_id


def compare_ids(id1: str, id2: str) -> bool:
    """Compare Salesforce IDs (handles 15 vs 18 character).

    Args:
        id1: First Salesforce ID
        id2: Second Salesforce ID

    Returns:
        True if IDs are equal (ignoring 15 vs 18 char difference)

    Example:
        >>> compare_ids('005B0000000hMtx', '005B0000000hMtxIAI')
        True
        >>> compare_ids('005B0000000hMtx', '005B0000000abc')
        False
    """
    # Handle None/empty cases
    if not id1 or not id2:
        return id1 == id2

    # Normalize and compare
    return normalize_id(id1) == normalize_id(id2)


def id_in_list(salesforce_id: str, id_list: list[str]) -> bool:
    """Check if ID is in list (handles 15/18 char comparison).

    Args:
        salesforce_id: Salesforce ID to check
        id_list: List of Salesforce IDs

    Returns:
        True if ID is in list (ignoring 15 vs 18 char difference)

    Example:
        >>> id_in_list('005B0000000hMtx', ['005B0000000hMtxIAI', '005B0000000abc'])
        True
        >>> id_in_list('005B0000000xyz', ['005B0000000hMtxIAI', '005B0000000abc'])
        False
    """
    if not salesforce_id:
        return False

    if not id_list:
        return False

    normalized = normalize_id(salesforce_id)
    return any(normalize_id(id_item) == normalized for id_item in id_list if id_item)


def is_valid_id(salesforce_id: str) -> bool:
    """Check if string is a valid Salesforce ID format.

    Args:
        salesforce_id: String to validate

    Returns:
        True if valid 15 or 18 character Salesforce ID format

    Example:
        >>> is_valid_id('005B0000000hMtx')
        True
        >>> is_valid_id('005B0000000hMtxIAI')
        True
        >>> is_valid_id('invalid')
        False
    """
    if not salesforce_id:
        return False

    # Must be 15 or 18 characters
    if len(salesforce_id) not in (15, 18):
        return False

    # Must be alphanumeric
    if not salesforce_id.isalnum():
        return False

    return True

