"""Tests for results module."""

import pytest

from forcepy.results import Result, ResultSet


class TestResult:
    """Test Result class."""

    def test_create_result(self):
        """Test creating Result."""
        r = Result({"Id": "001", "Name": "Test"})
        assert r.Id == "001"
        assert r.Name == "Test"

    def test_attribute_access(self):
        """Test attribute access."""
        r = Result({"Id": "001", "Name": "Test"})
        assert r["Id"] == "001"
        assert r.Id == "001"

    def test_nested_access(self):
        """Test nested field access."""
        r = Result({"Id": "001", "Account": {"Name": "Acme Corp", "Industry": "Tech"}})
        assert r.Account.Name == "Acme Corp"

    def test_get_field(self):
        """Test get_field method."""
        r = Result({"Id": "001", "Name": "Test"})
        assert r.get_field("Name") == "Test"
        assert r.get_field("Missing", "default", raise_keyerror=False) == "default"
        # Or use .get() which doesn't raise
        assert r.get("Missing", "default") == "default"

    def test_get_field_nested(self):
        """Test get_field with nested token."""
        r = Result({"Account": {"Name": "Acme Corp"}})
        assert r.get_field("Account__Name") == "Acme Corp"

    def test_serialize(self):
        """Test serialize method."""
        r = Result({"Id": "001", "Name": "Test"})
        serialized = r.serialize()
        assert serialized == {"Id": "001", "Name": "Test"}
        assert isinstance(serialized, dict)


