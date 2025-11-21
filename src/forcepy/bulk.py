"""Salesforce Bulk API 2.0 implementation for forcepy.

Provides efficient handling of large-scale data operations with async job management.
"""

import csv
import io
import json
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class BulkJob:
    """Represents a Salesforce Bulk API 2.0 job.

    A job tracks the processing of bulk operations (insert, update, upsert, delete, query).
    Jobs run asynchronously on Salesforce's servers.

    Attributes:
        job_id: Unique job identifier
        state: Current job state (Open, UploadComplete, InProgress, JobComplete, Failed, Aborted)
        object_name: Salesforce object being operated on
        operation: Operation type (insert, update, upsert, delete, query)
        created_date: Job creation timestamp
    """

    def __init__(self, client: Any, job_id: str, object_name: str, operation: str, job_info: dict[str, Any]):
        """Initialize a bulk job.

        Args:
            client: Salesforce client instance
            job_id: Unique job identifier
            object_name: Salesforce object name
            operation: Operation type
            job_info: Job metadata from Salesforce
        """
        self.client = client
        self.job_id = job_id
        self.object_name = object_name
        self.operation = operation
        self._job_info = job_info

    @property
    def state(self) -> str:
        """Current job state."""
        return self._job_info.get("state", "Unknown")

    @property
    def created_date(self) -> Optional[str]:
        """Job creation timestamp."""
        return self._job_info.get("createdDate")

    @property
    def number_records_processed(self) -> int:
        """Number of records processed."""
        return self._job_info.get("numberRecordsProcessed", 0)

    @property
    def number_records_failed(self) -> int:
        """Number of records that failed."""
        return self._job_info.get("numberRecordsFailed", 0)

    def refresh(self) -> None:
        """Refresh job status from Salesforce."""
        url = f"/services/data/v{self.client.version}/jobs/ingest/{self.job_id}"
        self._job_info = self.client.http("GET", url)
        logger.debug(f"Job {self.job_id} status: {self.state}")

    def wait_for_completion(
        self,
        poll_interval: int = 5,
        timeout: Optional[int] = None,
        callback: Optional[Callable[["BulkJob"], None]] = None,
    ) -> "BulkJob":
        """Wait for job to complete with async polling.

        Args:
            poll_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (default: None = no timeout)
            callback: Optional callback function called on completion

        Returns:
            Self for method chaining

        Raises:
            BulkJobTimeout: If timeout is reached
            BulkJobError: If job fails
        """
        from .exceptions import BulkJobError, BulkJobTimeout

        start_time = time.time()

        while True:
            self.refresh()

            # Check terminal states
            if self.state == "JobComplete":
                logger.info(f"Job {self.job_id} completed successfully")
                if callback:
                    callback(self)
                return self

            elif self.state == "Failed":
                error_msg = self._job_info.get("errorMessage", "Job failed")
                raise BulkJobError(f"Job {self.job_id} failed: {error_msg}")

            elif self.state == "Aborted":
                raise BulkJobError(f"Job {self.job_id} was aborted")

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise BulkJobTimeout(f"Job {self.job_id} timed out after {timeout} seconds")

            # Continue polling
            logger.debug(f"Job {self.job_id} state: {self.state}, waiting {poll_interval}s...")
            time.sleep(poll_interval)

    def get_results(self) -> dict[str, Any]:
        """Get job results including successful and failed records.

        Returns:
            Dictionary with 'successful' and 'failed' record lists
        """
        # Get successful results
        success_url = f"/services/data/v{self.client.version}/jobs/ingest/{self.job_id}/successfulResults"
        try:
            success_response = self.client.http("GET", success_url)
            successful_records = self._parse_csv_response(success_response) if isinstance(success_response, str) else []
        except Exception as e:
            logger.warning(f"Failed to retrieve successful results: {e}")
            successful_records = []

        # Get failed results
        failed_url = f"/services/data/v{self.client.version}/jobs/ingest/{self.job_id}/failedResults"
        try:
            failed_response = self.client.http("GET", failed_url)
            failed_records = self._parse_csv_response(failed_response) if isinstance(failed_response, str) else []
        except Exception as e:
            logger.warning(f"Failed to retrieve failed results: {e}")
            failed_records = []

        return {
            "successful": successful_records,
            "failed": failed_records,
            "total_processed": self.number_records_processed,
            "total_failed": self.number_records_failed,
        }

    def _parse_csv_response(self, csv_text: str) -> list[dict[str, Any]]:
        """Parse CSV response from Salesforce.

        Args:
            csv_text: CSV formatted response

        Returns:
            List of record dictionaries
        """
        if not csv_text or not csv_text.strip():
            return []

        reader = csv.DictReader(io.StringIO(csv_text))
        return list(reader)

    def abort(self) -> None:
        """Abort the job.

        Raises:
            BulkJobError: If abort fails
        """
        from .exceptions import BulkJobError

        url = f"/services/data/v{self.client.version}/jobs/ingest/{self.job_id}"
        try:
            self.client.http("PATCH", url, json={"state": "Aborted"})
            self.refresh()
            logger.info(f"Job {self.job_id} aborted")
        except Exception as e:
            raise BulkJobError(f"Failed to abort job {self.job_id}: {e}")

    def __repr__(self) -> str:
        return f"<BulkJob(id={self.job_id}, state={self.state}, operation={self.operation}, object={self.object_name})>"


