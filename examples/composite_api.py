"""Composite API examples for forcepy.

Demonstrates batch operations with up to 25 subrequests in a single API call.
"""

from forcepy import CompositeError, Salesforce, validate_composite_response

# Initialize client (auto-authenticates)
sf = Salesforce(username="user@example.com", password="password")

print("=== Composite API Examples ===\n")

# Example 1: Basic Composite Request
print("1. Basic Composite Request")
print("-" * 50)

composite = sf.composite()
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "NewAccount1", body={"Name": "Acme Corp"}
)
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "NewAccount2", body={"Name": "Global Industries"}
)

response = composite.execute()
print(f"Created {len(response)} accounts")
print(f"Account 1 ID: {response['NewAccount1'].body['id']}")
print(f"Account 2 ID: {response['NewAccount2'].body['id']}\n")

# Example 2: Reference Previous Results
print("2. Reference Previous Results with @{referenceId.field}")
print("-" * 50)

composite = sf.composite()

# Create account
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "NewAccount",
    body={"Name": "Tech Startup"},
)

# Create contact linked to the account (using @{NewAccount.id})
composite.post(
    f"/services/data/v{sf.version}/sobjects/Contact",
    "NewContact",
    body={
        "FirstName": "John",
        "LastName": "Doe",
        "AccountId": "@{NewAccount.id}",  # Reference from previous request
    },
)

# Query the account we just created
composite.get(
    f"/services/data/v{sf.version}/sobjects/Account/@{{NewAccount.id}}",
    "GetAccount",
)

response = composite.execute()
print(f"Account ID: {response['NewAccount'].body['id']}")
print(f"Contact ID: {response['NewContact'].body['id']}")
print(f"Account Name: {response['GetAccount'].body['Name']}\n")

# Example 3: All-or-None (Transaction-like)
print("3. All-or-None Mode (Transaction-like)")
print("-" * 50)

try:
    composite = sf.composite(all_or_none=True)  # All must succeed or all fail

    composite.post(
        f"/services/data/v{sf.version}/sobjects/Account", "GoodAccount", body={"Name": "Valid Account"}
    )

    # This will fail (missing required field)
    composite.post(
        f"/services/data/v{sf.version}/sobjects/Contact",
        "BadContact",
        body={"FirstName": "John"},  # Missing required LastName
    )

    response = composite.execute()
    print("All succeeded (won't get here)")

except CompositeError as e:
    print(f"✗ Transaction failed: {e}")
    print("  All changes rolled back\n")

# Example 4: Mixed Operations (CRUD)
print("4. Mixed CRUD Operations")
print("-" * 50)

composite = sf.composite()

# Create
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "CreateAccount", body={"Name": "New Company"}
)

# Read
composite.get(
    f"/services/data/v{sf.version}/sobjects/Account/@{{CreateAccount.id}}",
    "ReadAccount",
)

# Update
composite.patch(
    f"/services/data/v{sf.version}/sobjects/Account/@{{CreateAccount.id}}",
    "UpdateAccount",
    body={"Phone": "(555) 123-4567"},
)

# Delete (commented out to avoid actually deleting)
# composite.delete(
#     f'/services/data/v{sf.version}/sobjects/Account/@{{CreateAccount.id}}',
#     'DeleteAccount'
# )

response = composite.execute()
print(f"Created: {response['CreateAccount'].body['id']}")
print(f"Read Name: {response['ReadAccount'].body['Name']}")
print(f"Updated: {response['UpdateAccount'].is_success()}\n")

# Example 5: Method Chaining
print("5. Method Chaining (Fluent API)")
print("-" * 50)

response = (
    sf.composite()
    .post(f"/services/data/v{sf.version}/sobjects/Account", "Acc1", body={"Name": "Company A"})
    .post(f"/services/data/v{sf.version}/sobjects/Account", "Acc2", body={"Name": "Company B"})
    .post(f"/services/data/v{sf.version}/sobjects/Account", "Acc3", body={"Name": "Company C"})
    .execute()
)

print(f"Created {len(response)} accounts via chaining\n")

# Example 6: Validate Response
print("6. Validate Response with Helper")
print("-" * 50)

composite = sf.composite()
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "Account1", body={"Name": "Test"}
)
response = composite.execute()

# Validate all succeeded
try:
    validate_composite_response(response)
    print("✓ All subrequests succeeded")
except CompositeError as e:
    print(f"✗ Some subrequests failed: {e}")
print()

# Example 7: Iterate Over Responses
print("7. Iterate Over All Responses")
print("-" * 50)

