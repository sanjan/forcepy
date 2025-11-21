"""Tests for query module."""

import datetime

from forcepy.query import BOOL, DATE, IN, Q, compile_key_value, compile_where_clause, format_datetime, select


class TestQueryHelpers:
    """Test query helper functions."""

    def test_in_function(self):
        """Test IN() function."""
        result = IN(["a", "b", "c"])
        # IN uses set() so order may vary - just check all values are present
        assert "a" in result
        assert "b" in result
        assert "c" in result
        assert result.startswith("(") and result.endswith(")")

    def test_bool_function(self):
        """Test BOOL() function."""
        assert BOOL(True) == "true"
        assert BOOL(False) == "false"

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45)
        assert format_datetime(dt) == "2023-01-15T10:30:45.0000Z"

        date = datetime.date(2023, 1, 15)
        assert format_datetime(date) == "2023-01-15T00:00:00.0000Z"

    def test_date_function(self):
        """Test DATE() function."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45)
        assert DATE(dt) == "2023-01-15T10:30:45.0000Z"


class TestQObject:
    """Test Q object for query building."""

    def test_simple_q(self):
        """Test simple Q object."""
        q = Q(Status="New")
        # Simple Q wraps in parens with wrap=True
        result = q.compile()
        assert "Status" in result
        assert "New" in result

    def test_q_and(self):
        """Test Q AND operator."""
        q = Q(Status="New") & Q(Priority="High")
        result = q.compile()
        assert "Status" in result
        assert "New" in result
        assert "AND" in result
        assert "Priority" in result
        assert "High" in result

    def test_q_or(self):
        """Test Q OR operator."""
        q = Q(Status="New") | Q(Status="Closed")
        result = q.compile()
        assert "Status" in result
        assert "New" in result
        assert "OR" in result
        assert "Closed" in result

    def test_q_not(self):
        """Test Q NOT operator."""
        q = ~Q(Status="Closed")
        assert "NOT" in q.compile()
        assert "Closed" in q.compile()

    def test_complex_q(self):
        """Test complex Q combination."""
        q = (Q(Status="New") | Q(Status="In Progress")) & Q(Priority="High")
        result = q.compile()
        assert "OR" in result
        assert "AND" in result
        assert "New" in result
        assert "High" in result


class TestCompileKeyValue:
    """Test compile_key_value function."""

    def test_simple_equality(self):
        """Test simple field = value."""
        assert compile_key_value("Status", "New") == "Status = 'New'"

    def test_gt_operator(self):
        """Test greater than operator."""
        assert compile_key_value("Amount__gt", 1000) == "Amount > 1000"

    def test_gte_operator(self):
        """Test greater than or equal operator."""
        assert compile_key_value("Amount__gte", 1000) == "Amount >= 1000"

    def test_lt_operator(self):
        """Test less than operator."""
        assert compile_key_value("Amount__lt", 1000) == "Amount < 1000"

    def test_lte_operator(self):
        """Test less than or equal operator."""
        assert compile_key_value("Amount__lte", 1000) == "Amount <= 1000"

    def test_ne_operator(self):
        """Test not equal operator."""
        assert compile_key_value("Status__ne", "Closed") == "Status != 'Closed'"

    def test_in_operator(self):
        """Test IN operator."""
        result = compile_key_value("Status__in", ["New", "Open"])
        assert "IN" in result
        assert "New" in result
        assert "Open" in result

    def test_like_operator(self):
        """Test LIKE operator."""
        assert compile_key_value("Name__like", "%test%") == "Name LIKE '%test%'"

    def test_null_value(self):
        """Test null value."""
        assert compile_key_value("Description", None) == "Description = null"

    def test_boolean_value(self):
        """Test boolean value."""
        assert compile_key_value("IsActive", True) == "IsActive = true"
        assert compile_key_value("IsActive", False) == "IsActive = false"

    def test_datetime_value(self):
        """Test datetime value."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45)
        result = compile_key_value("CreatedDate", dt)
        assert "CreatedDate" in result
        assert "2023-01-15T10:30:45.0000Z" in result

    def test_list_value(self):
        """Test list value converts to IN."""
        result = compile_key_value("Status", ["New", "Open"])
        assert "New" in result
        assert "Open" in result


class TestCompileWhereClause:
    """Test compile_where_clause function."""

    def test_simple_kwargs(self):
        """Test simple kwargs."""
        result = compile_where_clause(Status="New", Priority="High")
        assert "Status" in result
        assert "Priority" in result
        assert "AND" in result

    def test_q_object(self):
        """Test Q object argument."""
        q = Q(Status="New") | Q(Status="Open")
        result = compile_where_clause(q)
        assert "Status" in result
        assert "OR" in result

    def test_q_and_kwargs(self):
        """Test Q object with kwargs."""
        q = Q(Status="New")
        result = compile_where_clause(q, Priority="High")
        assert "Status" in result
        assert "Priority" in result
        assert "AND" in result


class TestSelectFunction:
    """Test select function."""

    def test_basic_select(self):
        """Test basic SELECT statement."""
        query = select(sobject="Account", fields=["Id", "Name"])
        assert "SELECT Id, Name" in query
        assert "FROM Account" in query

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        query = select(sobject="Account", fields=["Id", "Name"], Industry="Technology")
        assert "WHERE" in query
        assert "Industry" in query

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY."""
        query = select(sobject="Account", fields=["Id", "Name"], order_by="Name")
        assert "ORDER BY Name ASC" in query

    def test_select_with_order_by_desc(self):
        """Test SELECT with ORDER BY DESC."""
        query = select(sobject="Account", fields=["Id", "Name"], order_by="-CreatedDate")
        assert "ORDER BY CreatedDate DESC" in query

    def test_select_with_limit(self):
        """Test SELECT with LIMIT."""
        query = select(sobject="Account", fields=["Id", "Name"], limit=10)
        assert "LIMIT 10" in query

    def test_select_fields_string(self):
        """Test SELECT with fields as string."""
        query = select(sobject="Account", fields="Id, Name, Industry")
        assert "SELECT Id, Name, Industry" in query
