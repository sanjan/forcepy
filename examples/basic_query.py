"""Basic forcepy query example."""

from forcepy import Salesforce

# Initialize client (auto-authenticates)
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

# Simple query
print("=== Simple Query ===")
accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 5")
for account in accounts:
    print(f"{account.Name} ({account.Industry})")

# Query with filtering
print("\n=== Filter Results ===")
cases = sf.query("SELECT Id, CaseNumber, Status, Priority FROM Case LIMIT 100")
high_priority = cases.filter(Priority="High")
print(f"Found {len(high_priority)} high priority cases")

# Group by status
print("\n=== Group By ===")
by_status = cases.group_by("Status").count()
for status, count in by_status.items():
    print(f"{status}: {count}")

# Order by field
print("\n=== Order By ===")
recent_cases = cases.order_by("CreatedDate", asc=False)[:5]
for case in recent_cases:
    print(f"Case {case.CaseNumber} - {case.Status}")

# Dot notation field access
print("\n=== Nested Field Access ===")
contacts = sf.query("SELECT Id, Name, Account.Name FROM Contact LIMIT 5")
for contact in contacts:
    account_name = contact.get("Account", {}).get("Name", "No Account")
    print(f"{contact.Name} works at {account_name}")

# Values list
print("\n=== Extract Values ===")
case_numbers = cases.values_list("CaseNumber", flat=True)
print(f"Case numbers: {case_numbers[:10]}")

# Earliest/Latest
print("\n=== Earliest/Latest ===")
oldest = cases.earliest("CreatedDate")
newest = cases.latest("CreatedDate")
print(f"Oldest case: {oldest.CaseNumber}")
print(f"Newest case: {newest.CaseNumber}")
