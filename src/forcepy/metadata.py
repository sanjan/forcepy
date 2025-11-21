"""Metadata and describe operations for forcepy.

Provides access to Salesforce object and field metadata with caching.
"""

import logging
from typing import Any, Optional

from .results import Result, ResultSet

logger = logging.getLogger(__name__)


class FieldDescribe(Result):
    """Describes a single field in a Salesforce object."""

    def __init__(self, data: dict[str, Any]):
        """Initialize field describe.

        Args:
            data: Field describe data from Salesforce
        """
        super().__init__(data)

    @property
    def is_required(self) -> bool:
        """Check if field is required for create operations.

        Returns:
            True if field cannot be null, has no default, and is createable
        """
        return (
            not self.get("nillable", True)
            and not self.get("defaultedOnCreate", False)
            and self.get("createable", False)
        )

    @property
    def is_updateable(self) -> bool:
        """Check if field is updateable.

        Returns:
            True if field can be updated
        """
        return self.get("updateable", False)

    @property
    def is_createable(self) -> bool:
        """Check if field can be set on create.

        Returns:
            True if field can be set when creating records
        """
        return self.get("createable", False)

    def __repr__(self):
        return f"<FieldDescribe({self.get('name')}: {self.get('type')})>"


class FieldDescribeSet(ResultSet):
    """Collection of field describes with helper methods."""

    dict_container = FieldDescribe

    def get_by_name(self, name: str) -> Optional[FieldDescribe]:
        """Get field by name (case-insensitive).

        Args:
            name: Field name

        Returns:
            FieldDescribe or None
        """
        name_lower = name.lower()
        for field in self:
            if field.get("name", "").lower() == name_lower:
                return field
        return None

    def required_fields(self) -> "FieldDescribeSet":
        """Get all required fields.

        Returns:
            FieldDescribeSet of required fields
        """
        return self.filter(lambda f: f.is_required)

    def updateable_fields(self) -> "FieldDescribeSet":
        """Get all updateable fields.

        Returns:
            FieldDescribeSet of updateable fields
        """
        return self.filter(lambda f: f.is_updateable)

    def createable_fields(self) -> "FieldDescribeSet":
        """Get all createable fields.

        Returns:
            FieldDescribeSet of createable fields
        """
        return self.filter(lambda f: f.is_createable)