composite = sf.composite()
for i in range(5):
    composite.post(
        f"/services/data/v{sf.version}/sobjects/Account", f"Account{i}", body={"Name": f"Company {i}"}
    )

response = composite.execute()

for sub_response in response:
    if sub_response.is_success():
        print(f"✓ {sub_response.reference_id}: {sub_response.body['id']}")
    else:
        print(f"✗ {sub_response.reference_id}: Failed")
print()

# Example 8: Check Errors
print("8. Check for Errors")
print("-" * 50)

composite = sf.composite(all_or_none=False)  # Continue on error
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "GoodAccount", body={"Name": "Valid"}
)
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "BadAccount",
    body={},  # Missing required Name field
)

response = composite.execute()

if response.all_succeeded():
    print("All succeeded")
else:
    errors = response.get_errors()
    print(f"Found {len(errors)} error(s):")
    for error in errors:
        print(f"  - {error['referenceId']}: HTTP {error['httpStatusCode']}")
        print(f"    {error['body']}")
print()

# Example 9: Query in Composite
print("9. Include Queries (Max 5 per composite)")
print("-" * 50)

composite = sf.composite()

# Create account
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account", "NewAccount", body={"Name": "Query Test"}
)

# Query to find it
query = "SELECT Id, Name FROM Account WHERE Name='Query Test'"
composite.get(
    f"/services/data/v{sf.version}/query?q={query}",
    "QueryAccount",
)

response = composite.execute()
print(f"Created: {response['NewAccount'].body['id']}")
print(f"Query found: {len(response['QueryAccount'].body['records'])} record(s)\n")

# Example 10: Bulk Update Pattern
print("10. Bulk Update Pattern (up to 25 records)")
print("-" * 50)

# First, get IDs of accounts to update (from previous queries)
account_ids = ["001xx0000012345", "001xx0000054321", "001xx0000067890"]

composite = sf.composite()
for i, account_id in enumerate(account_ids):
    composite.patch(
        f"/services/data/v{sf.version}/sobjects/Account/{account_id}",
        f"Update{i}",
        body={"Industry": "Technology"},
    )

try:
    response = composite.execute()
    successes = sum(1 for r in response if r.is_success())
    print(f"✓ Updated {successes}/{len(account_ids)} accounts")
except Exception as e:
    print(f"✗ Bulk update failed: {e}")
print()

# Example 11: Complex Workflow
print("11. Complex Multi-Step Workflow")
print("-" * 50)

composite = sf.composite(all_or_none=True)

# Step 1: Create parent account
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "ParentAccount",
    body={"Name": "Parent Corp", "Industry": "Technology"},
)

# Step 2: Create child account
composite.post(
    f"/services/data/v{sf.version}/sobjects/Account",
    "ChildAccount",
    body={
        "Name": "Subsidiary Inc",
        "ParentId": "@{ParentAccount.id}",  # Link to parent
        "Industry": "Technology",
    },
)

# Step 3: Create primary contact
composite.post(
    f"/services/data/v{sf.version}/sobjects/Contact",
    "PrimaryContact",
    body={
        "FirstName": "Jane",
        "LastName": "Smith",
        "AccountId": "@{ParentAccount.id}",
        "Email": "jane@parentcorp.com",
    },
)

# Step 4: Create opportunity
composite.post(
    f"/services/data/v{sf.version}/sobjects/Opportunity",
    "NewOpportunity",
    body={
        "Name": "Q1 Deal",
        "AccountId": "@{ParentAccount.id}",
        "StageName": "Prospecting",
        "CloseDate": "2024-12-31",
    },
)

# Step 5: Query to verify
composite.get(
    f"/services/data/v{sf.version}/sobjects/Account/@{{ParentAccount.id}}",
    "VerifyParent",
)

try:
    response = composite.execute()
    print("✓ Complex workflow completed:")
    print(f"  Parent Account: {response['ParentAccount'].body['id']}")
    print(f"  Child Account: {response['ChildAccount'].body['id']}")
    print(f"  Contact: {response['PrimaryContact'].body['id']}")
    print(f"  Opportunity: {response['NewOpportunity'].body['id']}")
except CompositeError as e:
    print(f"✗ Workflow failed: {e}")
print()

print("=== Performance Benefits ===")
print("-" * 50)
print("Single API call vs. multiple calls:")
print("  5 operations individually: ~5 API calls (~2-5 seconds)")
print("  5 operations composite: 1 API call (~0.5 seconds)")
print("  25 operations composite: 1 API call (~1 second)")
print("\nComposite API is 5-10x faster for batch operations!")
print("\nDone!")

