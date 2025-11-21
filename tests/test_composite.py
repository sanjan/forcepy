"""Tests for Composite API."""

import pytest

from forcepy.composite import (
    CompositeError,
    CompositeRequest,
    CompositeResponse,
    CompositeSubResponse,
    validate_composite_response,
)


class TestCompositeSubResponse:
    """Test CompositeSubResponse class."""

    def test_success_response(self):
        """Test successful subrequest response."""
        response_data = {
            "referenceId": "NewAccount",
            "httpStatusCode": 201,
            "body": {"id": "001xx000003DGbQ", "success": True},
        }
        sub_response = CompositeSubResponse(response_data)

        assert sub_response.reference_id == "NewAccount"
        assert sub_response.http_status_code == 201
        assert sub_response.is_success()
        assert sub_response.body["id"] == "001xx000003DGbQ"

    def test_error_response(self):
        """Test error subrequest response."""
        response_data = {"referenceId": "FailedRequest", "httpStatusCode": 400, "body": [{"message": "Required field missing"}]}
        sub_response = CompositeSubResponse(response_data)

        assert sub_response.reference_id == "FailedRequest"
        assert sub_response.http_status_code == 400
        assert not sub_response.is_success()


class TestCompositeResponse:
    """Test CompositeResponse class."""

    @pytest.fixture
    def success_response(self):
        """Create a successful composite response."""
        return CompositeResponse(
            {
                "compositeResponse": [
                    {"referenceId": "NewAccount", "httpStatusCode": 201, "body": {"id": "001xx000003DGbQ", "success": True}},
                    {"referenceId": "GetAccount", "httpStatusCode": 200, "body": {"Id": "001xx000003DGbQ", "Name": "Test"}},
                ]
            }
        )

    @pytest.fixture
    def mixed_response(self):
        """Create a mixed success/failure composite response."""
        return CompositeResponse(
            {
                "compositeResponse": [
                    {"referenceId": "NewAccount", "httpStatusCode": 201, "body": {"id": "001xx000003DGbQ"}},
                    {"referenceId": "FailedRequest", "httpStatusCode": 400, "body": [{"message": "Error"}]},
                ]
            }
        )

    def test_get_by_reference_id(self, success_response):
        """Test getting subrequest by reference ID."""
        sub_response = success_response.get("NewAccount")
        assert sub_response is not None
        assert sub_response.reference_id == "NewAccount"
        assert sub_response.http_status_code == 201

    def test_get_missing_reference_id(self, success_response):
        """Test getting non-existent reference ID."""
        sub_response = success_response.get("NonExistent")
        assert sub_response is None

    def test_getitem_access(self, success_response):
        """Test dict-like access with brackets."""
        sub_response = success_response["GetAccount"]
        assert sub_response.reference_id == "GetAccount"
        assert sub_response.http_status_code == 200

    def test_getitem_missing_raises_keyerror(self, success_response):
        """Test dict access with missing key raises KeyError."""
        with pytest.raises(KeyError, match="NonExistent"):
            success_response["NonExistent"]

    def test_all_succeeded_true(self, success_response):
        """Test all_succeeded returns True when all succeed."""
        assert success_response.all_succeeded()

    def test_all_succeeded_false(self, mixed_response):
        """Test all_succeeded returns False when any fail."""
        assert not mixed_response.all_succeeded()

    def test_get_errors(self, mixed_response):
        """Test getting error responses."""
        errors = mixed_response.get_errors()
        assert len(errors) == 1
        assert errors[0]["referenceId"] == "FailedRequest"
        assert errors[0]["httpStatusCode"] == 400

    def test_iteration(self, success_response):
        """Test iterating over responses."""
        responses = list(success_response)
        assert len(responses) == 2
        assert all(isinstance(r, CompositeSubResponse) for r in responses)

    def test_length(self, success_response):
        """Test getting number of responses."""
        assert len(success_response) == 2


