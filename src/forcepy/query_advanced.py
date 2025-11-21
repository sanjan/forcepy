"""Advanced query features for forcepy.

Provides utilities for SELECT * expansion, workbench URL generation, and more.
"""

import logging
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


def expand_select_star(soql: str, describe_func, sobject_name: Optional[str] = None) -> str:
    """Expand SELECT * to all fields.

    Args:
        soql: SOQL query with SELECT *
        describe_func: Function to get object describe (e.g., sf.describe)
        sobject_name: Object name if not detectable from query

    Returns:
        SOQL with * expanded to all field names

    Example:
        >>> expanded = expand_select_star("SELECT * FROM Account WHERE Name LIKE 'A%'", sf.describe)
        >>> print(expanded)
        SELECT Id, Name, Industry, ... FROM Account WHERE Name LIKE 'A%'
    """
    if "*" not in soql:
        return soql

    # Extract object name from FROM clause
    if sobject_name is None:
        sobject_name = _extract_sobject_from_query(soql)
        if not sobject_name:
            raise ValueError("Could not determine sobject from query. Provide sobject_name parameter.")

    # Get describe
    describe = describe_func(sobject_name)

    # Get all queryable field names
    field_names = [
        f.get("name")
        for f in describe.fields
        if f.get("name") not in ("attributes",)  # Skip special fields
    ]

    # Replace * with field list
    fields_str = ", ".join(field_names)
    expanded = soql.replace("SELECT *", f"SELECT {fields_str}", 1)

    logger.debug(f"Expanded SELECT * to {len(field_names)} fields for {sobject_name}")

    return expanded


def _extract_sobject_from_query(soql: str) -> Optional[str]:
    """Extract sobject name from SOQL query.

    Args:
        soql: SOQL query

    Returns:
        Sobject name or None
    """
    soql_upper = soql.upper()
    from_idx = soql_upper.find(" FROM ")
    if from_idx == -1:
        return None

    # Get text after FROM
    after_from = soql[from_idx + 6 :].strip()

    # Get first word (sobject name)
    words = after_from.split()
    if not words:
        return None

    sobject_name = words[0].strip()

    # Remove any trailing characters (WHERE, ORDER, etc.)
    for keyword in (" WHERE", " ORDER", " GROUP", " LIMIT", " OFFSET", " FOR"):
        if keyword in sobject_name.upper():
            sobject_name = sobject_name[: sobject_name.upper().index(keyword)]

    return sobject_name.strip()


def generate_workbench_url(
    soql: str, instance_url: str, base_workbench_url: str = "https://workbench.developerforce.com"
) -> str:
    """Generate Workbench URL for a SOQL query.

    Args:
        soql: SOQL query
        instance_url: Salesforce instance URL (e.g., https://na1.salesforce.com)
        base_workbench_url: Base Workbench URL (default: https://workbench.developerforce.com)
            - Can be customized for self-hosted Workbench instances
            - Examples:
                - "https://workbench.developerforce.com" (official)
                - "https://your-workbench.company.com" (self-hosted)

    Returns:
        Workbench URL with pre-filled query

    Example:
        >>> url = generate_workbench_url(
        ...     "SELECT Id, Name FROM Account LIMIT 10",
        ...     sf.instance_url
        ... )
        >>> print(url)
        https://workbench.developerforce.com/query.php?query=SELECT+Id%2C+Name+...
    """
    # Extract instance name from URL
    instance_name = instance_url.replace("https://", "").replace("http://", "").split(".")[0]

    # URL encode the query
    encoded_query = quote(soql)

    # Build Workbench URL
    workbench_url = f"{base_workbench_url.rstrip('/')}/query.php"
    workbench_url += f"?query={encoded_query}"
    workbench_url += f"&instance={instance_name}"

    return workbench_url


def generate_soql_explorer_url(soql: str, instance_url: str) -> str:
    """Generate SOQL Explorer URL (Salesforce Developer Console style).

    Note: This generates a URL that opens the query in a format similar
    to Developer Console's Query Editor.

    Args:
        soql: SOQL query
        instance_url: Salesforce instance URL

    Returns:
        SOQL Explorer URL

    Example:
        >>> url = generate_soql_explorer_url(
        ...     "SELECT Id FROM Account",
        ...     sf.instance_url
        ... )
    """
    encoded_query = quote(soql)
    return f"{instance_url.rstrip('/')}/_ui/common/apex/debug/ApexCSIPage?query={encoded_query}"


class WorkbenchConfig:
    """Configuration for Workbench URL generation.

    Allows customization of Workbench base URL for organizations
    using self-hosted Workbench instances.
    """

    def __init__(self, base_url: str = "https://workbench.developerforce.com"):
        """Initialize Workbench config.

        Args:
            base_url: Base Workbench URL
        """
        self.base_url = base_url.rstrip("/")

    def generate_url(self, soql: str, instance_url: str) -> str:
        """Generate Workbench URL with this config.

        Args:
            soql: SOQL query
            instance_url: Salesforce instance URL

        Returns:
            Workbench URL
        """
        return generate_workbench_url(soql, instance_url, self.base_url)


def format_soql(soql: str, indent: str = "  ") -> str:
    """Format SOQL query for readability.

    Args:
        soql: SOQL query to format
        indent: Indentation string (default: 2 spaces)

    Returns:
        Formatted SOQL query

    Example:
        >>> formatted = format_soql("SELECT Id, Name, Industry FROM Account WHERE Name LIKE 'A%' ORDER BY Name")
        >>> print(formatted)
        SELECT
          Id,
          Name,
          Industry
        FROM Account
        WHERE Name LIKE 'A%'
        ORDER BY Name
    """
    # Simple formatter - split on keywords and indent
    keywords = ["SELECT", "FROM", "WHERE", "ORDER BY", "GROUP BY", "LIMIT", "OFFSET", "HAVING"]

    formatted = soql
    for keyword in keywords:
        formatted = formatted.replace(f" {keyword} ", f"\n{keyword} ")

    # Indent fields after SELECT
    lines = formatted.split("\n")
    result_lines = []
    in_select = False

    for line in lines:
        if line.startswith("SELECT"):
            result_lines.append(line)
            in_select = True
        elif in_select and not any(line.startswith(kw) for kw in keywords[1:]):
            # Split fields and indent
            fields = [f.strip() for f in line.split(",")]
            for i, field in enumerate(fields):
                if i == 0 and not result_lines[-1].endswith("SELECT"):
                    result_lines.append(f"{indent}{field}")
                elif field:
                    result_lines[-1] += ","
                    result_lines.append(f"{indent}{field}")
        else:
            in_select = False
            result_lines.append(line)

    return "\n".join(result_lines)
