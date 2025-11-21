"""Tests for query building helpers."""

from datetime import datetime

from forcepy.query_helpers import compile_where_clause, prettyprint_soql


class TestCompileWhereClause:
    """Test compile_where_clause function."""

    def test_simple_equality(self):
        """Test simple equality condition."""
        clause = compile_where_clause(Status='New')
        assert clause == "Status='New'"

    def test_multiple_equality(self):
        """Test multiple equality conditions."""
        clause = compile_where_clause(Status='New', Priority='High')
        assert "Status='New'" in clause
        assert "Priority='High'" in clause
        assert " AND " in clause

    def test_in_operator(self):
        """Test IN operator."""
        clause = compile_where_clause(Status__in=['New', 'In Progress'])
        # Order may vary, so check both possibilities
        assert "Status IN" in clause
        assert "'New'" in clause
        assert "'In Progress'" in clause

    def test_gt_operator(self):
        """Test greater than operator."""
        clause = compile_where_clause(Amount__gt=1000)
        assert "Amount>1000" in clause

    def test_lt_operator(self):
        """Test less than operator."""
        clause = compile_where_clause(Amount__lt=500)
        assert "Amount<500" in clause

    def test_gte_operator(self):
        """Test greater than or equal operator."""
        clause = compile_where_clause(Amount__gte=1000)
        assert "Amount>=1000" in clause

    def test_lte_operator(self):
        """Test less than or equal operator."""
        clause = compile_where_clause(Amount__lte=500)
        assert "Amount<=500" in clause

    def test_ne_operator(self):
        """Test not equal operator."""
        clause = compile_where_clause(Status__ne='Closed')
        assert "Status!='Closed'" in clause

    def test_contains_operator(self):
        """Test LIKE contains operator."""
        clause = compile_where_clause(Name__contains='test')
        assert "Name LIKE '%test%'" in clause

    def test_startswith_operator(self):
        """Test LIKE startswith operator."""
        clause = compile_where_clause(Name__startswith='A')
        assert "Name LIKE 'A%'" in clause

    def test_endswith_operator(self):
        """Test LIKE endswith operator."""
        clause = compile_where_clause(Name__endswith='Inc')
        assert "Name LIKE '%Inc'" in clause

    def test_boolean_value(self):
        """Test boolean value formatting."""
        clause = compile_where_clause(IsActive=True)
        assert "IsActive=true" in clause

        clause = compile_where_clause(IsActive=False)
        assert "IsActive=false" in clause

    def test_numeric_value(self):
        """Test numeric value formatting."""
        clause = compile_where_clause(Amount=1500.50)
        assert "Amount=1500.5" in clause

    def test_null_value(self):
        """Test null value formatting."""
        clause = compile_where_clause(Email=None)
        assert "Email=null" in clause

    def test_datetime_value(self):
        """Test datetime value formatting."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        clause = compile_where_clause(CreatedDate=dt)
        assert "CreatedDate=" in clause
        assert "2024-01-01" in clause

    def test_string_escaping(self):
        """Test single quote escaping."""
        clause = compile_where_clause(Name="O'Brien")
        assert "Name='O\\'Brien'" in clause

    def test_like_escaping(self):
        """Test LIKE wildcard escaping."""
        clause = compile_where_clause(Name__contains="50%")
        assert "Name LIKE '%50\\%%'" in clause

    def test_complex_query(self):
        """Test complex query with multiple operators."""
        clause = compile_where_clause(
            Status='New',
            Priority__in=['High', 'Critical'],
            Amount__gte=1000,
            Name__startswith='A'
        )
        assert "Status='New'" in clause
        # Check IN clause components (order may vary)
        assert "Priority IN" in clause
        assert "'High'" in clause
        assert "'Critical'" in clause
        assert "Amount>=1000" in clause
        assert "Name LIKE 'A%'" in clause
        assert clause.count(" AND ") == 3

    def test_empty_kwargs(self):
        """Test with no arguments."""
        clause = compile_where_clause()
        assert clause == ""


class TestPrettyprintSoql:
    """Test prettyprint_soql function."""

    def test_simple_query(self):
        """Test simple query formatting."""
        query = "SELECT Id, Name FROM Account"
        formatted = prettyprint_soql(query)
        assert "SELECT" in formatted
        assert "FROM Account" in formatted

    def test_with_where(self):
        """Test query with WHERE clause."""
        query = "SELECT Id FROM Account WHERE Name != null"
        formatted = prettyprint_soql(query)
        assert "SELECT" in formatted
        assert "FROM Account" in formatted
        assert "WHERE" in formatted

    def test_returns_string(self):
        """Test that function returns a string."""
        query = "SELECT Id FROM Account"
        formatted = prettyprint_soql(query)
        assert isinstance(formatted, str)

