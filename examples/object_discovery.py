"""Object discovery examples - for Salesforce newcomers."""

from forcepy import Salesforce

# Initialize client (auto-authenticates if username/password provided)
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

print("=== Discovering Available Objects ===\n")

# Example 1: Get all objects
print("Example 1: Get all objects")
all_objects = sf.describe_global()
print(f"Found {len(all_objects)} total objects\n")

# Example 2: List custom objects only
print("Example 2: Custom objects only")
custom_objects = sf.list_objects(custom_only=True)
print(f"Found {len(custom_objects)} custom objects")
for obj in custom_objects[:5]:  # First 5
    print(f"  - {obj['name']}: {obj['label']}")
print()

# Example 3: List queryable objects
print("Example 3: Queryable objects")
queryable = sf.list_objects(queryable_only=True)
print(f"Found {len(queryable)} queryable objects")
for obj in queryable[:5]:  # First 5
    print(f"  - {obj['name']}")
print()

# Example 4: Find objects by pattern
print("Example 4: Find objects matching 'Account'")
account_objects = sf.list_objects(pattern=".*account.*")
for obj in account_objects:
    print(f"  - {obj['name']}: {obj['label']}")
print()

# Example 5: Print formatted table (interactive exploration)
print("Example 5: Print formatted object list")
sf.print_objects(custom_only=True, limit=10)
print()

# Example 6: Get detailed information about an object
print("Example 6: Detailed object information")
describe = sf.describe('Account')
print(f"Object: {describe.name}")
print(f"Label: {describe.label}")
print(f"Fields: {len(describe.fields)}")
print(f"Is queryable: {describe.is_queryable}")
print(f"Is createable: {describe.is_createable}")
print()

# Example 7: Determine object type from record ID
print("Example 7: Identify object type from ID")

# Example IDs (these are common key prefixes) - 15 characters
example_ids = {
    '001B00000123456': 'Should be Account',
    '003B00000123456': 'Should be Contact',
    '006B00000123456': 'Should be Opportunity',
    '500B00000123456': 'Should be Case',
}

for record_id, expected in example_ids.items():
    try:
        obj_type = sf.get_object_type_from_id(record_id)
        print(f"  ID {record_id[:3]}... -> {obj_type or 'Unknown'} ({expected})")
    except ValueError as e:
        print(f"  Invalid ID: {e}")
print()

# Example 8: Working with query results - identify object types
print("Example 8: Identify object types from query results")

# When you have IDs but don't know what they are
mixed_ids = [
    '001B00000123456',  # Account
    '003B00000123456',  # Contact
    '006B00000123456',  # Opportunity
]

for record_id in mixed_ids:
    obj_type = sf.get_object_type_from_id(record_id)
    if obj_type:
        # Now you can query the specific object
        print(f"  {record_id} is a {obj_type}")
        # query = f"SELECT Id, Name FROM {obj_type} WHERE Id = '{record_id}'"
        # result = sf.query(query)
print()

# Example 9: Filter by multiple criteria
print("Example 9: Complex filtering")
custom_queryable = sf.list_objects(
    custom_only=True,
    queryable_only=True,
    createable_only=True
)
print(f"Custom, queryable, createable objects: {len(custom_queryable)}")
for obj in custom_queryable[:3]:
    print(f"  - {obj['name']}")
print()

# Example 10: Explore object metadata
print("Example 10: Explore standard objects")
standard_objects = [obj for obj in all_objects if not obj.get('custom', False)]
print(f"Total standard objects: {len(standard_objects)}")

# Group by key prefix
by_prefix = {}
for obj in standard_objects[:20]:  # Sample
    prefix = obj.get('keyPrefix', 'None')
    if prefix:
        by_prefix[prefix] = obj['name']

print("\nSample key prefixes:")
for prefix, name in sorted(by_prefix.items())[:10]:
    print(f"  {prefix} -> {name}")
print()

print("💡 Tips for newcomers:")
print("  - Use print_objects() for quick interactive exploration")
print("  - Use list_objects() with filters to find specific objects")
print("  - Use get_object_type_from_id() when you have IDs but don't know the object")
print("  - Use describe() to get detailed field information")
print("  - Custom objects always end with '__c'")
print("  - Key prefixes (first 3 chars of ID) identify the object type")

