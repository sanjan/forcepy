"""Tests for security token parameter."""

from unittest.mock import patch

from forcepy import Salesforce


class TestSecurityToken:
    """Test security token functionality."""

    def test_security_token_appended_to_password(self):
        """Test that security token is appended to password in __init__."""
        sf = Salesforce(
            username="user@example.com",
            password="mypassword",
            security_token="ABC123",
            session_id="dummy",  # Skip auto-login
        )
        assert sf.password == "mypasswordABC123"
        assert sf.security_token == "ABC123"

    def test_no_security_token_password_unchanged(self):
        """Test that password is unchanged when no security token provided."""
        sf = Salesforce(
            username="user@example.com",
            password="mypassword",
            session_id="dummy",  # Skip auto-login
        )
        assert sf.password == "mypassword"
        assert sf.security_token is None

    def test_security_token_none_password_unchanged(self):
        """Test that password is unchanged when security_token is None."""
        sf = Salesforce(
            username="user@example.com",
            password="mypassword",
            security_token=None,
            session_id="dummy",  # Skip auto-login
        )
        assert sf.password == "mypassword"
        assert sf.security_token is None

    def test_no_password_with_security_token(self):
        """Test that security token without password doesn't break."""
        sf = Salesforce(
            username="user@example.com",
            password=None,
            security_token="ABC123",
            session_id="dummy",  # Skip auto-login
        )
        assert sf.password is None
        assert sf.security_token == "ABC123"

    @patch("forcepy.client.auth.soap_login")
    def test_login_with_security_token_in_kwargs(self, mock_login):
        """Test that login() appends security token from kwargs."""
        mock_login.return_value = ("mock_session", "https://na1.salesforce.com")

        sf = Salesforce()
        sf.login(username="user@example.com", password="mypassword", security_token="TOKEN123")

        # Verify soap_login was called with password+token
        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args
        assert call_kwargs[1]["password"] == "mypasswordTOKEN123"

    @patch("forcepy.client.auth.soap_login")
    def test_login_uses_instance_security_token(self, mock_login):
        """Test that login() uses instance security_token if not in kwargs."""
        mock_login.return_value = ("mock_session", "https://na1.salesforce.com")

        sf = Salesforce(
            username="user@example.com",
            password="mypassword",
            security_token="INSTANCE_TOKEN",
            session_id="dummy",  # Skip auto-login in __init__
        )

        # Manually call login (without passing security_token in kwargs)
        # Reset password to simulate calling with different password
        sf.password = "differentpass"
        sf.login()

        # Should use instance security_token
        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args
        # Should have appended INSTANCE_TOKEN to the current password
        assert call_kwargs[1]["password"] == "differentpassINSTANCE_TOKEN"

    @patch("forcepy.client.auth.soap_login")
    def test_login_does_not_double_append_token(self, mock_login):
        """Test that security token is not appended twice."""
        mock_login.return_value = ("mock_session", "https://na1.salesforce.com")

        sf = Salesforce(
            username="user@example.com",
            password="mypasswordTOKEN123",  # Already has token
            security_token="TOKEN123",
            session_id="dummy",
        )

        # Password should already have token from __init__
        assert sf.password == "mypasswordTOKEN123TOKEN123"

        # When login is called, it should check if token is already appended
        sf.password = "mypasswordTOKEN123"  # Reset to single token
        sf.login()

        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args
        # Should not double-append (the endswith check prevents this)
        assert call_kwargs[1]["password"] == "mypasswordTOKEN123"

    def test_empty_security_token_string(self):
        """Test that empty string security token doesn't append anything."""
        sf = Salesforce(username="user@example.com", password="mypassword", security_token="", session_id="dummy")
        # Empty string is falsy in Python, so no append
        assert sf.password == "mypassword"

    @patch("forcepy.client.auth.soap_login")
    def test_auto_login_with_security_token(self, mock_login):
        """Test that auto-login works with security token."""
        mock_login.return_value = ("mock_session", "https://na1.salesforce.com")

        # This should trigger auto-login
        sf = Salesforce(username="user@example.com", password="mypassword", security_token="AUTO_TOKEN")

        # Verify soap_login was called with password+token
        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args
        assert call_kwargs[1]["password"] == "mypasswordAUTO_TOKEN"
