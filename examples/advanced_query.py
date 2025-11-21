"""Advanced query features examples for forcepy.

Demonstrates SELECT * expansion, workbench URLs, iterquery, and more.
"""

import webbrowser

from forcepy import Salesforce, expand_select_star, format_soql, generate_workbench_url

# Initialize client (auto-authenticates)
sf = Salesforce(username="user@example.com", password="password")

print("=== Advanced Query Features ===\n")

# Example 1: SELECT * Expansion
print("1. SELECT * Expansion")
print("-" * 50)

# Query with SELECT *
soql = "SELECT * FROM Account LIMIT 5"
print(f"Original query: {soql}")

# Expand using helper function
expanded = expand_select_star(soql, sf.describe)
print(f"Expanded query: {expanded[:100]}...\n")

# Or use the built-in parameter
results = sf.query("SELECT * FROM Account LIMIT 5", expand_select_star=True)
print(f"Retrieved {len(results)} account(s) with all fields")
if results:
    print(f"Fields in result: {list(results[0].to_dict().keys())[:10]}...\n")

# Example 2: Iterquery for Large Datasets
print("2. Iterquery for Large Datasets")
print("-" * 50)

# Use iterquery for efficient pagination
count = 0
for account in sf.iterquery("SELECT Id, Name FROM Account"):
    count += 1
    if count <= 3:
        print(f"  {count}. {account.Name}")
    if count >= 100:  # Stop after 100 for demo
        break

print(f"... processed {count} account(s) efficiently\n")

# Example 3: Workbench URL Generation
print("3. Workbench URL Generation")
print("-" * 50)

soql = "SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology' ORDER BY Name LIMIT 100"
workbench_url = sf.get_workbench_url(soql)

print(f"SOQL Query:")
print(f"  {soql}\n")
print(f"Workbench URL:")
print(f"  {workbench_url}\n")
print(f"Open in browser: webbrowser.open(workbench_url)")

# Uncomment to actually open
# webbrowser.open(workbench_url)

# Example 4: Custom Workbench URL
print("4. Custom Workbench URL (Self-Hosted)")
print("-" * 50)

# Set custom Workbench instance
sf.set_workbench_url("https://workbench.mycompany.com")
custom_url = sf.get_workbench_url("SELECT Id FROM Contact LIMIT 10")
print(f"Custom Workbench URL:")
print(f"  {custom_url}\n")

# Reset to default
sf.set_workbench_url("https://workbench.developerforce.com")

# Example 5: SOQL Formatting
print("5. Format SOQL for Readability")
print("-" * 50)

complex_soql = "SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees FROM Account WHERE Industry = 'Technology' AND AnnualRevenue > 1000000 ORDER BY AnnualRevenue DESC LIMIT 50"

print("Original (one line):")
print(f"  {complex_soql[:80]}...")

formatted = format_soql(complex_soql)
print("\nFormatted:")
for line in formatted.split("\n"):
    print(f"  {line}")
print()

# Example 6: Workbench URL with SELECT *
print("6. Workbench URL with Expanded SELECT *")
print("-" * 50)

# Expand SELECT * and generate workbench URL
star_query = "SELECT * FROM Contact WHERE Email != null LIMIT 20"
print(f"Original: {star_query}")

expanded = expand_select_star(star_query, sf.describe)
print(f"Expanded: {expanded[:80]}...")

url = generate_workbench_url(expanded, sf.instance_url)
print(f"Workbench URL generated with all fields\n")

# Example 7: Dynamic Query Building
print("7. Dynamic Query Building with Metadata")
print("-" * 50)

# Get all updateable fields for Account
account_describe = sf.describe("Account")
updateable_fields = [f.get("name") for f in account_describe.fields.updateable_fields()[:10]]

# Build query dynamically
fields_str = ", ".join(updateable_fields)
dynamic_query = f"SELECT {fields_str} FROM Account WHERE LastModifiedDate = TODAY"

