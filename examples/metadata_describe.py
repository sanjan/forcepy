"""Metadata and describe operations examples for forcepy.

Demonstrates how to inspect Salesforce object and field metadata.
"""

from forcepy import Salesforce

# Initialize client (auto-authenticates)
sf = Salesforce(username="user@example.com", password="password")

print("=== Metadata & Describe Examples ===\n")

# Example 1: Describe an Object
print("1. Describe an Object")
print("-" * 50)

account_describe = sf.describe("Account")
print(f"Object: {account_describe.get('name')}")
print(f"Label: {account_describe.get('label')}")
print(f"Fields: {len(account_describe.fields)}")
print(f"Queryable: {account_describe.is_queryable}")
print(f"Createable: {account_describe.is_createable}")
print(f"Updateable: {account_describe.is_updateable}")
print(f"Deletable: {account_describe.is_deletable}\n")

# Example 2: Get Field Information
print("2. Get Field Information")
print("-" * 50)

name_field = account_describe.get_field_describe("Name")
print(f"Field: {name_field.get('name')}")
print(f"Type: {name_field.get('type')}")
print(f"Length: {name_field.get('length')}")
print(f"Required: {name_field.is_required}")
print(f"Createable: {name_field.is_createable}")
print(f"Updateable: {name_field.is_updateable}\n")

# Example 3: List All Fields
print("3. List All Fields")
print("-" * 50)

print("All field names:")
for i, field_name in enumerate(account_describe.field_names[:10], 1):
    print(f"  {i}. {field_name}")
print(f"  ... and {len(account_describe.field_names) - 10} more\n")

# Example 4: Get Required Fields
print("4. Get Required Fields")
print("-" * 50)

required_fields = account_describe.required_fields
print(f"Found {len(required_fields)} required field(s):")
for field in required_fields:
    print(f"  - {field.get('name')} ({field.get('type')})")
print()

# Example 5: Get Updateable Fields
print("5. Get Updateable Fields (first 10)")
print("-" * 50)

updateable = account_describe.fields.updateable_fields()
print(f"Found {len(updateable)} updateable field(s):")
for field in list(updateable)[:10]:
    print(f"  - {field.get('name')}")
print(f"  ... and {len(updateable) - 10} more\n")

# Example 6: Picklist Values
print("6. Get Picklist Values")
print("-" * 50)

# Assuming Industry is a picklist field
try:
    industry_values = account_describe.get_picklist_values("Industry")
    print(f"Industry picklist values ({len(industry_values)} active):")
    for value in industry_values[:5]:
        print(f"  - {value['value']}: {value['label']}")
    if len(industry_values) > 5:
        print(f"  ... and {len(industry_values) - 5} more")
except ValueError as e:
    print(f"Could not get picklist values: {e}")
print()

# Example 7: Global Describe (List All Objects)
print("7. Global Describe - List All Objects")
print("-" * 50)

all_objects = sf.describe_global()
print(f"Found {len(all_objects)} sobjects")
print("\nStandard objects (first 10):")
standard = [obj for obj in all_objects if not obj.get("custom", False)]
for i, obj in enumerate(standard[:10], 1):
    print(f"  {i}. {obj['name']} - {obj['label']}")

print("\nCustom objects (first 5):")
custom = [obj for obj in all_objects if obj.get("custom", False)]
if custom:
    for i, obj in enumerate(custom[:5], 1):
        print(f"  {i}. {obj['name']} - {obj['label']}")
else:
    print("  (none found)")
print()

# Example 8: Org Limits
print("8. Get Org Limits")
print("-" * 50)

limits = sf.get_limits()
print("Key org limits:")
print(f"  Daily API Requests: {limits['DailyApiRequests']['Remaining']:,}/{limits['DailyApiRequests']['Max']:,}")
print(f"  Concurrent API Requests: {limits.get('ConcurrentAsyncGetReportInstances', {}).get('Remaining', 'N/A')}")
print(f"  DML Rows: {limits.get('DailyDurableStreamingApiEvents', {}).get('Remaining', 'N/A')}")
print()

