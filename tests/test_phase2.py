"""Tests for Phase 2 features: retry logic, pagination, iterquery threading, dependent picklists."""

import base64
from unittest.mock import Mock, patch

import pytest

from forcepy import Salesforce
from forcepy.exceptions import APIError
from forcepy.sobject import SobjectSet


class TestRetryLogic:
    """Test auto-retry logic with configurable parameters."""

    def test_retry_configuration(self):
        """Test retry configuration in constructor."""
        sf = Salesforce(
            session_id="test-session",
            instance_url="https://test.salesforce.com",
            max_retries=5,
            retry_delay=10.0,
            retry_backoff=False,
        )
        assert sf.max_retries == 5
        assert sf.retry_delay == 10.0
        assert sf.retry_backoff is False

    def test_default_retry_configuration(self):
        """Test default retry configuration."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")
        assert sf.max_retries == 3
        assert sf.retry_delay == 6.0
        assert sf.retry_backoff is True

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_retry_on_503(self, mock_sleep, mock_request):
        """Test retry on 503 Service Unavailable."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com", max_retries=2)

        # First attempt: 503, second attempt: 503, third: success
        response_503 = Mock(
            status_code=503, content=b'{"message": "Service unavailable"}', headers={"Content-Type": "application/json"}
        )
        response_503.json.return_value = {"message": "Service unavailable"}

        response_200 = Mock(status_code=200, content=b'{"success": true}', headers={"Content-Type": "application/json"})
        response_200.json.return_value = {"success": True}

        mock_request.side_effect = [response_503, response_503, response_200]

        result = sf.http("GET", "/test")
        assert result == {"success": True}
        assert mock_request.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_retry_on_502(self, mock_sleep, mock_request):
        """Test retry on 502 Bad Gateway."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com", max_retries=1)

        response_502 = Mock(status_code=502, content=b"Bad Gateway", headers={"Content-Type": "text/html"})
        response_200 = Mock(status_code=200, content=b'{"success": true}', headers={"Content-Type": "application/json"})
        response_200.json.return_value = {"success": True}

        mock_request.side_effect = [response_502, response_200]

        result = sf.http("GET", "/test")
        assert result == {"success": True}
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_retry_on_unable_to_lock_row(self, mock_sleep, mock_request):
        """Test retry on UNABLE_TO_LOCK_ROW error."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com", max_retries=1)

        response_400 = Mock(
            status_code=400,
            content=b'[{"errorCode": "UNABLE_TO_LOCK_ROW", "message": "Row locked"}]',
            headers={"Content-Type": "application/json"},
        )
        response_400.json.return_value = [{"errorCode": "UNABLE_TO_LOCK_ROW", "message": "Row locked"}]

        response_200 = Mock(status_code=200, content=b'{"success": true}', headers={"Content-Type": "application/json"})
        response_200.json.return_value = {"success": True}

        mock_request.side_effect = [response_400, response_200]

        result = sf.http("GET", "/test")
        assert result == {"success": True}
        assert mock_request.call_count == 2

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_retry_exhausted(self, mock_sleep, mock_request):
        """Test that error is raised after max retries."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com", max_retries=2)

        mock_request.return_value = Mock(
            status_code=503,
            content=b'{"message": "Service unavailable"}',
            headers={"Content-Type": "application/json"},
            json=lambda: {"message": "Service unavailable"},
        )

        with pytest.raises(APIError, match="Rate limited \\(429\\) after|HTTP 503"):
            sf.http("GET", "/test")

        assert mock_request.call_count == 3  # Initial + 2 retries

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep, mock_request):
        """Test exponential backoff calculation."""
        sf = Salesforce(
            session_id="test-session",
            instance_url="https://test.salesforce.com",
            max_retries=3,
            retry_delay=2.0,
            retry_backoff=True,
        )

        mock_request.side_effect = [
            Mock(status_code=503, content=b"{}", headers={"Content-Type": "application/json"}),
            Mock(status_code=503, content=b"{}", headers={"Content-Type": "application/json"}),
            Mock(status_code=503, content=b"{}", headers={"Content-Type": "application/json"}),
            Mock(status_code=200, content=b'{"success": true}', headers={"Content-Type": "application/json"}),
        ]

        sf.http("GET", "/test")

        # Check sleep calls for exponential backoff: 2.0, 4.0, 8.0
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [2.0, 4.0, 8.0]

    @patch("forcepy.client.requests.Session.request")
    @patch("time.sleep")
    def test_no_backoff(self, mock_sleep, mock_request):
        """Test fixed delay without backoff."""
        sf = Salesforce(
            session_id="test-session",
            instance_url="https://test.salesforce.com",
            max_retries=2,
            retry_delay=5.0,
            retry_backoff=False,
        )

        mock_request.side_effect = [
            Mock(status_code=503, content=b"{}", headers={"Content-Type": "application/json"}),
            Mock(status_code=503, content=b"{}", headers={"Content-Type": "application/json"}),
            Mock(status_code=200, content=b'{"success": true}', headers={"Content-Type": "application/json"}),
        ]

        sf.http("GET", "/test")

        # Check sleep calls for fixed delay: 5.0, 5.0
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [5.0, 5.0]


class TestManualPagination:
    """Test manual pagination control."""

    @patch("forcepy.client.Salesforce.http")
    def test_query_pagination_metadata(self, mock_http):
        """Test that query() stores pagination metadata."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_http.return_value = {
            "records": [{"Id": "001", "Name": "Test"}],
            "nextRecordsUrl": "/services/data/v53.0/query/01gxx-xxx",
            "done": False,
            "totalSize": 2500,
        }

        results = sf.query("SELECT Id, Name FROM Account")

        assert isinstance(results, SobjectSet)
        assert len(results) == 1
        assert results.next_records_url == "/services/data/v53.0/query/01gxx-xxx"
        assert results.done is False
        assert results.total_size == 2500

    @patch("forcepy.client.Salesforce.http")
    def test_query_more(self, mock_http):
        """Test query_more() method."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_http.return_value = {
            "records": [{"Id": "002", "Name": "Test 2"}],
            "nextRecordsUrl": None,
            "done": True,
            "totalSize": 2500,
        }

        results = sf.query_more("/services/data/v53.0/query/01gxx-xxx")

        assert isinstance(results, SobjectSet)
        assert len(results) == 1
        assert results.next_records_url is None
        assert results.done is True

    @patch("forcepy.client.Salesforce.http")
    def test_query_pagination_loop(self, mock_http):
        """Test manual pagination loop."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        # Mock two pages of results
        mock_http.side_effect = [
            {"records": [{"Id": "001"}], "nextRecordsUrl": "/query/page2", "done": False, "totalSize": 2},
            {"records": [{"Id": "002"}], "nextRecordsUrl": None, "done": True, "totalSize": 2},
        ]

        all_records = []
        results = sf.query("SELECT Id FROM Account")
        all_records.extend(results)

        while not results.done:
            results = sf.query_more(results.next_records_url)
            all_records.extend(results)

        assert len(all_records) == 2
        assert mock_http.call_count == 2


