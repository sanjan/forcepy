"""Sobject and SobjectSet classes for forcepy."""

from typing import Any, Optional

from .query import parse_datetime
from .results import Result, ResultSet


class Sobject(Result):
    """Salesforce object record with enhanced functionality."""

    nested_token = "."

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        # Auto-parse datetime fields
        for key in self:
            if (
                key.endswith(("Date", "Date__c", "At", "At__c", "_Time__c", "Start__c", "End__c"))
                or "_On_" in key
                or "Date_Time" in key
            ):
                value = self[key]
                if isinstance(value, str) and "T" in value:
                    try:
                        self[key] = parse_datetime(value)
                    except (ValueError, AttributeError):
                        pass

    def patch(self, client: Any, **kwargs: Any) -> Any:
        """Update this record in Salesforce.

        Args:
            client: Salesforce client instance
            **kwargs: Fields to update

        Returns:
            API response
        """
        if "attributes" not in self or "url" not in self.attributes:
            raise ValueError("Cannot patch record without attributes.url")

        # Update via client
        sobject_type = self.attributes["type"]
        record_id = self.Id

        response = client.sobjects[sobject_type][record_id].patch(**kwargs)
        self.update(kwargs)
        return response

    def delete(self, client: Any) -> Any:
        """Delete this record from Salesforce.

        Args:
            client: Salesforce client instance

        Returns:
            API response
        """
        if "attributes" not in self or "url" not in self.attributes:
            raise ValueError("Cannot delete record without attributes.url")

        sobject_type = self.attributes["type"]
        record_id = self.Id

        return client.sobjects[sobject_type][record_id].delete()

    def refresh(self, client: Any) -> None:
        """Refresh this record from Salesforce.

        Args:
            client: Salesforce client instance
        """
        if "attributes" not in self or "url" not in self.attributes:
            raise ValueError("Cannot refresh record without attributes.url")

        sobject_type = self.attributes["type"]
        record_id = self.Id

        fresh_data = client.sobjects[sobject_type][record_id].get()
        self.clear()
        self.update(fresh_data)


class SobjectSet(ResultSet):
    """Collection of Sobject instances with enhanced query methods."""

    dict_container = Sobject

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Pagination metadata
        self.next_records_url: Optional[str] = None
        self.done: bool = True
        self.total_size: Optional[int] = None

    def split_fields(self, field: str) -> list:
        """Split field name for nested access.

        Args:
            field: Field name

        Returns:
            List of field parts
        """
        parts = []
        for part in field.split("__"):
            if part in ("r", "c") and parts:
                parts[-1] += f"__{part}"
            else:
                parts.append(part)
        return parts

    def earliest(self, field: str = "CreatedDate") -> Optional[Sobject]:
        """Get earliest record by date field.

        Args:
            field: Date field to sort by

        Returns:
            Earliest Sobject or None
        """
        if not self:
            return None
        return self.order_by(field, asc=True)[0]

    def latest(self, field: str = "CreatedDate") -> Optional[Sobject]:
        """Get latest record by date field.

        Args:
            field: Date field to sort by

        Returns:
            Latest Sobject or None
        """
        if not self:
            return None
        return self.order_by(field, asc=False)[0]


# Set Sobject.list_container
Sobject.list_container = SobjectSet
