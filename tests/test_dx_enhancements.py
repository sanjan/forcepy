"""Tests for developer experience enhancements."""

import io
import tempfile
from pathlib import Path

import pytest

from forcepy.results import Result, ResultSet


class TestConvenienceMethods:
    """Test .first() and .last() convenience methods."""

    def test_first_with_results(self):
        """Test .first() returns first result."""
        results = ResultSet([
            Result({"Id": "001", "Name": "First"}),
            Result({"Id": "002", "Name": "Second"}),
            Result({"Id": "003", "Name": "Third"}),
        ])
        
        first = results.first()
        assert first is not None
        assert first["Id"] == "001"
        assert first["Name"] == "First"

    def test_first_empty(self):
        """Test .first() returns None for empty ResultSet."""
        results = ResultSet()
        assert results.first() is None

    def test_last_with_results(self):
        """Test .last() returns last result."""
        results = ResultSet([
            Result({"Id": "001", "Name": "First"}),
            Result({"Id": "002", "Name": "Second"}),
            Result({"Id": "003", "Name": "Third"}),
        ])
        
        last = results.last()
        assert last is not None
        assert last["Id"] == "003"
        assert last["Name"] == "Third"

    def test_last_empty(self):
        """Test .last() returns None for empty ResultSet."""
        results = ResultSet()
        assert results.last() is None

    def test_first_last_single_element(self):
        """Test .first() and .last() return same element for single-item ResultSet."""
        results = ResultSet([Result({"Id": "001", "Name": "Only"})])
        
        assert results.first() == results.last()
        assert results.first()["Id"] == "001"