class TestExpandSelectStarParameter:
    """Test expand_select_star parameter in query()."""

    @patch("forcepy.client.Salesforce.describe")
    @patch("forcepy.client.Salesforce.http")
    def test_query_with_expand_parameter(self, mock_http, mock_describe):
        """Test query() with expand_select_star=True."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        # Mock describe to return field list
        field1 = Mock()
        field1.get = Mock(side_effect=lambda k, d=None: "Id" if k == "name" else d)

        field2 = Mock()
        field2.get = Mock(side_effect=lambda k, d=None: "Name" if k == "name" else d)

        mock_describe_obj = Mock()
        mock_describe_obj.fields = [field1, field2]  # Make fields iterable
        mock_describe.return_value = mock_describe_obj

        mock_http.return_value = {"records": [{"Id": "001", "Name": "Test"}], "done": True}

        sf.query("SELECT * FROM Account LIMIT 1", expand_select_star=True)

        # Check that http was called (expansion happened)
        assert mock_http.called
        # Check that describe was called
        assert mock_describe.called
        # Check that SELECT * was expanded
        call_args = mock_http.call_args
        query_param = call_args[1]["params"]["q"]
        # After expansion, should have field names
        assert ("Id" in query_param and "Name" in query_param) or "SELECT *" not in query_param

    @patch("forcepy.client.Salesforce.http")
    def test_query_without_expand_parameter(self, mock_http):
        """Test query() without expand_select_star (default False)."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_http.return_value = {"records": [], "done": True}

        # Should not try to expand
        sf.query("SELECT * FROM Account", expand_select_star=False)

        # Check the query was passed as-is
        call_args = mock_http.call_args
        assert "SELECT *" in call_args[1]["params"]["q"]


