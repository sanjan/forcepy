"""Tests for Bulk API functionality."""

import json
from unittest.mock import Mock, patch

import pytest

from forcepy import Salesforce
from forcepy.bulk import BulkAPI, BulkJob, BulkObjectOperations, records_to_csv, records_to_json, validate_records
from forcepy.exceptions import BulkJobError, BulkJobTimeout


@pytest.fixture
def sf():
    """Create a mock Salesforce client."""
    with patch("forcepy.auth.soap_login") as mock_login:
        # soap_login returns (session_id, instance_url) tuple
        mock_login.return_value = ("mock_session", "https://na1.salesforce.com")

        with patch.object(Salesforce, "http") as mock_http:
            # Mock the userinfo call
            mock_http.return_value = {"user_id": "005B0000001234567"}

            client = Salesforce(username="test@example.com", password="password123")
            client.version = "59.0"
            yield client


class TestBulkJob:
    """Tests for BulkJob class."""

    def test_job_initialization(self, sf):
        """Test job initialization."""
        job_info = {
            "id": "job123",
            "state": "Open",
            "createdDate": "2025-01-01T00:00:00Z",
            "numberRecordsProcessed": 0,
            "numberRecordsFailed": 0,
        }

        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        assert job.job_id == "job123"
        assert job.object_name == "Account"
        assert job.operation == "insert"
        assert job.state == "Open"
        assert job.created_date == "2025-01-01T00:00:00Z"
        assert job.number_records_processed == 0
        assert job.number_records_failed == 0

    def test_job_refresh(self, sf):
        """Test job status refresh."""
        job_info = {"id": "job123", "state": "Open"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        updated_info = {"id": "job123", "state": "InProgress", "numberRecordsProcessed": 50}

        with patch.object(sf, "http", return_value=updated_info):
            job.refresh()

        assert job.state == "InProgress"
        assert job.number_records_processed == 50

    def test_wait_for_completion_success(self, sf):
        """Test waiting for job completion."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        # Simulate state progression
        states = [
            {"id": "job123", "state": "InProgress"},
            {"id": "job123", "state": "JobComplete", "numberRecordsProcessed": 100},
        ]

        with patch.object(sf, "http", side_effect=states):
            result = job.wait_for_completion(poll_interval=0.1)

        assert result == job
        assert job.state == "JobComplete"
        assert job.number_records_processed == 100

    def test_wait_for_completion_with_callback(self, sf):
        """Test waiting with callback function."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        callback_called = {"called": False, "job": None}

        def callback(job):
            callback_called["called"] = True
            callback_called["job"] = job

        complete_info = {"id": "job123", "state": "JobComplete"}

        with patch.object(sf, "http", return_value=complete_info):
            job.wait_for_completion(poll_interval=0.1, callback=callback)

        assert callback_called["called"]
        assert callback_called["job"] == job

    def test_wait_for_completion_failed_job(self, sf):
        """Test handling of failed job."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        failed_info = {"id": "job123", "state": "Failed", "errorMessage": "Processing error"}

        with patch.object(sf, "http", return_value=failed_info):
            with pytest.raises(BulkJobError) as exc_info:
                job.wait_for_completion(poll_interval=0.1)

        assert "Processing error" in str(exc_info.value)

    def test_wait_for_completion_aborted_job(self, sf):
        """Test handling of aborted job."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        aborted_info = {"id": "job123", "state": "Aborted"}

        with patch.object(sf, "http", return_value=aborted_info):
            with pytest.raises(BulkJobError) as exc_info:
                job.wait_for_completion(poll_interval=0.1)

        assert "aborted" in str(exc_info.value).lower()

    def test_wait_for_completion_timeout(self, sf):
        """Test job timeout."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        in_progress_info = {"id": "job123", "state": "InProgress"}

        with patch.object(sf, "http", return_value=in_progress_info):
            with pytest.raises(BulkJobTimeout):
                job.wait_for_completion(poll_interval=0.1, timeout=0.3)

    def test_get_results(self, sf):
        """Test getting job results."""
        job_info = {"id": "job123", "state": "JobComplete", "numberRecordsProcessed": 2, "numberRecordsFailed": 1}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        success_csv = "sf__Id,sf__Created\n001xxx,true\n001yyy,true"
        failed_csv = "sf__Id,sf__Error\n001zzz,REQUIRED_FIELD_MISSING"

        with patch.object(sf, "http", side_effect=[success_csv, failed_csv]):
            results = job.get_results()

        assert len(results["successful"]) == 2
        assert len(results["failed"]) == 1
        assert results["total_processed"] == 2
        assert results["total_failed"] == 1

    def test_get_results_empty(self, sf):
        """Test getting results when no data."""
        job_info = {"id": "job123", "state": "JobComplete", "numberRecordsProcessed": 0}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        with patch.object(sf, "http", side_effect=["", ""]):
            results = job.get_results()

        assert results["successful"] == []
        assert results["failed"] == []

    def test_abort_job(self, sf):
        """Test aborting a job."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        aborted_info = {"id": "job123", "state": "Aborted"}

        with patch.object(sf, "http", side_effect=[None, aborted_info]):
            job.abort()

        assert job.state == "Aborted"

    def test_abort_job_error(self, sf):
        """Test error handling when aborting job."""
        job_info = {"id": "job123", "state": "InProgress"}
        job = BulkJob(sf, "job123", "Account", "insert", job_info)

        with patch.object(sf, "http", side_effect=Exception("Network error")):
            with pytest.raises(BulkJobError) as exc_info:
                job.abort()

        assert "Failed to abort" in str(exc_info.value)


class TestBulkObjectOperations:
    """Tests for BulkObjectOperations class."""

    def test_initialization(self, sf):
        """Test object operations initialization."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        assert ops.bulk_api == bulk_api
        assert ops.object_name == "Account"

    def test_insert_operation(self, sf):
        """Test insert operation."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        records = [{"Name": "Test Account"}]

        with patch.object(bulk_api, "_create_job", return_value=Mock()) as mock_create:
            result = ops.insert(records)

        mock_create.assert_called_once_with("Account", "insert", records)
        assert isinstance(result, Mock)

    def test_update_operation(self, sf):
        """Test update operation."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        records = [{"Id": "001xxx", "Name": "Updated Account"}]

        with patch.object(bulk_api, "_create_job", return_value=Mock()) as mock_create:
            ops.update(records)

        mock_create.assert_called_once_with("Account", "update", records)

    def test_upsert_operation(self, sf):
        """Test upsert operation."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        records = [{"External_Id__c": "EXT123", "Name": "Upsert Account"}]

        with patch.object(bulk_api, "_create_job", return_value=Mock()) as mock_create:
            ops.upsert(records, external_id_field="External_Id__c")

        mock_create.assert_called_once_with("Account", "upsert", records, external_id_field="External_Id__c")

    def test_delete_operation(self, sf):
        """Test delete operation."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        records = [{"Id": "001xxx"}]

        with patch.object(bulk_api, "_create_job", return_value=Mock()) as mock_create:
            ops.delete(records)

        mock_create.assert_called_once_with("Account", "delete", records)

    def test_query_operation(self, sf):
        """Test query operation."""
        bulk_api = BulkAPI(sf)
        ops = BulkObjectOperations(bulk_api, "Account")

        soql = "SELECT Id, Name FROM Account"

        with patch.object(bulk_api, "_execute_query", return_value=[]) as mock_query:
            ops.query(soql)

        mock_query.assert_called_once_with("Account", soql)


class TestBulkAPI:
    """Tests for BulkAPI class."""

    def test_initialization(self, sf):
        """Test BulkAPI initialization."""
        bulk_api = BulkAPI(sf)
        assert bulk_api.client == sf

    def test_dynamic_object_access(self, sf):
        """Test dynamic object access via __getattr__."""
        bulk_api = BulkAPI(sf)
        ops = bulk_api.Account

        assert isinstance(ops, BulkObjectOperations)
        assert ops.object_name == "Account"

    def test_create_job_success(self, sf):
        """Test successful job creation."""
        bulk_api = BulkAPI(sf)
        records = [{"Name": "Test Account", "Industry": "Technology"}]

        job_response = {"id": "job123", "state": "Open"}

        with patch.object(sf, "http", side_effect=[job_response, None, None]):
            job = bulk_api._create_job("Account", "insert", records)

        assert isinstance(job, BulkJob)
        assert job.job_id == "job123"
        assert job.object_name == "Account"
        assert job.operation == "insert"

    def test_create_job_empty_records(self, sf):
        """Test job creation with empty records list."""
        bulk_api = BulkAPI(sf)

        with pytest.raises(BulkJobError) as exc_info:
            bulk_api._create_job("Account", "insert", [])

        assert "empty records" in str(exc_info.value).lower()

    def test_create_job_with_external_id(self, sf):
        """Test job creation with external ID field."""
        bulk_api = BulkAPI(sf)
        records = [{"External_Id__c": "EXT123", "Name": "Test"}]

        job_response = {"id": "job123", "state": "Open"}

        with patch.object(sf, "http", side_effect=[job_response, None, None]) as mock_http:
            bulk_api._create_job("Account", "upsert", records, external_id_field="External_Id__c")

        # Check that externalIdFieldName was passed in job creation
        call_args = mock_http.call_args_list[0]
        json_data = call_args[1]["json"]
        assert json_data["externalIdFieldName"] == "External_Id__c"

    def test_upload_data(self, sf):
        """Test data upload."""
        bulk_api = BulkAPI(sf)
        records = [{"Name": "Account 1", "Industry": "Technology"}, {"Name": "Account 2", "Industry": "Finance"}]

        with patch.object(sf, "http") as mock_http:
            bulk_api._upload_data("job123", records)

        mock_http.assert_called_once()
        call_args = mock_http.call_args
        assert "batches" in call_args[0][1]
        # Verify JSON Lines format
        data = call_args[1]["data"].decode("utf-8")
        lines = data.strip().split("\n")
        assert len(lines) == 2

    def test_upload_data_error(self, sf):
        """Test error handling during data upload."""
        bulk_api = BulkAPI(sf)
        records = [{"Name": "Test"}]

        with patch.object(sf, "http", side_effect=Exception("Upload failed")):
            with pytest.raises(BulkJobError) as exc_info:
                bulk_api._upload_data("job123", records)

        assert "Failed to upload" in str(exc_info.value)

    def test_close_job(self, sf):
        """Test closing a job."""
        bulk_api = BulkAPI(sf)

        with patch.object(sf, "http") as mock_http:
            bulk_api._close_job("job123")

        mock_http.assert_called_once()
        call_args = mock_http.call_args
        assert call_args[1]["json"]["state"] == "UploadComplete"

    def test_close_job_error(self, sf):
        """Test error handling when closing job."""
        bulk_api = BulkAPI(sf)

        with patch.object(sf, "http", side_effect=Exception("Close failed")):
            with pytest.raises(BulkJobError) as exc_info:
                bulk_api._close_job("job123")

        assert "Failed to close" in str(exc_info.value)

    def test_execute_query(self, sf):
        """Test bulk query execution."""
        bulk_api = BulkAPI(sf)
        soql = "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"

        job_response = {"id": "query123", "state": "JobComplete"}
        results_csv = "Id,Name\n001xxx,Account 1\n001yyy,Account 2"

        with patch.object(sf, "http", side_effect=[job_response, job_response, results_csv]):
            results = bulk_api._execute_query("Account", soql)

        assert len(results) == 2
        assert results[0]["Id"] == "001xxx"
        assert results[1]["Name"] == "Account 2"

    def test_execute_query_error(self, sf):
        """Test error handling during query execution."""
        bulk_api = BulkAPI(sf)
        soql = "SELECT Id FROM Account"

        job_response = {"id": "query123", "state": "JobComplete"}

        with patch.object(sf, "http", side_effect=[job_response, job_response, Exception("Results fetch failed")]):
            with pytest.raises(BulkJobError) as exc_info:
                bulk_api._execute_query("Account", soql)

        assert "Failed to retrieve query results" in str(exc_info.value)


class TestDataFormatConversion:
    """Tests for data format conversion utilities."""

    def test_records_to_json(self):
        """Test converting records to JSON."""
        records = [{"Name": "Account 1", "Industry": "Technology"}, {"Name": "Account 2", "Industry": "Finance"}]

        result = records_to_json(records)

        lines = result.split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == records[0]
        assert json.loads(lines[1]) == records[1]

    def test_records_to_csv(self):
        """Test converting records to CSV."""
        records = [{"Name": "Account 1", "Industry": "Technology"}, {"Name": "Account 2", "Industry": "Finance"}]

        result = records_to_csv(records)

        lines = result.strip().split("\n")
        assert len(lines) == 3  # Header + 2 records
        assert "Name,Industry" in lines[0]
        assert "Account 1,Technology" in lines[1]

    def test_records_to_csv_empty(self):
        """Test converting empty records to CSV."""
        result = records_to_csv([])
        assert result == ""

    def test_validate_records_empty(self):
        """Test validation fails for empty records."""
        with pytest.raises(ValueError) as exc_info:
            validate_records([], "insert")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_validate_records_update_missing_id(self):
        """Test validation fails for update without Id."""
        records = [{"Name": "Test"}]

        with pytest.raises(ValueError) as exc_info:
            validate_records(records, "update")

        assert "missing required" in str(exc_info.value).lower()
        assert "Id" in str(exc_info.value)

    def test_validate_records_delete_missing_id(self):
        """Test validation fails for delete without Id."""
        records = [{"Name": "Test"}]

        with pytest.raises(ValueError) as exc_info:
            validate_records(records, "delete")

        assert "missing required" in str(exc_info.value).lower()
        assert "Id" in str(exc_info.value)

    def test_validate_records_insert_success(self):
        """Test validation passes for insert."""
        records = [{"Name": "Test"}]
        # Should not raise
        validate_records(records, "insert")


class TestBulkAPIIntegration:
    """Integration tests for Bulk API."""

    def test_bulk_property_on_client(self, sf):
        """Test bulk property exists on Salesforce client."""
        assert hasattr(sf, "bulk")
        assert isinstance(sf.bulk, BulkAPI)

    def test_bulk_property_cached(self, sf):
        """Test bulk property is cached."""
        bulk1 = sf.bulk
        bulk2 = sf.bulk
        assert bulk1 is bulk2

    def test_end_to_end_insert(self, sf):
        """Test end-to-end insert operation."""
        records = [{"Name": "Account 1", "Industry": "Technology"}, {"Name": "Account 2", "Industry": "Finance"}]

        job_response = {"id": "job123", "state": "Open"}
        complete_response = {
            "id": "job123",
            "state": "JobComplete",
            "numberRecordsProcessed": 2,
            "numberRecordsFailed": 0,
        }
        success_csv = "sf__Id,sf__Created\n001xxx,true\n001yyy,true"

        with patch.object(sf, "http", side_effect=[job_response, None, None, complete_response, success_csv, ""]):
            job = sf.bulk.Account.insert(records)
            job.wait_for_completion(poll_interval=0.1)
            results = job.get_results()

        assert len(results["successful"]) == 2
        assert results["total_failed"] == 0

    def test_end_to_end_update(self, sf):
        """Test end-to-end update operation."""
        records = [{"Id": "001xxx", "Name": "Updated Account 1"}, {"Id": "001yyy", "Name": "Updated Account 2"}]

        job_response = {"id": "job123", "state": "Open"}
        complete_response = {"id": "job123", "state": "JobComplete", "numberRecordsProcessed": 2}

        with patch.object(sf, "http", side_effect=[job_response, None, None, complete_response]):
            job = sf.bulk.Account.update(records)
            job.wait_for_completion(poll_interval=0.1)

        assert job.state == "JobComplete"

    def test_end_to_end_query(self, sf):
        """Test end-to-end query operation."""
        soql = "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"

        job_response = {"id": "query123", "state": "JobComplete"}
        results_csv = "Id,Name\n001xxx,Account 1\n001yyy,Account 2"

        with patch.object(sf, "http", side_effect=[job_response, job_response, results_csv]):
            results = sf.bulk.Account.query(soql)

        assert len(results) == 2
        assert results[0]["Id"] == "001xxx"

    def test_concurrent_jobs(self, sf):
        """Test handling multiple concurrent jobs."""
        records1 = [{"Name": "Account 1"}]
        records2 = [{"FirstName": "John", "LastName": "Doe"}]

        job1_response = {"id": "job1", "state": "Open"}
        job2_response = {"id": "job2", "state": "Open"}

        with patch.object(
            sf,
            "http",
            side_effect=[
                job1_response,
                None,
                None,  # Job 1 creation
                job2_response,
                None,
                None,  # Job 2 creation
            ],
        ):
            job1 = sf.bulk.Account.insert(records1)
            job2 = sf.bulk.Contact.insert(records2)

        assert job1.job_id == "job1"
        assert job2.job_id == "job2"
        assert job1.object_name == "Account"
        assert job2.object_name == "Contact"