class BulkObjectOperations:
    """Dynamic object operations for Bulk API.

    Provides insert, update, upsert, delete, and query operations for a specific object.
    """

    def __init__(self, bulk_api: "BulkAPI", object_name: str):
        """Initialize object operations.

        Args:
            bulk_api: Parent BulkAPI instance
            object_name: Salesforce object name
        """
        self.bulk_api = bulk_api
        self.object_name = object_name

    def insert(self, records: list[dict[str, Any]]) -> BulkJob:
        """Insert records.

        Args:
            records: List of record dictionaries

        Returns:
            BulkJob instance for monitoring
        """
        return self.bulk_api._create_job(self.object_name, "insert", records)

    def update(self, records: list[dict[str, Any]]) -> BulkJob:
        """Update records.

        Args:
            records: List of record dictionaries (must include Id field)

        Returns:
            BulkJob instance for monitoring
        """
        return self.bulk_api._create_job(self.object_name, "update", records)

    def upsert(self, records: list[dict[str, Any]], external_id_field: str) -> BulkJob:
        """Upsert records using external ID.

        Args:
            records: List of record dictionaries
            external_id_field: External ID field name

        Returns:
            BulkJob instance for monitoring
        """
        return self.bulk_api._create_job(self.object_name, "upsert", records, external_id_field=external_id_field)

    def delete(self, records: list[dict[str, Any]]) -> BulkJob:
        """Delete records.

        Args:
            records: List of record dictionaries (must include Id field)

        Returns:
            BulkJob instance for monitoring
        """
        return self.bulk_api._create_job(self.object_name, "delete", records)

    def query(self, soql: str) -> list[dict[str, Any]]:
        """Execute bulk query.

        Args:
            soql: SOQL query string

        Returns:
            List of result records
        """
        return self.bulk_api._execute_query(self.object_name, soql)


