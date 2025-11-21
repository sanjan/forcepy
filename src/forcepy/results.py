"""Result containers for forcepy with filtering, grouping, and ordering capabilities."""

import collections
import csv
import datetime
import io
import re
from collections.abc import Iterator
from typing import Any, Callable, Optional, Union


class AttrDict(dict):
    """Dict that allows attribute access to keys."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, attr: str) -> Any:
        try:
            return self[attr]
        except KeyError as exc:
            raise AttributeError(str(exc))

    def __getitem__(self, item: str) -> Any:
        try:
            return super().__getitem__(item)
        except KeyError:
            raise KeyError(
                f"'{self.__class__.__name__}' object has no attribute '{item}', "
                f"available fields are: {', '.join(map(str, self.keys()))}"
            )


class Result(AttrDict):
    """Dict-like container with attribute access for Salesforce records."""

    nested_token = "__"
    list_container = "ResultSet"  # Will be set after ResultSet is defined

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Convert nested dicts to Result objects
        for key, value in list(self.items()):
            if isinstance(value, dict) and not isinstance(value, Result):
                self[key] = Result(value)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        return hash(self) == hash(other)

    def get_field(self, field: str, default: Any = None, raise_keyerror: bool = True) -> Any:
        """Get a field value, supporting nested access with __ separator.

        Args:
            field: Field name, can use __ for nested access
            default: Default value if field not found
            raise_keyerror: Whether to raise KeyError if field not found

        Returns:
            Field value
        """
        if self.nested_token in field:
            result = self
            for subfield in field.split(self.nested_token):
                try:
                    result = result[subfield]
                except (KeyError, TypeError):
                    if raise_keyerror:
                        raise
                    return default
            return result

        try:
            return self[field]
        except KeyError:
            if raise_keyerror:
                raise
            return default

    def get(self, field: str, default: Any = None) -> Any:
        """Get field value without raising KeyError."""
        return self.get_field(field, default, raise_keyerror=False)

    def serialize(self) -> dict[str, Any]:
        """Serialize to plain dict."""
        result = {}
        for k, v in self.items():
            if callable(v) or (isinstance(k, str) and k.startswith("_")):
                continue
            if isinstance(v, datetime.datetime):
                v = v.isoformat()
            elif hasattr(v, "serialize"):
                v = v.serialize()
            elif isinstance(v, list):
                v = [item.serialize() if hasattr(item, "serialize") else item for item in v]
            result[k] = v
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"


def split_fields(field: str) -> list[str]:
    """Split field name by __ but preserve SOQL patterns like __r and __c."""
    parts = []
    for part in field.split("__"):
        if part in ("r", "c") and parts:
            parts[-1] += f"__{part}"
        else:
            parts.append(part)
    return parts


def get_result_field(value: Any, field: str, ignore_missing: bool = False) -> Any:
    """Get field from result, handling nested access."""
    for subfield in split_fields(field):
        if isinstance(value, list):
            value = [get_result_field(v, subfield, ignore_missing) for v in value]
        else:
            try:
                value = value[subfield]
            except (KeyError, TypeError):
                if ignore_missing:
                    return None
                raise
        if value is None:
            return None
    return value


def get_filter_lookups(**kwargs: Any) -> list[tuple[str, Callable]]:
    """Build filter lookup functions from kwargs."""
    lookups = []

    def evaluate(target: Any, result: Any) -> Any:
        return target(result) if callable(target) else target

    for field, target in kwargs.items():
        # Parse field lookups
        if field.endswith(("__in", "__IN")):
            field = re.sub(r"__in$", "", field, flags=re.IGNORECASE)
            target_set = set(target) if isinstance(target, (list, tuple, set)) else target

            def lookup(v, r, t=target_set):
                return v in evaluate(t, r)

        elif field.endswith(("__contains", "__CONTAINS")):
            field = re.sub(r"__contains$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and evaluate(t, r) in v

        elif field.endswith(("__startswith", "__STARTSWITH")):
            field = re.sub(r"__startswith$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and v.startswith(evaluate(t, r))

        elif field.endswith(("__endswith", "__ENDSWITH")):
            field = re.sub(r"__endswith$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and v.endswith(evaluate(t, r))

        elif field.endswith(("__gt", "__GT")):
            field = re.sub(r"__gt$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v > evaluate(t, r)

        elif field.endswith(("__gte", "__GTE")):
            field = re.sub(r"__gte$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v >= evaluate(t, r)

        elif field.endswith(("__lt", "__LT")):
            field = re.sub(r"__lt$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v < evaluate(t, r)

        elif field.endswith(("__lte", "__LTE")):
            field = re.sub(r"__lte$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v <= evaluate(t, r)

        elif field.endswith(("__ne", "__NE")):
            field = re.sub(r"__ne$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v != evaluate(t, r)

        elif field.endswith(("__isnull", "__ISNULL")):
            field = re.sub(r"__isnull$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return (v is None) if evaluate(t, r) else (v is not None)

        elif field.endswith(("__icontains", "__ICONTAINS")):
            field = re.sub(r"__icontains$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                if v is None:
                    return False
                if isinstance(v, list):
                    # Handle list fields
                    return any(str(evaluate(t, r)).lower() in str(item).lower() for item in v)
                return str(evaluate(t, r)).lower() in str(v).lower()

        elif field.endswith(("__istartswith", "__ISTARTSWITH")):
            field = re.sub(r"__istartswith$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and str(v).lower().startswith(str(evaluate(t, r)).lower())

        elif field.endswith(("__iendswith", "__IENDSWITH")):
            field = re.sub(r"__iendswith$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and str(v).lower().endswith(str(evaluate(t, r)).lower())

        elif field.endswith(("__iexact", "__IEXACT")):
            field = re.sub(r"__iexact$", "", field, flags=re.IGNORECASE)

            def lookup(v, r, t=target):
                return v is not None and str(v).lower() == str(evaluate(t, r)).lower()

        else:
            # Exact match
            def lookup(v, r, t=target):
                return v == evaluate(t, r)

        lookups.append((field, lookup))

    return lookups


class ResultSet(collections.UserList):
    """List-like container with powerful filtering and grouping methods."""

    dict_container = Result

    def __getitem__(self, key: Union[int, slice]) -> Union[Result, "ResultSet"]:
        result = super().__getitem__(key)
        if isinstance(key, slice):
            return type(self)(result)
        return result

    def filter(self, *args: Callable, ignore_missing: bool = False, **kwargs: Any) -> "ResultSet":
        """Filter results by field values.

        Supports lookups:
        - field=value: exact match
        - field__in=[...]: value in list
        - field__contains=value: value in field
        - field__startswith=value: field starts with value
        - field__endswith=value: field ends with value
        - field__gt/gte/lt/lte=value: comparison
        - field__ne=value: not equal
        - field__isnull=True/False: null check
        - field__icontains=value: case-insensitive contains
        - field__istartswith=value: case-insensitive starts with
        - field__iendswith=value: case-insensitive ends with
        - field__iexact=value: case-insensitive exact match

        Args:
            *args: Filter functions
            ignore_missing: Ignore missing fields
            **kwargs: Field lookups

        Returns:
            Filtered ResultSet
        """
        lookups = get_filter_lookups(**kwargs)
        result = type(self)()

        for item in self:
            keep = True
            for field, lookup in lookups:
                try:
                    value = get_result_field(item, field, ignore_missing=ignore_missing)
                except (KeyError, TypeError):
                    keep = False
                    break

                if not lookup(value, item):
                    keep = False
                    break

            if keep:
                for func in args:
                    if not func(item):
                        keep = False
                        break

            if keep:
                result.append(item)

        return result

    def exclude(self, **kwargs: Any) -> "ResultSet":
        """Exclude results matching criteria."""
        all_items = set(id(item) for item in self)
        filtered_items = set(id(item) for item in self.filter(**kwargs))
        excluded_ids = all_items - filtered_items
        return type(self)(item for item in self if id(item) in excluded_ids)

    def get(self, **kwargs: Any) -> Result:
        """Get single result matching criteria."""
        results = self.filter(**kwargs)
        if not results:
            raise ValueError(f"No results for {kwargs}")
        if len(results) > 1:
            raise ValueError(f"Multiple results for {kwargs}")
        return results[0]

    def get_or_none(self, **kwargs: Any) -> Optional[Result]:
        """Get single result or None."""
        try:
            return self.get(**kwargs)
        except ValueError:
            return None

    def first(self) -> Optional[Result]:
        """Get first result or None."""
        return self[0] if self else None

    def last(self) -> Optional[Result]:
        """Get last result or None."""
        return self[-1] if self else None

    def group_by(self, *fields: Union[str, Callable]) -> dict[Any, "ResultSet"]:
        """Group results by field values.

        Args:
            *fields: Field names or callables

        Returns:
            Dict mapping group keys to ResultSets
        """
        groups: dict[Any, ResultSet] = collections.defaultdict(lambda: type(self)())
        multiple = len(fields) > 1

        for item in self:
            key_parts = []
            for field in fields:
                if callable(field):
                    value = field(item)
                else:
                    value = item.get_field(field)

                if not multiple:
                    key = value
                    break
                key_parts.append(value)
            else:
                key = tuple(key_parts)

            groups[key].append(item)

        # Convert to AggregateSet with count method
        return AggregateSet(groups)

    def order_by(self, *fields: Union[str, Callable], asc: bool = True, ignore_missing: bool = False) -> "ResultSet":
        """Sort results by field values.

        Args:
            *fields: Field names or callables
            asc: Sort ascending (True) or descending (False)
            ignore_missing: Ignore missing fields

        Returns:
            Sorted ResultSet
        """

        def sort_key(item: Result) -> tuple:
            if len(fields) == 1:
                field = fields[0]
                value = field(item) if callable(field) else item.get_field(field, raise_keyerror=not ignore_missing)
                return (value is not None, value)

            values = []
            for field in fields:
                value = field(item) if callable(field) else item.get_field(field, raise_keyerror=not ignore_missing)
                values.append((value is not None, value))
            return tuple(values)

        return type(self)(sorted(self, key=sort_key, reverse=not asc))

    def values_list(self, *fields: str, flat: bool = False, ignore_missing: bool = False) -> list:
        """Extract field values as list.

        Args:
            *fields: Field names
            flat: Return flat list (only for single field)
            ignore_missing: Ignore missing fields

        Returns:
            List of values or tuples
        """
        if flat and len(fields) != 1:
            raise ValueError("flat=True requires exactly one field")

        result = []
        for item in self:
            if flat:
                try:
                    value = item.get_field(fields[0])
                    result.append(value)
                except KeyError:
                    if not ignore_missing:
                        raise
            else:
                values = tuple(item.get_field(field, raise_keyerror=not ignore_missing) for field in fields)
                result.append(values)

        return result

    def ivalues(self, *fields: str, **kwargs: Any) -> Iterator:
        """Iterate over field values."""
        return iter(self.values_list(*fields, **kwargs))

    def earliest(self, field: str = "CreatedDate") -> Optional[Result]:
        """Get earliest record by field."""
        if not self:
            return None
        return self.order_by(field, asc=True)[0]

    def latest(self, field: str = "CreatedDate") -> Optional[Result]:
        """Get latest record by field."""
        if not self:
            return None
        return self.order_by(field, asc=False)[0]

    def serialize(self) -> list[dict[str, Any]]:
        """Serialize to list of dicts."""
        return [item.serialize() if hasattr(item, "serialize") else item for item in self]

    def to_csv(self, filepath: Optional[str] = None) -> Union[str, None]:
        """Export results to CSV format.

        Args:
            filepath: Optional file path to write. If None, returns CSV string.

        Returns:
            CSV string if filepath is None, otherwise None

        Example:
            >>> accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 10")
            >>> # Get CSV string
            >>> csv_data = accounts.records.to_csv()
            >>> # Or write to file
            >>> accounts.records.to_csv('accounts.csv')
        """
        if not self:
            return "" if filepath is None else None

        # Get all unique keys across all records
        fieldnames = []
        seen = set()
        for result in self:
            for key in result.keys():
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for result in self:
            # Convert None to empty string for CSV
            row = {k: ("" if v is None else v) for k, v in result.items()}
            writer.writerow(row)

        csv_content = output.getvalue()

        if filepath:
            with open(filepath, "w", newline="") as f:
                f.write(csv_content)
            return None
        return csv_content

    @classmethod
    def from_csv(cls, filepath_or_data: Union[str, "io.IOBase"]) -> "ResultSet":
        """Import results from CSV format.

        Args:
            filepath_or_data: File path string or file-like object

        Returns:
            ResultSet containing imported records

        Example:
            >>> # From file
            >>> accounts = ResultSet.from_csv('accounts.csv')
            >>> # From string
            >>> import io
            >>> csv_data = "Id,Name\\n001xxx,Acme Corp"
            >>> accounts = ResultSet.from_csv(io.StringIO(csv_data))
        """
        if isinstance(filepath_or_data, str):
            if "\n" in filepath_or_data or "," in filepath_or_data:
                # It's CSV data, not a filepath
                file_obj = io.StringIO(filepath_or_data)
            else:
                # It's a filepath
                file_obj = open(filepath_or_data, newline="")
        else:
            file_obj = filepath_or_data

        try:
            reader = csv.DictReader(file_obj)
            results = cls()
            for row in reader:
                # Convert empty strings back to None
                cleaned_row = {k: (None if v == "" else v) for k, v in row.items()}
                results.append(Result(cleaned_row))
            return results
        finally:
            if isinstance(filepath_or_data, str) and "\n" not in filepath_or_data and "," not in filepath_or_data:
                file_obj.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"


class AggregateSet(dict):
    """Dict subclass for grouped results with aggregation methods."""

    def count(self) -> dict[Any, int]:
        """Count items in each group."""
        return {key: len(value) for key, value in self.items()}

    def sum(self, field: Optional[str] = None) -> dict[Any, Any]:
        """Sum field values in each group."""
        if field is None:
            raise ValueError("field required for sum()")
        return {key: sum(item.get_field(field) for item in value) for key, value in self.items()}

    def avg(self, field: str) -> dict[Any, float]:
        """Average field values in each group."""
        result = {}
        for key, value in self.items():
            values = [item.get_field(field) for item in value]
            result[key] = sum(values) / len(values) if values else 0
        return result


# Set Result.list_container after ResultSet is defined
Result.list_container = ResultSet
