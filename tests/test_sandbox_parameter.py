"""Tests for sandbox parameter."""

from forcepy import Salesforce


class TestSandboxParameter:
    """Test sandbox parameter behavior."""

    def test_default_production_url(self):
        """Test that default is production URL."""
        sf = Salesforce()
        assert sf.base_url == "https://login.salesforce.com"
        assert sf.sandbox is False

    def test_sandbox_true_uses_test_url(self):
        """Test that sandbox=True uses test.salesforce.com."""
        sf = Salesforce(sandbox=True)
        assert sf.base_url == "https://test.salesforce.com"
        assert sf.sandbox is True

    def test_sandbox_false_uses_login_url(self):
        """Test that sandbox=False uses login.salesforce.com."""
        sf = Salesforce(sandbox=False)
        assert sf.base_url == "https://login.salesforce.com"
        assert sf.sandbox is False

    def test_explicit_base_url_overrides_sandbox(self):
        """Test that explicit base_url overrides sandbox parameter."""
        sf = Salesforce(base_url="https://custom.salesforce.com", sandbox=True)
        assert sf.base_url == "https://custom.salesforce.com"
        # sandbox flag is still set
        assert sf.sandbox is True

    def test_get_login_url_returns_base_url(self):
        """Test that get_login_url returns the configured base_url."""
        # Production
        sf_prod = Salesforce()
        assert sf_prod.get_login_url() == "https://login.salesforce.com"

        # Sandbox
        sf_sandbox = Salesforce(sandbox=True)
        assert sf_sandbox.get_login_url() == "https://test.salesforce.com"

        # Custom
        sf_custom = Salesforce(base_url="https://custom.my.salesforce.com")
        assert sf_custom.get_login_url() == "https://custom.my.salesforce.com"

    def test_sandbox_with_credentials_no_auth_attempt(self):
        """Test that sandbox parameter doesn't break credential storage."""
        # We don't want to actually authenticate in unit tests
        # Just verify the parameters are stored correctly
        sf = Salesforce(
            username="user@example.com",
            password="pass",
            sandbox=True,
            session_id="dummy",  # Provide session_id to skip auto-login
        )
        assert sf.username == "user@example.com"
        assert sf.password == "pass"
        assert sf.sandbox is True
        assert sf.base_url == "https://test.salesforce.com"