class BulkAPI:
    """Salesforce Bulk API 2.0 interface.

    Provides efficient large-scale data operations with async job management.

    Example:
        >>> sf = Salesforce(username='user', password='pass')
        >>>
        >>> # Insert records
        >>> job = sf.bulk.Account.insert([
        ...     {'Name': 'Account 1', 'Industry': 'Technology'},
        ...     {'Name': 'Account 2', 'Industry': 'Finance'}
        ... ])
        >>>
        >>> # Wait for completion
        >>> job.wait_for_completion(poll_interval=5)
        >>> results = job.get_results()
        >>> print(f"Successful: {len(results['successful'])}")
    """

    def __init__(self, client: Any):
        """Initialize Bulk API.

        Args:
            client: Salesforce client instance
        """
        self.client = client

    def __getattr__(self, name: str) -> BulkObjectOperations:
        """Dynamic object access.

        Args:
            name: Salesforce object name

        Returns:
            BulkObjectOperations for the object
        """
        return BulkObjectOperations(self, name)

    def _create_job(
        self, object_name: str, operation: str, records: list[dict[str, Any]], external_id_field: Optional[str] = None
    ) -> BulkJob:
        """Create and execute a bulk job.

        Args:
            object_name: Salesforce object name
            operation: Operation type (insert, update, upsert, delete)
            records: List of record dictionaries
            external_id_field: External ID field for upsert

        Returns:
            BulkJob instance
        """
        from .exceptions import BulkJobError

        # Validate records
        if not records:
            raise BulkJobError("Cannot create job with empty records list")

        # Create job
        job_data = {
            "object": object_name,
            "operation": operation,
            "contentType": "JSON",  # Use JSON format (Bulk API 2.0)
        }

        if external_id_field:
            job_data["externalIdFieldName"] = external_id_field

        create_url = f"/services/data/v{self.client.version}/jobs/ingest"
        job_info = self.client.http("POST", create_url, json=job_data)
        job_id = job_info["id"]

        logger.info(f"Created bulk job {job_id} for {operation} on {object_name}")

        # Upload data
        self._upload_data(job_id, records)

        # Close job to start processing
        self._close_job(job_id)

        return BulkJob(self.client, job_id, object_name, operation, job_info)

    def _upload_data(self, job_id: str, records: list[dict[str, Any]]) -> None:
        """Upload data to job.

        Args:
            job_id: Job identifier
            records: List of record dictionaries
        """
        from .exceptions import BulkJobError

        # Convert records to JSON Lines format (newline-delimited JSON)
        json_lines = "\n".join(json.dumps(record) for record in records)

        upload_url = f"/services/data/v{self.client.version}/jobs/ingest/{job_id}/batches"

        try:
            self.client.http(
                "PUT", upload_url, data=json_lines.encode("utf-8"), headers={"Content-Type": "application/json"}
            )
            logger.debug(f"Uploaded {len(records)} records to job {job_id}")
        except Exception as e:
            raise BulkJobError(f"Failed to upload data to job {job_id}: {e}")

    def _close_job(self, job_id: str) -> None:
        """Close job to start processing.

        Args:
            job_id: Job identifier
        """
        from .exceptions import BulkJobError

        close_url = f"/services/data/v{self.client.version}/jobs/ingest/{job_id}"
        try:
            self.client.http("PATCH", close_url, json={"state": "UploadComplete"})
            logger.debug(f"Closed job {job_id}, processing started")
        except Exception as e:
            raise BulkJobError(f"Failed to close job {job_id}: {e}")

    def _execute_query(self, object_name: str, soql: str) -> list[dict[str, Any]]:
        """Execute bulk query and return results.

        Args:
            object_name: Salesforce object name
            soql: SOQL query

        Returns:
            List of result records
        """
        from .exceptions import BulkJobError

        # Create query job
        job_data = {"operation": "query", "query": soql}

        create_url = f"/services/data/v{self.client.version}/jobs/query"
        job_info = self.client.http("POST", create_url, json=job_data)
        job_id = job_info["id"]

        logger.info(f"Created bulk query job {job_id}")

        # Wait for completion
        job = BulkJob(self.client, job_id, object_name, "query", job_info)
        job.wait_for_completion()

        # Get results
        results_url = f"/services/data/v{self.client.version}/jobs/query/{job_id}/results"
        try:
            csv_response = self.client.http("GET", results_url)
            return job._parse_csv_response(csv_response) if isinstance(csv_response, str) else []
        except Exception as e:
            raise BulkJobError(f"Failed to retrieve query results: {e}")


def records_to_json(records: list[dict[str, Any]]) -> str:
    """Convert Python dicts/lists to JSON format.

    Args:
        records: List of record dictionaries

    Returns:
        JSON Lines formatted string (newline-delimited JSON)
    """
    return "\n".join(json.dumps(record) for record in records)


def records_to_csv(records: list[dict[str, Any]]) -> str:
    """Convert Python dicts/lists to CSV format.

    Args:
        records: List of record dictionaries

    Returns:
        CSV formatted string
    """
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def validate_records(records: list[dict[str, Any]], operation: str) -> None:
    """Validate record structure before upload.

    Args:
        records: List of record dictionaries
        operation: Operation type

    Raises:
        ValueError: If validation fails
    """
    if not records:
        raise ValueError("Records list cannot be empty")

    if operation in ("update", "delete"):
        # Must have Id field
        for i, record in enumerate(records):
            if "Id" not in record:
                raise ValueError(f"Record {i} missing required 'Id' field for {operation} operation")

    # All records should have same structure (same fields)
    if len(records) > 1:
        first_keys = set(records[0].keys())
        for i, record in enumerate(records[1:], start=1):
            if set(record.keys()) != first_keys:
                logger.warning(f"Record {i} has different fields than first record")
