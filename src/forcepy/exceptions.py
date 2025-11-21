"""Custom exceptions for forcepy."""


class SalesforceError(Exception):
    """Base exception for all Salesforce errors."""

    pass


class AuthenticationError(SalesforceError):
    """Raised when authentication fails."""

    pass


class QueryError(SalesforceError):
    """Raised when a SOQL query fails."""

    pass


class CompositeError(SalesforceError):
    """Raised when a composite request fails."""

    def __init__(self, message: str, response=None):
        super().__init__(message)
        self.response = response


class APIError(SalesforceError):
    """Raised when an API call fails."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class RetryableError(APIError):
    """Raised when an error should trigger a retry."""

    pass


class ValidationError(SalesforceError):
    """Raised when validation fails."""

    pass


class BulkAPIError(SalesforceError):
    """Base exception for Bulk API errors."""

    pass


class BulkJobError(BulkAPIError):
    """Raised when a bulk job fails or encounters an error."""

    pass


class BulkJobTimeout(BulkAPIError):
    """Raised when a bulk job times out."""

    pass