# Example 9: Caching Behavior
print("9. Caching Behavior")
print("-" * 50)

import time

# First call - fetches from Salesforce
start = time.time()
describe1 = sf.describe("Account", use_cache=False)
elapsed1 = time.time() - start

# Second call - uses cache
start = time.time()
describe2 = sf.describe("Account", use_cache=True)
elapsed2 = time.time() - start

print(f"First call (no cache): {elapsed1*1000:.1f}ms")
print(f"Second call (cached): {elapsed2*1000:.1f}ms")
print(f"Speed improvement: {elapsed1/elapsed2:.0f}x faster\n")

# Example 10: Build Dynamic Query from Metadata
print("10. Build Dynamic Query from Metadata")
print("-" * 50)

# Get all queryable fields
contact_describe = sf.describe("Contact")
queryable_fields = [
    f.get("name")
    for f in contact_describe.fields
    if f.get("name") not in ("attributes", "Photo", "Jigsaw")  # Skip special fields
][:10]  # Limit to first 10

# Build SOQL query
fields_str = ", ".join(queryable_fields)
soql = f"SELECT {fields_str} FROM Contact LIMIT 5"
print(f"Generated query:\n{soql}\n")

try:
    results = sf.query(soql)
    print(f"Found {len(results)} contact(s)")
    if results:
        first = results[0]
        print(f"First contact: {first.get('FirstName')} {first.get('LastName')}")
except Exception as e:
    print(f"Query failed: {e}")
print()

# Example 11: Validate Field Names Before Insert
print("11. Validate Field Names Before Insert")
print("-" * 50)

def validate_fields(sobject_name, data):
    """Validate field names exist and are createable."""
    describe = sf.describe(sobject_name)
    createable_fields = {f.get("name").lower() for f in describe.fields.createable_fields()}

    errors = []
    for field_name in data.keys():
        if field_name.lower() not in createable_fields:
            errors.append(f"Field '{field_name}' is not createable or doesn't exist")

    return errors

# Test with valid data
valid_data = {"Name": "Test Account", "Industry": "Technology"}
errors = validate_fields("Account", valid_data)
if errors:
    print(f"❌ Validation failed:")
    for error in errors:
        print(f"   {error}")
else:
    print(f"✓ Valid data: {valid_data}")

# Test with invalid data
invalid_data = {"Name": "Test", "InvalidField": "value", "Id": "001xx"}
errors = validate_fields("Account", invalid_data)
if errors:
    print(f"❌ Validation failed:")
    for error in errors:
        print(f"   {error}")
print()

# Example 12: Find Custom Fields
print("12. Find Custom Fields")
print("-" * 50)

custom_fields = [f for f in account_describe.fields if f.get("custom", False)]
print(f"Found {len(custom_fields)} custom field(s):")
for field in custom_fields[:5]:
    print(f"  - {field.get('name')} ({field.get('type')})")
if len(custom_fields) > 5:
    print(f"  ... and {len(custom_fields) - 5} more")
print()

# Example 13: Relationship Fields
print("13. Find Relationship Fields")
print("-" * 50)

relationship_fields = [
    f for f in account_describe.fields if f.get("type") in ("reference", "lookup", "master-detail")
]
print(f"Found {len(relationship_fields)} relationship field(s):")
for field in relationship_fields[:5]:
    ref_to = field.get("referenceTo", [])
    print(f"  - {field.get('name')} → {', '.join(ref_to)}")
if len(relationship_fields) > 5:
    print(f"  ... and {len(relationship_fields) - 5} more")
print()

print("=== Performance Benefits ===")
print("-" * 50)
print("✓ Metadata cached automatically")
print("✓ 100-1000x faster than repeated API calls")
print("✓ Use to build dynamic queries and validate data")
print("✓ Essential for building generic Salesforce tools")
print("\nDone!")