class TestIterqueryThreading:
    """Test iterquery with threading support."""

    @patch("forcepy.client.Salesforce.http")
    def test_iterquery_yields_pages(self, mock_http):
        """Test that iterquery yields SobjectSet pages."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_http.side_effect = [
            {"records": [{"Id": f"00{i}"} for i in range(3)], "nextRecordsUrl": "/query/page2", "done": False},
            {"records": [{"Id": f"01{i}"} for i in range(2)], "nextRecordsUrl": None, "done": True},
        ]

        pages = list(sf.iterquery("SELECT Id FROM Account", threaded=False))

        assert len(pages) == 2
        assert isinstance(pages[0], SobjectSet)
        assert len(pages[0]) == 3
        assert len(pages[1]) == 2

    @patch("forcepy.client.Salesforce.http")
    def test_iterquery_with_threading(self, mock_http):
        """Test iterquery with threaded=True."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_http.side_effect = [
            {"records": [{"Id": f"00{i}"} for i in range(3)], "nextRecordsUrl": "/query/page2", "done": False},
            {"records": [{"Id": f"01{i}"} for i in range(2)], "nextRecordsUrl": None, "done": True},
        ]

        pages = list(sf.iterquery("SELECT Id FROM Account", threaded=True))

        assert len(pages) == 2
        assert isinstance(pages[0], SobjectSet)
        assert len(pages[0]) == 3
        assert len(pages[1]) == 2


class TestDependentPicklists:
    """Test dependent picklist support."""

    def test_decode_validfor_bitmap(self):
        """Test validFor bitmap decoding."""
        from forcepy.utils import decode_validfor_bitmap

        # Test bitmap: 10000000 (first bit set)
        bitmap = base64.b64encode(b"\x80").decode("ascii")
        assert decode_validfor_bitmap(bitmap, 0) is True
        assert decode_validfor_bitmap(bitmap, 1) is False

        # Test bitmap: 01000000 (second bit set)
        bitmap = base64.b64encode(b"\x40").decode("ascii")
        assert decode_validfor_bitmap(bitmap, 0) is False
        assert decode_validfor_bitmap(bitmap, 1) is True

    def test_get_dependent_picklist_values(self):
        """Test ObjectDescribe.get_dependent_picklist_values()."""
        from forcepy.metadata import ObjectDescribe

        describe_data = {
            "name": "Case",
            "fields": [
                {
                    "name": "Category__c",
                    "type": "picklist",
                    "picklistValues": [
                        {"value": "Hardware", "label": "Hardware", "active": True},
                        {"value": "Software", "label": "Software", "active": True},
                    ],
                },
                {
                    "name": "Sub_Category__c",
                    "type": "picklist",
                    "controllerName": "Category__c",
                    "picklistValues": [
                        {
                            "value": "Laptop",
                            "label": "Laptop",
                            "active": True,
                            "validFor": base64.b64encode(b"\x80").decode("ascii"),  # Valid for index 0 (Hardware)
                        },
                        {
                            "value": "Desktop",
                            "label": "Desktop",
                            "active": True,
                            "validFor": base64.b64encode(b"\x80").decode("ascii"),  # Valid for index 0 (Hardware)
                        },
                        {
                            "value": "Bug",
                            "label": "Bug",
                            "active": True,
                            "validFor": base64.b64encode(b"\x40").decode("ascii"),  # Valid for index 1 (Software)
                        },
                    ],
                },
            ],
        }

        describe = ObjectDescribe(describe_data)

        # Get values for Hardware
        hardware_values = describe.get_dependent_picklist_values("Sub_Category__c", controlling_value="Hardware")
        assert len(hardware_values) == 2
        assert hardware_values[0]["value"] == "Laptop"
        assert hardware_values[1]["value"] == "Desktop"

        # Get values for Software
        software_values = describe.get_dependent_picklist_values("Sub_Category__c", controlling_value="Software")
        assert len(software_values) == 1
        assert software_values[0]["value"] == "Bug"

    @patch("forcepy.client.Salesforce.describe")
    def test_get_picklist_values_client_method(self, mock_describe):
        """Test Salesforce.get_picklist_values() client method."""
        sf = Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

        mock_describe_obj = Mock()
        mock_describe_obj.get_dependent_picklist_values.return_value = [{"value": "Laptop", "label": "Laptop"}]
        mock_describe.return_value = mock_describe_obj

        values = sf.get_picklist_values("Case", "Sub_Category__c", controlling_value="Hardware")

        assert len(values) == 1
        assert values[0]["value"] == "Laptop"
        mock_describe.assert_called_once_with("Case")
        mock_describe_obj.get_dependent_picklist_values.assert_called_once()