print(f"Dynamically built query:")
print(f"  {dynamic_query[:80]}...")
print(f"\nFields included: {len(updateable_fields)}")

# Generate Workbench URL for it
url = sf.get_workbench_url(dynamic_query)
print(f"Workbench URL: {url[:80]}...\n")

# Example 8: SOQL Explorer URL (Developer Console style)
print("8. SOQL Explorer URL")
print("-" * 50)

from forcepy import generate_soql_explorer_url

soql = "SELECT Id, Subject, Status FROM Case WHERE IsClosed = false"
explorer_url = generate_soql_explorer_url(soql, sf.instance_url)

print(f"Query: {soql}")
print(f"SOQL Explorer URL: {explorer_url[:80]}...\n")

# Example 9: Iterquery with Progress Tracking
print("9. Iterquery with Progress Tracking")
print("-" * 50)

import time

print("Processing records...")
start = time.time()
records_processed = 0

for account in sf.iterquery("SELECT Id, Name, Industry FROM Account"):
    records_processed += 1

    # Progress indicator every 100 records
    if records_processed % 100 == 0:
        print(f"  Processed {records_processed:,} records...")

    # Limit for demo
    if records_processed >= 500:
        break

elapsed = time.time() - start
print(f"\n✓ Processed {records_processed:,} records in {elapsed:.2f}s")
print(f"  Rate: {records_processed/elapsed:.0f} records/second\n")

# Example 10: Query Comparison
print("10. Query Performance Comparison")
print("-" * 50)

# Small batch with SELECT *
print("Approach 1: SELECT * (auto-expanded)")
start = time.time()
results1 = sf.query("SELECT * FROM Account LIMIT 100", expand_select_star=True)
time1 = time.time() - start
print(f"  Time: {time1*1000:.0f}ms")
print(f"  Records: {len(results1)}")
print(f"  Fields per record: {len(results1[0].to_dict()) if results1 else 0}")

print("\nApproach 2: Specific fields only")
start = time.time()
results2 = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 100")
time2 = time.time() - start
print(f"  Time: {time2*1000:.0f}ms")
print(f"  Records: {len(results2)}")
print(f"  Fields per record: {len(results2[0].to_dict()) if results2 else 0}")

print(f"\nConclusion: Specific fields are {time1/time2:.1f}x faster\n")

# Example 11: Helper Function Usage
print("11. Standalone Helper Functions")
print("-" * 50)

# Use helpers without client instance
from forcepy import WorkbenchConfig

config = WorkbenchConfig("https://custom-workbench.example.com")
soql = "SELECT Id FROM Account"
url = config.generate_url(soql, "https://na1.salesforce.com")
print(f"Custom Workbench URL: {url[:60]}...")

# Format SOQL standalone
formatted = format_soql("SELECT Id, Name FROM Account WHERE Name != null")
print(f"\nFormatted SOQL:\n{formatted}\n")

# Example 12: Query Workbench from Query History
print("12. Generate Workbench URLs from Query History")
print("-" * 50)

# Simulate query history
query_history = [
    "SELECT Id, Name FROM Account WHERE CreatedDate = TODAY",
    "SELECT Id, Subject FROM Case WHERE IsClosed = false",
    "SELECT Id, Email FROM Contact WHERE Email != null",
]

print("Recent queries with Workbench URLs:")
for i, query in enumerate(query_history, 1):
    url = sf.get_workbench_url(query)
    print(f"  {i}. {query[:50]}...")
    print(f"     URL: {url[:70]}...")
print()

print("=== Best Practices ===")
print("-" * 50)
print("✓ Use iterquery() for large datasets (> 2000 records)")
print("✓ Avoid SELECT * in production (use specific fields)")
print("✓ Use SELECT * expansion for debugging/exploration")
print("✓ Generate Workbench URLs for query sharing/debugging")
print("✓ Custom Workbench URLs for enterprise deployments")
print("✓ Format SOQL for documentation and code reviews")
print("\nDone!")