class TestCompositeRequest:
    """Test CompositeRequest builder."""

    @pytest.fixture
    def mock_client(self, mocker):
        """Create a mock Salesforce client."""
        client = mocker.Mock()
        client.version = "53.0"
        client.http = mocker.Mock(
            return_value={
                "compositeResponse": [
                    {"referenceId": "NewAccount", "httpStatusCode": 201, "body": {"id": "001xx", "success": True}}
                ]
            }
        )
        return client

    def test_add_subrequest(self, mock_client):
        """Test adding a subrequest."""
        composite = CompositeRequest(mock_client)
        composite.add("POST", "/services/data/v53.0/sobjects/Account", "NewAccount", body={"Name": "Test"})

        assert len(composite) == 1
        assert composite.subrequests[0]["method"] == "POST"
        assert composite.subrequests[0]["referenceId"] == "NewAccount"

    def test_post_shortcut(self, mock_client):
        """Test POST shortcut method."""
        composite = CompositeRequest(mock_client)
        composite.post("/services/data/v53.0/sobjects/Account", "NewAccount", body={"Name": "Test"})

        assert composite.subrequests[0]["method"] == "POST"

    def test_get_shortcut(self, mock_client):
        """Test GET shortcut method."""
        composite = CompositeRequest(mock_client)
        composite.get("/services/data/v53.0/sobjects/Account/001xx", "GetAccount")

        assert composite.subrequests[0]["method"] == "GET"
        assert "body" not in composite.subrequests[0]

    def test_patch_shortcut(self, mock_client):
        """Test PATCH shortcut method."""
        composite = CompositeRequest(mock_client)
        composite.patch("/services/data/v53.0/sobjects/Account/001xx", "UpdateAccount", body={"Name": "Updated"})

        assert composite.subrequests[0]["method"] == "PATCH"

    def test_delete_shortcut(self, mock_client):
        """Test DELETE shortcut method."""
        composite = CompositeRequest(mock_client)
        composite.delete("/services/data/v53.0/sobjects/Account/001xx", "DeleteAccount")

        assert composite.subrequests[0]["method"] == "DELETE"

    def test_chaining(self, mock_client):
        """Test method chaining."""
        composite = (
            CompositeRequest(mock_client)
            .post("/services/data/v53.0/sobjects/Account", "NewAccount", body={"Name": "Test"})
            .get("/services/data/v53.0/sobjects/Account/@{NewAccount.id}", "GetAccount")
        )

        assert len(composite) == 2

    def test_execute_empty_fails(self, mock_client):
        """Test executing empty composite fails."""
        composite = CompositeRequest(mock_client)
        with pytest.raises(ValueError, match="No subrequests"):
            composite.execute()

    def test_execute_too_many_fails(self, mock_client):
        """Test executing with > 25 subrequests fails."""
        composite = CompositeRequest(mock_client)
        for i in range(26):
            composite.add("GET", f"/services/data/v53.0/sobjects/Account/{i}", f"req{i}")

        with pytest.raises(ValueError, match="Too many subrequests"):
            composite.execute()

    def test_execute_success(self, mock_client):
        """Test successful execution."""
        composite = CompositeRequest(mock_client)
        composite.post("/services/data/v53.0/sobjects/Account", "NewAccount", body={"Name": "Test"})

        response = composite.execute()

        assert isinstance(response, CompositeResponse)
        mock_client.http.assert_called_once()
        call_args = mock_client.http.call_args
        assert call_args[0][0] == "POST"
        assert "/composite" in call_args[0][1]

    def test_execute_all_or_none_failure(self, mock_client):
        """Test allOrNone=True raises on failure."""
        mock_client.http.return_value = {
            "compositeResponse": [
                {"referenceId": "NewAccount", "httpStatusCode": 400, "body": [{"message": "Error"}]}
            ]
        }

        composite = CompositeRequest(mock_client, all_or_none=True)
        composite.post("/services/data/v53.0/sobjects/Account", "NewAccount", body={"Name": "Test"})

        with pytest.raises(CompositeError, match="Composite request failed"):
            composite.execute()


class TestValidateCompositeResponse:
    """Test validate_composite_response function."""

    def test_validate_success(self):
        """Test validating successful response."""
        response = CompositeResponse(
            {"compositeResponse": [{"referenceId": "req1", "httpStatusCode": 200, "body": {}}]}
        )

        assert validate_composite_response(response)

    def test_validate_failure_raises(self):
        """Test validating failed response raises error."""
        response = CompositeResponse(
            {"compositeResponse": [{"referenceId": "req1", "httpStatusCode": 400, "body": {"message": "Error"}}]}
        )

        with pytest.raises(CompositeError, match="Composite request had 1 failure"):
            validate_composite_response(response)

    def test_validate_failure_no_raise(self):
        """Test validating failed response without raising."""
        response = CompositeResponse(
            {"compositeResponse": [{"referenceId": "req1", "httpStatusCode": 400, "body": {}}]}
        )

        assert not validate_composite_response(response, raise_on_error=False)

