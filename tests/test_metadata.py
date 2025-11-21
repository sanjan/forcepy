"""Tests for metadata and describe operations."""

import pytest

from forcepy.metadata import DescribeCache, FieldDescribe, FieldDescribeSet, ObjectDescribe


class TestFieldDescribe:
    """Test FieldDescribe class."""

    @pytest.fixture
    def required_field(self):
        """Create a required field."""
        return FieldDescribe(
            {
                "name": "Name",
                "type": "string",
                "length": 255,
                "nillable": False,
                "defaultedOnCreate": False,
                "createable": True,
                "updateable": True,
            }
        )

    @pytest.fixture
    def optional_field(self):
        """Create an optional field."""
        return FieldDescribe(
            {
                "name": "Phone",
                "type": "phone",
                "nillable": True,
                "createable": True,
                "updateable": True,
            }
        )

    def test_is_required_true(self, required_field):
        """Test is_required for required field."""
        assert required_field.is_required

    def test_is_required_false(self, optional_field):
        """Test is_required for optional field."""
        assert not optional_field.is_required

    def test_is_updateable(self, required_field):
        """Test is_updateable."""
        assert required_field.is_updateable

    def test_is_createable(self, required_field):
        """Test is_createable."""
        assert required_field.is_createable


class TestFieldDescribeSet:
    """Test FieldDescribeSet class."""

    @pytest.fixture
    def field_set(self):
        """Create a field set."""
        return FieldDescribeSet(
            [
                FieldDescribe(
                    {
                        "name": "Id",
                        "type": "id",
                        "nillable": False,
                        "createable": False,
                        "updateable": False,
                    }
                ),
                FieldDescribe(
                    {
                        "name": "Name",
                        "type": "string",
                        "nillable": False,
                        "defaultedOnCreate": False,
                        "createable": True,
                        "updateable": True,
                    }
                ),
                FieldDescribe(
                    {
                        "name": "Phone",
                        "type": "phone",
                        "nillable": True,
                        "createable": True,
                        "updateable": True,
                    }
                ),
            ]
        )

    def test_get_by_name(self, field_set):
        """Test getting field by name."""
        field = field_set.get_by_name("Name")
        assert field is not None
        assert field.get("name") == "Name"

    def test_get_by_name_case_insensitive(self, field_set):
        """Test case-insensitive field lookup."""
        field = field_set.get_by_name("name")
        assert field is not None
        assert field.get("name") == "Name"

    def test_get_by_name_missing(self, field_set):
        """Test getting non-existent field."""
        field = field_set.get_by_name("NonExistent")
        assert field is None

    def test_required_fields(self, field_set):
        """Test filtering required fields."""
        required = field_set.required_fields()
        assert len(required) == 1
        assert required[0].get("name") == "Name"

    def test_updateable_fields(self, field_set):
        """Test filtering updateable fields."""
        updateable = field_set.updateable_fields()
        assert len(updateable) == 2
        names = [f.get("name") for f in updateable]
        assert "Name" in names
        assert "Phone" in names

    def test_createable_fields(self, field_set):
        """Test filtering createable fields."""
        createable = field_set.createable_fields()
        assert len(createable) == 2
        names = [f.get("name") for f in createable]
        assert "Name" in names
        assert "Phone" in names


