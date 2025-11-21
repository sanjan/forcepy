"""Tests for Salesforce ID utilities."""


from forcepy.id_utils import compare_ids, id_in_list, is_valid_id, normalize_id


class TestNormalizeId:
    """Test normalize_id function."""

    def test_15_char_id(self):
        """Test 15 character ID is unchanged."""
        id_15 = "005B0000000hMtx"
        assert normalize_id(id_15) == "005B0000000hMtx"

    def test_18_char_id(self):
        """Test 18 character ID is normalized to 15."""
        id_18 = "005B0000000hMtxIAI"
        assert normalize_id(id_18) == "005B0000000hMtx"

    def test_empty_string(self):
        """Test empty string is returned as-is."""
        assert normalize_id("") == ""

    def test_none(self):
        """Test None is returned as-is."""
        assert normalize_id(None) is None

    def test_short_id(self):
        """Test ID shorter than 15 chars is returned as-is."""
        short_id = "00512345"
        assert normalize_id(short_id) == "00512345"


class TestCompareIds:
    """Test compare_ids function."""

    def test_same_15_char_ids(self):
        """Test comparing same 15 char IDs."""
        assert compare_ids("005B0000000hMtx", "005B0000000hMtx")

    def test_same_18_char_ids(self):
        """Test comparing same 18 char IDs."""
        assert compare_ids("005B0000000hMtxIAI", "005B0000000hMtxIAI")

    def test_15_vs_18_char_same(self):
        """Test comparing 15 vs 18 char of same ID."""
        assert compare_ids("005B0000000hMtx", "005B0000000hMtxIAI")
        assert compare_ids("005B0000000hMtxIAI", "005B0000000hMtx")

    def test_different_ids(self):
        """Test comparing different IDs."""
        assert not compare_ids("005B0000000hMtx", "005B0000000abc")
        assert not compare_ids("005B0000000hMtxIAI", "005B0000000abcXYZ")

    def test_empty_strings(self):
        """Test comparing empty strings."""
        assert compare_ids("", "")
        assert not compare_ids("005B0000000hMtx", "")
        assert not compare_ids("", "005B0000000hMtx")

    def test_none_values(self):
        """Test comparing None values."""
        assert compare_ids(None, None)
        assert not compare_ids("005B0000000hMtx", None)
        assert not compare_ids(None, "005B0000000hMtx")


class TestIdInList:
    """Test id_in_list function."""

    def test_15_char_in_15_char_list(self):
        """Test 15 char ID in list of 15 char IDs."""
        assert id_in_list("005B0000000hMtx", ["005B0000000hMtx", "005B0000000abc"])

    def test_18_char_in_18_char_list(self):
        """Test 18 char ID in list of 18 char IDs."""
        assert id_in_list("005B0000000hMtxIAI", ["005B0000000hMtxIAI", "005B0000000abcXYZ"])

    def test_15_char_in_18_char_list(self):
        """Test 15 char ID in list of 18 char IDs."""
        assert id_in_list("005B0000000hMtx", ["005B0000000hMtxIAI", "005B0000000abcXYZ"])

    def test_18_char_in_15_char_list(self):
        """Test 18 char ID in list of 15 char IDs."""
        assert id_in_list("005B0000000hMtxIAI", ["005B0000000hMtx", "005B0000000abc"])

    def test_id_not_in_list(self):
        """Test ID not in list."""
        assert not id_in_list("005B0000000xyz", ["005B0000000hMtx", "005B0000000abc"])

    def test_empty_id(self):
        """Test empty ID."""
        assert not id_in_list("", ["005B0000000hMtx", "005B0000000abc"])

    def test_empty_list(self):
        """Test empty list."""
        assert not id_in_list("005B0000000hMtx", [])

    def test_list_with_none(self):
        """Test list containing None values."""
        assert id_in_list("005B0000000hMtx", ["005B0000000hMtx", None, "005B0000000abc"])

    def test_list_with_empty(self):
        """Test list containing empty strings."""
        assert id_in_list("005B0000000hMtx", ["005B0000000hMtx", "", "005B0000000abc"])


class TestIsValidId:
    """Test is_valid_id function."""

    def test_valid_15_char_id(self):
        """Test valid 15 character ID."""
        assert is_valid_id("005B0000000hMtx")

    def test_valid_18_char_id(self):
        """Test valid 18 character ID."""
        assert is_valid_id("005B0000000hMtxIAI")

    def test_invalid_length(self):
        """Test invalid length IDs."""
        assert not is_valid_id("005B000")  # Too short
        assert not is_valid_id("005B0000000hMtx123456")  # Too long

    def test_invalid_characters(self):
        """Test IDs with invalid characters."""
        assert not is_valid_id("005B0000000hMt@")  # Special char
        assert not is_valid_id("005B0000000hM x")  # Space

    def test_empty_string(self):
        """Test empty string."""
        assert not is_valid_id("")

    def test_none(self):
        """Test None value."""
        assert not is_valid_id(None)

