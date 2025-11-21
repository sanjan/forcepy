"""Composite context manager example."""

from forcepy import Salesforce

# Initialize client (auto-authenticates if username/password provided)
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

print("=== Composite Context Manager ===\n")

# Example 1: Basic batching with context manager
print("Example 1: Creating multiple records with context manager")
with sf as batch:
    # All these operations are queued, not executed immediately
    batch.sobjects.Account.post(Name="Acme Corp", Industry="Technology")
    batch.sobjects.Account.post(Name="Globex Inc", Industry="Manufacturing")
    batch.sobjects.Account.post(Name="Initech", Industry="Software")

    print("  - Queued 3 Account creates")
# Composite request executes automatically on exit
print("  ✅ Batch executed!\n")


# Example 2: Mixed CRUD operations
print("Example 2: Mixed operations (create, update, delete)")
with sf as batch:
    # Create
    batch.sobjects.Contact.post(FirstName="John", LastName="Doe", Email="john.doe@example.com")

    # Update (replace 'contact-id' with actual ID)
    # batch.sobjects.Contact['003xxxxxxxxxxxxxxx'].patch(Phone='555-1234')

    # Delete (replace 'old-contact-id' with actual ID)
    # batch.sobjects.Contact['003xxxxxxxxxxxxxxx'].delete()

    print("  - Queued mixed operations")
print("  ✅ Batch executed!\n")


# Example 3: Error handling
print("Example 3: Exception handling")
try:
    with sf as batch:
        batch.sobjects.Account.post(Name="Test Account")
        # Simulate an error during batching
        raise ValueError("Something went wrong!")
except ValueError as e:
    print(f"  ⚠️  Exception occurred: {e}")
    print("  ℹ️  Composite request was NOT executed due to exception\n")


# Example 4: Compare with manual composite API
print("Example 4: Manual vs Context Manager")
print("  Manual composite API:")
composite = sf.composite(all_or_none=False)
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "NewAccount1",
    body={"Name": "Manual Account 1"}
)
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "NewAccount2",
    body={"Name": "Manual Account 2"}
)
response = composite.execute()
print(f"    ✅ Created {len(response.composite_response)} records\n")

print("  Context manager (equivalent):")
with sf as batch:
    batch.sobjects.Account.post(Name="Context Account 1")
    batch.sobjects.Account.post(Name="Context Account 2")
print("    ✅ Same result, cleaner syntax!\n")


# Example 5: Accessing results
print("Example 5: Working with batch results")
# Note: The context manager returns results on exit, but they're not easily accessible
# For fine-grained control over results, use the manual composite API instead
composite = sf.composite(all_or_none=False)
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "NewAccount",
    body={"Name": "Result Check Account", "Industry": "Technology"}
)
response = composite.execute()

for subrequest in response.composite_response:
    print(f"  Reference ID: {subrequest.reference_id}")
    print(f"  Status Code: {subrequest.http_status_code}")
    if subrequest.is_success:
        print(f"  Created ID: {subrequest.body.get('id')}")
    print()

print("\n💡 Tip: Use context manager for simple batching.")
print("   Use manual composite API when you need fine-grained control over results.")

