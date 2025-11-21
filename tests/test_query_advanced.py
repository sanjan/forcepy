"""Tests for advanced query features."""

import pytest

from forcepy.query_advanced import (
    WorkbenchConfig,
    _extract_sobject_from_query,
    expand_select_star,
    format_soql,
    generate_soql_explorer_url,
    generate_workbench_url,
)


class TestExtractSobjectFromQuery:
    """Test sobject extraction from SOQL."""

    def test_simple_query(self):
        """Test extracting from simple query."""
        soql = "SELECT Id FROM Account"
        assert _extract_sobject_from_query(soql) == "Account"

    def test_with_where_clause(self):
        """Test extracting with WHERE clause."""
        soql = "SELECT Id, Name FROM Contact WHERE LastName = 'Smith'"
        assert _extract_sobject_from_query(soql) == "Contact"

    def test_with_order_by(self):
        """Test extracting with ORDER BY."""
        soql = "SELECT * FROM Case ORDER BY CreatedDate DESC"
        assert _extract_sobject_from_query(soql) == "Case"

    def test_with_limit(self):
        """Test extracting with LIMIT."""
        soql = "SELECT Id FROM Account LIMIT 10"
        assert _extract_sobject_from_query(soql) == "Account"

    def test_case_insensitive(self):
        """Test case insensitive extraction."""
        soql = "select id from account"
        assert _extract_sobject_from_query(soql) == "account"

    def test_no_from_clause(self):
        """Test query without FROM clause."""
        soql = "SELECT Id"
        assert _extract_sobject_from_query(soql) is None


class TestExpandSelectStar:
    """Test SELECT * expansion."""

    @pytest.fixture
    def mock_describe_func(self, mocker):
        """Create a mock describe function."""

        def describe(sobject_name):
            mock = mocker.Mock()
            mock.fields = [
                mocker.Mock(**{"get.return_value": "Id"}),
                mocker.Mock(**{"get.return_value": "Name"}),
                mocker.Mock(**{"get.return_value": "Industry"}),
                mocker.Mock(**{"get.return_value": "attributes"}),  # Should be excluded
            ]
            # Make each field's get() method work properly
            for i, field in enumerate(mock.fields[:-1]):  # Exclude attributes
                field.get.side_effect = lambda key, default=None, idx=i: ["Id", "Name", "Industry"][idx] if key == "name" else None

            # Special handling for attributes field
            mock.fields[-1].get.side_effect = lambda key, default=None: "attributes" if key == "name" else None

            return mock

        return describe

    def test_expand_simple_query(self, mock_describe_func):
        """Test expanding simple query."""
        soql = "SELECT * FROM Account"
        expanded = expand_select_star(soql, mock_describe_func, "Account")
        assert "Id, Name, Industry" in expanded
        assert "attributes" not in expanded
        assert "FROM Account" in expanded

    def test_expand_with_where(self, mock_describe_func):
        """Test expanding query with WHERE."""
        soql = "SELECT * FROM Account WHERE Name LIKE 'A%'"
        expanded = expand_select_star(soql, mock_describe_func, "Account")
        assert "Id, Name, Industry" in expanded
        assert "WHERE Name LIKE 'A%'" in expanded

    def test_no_star_unchanged(self, mock_describe_func):
        """Test query without * is unchanged."""
        soql = "SELECT Id, Name FROM Account"
        expanded = expand_select_star(soql, mock_describe_func, "Account")
        assert expanded == soql

    def test_auto_detect_sobject(self, mock_describe_func):
        """Test auto-detecting sobject from query."""
        soql = "SELECT * FROM Account LIMIT 10"
        expanded = expand_select_star(soql, mock_describe_func)
        assert "Id, Name, Industry" in expanded

    def test_missing_sobject_raises(self, mock_describe_func):
        """Test missing sobject raises error."""
        soql = "SELECT *"
        with pytest.raises(ValueError, match="Could not determine sobject"):
            expand_select_star(soql, mock_describe_func)


class TestGenerateWorkbenchUrl:
    """Test Workbench URL generation."""

    def test_basic_url(self):
        """Test basic URL generation."""
        soql = "SELECT Id FROM Account"
        instance_url = "https://na1.salesforce.com"
        url = generate_workbench_url(soql, instance_url)

        assert "workbench.developerforce.com" in url
        assert "query.php" in url
        assert "SELECT" in url
        assert "instance=na1" in url

    def test_custom_workbench_url(self):
        """Test custom Workbench base URL."""
        soql = "SELECT Id FROM Account"
        instance_url = "https://cs1.salesforce.com"
        custom_base = "https://workbench.mycompany.com"
        url = generate_workbench_url(soql, instance_url, custom_base)

        assert "workbench.mycompany.com" in url
        assert "instance=cs1" in url

    def test_url_encoding(self):
        """Test special characters are URL encoded."""
        soql = "SELECT Id, Name FROM Account WHERE Name = 'Test & Co.'"
        instance_url = "https://na1.salesforce.com"
        url = generate_workbench_url(soql, instance_url)

        # & should be encoded as %26
        assert "%26" in url


class TestGenerateSoqlExplorerUrl:
    """Test SOQL Explorer URL generation."""

    def test_basic_url(self):
        """Test basic URL generation."""
        soql = "SELECT Id FROM Account"
        instance_url = "https://na1.salesforce.com"
        url = generate_soql_explorer_url(soql, instance_url)

        assert instance_url in url
        assert "ApexCSIPage" in url
        assert "query=" in url


class TestWorkbenchConfig:
    """Test WorkbenchConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = WorkbenchConfig()
        assert "workbench.developerforce.com" in config.base_url

    def test_custom_config(self):
        """Test custom configuration."""
        custom_url = "https://workbench.example.com"
        config = WorkbenchConfig(custom_url)
        assert config.base_url == custom_url

    def test_trailing_slash_removed(self):
        """Test trailing slash is removed."""
        config = WorkbenchConfig("https://workbench.example.com/")
        assert config.base_url == "https://workbench.example.com"

    def test_generate_url(self):
        """Test URL generation with config."""
        config = WorkbenchConfig("https://workbench.mycompany.com")
        soql = "SELECT Id FROM Account"
        instance_url = "https://na1.salesforce.com"
        url = config.generate_url(soql, instance_url)

        assert "workbench.mycompany.com" in url


class TestFormatSoql:
    """Test SOQL formatting."""

    def test_format_simple_query(self):
        """Test formatting simple query."""
        soql = "SELECT Id, Name FROM Account"
        formatted = format_soql(soql)

        assert "SELECT" in formatted
        assert "FROM Account" in formatted
        # Check that output has multiple lines
        lines = formatted.split("\n")
        assert len(lines) >= 2

    def test_format_with_where(self):
        """Test formatting query with WHERE."""
        soql = "SELECT Id, Name FROM Account WHERE Name LIKE 'A%'"
        formatted = format_soql(soql)

        assert "SELECT" in formatted
        assert "FROM Account" in formatted
        assert "WHERE" in formatted

    def test_format_complex_query(self):
        """Test formatting complex query."""
        soql = "SELECT Id, Name, Industry FROM Account WHERE Name LIKE 'A%' ORDER BY Name LIMIT 10"
        formatted = format_soql(soql)

        assert "SELECT" in formatted
        assert "FROM Account" in formatted
        assert "WHERE" in formatted
        assert "ORDER BY Name" in formatted
        assert "LIMIT 10" in formatted