class TestCaseInsensitiveFilters:
    """Test case-insensitive filter lookups."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return ResultSet([
            Result({"Id": "001", "Subject": "URGENT: Server Down", "Status": "New"}),
            Result({"Id": "002", "Subject": "Question about API", "Status": "OPEN"}),
            Result({"Id": "003", "Subject": "Urgent Request", "Status": "Closed"}),
            Result({"Id": "004", "Subject": "Feature Request", "Status": "new"}),
            Result({"Id": "005", "Subject": "Bug Report", "Status": "Open"}),
        ])

    def test_icontains(self, sample_data):
        """Test __icontains lookup."""
        # Case-insensitive contains
        urgent = sample_data.filter(Subject__icontains="urgent")
        assert len(urgent) == 2
        assert urgent[0]["Id"] == "001"
        assert urgent[1]["Id"] == "003"

    def test_icontains_with_different_cases(self, sample_data):
        """Test __icontains with various cases."""
        # Search with lowercase
        api = sample_data.filter(Subject__icontains="api")
        assert len(api) == 1
        assert api[0]["Id"] == "002"
        
        # Search with uppercase
        api_upper = sample_data.filter(Subject__icontains="API")
        assert len(api_upper) == 1
        assert api_upper[0]["Id"] == "002"

    def test_istartswith(self, sample_data):
        """Test __istartswith lookup."""
        urgent_start = sample_data.filter(Subject__istartswith="urgent")
        assert len(urgent_start) == 2
        assert urgent_start[0]["Id"] == "001"
        assert urgent_start[1]["Id"] == "003"

    def test_iendswith(self, sample_data):
        """Test __iendswith lookup."""
        requests = sample_data.filter(Subject__iendswith="request")
        assert len(requests) == 2
        assert requests[0]["Id"] == "003"
        assert requests[1]["Id"] == "004"

    def test_iexact(self, sample_data):
        """Test __iexact lookup."""
        # Exact match, case-insensitive
        new_cases = sample_data.filter(Status__iexact="new")
        assert len(new_cases) == 2
        assert new_cases[0]["Id"] == "001"
        assert new_cases[1]["Id"] == "004"
        
        open_cases = sample_data.filter(Status__iexact="OPEN")
        assert len(open_cases) == 2
        assert open_cases[0]["Id"] == "002"
        assert open_cases[1]["Id"] == "005"

    def test_icontains_with_none_values(self):
        """Test __icontains handles None values."""
        results = ResultSet([
            Result({"Id": "001", "Subject": "Test"}),
            Result({"Id": "002", "Subject": None}),
            Result({"Id": "003", "Subject": "Another Test"}),
        ])
        
        filtered = results.filter(Subject__icontains="test")
        assert len(filtered) == 2
        assert filtered[0]["Id"] == "001"
        assert filtered[1]["Id"] == "003"

    def test_icontains_with_list_fields(self):
        """Test __icontains with list fields."""
        results = ResultSet([
            Result({"Id": "001", "Tags": ["IMPORTANT", "Urgent"]}),
            Result({"Id": "002", "Tags": ["Normal", "Review"]}),
            Result({"Id": "003", "Tags": ["urgent", "Bug"]}),
        ])
        
        filtered = results.filter(Tags__icontains="urgent")
        assert len(filtered) == 2
        assert filtered[0]["Id"] == "001"
        assert filtered[1]["Id"] == "003"

    def test_case_sensitive_vs_insensitive(self, sample_data):
        """Compare case-sensitive and case-insensitive filters."""
        # Case-sensitive contains
        sensitive = sample_data.filter(Subject__contains="urgent")
        assert len(sensitive) == 0  # No lowercase "urgent" at start
        
        # Case-insensitive contains
        insensitive = sample_data.filter(Subject__icontains="urgent")
        assert len(insensitive) == 2  # Finds both "URGENT" and "Urgent"


class TestCSVExportImport:
    """Test CSV export and import functionality."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for CSV testing."""
        return ResultSet([
            Result({"Id": "001", "Name": "Acme Corp", "Industry": "Technology", "Revenue": "1000000"}),
            Result({"Id": "002", "Name": "Globe Inc", "Industry": "Finance", "Revenue": "500000"}),
            Result({"Id": "003", "Name": "Star LLC", "Industry": None, "Revenue": "250000"}),
        ])

    def test_to_csv_returns_string(self, sample_data):
        """Test to_csv() returns CSV string when no filepath provided."""
        csv_output = sample_data.to_csv()
        
        assert isinstance(csv_output, str)
        assert "Id,Name,Industry,Revenue" in csv_output
        assert "001,Acme Corp,Technology,1000000" in csv_output
        assert "002,Globe Inc,Finance,500000" in csv_output

    def test_to_csv_handles_none_values(self, sample_data):
        """Test to_csv() converts None to empty string."""
        csv_output = sample_data.to_csv()
        
        # None should become empty string in CSV
        lines = csv_output.strip().split('\n')
        assert len(lines) == 4  # header + 3 data rows
        
        # Third row has None for Industry
        assert "003,Star LLC,,250000" in csv_output

    def test_to_csv_empty_resultset(self):
        """Test to_csv() with empty ResultSet."""
        empty = ResultSet()
        csv_output = empty.to_csv()
        
        assert csv_output == ""

    def test_to_csv_writes_to_file(self, sample_data):
        """Test to_csv() writes to file when filepath provided."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name
        
        try:
            result = sample_data.to_csv(filepath)
            assert result is None  # Should return None when writing to file
            
            # Read the file and verify contents
            with open(filepath, 'r') as f:
                content = f.read()
            
            assert "Id,Name,Industry,Revenue" in content
            assert "001,Acme Corp,Technology,1000000" in content
        finally:
            Path(filepath).unlink()

    def test_from_csv_string(self):
        """Test from_csv() with CSV string."""
        csv_data = "Id,Name,Industry\n001,Acme Corp,Technology\n002,Globe Inc,Finance"
        
        results = ResultSet.from_csv(csv_data)
        
        assert len(results) == 2
        assert results[0]["Id"] == "001"
        assert results[0]["Name"] == "Acme Corp"
        assert results[0]["Industry"] == "Technology"
        assert results[1]["Id"] == "002"

    def test_from_csv_file(self, sample_data):
        """Test from_csv() with file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name
        
        try:
            # Write sample data to file
            sample_data.to_csv(filepath)
            
            # Read it back
            loaded = ResultSet.from_csv(filepath)
            
            assert len(loaded) == len(sample_data)
            assert loaded[0]["Id"] == sample_data[0]["Id"]
            assert loaded[0]["Name"] == sample_data[0]["Name"]
        finally:
            Path(filepath).unlink()

    def test_from_csv_file_like_object(self):
        """Test from_csv() with file-like object."""
        csv_data = "Id,Name,Industry\n001,Acme Corp,Technology\n002,Globe Inc,Finance"
        file_obj = io.StringIO(csv_data)
        
        results = ResultSet.from_csv(file_obj)
        
        assert len(results) == 2
        assert results[0]["Id"] == "001"
        assert results[1]["Name"] == "Globe Inc"

    def test_from_csv_handles_empty_strings_as_none(self):
        """Test from_csv() converts empty strings back to None."""
        csv_data = "Id,Name,Industry\n001,Acme Corp,Technology\n002,Globe Inc,"
        
        results = ResultSet.from_csv(csv_data)
        
        assert results[0]["Industry"] == "Technology"
        assert results[1]["Industry"] is None

    def test_csv_round_trip(self, sample_data):
        """Test export and import round-trip preserves data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name
        
        try:
            # Export
            sample_data.to_csv(filepath)
            
            # Import
            loaded = ResultSet.from_csv(filepath)
            
            # Verify
            assert len(loaded) == len(sample_data)
            for original, reimported in zip(sample_data, loaded):
                assert original["Id"] == reimported["Id"]
                assert original["Name"] == reimported["Name"]
                # Note: None values become None after round-trip
                if original["Industry"] is None:
                    assert reimported["Industry"] is None
                else:
                    assert original["Industry"] == reimported["Industry"]
        finally:
            Path(filepath).unlink()

    def test_csv_with_special_characters(self):
        """Test CSV handles special characters properly."""
        results = ResultSet([
            Result({"Id": "001", "Name": "Company, Inc", "Notes": "Has \"quotes\""}),
            Result({"Id": "002", "Name": "Multi\nLine", "Notes": "Has\nNewlines"}),
        ])
        
        csv_output = results.to_csv()
        loaded = ResultSet.from_csv(csv_output)
        
        # CSV module should handle escaping
        assert len(loaded) == 2
        assert loaded[0]["Name"] == "Company, Inc"
        assert '"' in loaded[0]["Notes"]

    def test_csv_empty_resultset_to_file(self):
        """Test to_csv() with empty ResultSet writing to file."""
        empty = ResultSet()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name
        
        try:
            result = empty.to_csv(filepath)
            assert result is None
            
            # File should be empty
            with open(filepath, 'r') as f:
                content = f.read()
            assert content == ""
        finally:
            Path(filepath).unlink()

    def test_csv_varied_fields(self):
        """Test CSV with records having different fields."""
        results = ResultSet([
            Result({"Id": "001", "Name": "First", "Extra": "Value"}),
            Result({"Id": "002", "Name": "Second"}),
            Result({"Id": "003", "Name": "Third", "Another": "Field"}),
        ])
        
        csv_output = results.to_csv()
        
        # Should include all unique fields
        assert "Id" in csv_output
        assert "Name" in csv_output
        assert "Extra" in csv_output
        assert "Another" in csv_output
        
        # Reload and check
        loaded = ResultSet.from_csv(csv_output)
        assert len(loaded) == 3
        assert loaded[0]["Extra"] == "Value"
        assert loaded[1]["Extra"] is None  # Missing field becomes None
        assert loaded[2]["Another"] == "Field"


class TestIntegration:
    """Test DX enhancements work together."""

    def test_filter_then_first_last(self):
        """Test filtering then using .first() and .last()."""
        results = ResultSet([
            Result({"Id": "001", "Status": "Open", "Priority": "High"}),
            Result({"Id": "002", "Status": "Closed", "Priority": "Low"}),
            Result({"Id": "003", "Status": "Open", "Priority": "Medium"}),
            Result({"Id": "004", "Status": "Open", "Priority": "High"}),
        ])
        
        open_cases = results.filter(Status__iexact="open")
        assert len(open_cases) == 3
        
        first_open = open_cases.first()
        assert first_open["Id"] == "001"
        
        last_open = open_cases.last()
        assert last_open["Id"] == "004"

    def test_case_insensitive_filter_then_csv(self):
        """Test case-insensitive filtering then CSV export."""
        results = ResultSet([
            Result({"Id": "001", "Subject": "URGENT Issue"}),
            Result({"Id": "002", "Subject": "Normal Issue"}),
            Result({"Id": "003", "Subject": "Urgent Request"}),
        ])
        
        urgent = results.filter(Subject__icontains="urgent")
        csv_output = urgent.to_csv()
        
        assert "001" in csv_output
        assert "003" in csv_output
        assert "002" not in csv_output

    def test_csv_import_then_filter(self):
        """Test importing CSV then filtering."""
        csv_data = "Id,Status,Priority\n001,Open,High\n002,OPEN,Low\n003,Closed,High"
        
        results = ResultSet.from_csv(csv_data)
        open_cases = results.filter(Status__iexact="open")
        
        assert len(open_cases) == 2
        assert open_cases[0]["Id"] == "001"
        assert open_cases[1]["Id"] == "002"

