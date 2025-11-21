"""Query building helpers for forcepy.

Provides utilities for building SOQL WHERE clauses with operators.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def compile_where_clause(**kwargs) -> str:
    """Build WHERE clause from kwargs with __ operators.

    Supports operators:
    - __in: IN clause
    - __gt: Greater than
    - __lt: Less than
    - __gte: Greater than or equal
    - __lte: Less than or equal
    - __ne: Not equal
    - __contains: LIKE %value%
    - __startswith: LIKE value%
    - __endswith: LIKE %value
    - (no operator): Equality

    Args:
        **kwargs: Field filters with optional __ operators

    Returns:
        SOQL WHERE clause string

    Example:
        >>> clause = compile_where_clause(
        ...     Status='New',
        ...     Priority__in=['High', 'Critical'],
        ...     CreatedDate__gte='2024-01-01T00:00:00.000Z'
        ... )
        >>> print(clause)
        Status='New' AND Priority IN ('High','Critical') AND CreatedDate>='2024-01-01T00:00:00.000Z'
    """
    if not kwargs:
        return ""

    from .query import IN

    conditions = []

    for key, value in kwargs.items():
        # Parse field and operator
        if "__" in key:
            field, operator = key.rsplit("__", 1)
        else:
            field = key
            operator = "eq"

        # Format value
        formatted_value = _format_value(value)

        # Build condition based on operator
        if operator == "in":
            # IN clause
            if not isinstance(value, (list, tuple)):
                value = [value]
            in_clause = IN(value)
            conditions.append(f"{field} IN {in_clause}")
        elif operator == "gt":
            conditions.append(f"{field}>{formatted_value}")
        elif operator == "lt":
            conditions.append(f"{field}<{formatted_value}")
        elif operator == "gte":
            conditions.append(f"{field}>={formatted_value}")
        elif operator == "lte":
            conditions.append(f"{field}<={formatted_value}")
        elif operator == "ne":
            conditions.append(f"{field}!={formatted_value}")
        elif operator == "contains":
            # LIKE with wildcards on both sides
            conditions.append(f"{field} LIKE '%{_escape_like(value)}%'")
        elif operator == "startswith":
            # LIKE with wildcard at end
            conditions.append(f"{field} LIKE '{_escape_like(value)}%'")
        elif operator == "endswith":
            # LIKE with wildcard at start
            conditions.append(f"{field} LIKE '%{_escape_like(value)}'")
        elif operator == "eq":
            # Equality
            conditions.append(f"{field}={formatted_value}")
        else:
            # Unknown operator, treat as field name with __
            full_field = f"{field}__{operator}"
            conditions.append(f"{full_field}={formatted_value}")

    return " AND ".join(conditions)


def _format_value(value: Any) -> str:
    """Format a value for SOQL.

    Args:
        value: Value to format

    Returns:
        Formatted string for SOQL
    """
    from .query import BOOL, format_datetime

    if value is None:
        return "null"
    elif isinstance(value, bool):
        return BOOL(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        return format_datetime(value)
    elif isinstance(value, str):
        # Escape single quotes
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
    else:
        # Try to convert to string
        escaped = str(value).replace("'", "\\'")
        return f"'{escaped}'"


def _escape_like(value: str) -> str:
    """Escape special characters for LIKE clause.

    Args:
        value: String to escape

    Returns:
        Escaped string
    """
    # Escape single quotes and LIKE wildcards
    value = str(value)
    value = value.replace("'", "\\'")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return value


def prettyprint_soql(query: str) -> str:
    """Pretty print SOQL query.

    Alias for format_soql from query_advanced module.

    Args:
        query: SOQL query to format

    Returns:
        Formatted SOQL query

    Example:
        >>> query = "SELECT Id,Name FROM Account WHERE Status='Active' ORDER BY Name"
        >>> print(prettyprint_soql(query))
        SELECT
          Id,
          Name
        FROM Account
        WHERE Status='Active'
        ORDER BY Name
    """
    from .query_advanced import format_soql

    return format_soql(query)

