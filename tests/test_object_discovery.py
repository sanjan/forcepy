"""Tests for object discovery features."""

from unittest.mock import patch

import pytest

from forcepy import Salesforce


class TestObjectDiscovery:
    """Test object discovery helper methods."""

    @pytest.fixture
    def sf_client(self):
        return Salesforce(session_id="test-session", instance_url="https://test.salesforce.com")

    @pytest.fixture
    def mock_describe_global(self):
        return [
            {
                "name": "Account",
                "label": "Account",
                "labelPlural": "Accounts",
                "custom": False,
                "keyPrefix": "001",
                "queryable": True,
                "createable": True,
            },
            {
                "name": "Contact",
                "label": "Contact",
                "labelPlural": "Contacts",
                "custom": False,
                "keyPrefix": "003",
                "queryable": True,
                "createable": True,
            },
            {
                "name": "CustomObject__c",
                "label": "Custom Object",
                "labelPlural": "Custom Objects",
                "custom": True,
                "keyPrefix": "a00",
                "queryable": True,
                "createable": True,
            },
            {
                "name": "AnotherCustom__c",
                "label": "Another Custom",
                "labelPlural": "Another Customs",
                "custom": True,
                "keyPrefix": "a01",
                "queryable": False,
                "createable": False,
            },
        ]

    def test_get_object_type_from_id_standard(self, sf_client, mock_describe_global):
        """Test getting object type from standard object ID."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            obj_type = sf_client.get_object_type_from_id("001B00000123456")  # 15 chars
            assert obj_type == "Account"

            obj_type = sf_client.get_object_type_from_id("003B00000123456")  # 15 chars
            assert obj_type == "Contact"

    def test_get_object_type_from_id_custom(self, sf_client, mock_describe_global):
        """Test getting object type from custom object ID."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            obj_type = sf_client.get_object_type_from_id("a00B00000123456")  # 15 chars
            assert obj_type == "CustomObject__c"

    def test_get_object_type_from_id_18char(self, sf_client, mock_describe_global):
        """Test with 18-character ID."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            obj_type = sf_client.get_object_type_from_id("001B00000123456ABC")  # 18 chars
            assert obj_type == "Account"

    def test_get_object_type_from_id_not_found(self, sf_client, mock_describe_global):
        """Test with unknown key prefix."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            obj_type = sf_client.get_object_type_from_id("999B00000123456")  # 15 chars
            assert obj_type is None

    def test_get_object_type_from_id_invalid(self, sf_client):
        """Test with invalid ID."""
        with pytest.raises(ValueError, match="Invalid Salesforce ID"):
            sf_client.get_object_type_from_id("invalid-id")

    def test_list_objects_all(self, sf_client, mock_describe_global):
        """Test listing all objects."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            objects = sf_client.list_objects()
            assert len(objects) == 4

    def test_list_objects_custom_only(self, sf_client, mock_describe_global):
        """Test filtering for custom objects only."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            objects = sf_client.list_objects(custom_only=True)
            assert len(objects) == 2
            assert all(obj["custom"] for obj in objects)

    def test_list_objects_queryable_only(self, sf_client, mock_describe_global):
        """Test filtering for queryable objects only."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            objects = sf_client.list_objects(queryable_only=True)
            assert len(objects) == 3
            assert all(obj["queryable"] for obj in objects)

    def test_list_objects_createable_only(self, sf_client, mock_describe_global):
        """Test filtering for createable objects only."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            objects = sf_client.list_objects(createable_only=True)
            assert len(objects) == 3
            assert all(obj["createable"] for obj in objects)

    def test_list_objects_pattern(self, sf_client, mock_describe_global):
        """Test filtering by pattern."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            # Case-insensitive pattern matching
            objects = sf_client.list_objects(pattern=".*custom.*")
            assert len(objects) == 2
            assert all("custom" in obj["name"].lower() for obj in objects)

            # Specific pattern
            objects = sf_client.list_objects(pattern="^Account$")
            assert len(objects) == 1
            assert objects[0]["name"] == "Account"

    def test_list_objects_combined_filters(self, sf_client, mock_describe_global):
        """Test combining multiple filters."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            objects = sf_client.list_objects(custom_only=True, queryable_only=True)
            assert len(objects) == 1
            assert objects[0]["name"] == "CustomObject__c"

    def test_print_objects(self, sf_client, mock_describe_global, capsys):
        """Test print_objects output."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            sf_client.print_objects(limit=10)

            captured = capsys.readouterr()
            assert "Account" in captured.out
            assert "Contact" in captured.out
            assert "Total: 4 object(s)" in captured.out

    def test_print_objects_with_limit(self, sf_client, mock_describe_global, capsys):
        """Test print_objects with limit."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            sf_client.print_objects(limit=2)

            captured = capsys.readouterr()
            assert "... and 2 more (showing 2/4)" in captured.out

    def test_print_objects_custom_only(self, sf_client, mock_describe_global, capsys):
        """Test print_objects with custom_only filter."""
        with patch.object(sf_client, "describe_global", return_value=mock_describe_global):
            sf_client.print_objects(custom_only=True)

            captured = capsys.readouterr()
            assert "CustomObject__c" in captured.out
            assert "AnotherCustom__c" in captured.out
            # Standard objects should not be in output
            assert captured.out.count("Account") <= 1  # Only in header
