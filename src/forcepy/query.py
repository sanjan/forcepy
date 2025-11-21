"""SOQL query building utilities for forcepy."""

import datetime
from typing import Any, Union

UNSET = "*UNSET*"


def parse_datetime(value: str) -> datetime.datetime:
    """Parse Salesforce datetime string.

    Args:
        value: ISO format datetime string

    Returns:
        datetime object
    """
    value = value.rsplit(".", 1)[0]
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def format_datetime(date: Union[datetime.datetime, datetime.date]) -> str:
    """Format datetime for SOQL.

    Args:
        date: datetime or date object

    Returns:
        SOQL formatted datetime string
    """
    if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        strdate = date.isoformat() + "T00:00:00"
    elif hasattr(date, "tzinfo") and date.tzinfo not in (None, datetime.timezone.utc):
        raise ValueError(f"Date {date} is not in UTC")
    else:
        strdate = date.replace(tzinfo=None).isoformat(timespec="seconds")
    return strdate + ".0000Z"


def IN(values: Union[list, tuple, set]) -> str:
    """Format values for SOQL IN clause.

    Args:
        values: Collection of values

    Returns:
        SOQL IN clause formatted string
    """
    return str(tuple(set(values))).replace(",)", ")").replace("', '", "','")


def DATE(value: Union[datetime.datetime, datetime.date]) -> str:
    """Format date for SOQL.

    Args:
        value: datetime or date object

    Returns:
        SOQL formatted date string
    """
    return format_datetime(value)


def BOOL(value: bool) -> str:
    """Format boolean for SOQL.

    Args:
        value: Boolean value

    Returns:
        'true' or 'false'
    """
    return "true" if value else "false"


class Q:
    """Query object for building complex SOQL WHERE clauses.

    Supports boolean operators:
    - & (AND)
    - | (OR)
    - ~ (NOT)

    Example:
        >>> q = (Q(Status='New') | Q(Status='In Progress')) & Q(Priority='High')
        >>> q.compile()
        "((Status = 'New') OR (Status = 'In Progress')) AND Priority = 'High'"
    """

    def __init__(self, *args: Any, **query: Any):
        if args and query:
            raise ValueError("Cannot use both positional and keyword arguments")
        self.query = args if args else query

    def __or__(self, other: "Q") -> "Q":
        """OR operator (|)."""
        return type(self)(self, "OR", other)

    def __and__(self, other: "Q") -> "Q":
        """AND operator (&)."""
        return type(self)(self, "AND", other)

    def __invert__(self) -> "Q":
        """NOT operator (~)."""
        return type(self)("NOT", self)

    def compile(self) -> str:
        """Compile Q object to SOQL WHERE clause.

        Returns:
            SOQL WHERE clause string
        """
        if isinstance(self.query, dict):
            return compile_where_clause(wrap=True, **self.query)

        words = []
        for part in self.query:
            if isinstance(part, type(self)):
                words.append(part.compile())
            else:
                words.append(str(part))
        return "({})".format(" ".join(words))

    def __str__(self) -> str:
        return f"Q{self.query}"

    def __repr__(self) -> str:
        return str(self)


def compile_key_value(name: str, value: Any) -> str:
    """Compile a single field-value pair to SOQL.

    Args:
        name: Field name with optional lookup suffix
        value: Field value

    Returns:
        SOQL condition string
    """
    if value == UNSET:
        return ""

    statement = []

    # Handle special operators
    if name.endswith("__OR"):
        return "({})".format(" OR ".join(compile_key_value(*args) for args in value))
    elif name.endswith("__AND"):
        return "({})".format(" AND ".join(compile_key_value(*args) for args in value))

    # Parse field name and operator
    for part in name.split("__"):
        if part in ("c", "r") or part.startswith(("c.", "r.")):
            # SOQL relationship notation
            statement[-1] += f"__{part}"
        else:
            if statement:
                lpart = part.lower()
                if lpart == "ne":
                    part = "!="
                elif lpart in ("gt", "gte"):
                    part = ">" + ("=" if lpart == "gte" else "")
                elif lpart in ("lt", "lte"):
                    part = "<" + ("=" if lpart == "lte" else "")
                elif lpart == "ni":
                    part = "NOT IN"
                elif lpart == "like":
                    part = "LIKE"
                elif lpart == "in":
                    part = "IN"
                elif lpart in ("includes", "excludes"):
                    part = lpart.upper()
                else:
                    # Nested field
                    statement[-1] += f".{part}"
                    continue
            statement.append(part)

    # Add equals operator if no operator specified
    if len(statement) == 1:
        statement.append("=")

    # Format value
    if isinstance(value, (list, tuple, set)):
        value = IN(value)
    elif isinstance(value, (datetime.datetime, datetime.date)):
        value = DATE(value)
    elif isinstance(value, str):
        value = f"'{value}'"
    elif isinstance(value, bool):
        value = BOOL(value)
    elif value is None:
        value = "null"
    else:
        value = str(value)

    statement.append(value)
    return " ".join(statement)


def compile_where_clause(*args: Q, wrap: bool = False, **kwargs: Any) -> str:
    """Compile WHERE clause from Q objects and kwargs.

    Args:
        *args: Q objects
        wrap: Wrap in parentheses if multiple statements
        **kwargs: Field-value pairs

    Returns:
        SOQL WHERE clause string
    """
    statements = []

    if len(args) > 1 or (args and not isinstance(args[0], Q)):
        raise TypeError(f"Argument must be a single Q() object: {args}")

    if args:
        statement = args[0].compile()
        if kwargs:
            statement = f"({statement})"
        statements.append(statement)

    for name, value in kwargs.items():
        compiled = compile_key_value(name, value)
        if compiled:
            statements.append(compiled)

    result = " AND ".join(statements)
    if wrap and len(statements) > 1:
        result = f"({result})"

    return result


def select(
    *args: Q, sobject: str, fields: Union[str, list[str]], order_by: str = "", limit: int = 0, **where: Any
) -> str:
    """Build a complete SOQL query.

    Args:
        *args: Q objects for WHERE clause
        sobject: Salesforce object name
        fields: Fields to select (string or list)
        order_by: Field to order by (prefix with - for DESC)
        limit: LIMIT clause value
        **where: Field-value pairs for WHERE clause

    Returns:
        Complete SOQL query string
    """
    if not isinstance(fields, str):
        fields = ", ".join(fields)

    where_clause = compile_where_clause(*args, **where)

    clauses = [
        f"SELECT {fields}",
        f"FROM {sobject}",
    ]

    if where_clause:
        clauses.append(f"WHERE {where_clause}")

    if order_by:
        direction = "DESC" if order_by.startswith("-") else "ASC"
        order_by = order_by.lstrip("-")
        clauses.append(f"ORDER BY {order_by} {direction}")

    if limit:
        clauses.append(f"LIMIT {limit}")

    return "\n".join(clauses)