class ObjectDescribe(Result):
    """Describes a Salesforce object (sobject)."""

    def __init__(self, data: dict[str, Any]):
        """Initialize object describe.

        Args:
            data: Describe data from Salesforce
        """
        super().__init__(data)

        # Convert fields to FieldDescribeSet
        if "fields" in data:
            self.fields = FieldDescribeSet([FieldDescribe(f) for f in data["fields"]])
        else:
            self.fields = FieldDescribeSet()

    def get_field_describe(self, name: str) -> Optional[FieldDescribe]:
        """Get field describe by name.

        Args:
            name: Field name

        Returns:
            FieldDescribe or None
        """
        return self.fields.get_by_name(name)

    def get_picklist_values(self, field_name: str, active_only: bool = True) -> list[dict[str, Any]]:
        """Get picklist values for a field.

        Args:
            field_name: Name of picklist field
            active_only: Only return active values (default: True)

        Returns:
            List of picklist value dicts with 'value' and 'label' keys

        Raises:
            ValueError: If field not found or not a picklist
        """
        field = self.get_field_describe(field_name)
        if not field:
            raise ValueError(f"Field not found: {field_name}")

        field_type = field.get("type")
        if field_type not in ("picklist", "multipicklist"):
            raise ValueError(f"Field {field_name} is not a picklist (type: {field_type})")

        values = field.get("picklistValues", [])
        if active_only:
            values = [v for v in values if v.get("active", False)]

        return values

    def get_dependent_picklist_values(
        self, field_name: str, controlling_field: str = None, controlling_value: str = None, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get dependent picklist values filtered by controlling field value.

        Args:
            field_name: Name of the dependent picklist field
            controlling_field: Name of the controlling field (auto-detected if not provided)
            controlling_value: Value of the controlling field to filter by
            active_only: Only return active values (default: True)

        Returns:
            List of valid picklist values for the controlling value

        Example:
            >>> describe = sf.describe('Case')
            >>> # Get Sub_Category values valid when Category='Hardware'
            >>> values = describe.get_dependent_picklist_values(
            ...     'Sub_Category__c',
            ...     controlling_value='Hardware'
            ... )
        """
        from .utils import decode_validfor_bitmap

        # Get the dependent field
        field_desc = self.get_field_describe(field_name)
        if not field_desc:
            raise ValueError(f"Field {field_name} not found")

        # Convert to dict for easier access
        field = dict(field_desc)

        # Check if it's a picklist
        field_type = field.get("type")
        if field_type not in ("picklist", "multipicklist"):
            raise ValueError(f"Field {field_name} is not a picklist")

        # Get controlling field if not provided
        if not controlling_field:
            controlling_field = field.get("controllerName")
            if not controlling_field:
                # Not a dependent picklist, return all values
                return self.get_picklist_values(field_name, active_only=active_only)

        # Get controlling field's picklist values
        controlling_field_desc = self.get_field_describe(controlling_field)
        if not controlling_field_desc:
            raise ValueError(f"Controlling field {controlling_field} not found")

        controlling_values = controlling_field_desc.get("picklistValues", [])

        # Find index of the controlling value
        controlling_index = None
        for idx, val in enumerate(controlling_values):
            if val.get("value") == controlling_value:
                controlling_index = idx
                break

        if controlling_index is None:
            raise ValueError(f"Controlling value '{controlling_value}' not found in {controlling_field}")

        # Filter dependent values based on validFor bitmap
        dependent_values = field.get("picklistValues", [])
        valid_values = []

        for dep_val in dependent_values:
            # Check if active if requested
            if active_only and not dep_val.get("active", False):
                continue

            # Check validFor bitmap
            validfor = dep_val.get("validFor")
            if validfor and decode_validfor_bitmap(validfor, controlling_index):
                valid_values.append(dep_val)
            elif not validfor:
                # No validFor means it's valid for all
                valid_values.append(dep_val)

        return valid_values

    @property
    def field_names(self) -> list[str]:
        """Get list of all field names.

        Returns:
            List of field names
        """
        return [f.get("name") for f in self.fields]

    @property
    def required_fields(self) -> FieldDescribeSet:
        """Get all required fields.

        Returns:
            FieldDescribeSet of required fields
        """
        return self.fields.required_fields()

    @property
    def is_queryable(self) -> bool:
        """Check if object is queryable.

        Returns:
            True if object can be queried
        """
        return self.get("queryable", False)

    @property
    def is_createable(self) -> bool:
        """Check if records can be created.

        Returns:
            True if records can be created
        """
        return self.get("createable", False)

    @property
    def is_updateable(self) -> bool:
        """Check if records can be updated.

        Returns:
            True if records can be updated
        """
        return self.get("updateable", False)

    @property
    def is_deletable(self) -> bool:
        """Check if records can be deleted.

        Returns:
            True if records can be deleted
        """
        return self.get("deletable", False)

    def __repr__(self):
        return f"<ObjectDescribe({self.get('name')}: {len(self.fields)} fields)>"


class DescribeCache:
    """Cache for object describes."""

    def __init__(self, max_size: int = 100):
        """Initialize describe cache.

        Args:
            max_size: Maximum number of describes to cache
        """
        self._cache: dict[str, ObjectDescribe] = {}
        self._max_size = max_size

    def get(self, sobject_name: str) -> Optional[ObjectDescribe]:
        """Get cached describe.

        Args:
            sobject_name: Object name

        Returns:
            ObjectDescribe or None
        """
        return self._cache.get(sobject_name)

    def set(self, sobject_name: str, describe: ObjectDescribe) -> None:
        """Cache a describe.

        Args:
            sobject_name: Object name
            describe: ObjectDescribe to cache
        """
        # Simple LRU: if cache full, remove oldest entry
        if len(self._cache) >= self._max_size and sobject_name not in self._cache:
            # Remove first item (oldest in dict for Python 3.7+)
            first_key = next(iter(self._cache))
            del self._cache[first_key]
            logger.debug(f"Evicted {first_key} from describe cache")

        self._cache[sobject_name] = describe

    def clear(self) -> None:
        """Clear all cached describes."""
        self._cache.clear()

    def __len__(self):
        return len(self._cache)

    def __contains__(self, sobject_name: str):
        return sobject_name in self._cache