class TestObjectDescribe:
    """Test ObjectDescribe class."""

    @pytest.fixture
    def account_describe(self):
        """Create an Account describe."""
        return ObjectDescribe(
            {
                "name": "Account",
                "label": "Account",
                "queryable": True,
                "createable": True,
                "updateable": True,
                "deletable": True,
                "fields": [
                    {
                        "name": "Id",
                        "type": "id",
                        "nillable": False,
                        "createable": False,
                        "updateable": False,
                    },
                    {
                        "name": "Name",
                        "type": "string",
                        "nillable": False,
                        "defaultedOnCreate": False,
                        "createable": True,
                        "updateable": True,
                    },
                    {
                        "name": "Industry",
                        "type": "picklist",
                        "nillable": True,
                        "createable": True,
                        "updateable": True,
                        "picklistValues": [
                            {"value": "Technology", "label": "Technology", "active": True},
                            {"value": "Finance", "label": "Finance", "active": True},
                            {"value": "Healthcare", "label": "Healthcare", "active": False},
                        ],
                    },
                ],
            }
        )

    def test_fields_converted_to_set(self, account_describe):
        """Test that fields are converted to FieldDescribeSet."""
        assert isinstance(account_describe.fields, FieldDescribeSet)
        assert len(account_describe.fields) == 3

    def test_get_field(self, account_describe):
        """Test getting field by name."""
        field = account_describe.get_field_describe("Name")
        assert field is not None
        assert field.get("name") == "Name"

    def test_get_field_missing(self, account_describe):
        """Test getting non-existent field."""
        field = account_describe.get_field_describe("NonExistent")
        assert field is None

    def test_field_names(self, account_describe):
        """Test getting list of field names."""
        names = account_describe.field_names
        assert "Id" in names
        assert "Name" in names
        assert "Industry" in names

    def test_required_fields(self, account_describe):
        """Test getting required fields."""
        required = account_describe.required_fields
        assert len(required) == 1
        assert required[0].get("name") == "Name"

    def test_is_queryable(self, account_describe):
        """Test is_queryable property."""
        assert account_describe.is_queryable

    def test_is_createable(self, account_describe):
        """Test is_createable property."""
        assert account_describe.is_createable

    def test_is_updateable(self, account_describe):
        """Test is_updateable property."""
        assert account_describe.is_updateable

    def test_is_deletable(self, account_describe):
        """Test is_deletable property."""
        assert account_describe.is_deletable

    def test_get_picklist_values(self, account_describe):
        """Test getting picklist values."""
        values = account_describe.get_picklist_values("Industry")
        assert len(values) == 2  # Only active by default
        assert values[0]["value"] == "Technology"
        assert values[1]["value"] == "Finance"

    def test_get_picklist_values_include_inactive(self, account_describe):
        """Test getting picklist values including inactive."""
        values = account_describe.get_picklist_values("Industry", active_only=False)
        assert len(values) == 3
        assert values[2]["value"] == "Healthcare"

    def test_get_picklist_values_invalid_field(self, account_describe):
        """Test getting picklist values for non-existent field."""
        with pytest.raises(ValueError, match="Field not found"):
            account_describe.get_picklist_values("NonExistent")

    def test_get_picklist_values_non_picklist_field(self, account_describe):
        """Test getting picklist values for non-picklist field."""
        with pytest.raises(ValueError, match="not a picklist"):
            account_describe.get_picklist_values("Name")


class TestDescribeCache:
    """Test DescribeCache class."""

    def test_empty_cache(self):
        """Test empty cache."""
        cache = DescribeCache()
        assert len(cache) == 0
        assert "Account" not in cache

    def test_set_and_get(self):
        """Test setting and getting from cache."""
        cache = DescribeCache()
        describe = ObjectDescribe({"name": "Account", "fields": []})

        cache.set("Account", describe)
        assert len(cache) == 1
        assert "Account" in cache

        cached = cache.get("Account")
        assert cached is describe

    def test_get_missing(self):
        """Test getting non-existent item."""
        cache = DescribeCache()
        assert cache.get("Account") is None

    def test_clear(self):
        """Test clearing cache."""
        cache = DescribeCache()
        cache.set("Account", ObjectDescribe({"name": "Account", "fields": []}))
        cache.set("Contact", ObjectDescribe({"name": "Contact", "fields": []}))

        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0

    def test_max_size_eviction(self):
        """Test that cache evicts oldest when full."""
        cache = DescribeCache(max_size=2)

        cache.set("Account", ObjectDescribe({"name": "Account", "fields": []}))
        cache.set("Contact", ObjectDescribe({"name": "Contact", "fields": []}))
        assert len(cache) == 2

        # Adding third should evict first
        cache.set("Case", ObjectDescribe({"name": "Case", "fields": []}))
        assert len(cache) == 2
        assert "Account" not in cache  # Oldest evicted
        assert "Contact" in cache
        assert "Case" in cache
