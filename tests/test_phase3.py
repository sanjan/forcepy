"""Tests for Phase 3 features: session info and composite context manager."""

import time
from unittest.mock import Mock, patch

from forcepy import Salesforce


class TestSessionInfo:
    """Test session info properties."""

    @patch('forcepy.client.Salesforce.http')
    def test_session_info_after_login(self, mock_http):
        """Test that session info is captured after login."""
        # Mock userinfo response
        mock_http.return_value = {
            'user_id': '005B0000000hMtx',
            'username': 'user@example.com'
        }

        with patch('forcepy.auth.soap_login') as mock_soap:
            mock_soap.return_value = ('session-id-123', 'https://na1.salesforce.com')

            sf = Salesforce()
            sf.login(username='user@example.com', password='password')

        # Check session info properties
        assert sf.user_id == '005B0000000hMtx'
        assert sf.session_expires is not None
        assert sf.session_expires > time.time()  # Should be in the future

    def test_last_request_time_tracked(self):
        """Test that last_request_time is updated."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        assert sf.last_request_time is None  # No requests yet

        # Manually call http method (not via query, which would need more mocking)
        with patch.object(sf.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"records": [], "done": true}'
            mock_response.json.return_value = {'records': [], 'done': True}
            mock_request.return_value = mock_response

            before = time.time()
            sf.http("GET", "/services/data/v53.0/query", params={'q': 'SELECT Id FROM Account'})
            after = time.time()

        assert sf.last_request_time is not None
        assert before <= sf.last_request_time <= after

    def test_session_info_properties_default_none(self):
        """Test that session info properties default to None."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        # Should be None before login
        assert sf.user_id is None
        assert sf.session_expires is None
        assert sf.last_request_time is None

    @patch('forcepy.client.Salesforce.http')
    def test_user_id_from_cached_token(self, mock_http):
        """Test that user_id is restored from cached token."""
        # Use a shared cache instance
        from forcepy.token_cache import MemoryCache
        shared_cache = MemoryCache()

        with patch('forcepy.auth.soap_login') as mock_soap:
            mock_soap.return_value = ('session-id-123', 'https://na1.salesforce.com')

            # Mock userinfo to return user_id
            mock_http.return_value = {
                'user_id': '005B0000000hMtx',
                'username': 'user@example.com'
            }

            # First login - will cache token with user_id
            sf1 = Salesforce(
                username='user@example.com',
                password='password',
                cache_backend=shared_cache  # Use the shared cache
            )

            assert sf1.user_id == '005B0000000hMtx'

        # Second client with the same shared cache - should restore user_id from cache
        sf2 = Salesforce(
            username='user@example.com',
            password='password',
            cache_backend=shared_cache  # Same cache instance
        )

        # user_id should be restored from cache
        assert sf2.user_id == '005B0000000hMtx'
        # soap_login should only have been called once (for sf1)
        assert mock_soap.call_count == 1


class TestCompositeContextManager:
    """Test composite context manager (with statement)."""

    @patch('forcepy.client.Salesforce.http')
    def test_context_manager_basic(self, mock_http):
        """Test basic context manager usage."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        # Mock composite response
        mock_http.return_value = {
            'compositeResponse': [
                {'httpStatusCode': 201, 'referenceId': 'request_0'},
                {'httpStatusCode': 204, 'referenceId': 'request_1'}
            ]
        }

        with sf as batch:
            # These should be queued, not executed immediately
            batch.sobjects.Account.post(Name='Account 1')
            batch.sobjects.Account.post(Name='Account 2')

        # After exiting context, composite request should have been made
        mock_http.assert_called_once()
        call_args = mock_http.call_args
        assert call_args[0][0] == 'POST'  # Method
        assert 'composite' in call_args[0][1]  # URL

        # Check composite request structure
        composite_request = call_args[1]['json']
        assert 'compositeRequest' in composite_request
        assert len(composite_request['compositeRequest']) == 2

    @patch('forcepy.client.Salesforce.http')
    def test_context_manager_mixed_operations(self, mock_http):
        """Test context manager with mixed CRUD operations."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        mock_http.return_value = {
            'compositeResponse': [
                {'httpStatusCode': 201, 'referenceId': 'request_0'},
                {'httpStatusCode': 204, 'referenceId': 'request_1'},
                {'httpStatusCode': 204, 'referenceId': 'request_2'}
            ]
        }

        with sf as batch:
            batch.sobjects.Account.post(Name='New Account')
            batch.sobjects.Account['account-id'].patch(Industry='Technology')
            batch.sobjects.Contact['contact-id'].delete()

        # Check all operations were batched
        call_args = mock_http.call_args
        composite_request = call_args[1]['json']['compositeRequest']

        assert len(composite_request) == 3
        assert composite_request[0]['method'] == 'POST'
        assert composite_request[1]['method'] == 'PATCH'
        assert composite_request[2]['method'] == 'DELETE'

    @patch('forcepy.client.Salesforce.http')
    def test_context_manager_returns_placeholder(self, mock_http):
        """Test that operations in context return placeholder with referenceId."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        mock_http.return_value = {'compositeResponse': []}

        with sf as batch:
            result = batch.sobjects.Account.post(Name='Test')
            # Should return placeholder, not actual HTTP response
            assert isinstance(result, dict)
            assert 'referenceId' in result

    @patch('forcepy.client.Salesforce.http')
    def test_context_manager_exception_handling(self, mock_http):
        """Test that context manager handles exceptions properly."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        try:
            with sf as batch:
                batch.sobjects.Account.post(Name='Test')
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Composite request should NOT be executed due to exception
        mock_http.assert_not_called()

    @patch('forcepy.client.Salesforce.http')
    def test_context_manager_resets_batch_mode(self, mock_http):
        """Test that batch mode is reset after context exit."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        assert sf._batch_mode is False

        mock_http.return_value = {'compositeResponse': []}

        with sf as batch:
            assert batch._batch_mode is True

        # After exit, batch mode should be reset
        assert sf._batch_mode is False
        assert len(sf._batch_requests) == 0

    @patch('forcepy.client.Salesforce.http')
    def test_normal_operations_outside_context(self, mock_http):
        """Test that normal operations work outside context manager."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        # Outside context, operations should execute normally
        mock_http.return_value = {'id': 'account-123', 'success': True}

        result = sf.sobjects.Account.post(Name='Normal Operation')

        # Should return actual HTTP response, not placeholder
        assert result == {'id': 'account-123', 'success': True}
        assert mock_http.called

    @patch('forcepy.client.Salesforce.http')
    def test_empty_context_manager(self, mock_http):
        """Test context manager with no operations."""
        sf = Salesforce(
            session_id='test-session',
            instance_url='https://test.salesforce.com'
        )

        with sf:
            # No operations
            pass

        # Should not make any HTTP calls for empty batch
        mock_http.assert_not_called()

