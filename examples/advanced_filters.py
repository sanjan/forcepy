"""Advanced filtering with Q objects and client-side filters."""

from forcepy import Salesforce, Q

# Auto-authenticates on construction
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

# ===  Q Objects for SOQL WHERE Clauses ===
print("=== Q Objects ===")

# Simple Q object
q1 = Q(Status="New")
print(f"Q1: {q1.compile()}")  # Status = 'New'

# AND operator
q2 = Q(Status="New") & Q(Priority="High")
print(f"Q2: {q2.compile()}")  # (Status = 'New') AND (Priority = 'High')

# OR operator
q3 = Q(Status="New") | Q(Status="In Progress")
print(f"Q3: {q3.compile()}")  # (Status = 'New') OR (Status = 'In Progress')

# Complex combination
q4 = (Q(Status="New") | Q(Status="In Progress")) & Q(Priority="High")
print(f"Q4: {q4.compile()}")

# NOT operator
q5 = ~Q(Status="Closed")
print(f"Q5: {q5.compile()}")  # (NOT (Status = 'Closed'))

# Use Q object in query
where_clause = q4.compile()
query = f"SELECT Id, CaseNumber, Status, Priority FROM Case WHERE {where_clause} LIMIT 100"
cases = sf.query(query)
print(f"Found {len(cases)} cases matching criteria")

# === Client-Side Filtering ===
print("\n=== Client-Side Filtering ===")

# Get all cases
all_cases = sf.query("SELECT Id, CaseNumber, Status, Priority, CreatedDate FROM Case LIMIT 1000")

# Exact match
new_cases = all_cases.filter(Status="New")
print(f"New cases: {len(new_cases)}")

# Multiple conditions (AND)
high_priority_new = all_cases.filter(Status="New", Priority="High")
print(f"High priority new cases: {len(high_priority_new)}")

# IN lookup
open_statuses = all_cases.filter(Status__in=["New", "In Progress", "Escalated"])
print(f"Open cases: {len(open_statuses)}")

# Contains
critical_cases = all_cases.filter(Subject__contains="Critical")
print(f"Cases with 'Critical' in subject: {len(critical_cases)}")

# Greater than / Less than
import datetime

week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
recent_cases = all_cases.filter(CreatedDate__gt=week_ago)
print(f"Cases created in last 7 days: {len(recent_cases)}")

# Not equal
non_closed = all_cases.filter(Status__ne="Closed")
print(f"Non-closed cases: {len(non_closed)}")

# Null check
no_owner = all_cases.filter(OwnerId__isnull=True)
print(f"Cases without owner: {len(no_owner)}")

# Starts with
priority_cases = all_cases.filter(Priority__startswith="High")
print(f"High* priority cases: {len(priority_cases)}")

# === Exclude ===
print("\n=== Exclude ===")
not_new = all_cases.exclude(Status="New")
print(f"Cases that are not New: {len(not_new)}")

# === Chaining Filters ===
print("\n=== Chaining ===")
filtered = all_cases.filter(Priority="High").filter(Status="New").order_by("CreatedDate", asc=False)
print(f"High priority new cases (recent first): {len(filtered)}")

# === Custom Filter Functions ===
print("\n=== Custom Filters ===")


def is_weekend_case(case):
    """Check if case was created on weekend."""
    return case.CreatedDate.weekday() >= 5


weekend_cases = all_cases.filter(is_weekend_case)
print(f"Cases created on weekend: {len(weekend_cases)}")

# === Group and Aggregate ===
print("\n=== Grouping ===")

by_status = all_cases.group_by("Status")
print("Cases by status:")
for status, cases in by_status.items():
    print(f"  {status}: {len(cases)}")

# Count by status
counts = by_status.count()
print(f"\nStatus counts: {counts}")

# Group by multiple fields
by_status_priority = all_cases.group_by("Status", "Priority")
print(f"\nGrouped by Status and Priority: {len(by_status_priority)} groups")

# === Order By ===
print("\n=== Ordering ===")

oldest_first = all_cases.order_by("CreatedDate", asc=True)
newest_first = all_cases.order_by("CreatedDate", asc=False)

print(f"Oldest case: {oldest_first.first().CaseNumber}")
print(f"Newest case: {newest_first.first().CaseNumber}")

# Order by multiple fields
sorted_cases = all_cases.order_by("Priority", "CreatedDate")
print(f"Sorted by Priority, then CreatedDate: {len(sorted_cases)} cases")