class TestResultSet:
    """Test ResultSet class."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results."""
        return ResultSet(
            [
                Result({"Id": "001", "Name": "Case 1", "Status": "New", "Priority": "High"}),
                Result({"Id": "002", "Name": "Case 2", "Status": "Open", "Priority": "Low"}),
                Result({"Id": "003", "Name": "Case 3", "Status": "New", "Priority": "Medium"}),
                Result({"Id": "004", "Name": "Case 4", "Status": "Closed", "Priority": "High"}),
            ]
        )

    def test_create_resultset(self, sample_results):
        """Test creating ResultSet."""
        assert len(sample_results) == 4
        assert sample_results[0].Name == "Case 1"

    def test_filter_exact(self, sample_results):
        """Test exact match filter."""
        new_cases = sample_results.filter(Status="New")
        assert len(new_cases) == 2
        assert all(c.Status == "New" for c in new_cases)

    def test_filter_multiple(self, sample_results):
        """Test multiple field filter (AND)."""
        filtered = sample_results.filter(Status="New", Priority="High")
        assert len(filtered) == 1
        assert filtered[0].Id == "001"

    def test_filter_in(self, sample_results):
        """Test __in filter."""
        filtered = sample_results.filter(Status__in=["New", "Open"])
        assert len(filtered) == 3

    def test_filter_gt(self, sample_results):
        """Test __gt filter."""
        results = ResultSet(
            [
                Result({"Id": "001", "Amount": 100}),
                Result({"Id": "002", "Amount": 200}),
                Result({"Id": "003", "Amount": 50}),
            ]
        )
        filtered = results.filter(Amount__gt=100)
        assert len(filtered) == 1
        assert filtered[0].Amount == 200

    def test_filter_contains(self, sample_results):
        """Test __contains filter."""
        filtered = sample_results.filter(Name__contains="Case 1")
        assert len(filtered) == 1

    def test_exclude(self, sample_results):
        """Test exclude method."""
        not_closed = sample_results.exclude(Status="Closed")
        assert len(not_closed) == 3
        assert all(c.Status != "Closed" for c in not_closed)

    def test_get(self, sample_results):
        """Test get method."""
        case = sample_results.get(Id="001")
        assert case.Name == "Case 1"

    def test_get_multiple_error(self, sample_results):
        """Test get with multiple results raises error."""
        with pytest.raises(ValueError, match="Multiple results"):
            sample_results.get(Status="New")

    def test_get_none_error(self, sample_results):
        """Test get with no results raises error."""
        with pytest.raises(ValueError, match="No results"):
            sample_results.get(Id="999")

    def test_get_or_none(self, sample_results):
        """Test get_or_none method."""
        case = sample_results.get_or_none(Id="001")
        assert case is not None

        missing = sample_results.get_or_none(Id="999")
        assert missing is None

    def test_first(self, sample_results):
        """Test first method."""
        first = sample_results.first()
        assert first.Id == "001"

    def test_last(self, sample_results):
        """Test last method."""
        last = sample_results.last()
        assert last.Id == "004"

    def test_first_empty(self):
        """Test first on empty set."""
        empty = ResultSet()
        assert empty.first() is None

    def test_group_by(self, sample_results):
        """Test group_by method."""
        by_status = sample_results.group_by("Status")
        assert len(by_status) == 3  # New, Open, Closed
        assert len(by_status["New"]) == 2
        assert len(by_status["Open"]) == 1
        assert len(by_status["Closed"]) == 1

    def test_group_by_count(self, sample_results):
        """Test group_by with count."""
        counts = sample_results.group_by("Status").count()
        assert counts["New"] == 2
        assert counts["Open"] == 1
        assert counts["Closed"] == 1

    def test_order_by_asc(self, sample_results):
        """Test order_by ascending."""
        ordered = sample_results.order_by("Id", asc=True)
        assert ordered[0].Id == "001"
        assert ordered[-1].Id == "004"

    def test_order_by_desc(self, sample_results):
        """Test order_by descending."""
        ordered = sample_results.order_by("Id", asc=False)
        assert ordered[0].Id == "004"
        assert ordered[-1].Id == "001"

    def test_values_list(self, sample_results):
        """Test values_list method."""
        names = sample_results.values_list("Name", flat=True)
        assert len(names) == 4
        assert names[0] == "Case 1"
        assert names[1] == "Case 2"

    def test_values_list_multiple(self, sample_results):
        """Test values_list with multiple fields."""
        values = sample_results.values_list("Name", "Status")
        assert len(values) == 4
        assert values[0] == ("Case 1", "New")

    def test_earliest(self):
        """Test earliest method."""
        import datetime

        results = ResultSet(
            [
                Result({"Id": "001", "CreatedDate": datetime.datetime(2023, 1, 15)}),
                Result({"Id": "002", "CreatedDate": datetime.datetime(2023, 1, 10)}),
                Result({"Id": "003", "CreatedDate": datetime.datetime(2023, 1, 20)}),
            ]
        )
        earliest = results.earliest("CreatedDate")
        assert earliest.Id == "002"

    def test_latest(self):
        """Test latest method."""
        import datetime

        results = ResultSet(
            [
                Result({"Id": "001", "CreatedDate": datetime.datetime(2023, 1, 15)}),
                Result({"Id": "002", "CreatedDate": datetime.datetime(2023, 1, 10)}),
                Result({"Id": "003", "CreatedDate": datetime.datetime(2023, 1, 20)}),
            ]
        )
        latest = results.latest("CreatedDate")
        assert latest.Id == "003"

    def test_slice(self, sample_results):
        """Test slicing returns ResultSet."""
        sliced = sample_results[:2]
        assert isinstance(sliced, ResultSet)
        assert len(sliced) == 2

    def test_serialize(self, sample_results):
        """Test serialize method."""
        serialized = sample_results.serialize()
        assert isinstance(serialized, list)
        assert len(serialized) == 4
        assert serialized[0]["Name"] == "Case 1"


class TestAggregateSet:
    """Test AggregateSet class."""

    def test_count(self):
        """Test count method."""
        results = ResultSet(
            [
                Result({"Status": "New"}),
                Result({"Status": "New"}),
                Result({"Status": "Open"}),
            ]
        )
        counts = results.group_by("Status").count()
        assert counts["New"] == 2
        assert counts["Open"] == 1
