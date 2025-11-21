"""forcepy - Modern Python client for Salesforce.

Example:
    >>> from forcepy import Salesforce, Q
    >>> sf = Salesforce(username='user@example.com', password='password')
    >>> accounts = sf.query("SELECT Id, Name FROM Account LIMIT 10")
    >>> for account in accounts.records:
    ...     print(account.Name)
"""

__version__ = "0.1.0"

from .bulk import BulkAPI, BulkJob
from .chatter import Chatter, format_chatter_post
from .client import Salesforce
from .composite import CompositeError, CompositeRequest, CompositeResponse, validate_composite_response
from .exceptions import (
    APIError,
    AuthenticationError,
    BulkAPIError,
    BulkJobError,
    BulkJobTimeout,
    QueryError,
    RetryableError,
    SalesforceError,
    ValidationError,
)
from .id_utils import compare_ids, id_in_list, is_valid_id, normalize_id
from .metadata import DescribeCache, FieldDescribe, FieldDescribeSet, ObjectDescribe
from .query import BOOL, DATE, IN, Q, compile_where_clause, format_datetime, parse_datetime, select
from .query_advanced import (
    WorkbenchConfig,
    expand_select_star,
    format_soql,
    generate_soql_explorer_url,
    generate_workbench_url,
)
from .query_helpers import compile_where_clause as build_where_clause
from .query_helpers import prettyprint_soql
from .results import AggregateSet, Result, ResultSet
from .sobject import Sobject, SobjectSet
from .token_cache import MemoryCache, NullCache, RedisCache, TokenCache

__all__ = [
    # Main client
    "Salesforce",
    # Bulk API
    "BulkAPI",
    "BulkJob",
    # Chatter
    "Chatter",
    "format_chatter_post",
    # Composite API
    "CompositeRequest",
    "CompositeResponse",
    "CompositeError",
    "validate_composite_response",
    # Metadata/Describe
    "ObjectDescribe",
    "FieldDescribe",
    "FieldDescribeSet",
    "DescribeCache",
    # Token caching
    "TokenCache",
    "MemoryCache",
    "NullCache",
    "RedisCache",
    # Query building
    "Q",
    "compile_where_clause",
    "build_where_clause",
    "select",
    "IN",
    "DATE",
    "BOOL",
    "format_datetime",
    "parse_datetime",
    # Advanced query features
    "expand_select_star",
    "generate_workbench_url",
    "generate_soql_explorer_url",
    "format_soql",
    "prettyprint_soql",
    "WorkbenchConfig",
    # ID utilities
    "normalize_id",
    "compare_ids",
    "id_in_list",
    "is_valid_id",
    # Results
    "Result",
    "ResultSet",
    "AggregateSet",
    # Sobjects
    "Sobject",
    "SobjectSet",
    # Exceptions
    "SalesforceError",
    "AuthenticationError",
    "QueryError",
    "APIError",
    "RetryableError",
    "ValidationError",
    "BulkAPIError",
    "BulkJobError",
    "BulkJobTimeout",
]
