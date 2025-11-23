# Production-Ready Patterns for forcepy

This guide covers battle-tested patterns for using forcepy in production environments, based on real-world usage across enterprise systems.

## Table of Contents

- [Child Relationship Queries](#child-relationship-queries)
- [Parent Relationship Traversal](#parent-relationship-traversal)
- [Record Updates with .patch()](#record-updates-with-patch)
- [SOQL Helper Functions](#soql-helper-functions)
- [Multi-Instance Management](#multi-instance-management)
- [Query Timeouts](#query-timeouts)
- [Error Handling and Retries](#error-handling-and-retries)
- [Pagination and Large Datasets](#pagination-and-large-datasets)
- [Performance Optimization](#performance-optimization)

## Child Relationship Queries

Child relationship queries (subqueries) let you fetch related records in a single API call, drastically reducing the number of requests.

### Basic Subquery

```python
# Fetch accounts with their contacts
accounts = sf.query("""
    SELECT Id, Name, Industry,
           (SELECT Id, FirstName, LastName, Email FROM Contacts)
    FROM Account
    WHERE Industry = 'Technology'
    LIMIT 10
""")

# Access child records
for account in accounts:
    print(f"Account: {account.Name}")
    if account.Contacts:
        for contact in account.Contacts.records:
            print(f"  - {contact.FirstName} {contact.LastName}: {contact.Email}")
```

### Multiple Child Relationships

```python
# Fetch multiple child relationships in one query
accounts = sf.query("""
    SELECT Id, Name, AnnualRevenue,
           (SELECT Id, FirstName, LastName, Email FROM Contacts WHERE Active__c = true),
           (SELECT Id, Name, StageName, Amount FROM Opportunities WHERE StageName = 'Closed Won'),
           (SELECT Id, Subject, Status FROM Cases WHERE IsClosed = false)
    FROM Account
    WHERE Industry = 'Technology'
""")

for account in accounts:
    print(f"\n{account.Name} (${account.AnnualRevenue})")
    
    # Safe access patterns
    if account.Contacts:
        print(f"  Active Contacts: {len(account.Contacts.records)}")
    
    if account.Opportunities:
        total_won = sum(opp.Amount for opp in account.Opportunities.records if opp.Amount)
        print(f"  Total Won: ${total_won:,.2f}")
    
    # Default to empty list if no child records
    open_cases = account.Cases and account.Cases.records or []
    print(f"  Open Cases: {len(open_cases)}")
```

### Filtered Child Queries

```python
# Apply WHERE clause to child relationships
cases = sf.query("""
    SELECT Id, CaseNumber, Subject, Status,
           (SELECT Id, Body, CreatedDate, CreatedBy.Name 
            FROM CaseComments 
            WHERE IsPublished = true 
            ORDER BY CreatedDate DESC 
            LIMIT 5)
    FROM Case
    WHERE Status = 'Open'
    AND Priority = 'High'
""")

for case in cases:
    print(f"Case #{case.CaseNumber}: {case.Subject}")
    if case.CaseComments:
        print(f"  Latest comments:")
        for comment in case.CaseComments.records:
            print(f"    [{comment.CreatedDate}] {comment.CreatedBy.Name}: {comment.Body[:50]}...")
```

### Safe Access Patterns

```python
# Pattern 1: Check before iterating (recommended)
if account.Contacts:
    for contact in account.Contacts.records:
        process_contact(contact)

# Pattern 2: Default to empty list (compact)
for contact in account.Contacts and account.Contacts.records or []:
    process_contact(contact)

# Pattern 3: Use .get() method
contacts = account.get('Contacts')
if contacts:
    for contact in contacts.records:
        process_contact(contact)

# Pattern 4: Count child records
contact_count = len(account.Contacts.records) if account.Contacts else 0
```

## Parent Relationship Traversal

Access parent objects and their fields by traversing relationships.

### Basic Parent Traversal

```python
# Query contacts with account information
contacts = sf.query("""
    SELECT Id, FirstName, LastName, Email,
           Account.Name,
           Account.Industry,
           Account.AnnualRevenue
    FROM Contact
    WHERE Account.Industry = 'Technology'
""")

for contact in contacts:
    print(f"{contact.FirstName} {contact.LastName} works at {contact.Account.Name}")
    print(f"  Industry: {contact.Account.Industry}")
```

### Multi-Level Parent Traversal

```python
# Traverse multiple levels up
opportunities = sf.query("""
    SELECT Id, Name, StageName, Amount,
           Account.Name,
           Account.Owner.Name,
           Account.Owner.Email,
           Account.Owner.Manager.Name
    FROM Opportunity
    WHERE StageName = 'Negotiation/Review'
""")

for opp in opportunities:
    print(f"Opportunity: {opp.Name} (${opp.Amount})")
    print(f"  Account: {opp.Account.Name}")
    print(f"  Owner: {opp.Account.Owner.Name} ({opp.Account.Owner.Email})")
    if hasattr(opp.Account.Owner, 'Manager'):
        print(f"  Manager: {opp.Account.Owner.Manager.Name}")
```

### Combining Parent and Child Relationships

```python
# Query with both parent and child relationships
opportunities = sf.query("""
    SELECT Id, Name, StageName, Amount,
           Account.Name,
           Account.Owner.Name,
           (SELECT Id, FirstName, LastName, Role FROM OpportunityContactRoles)
    FROM Opportunity
    WHERE Account.Industry = 'Technology'
    AND StageName = 'Prospecting'
""")

for opp in opportunities:
    print(f"\n{opp.Name} - {opp.Account.Name}")
    print(f"  Owner: {opp.Account.Owner.Name}")
    
    if opp.OpportunityContactRoles:
        print(f"  Contact Roles:")
        for role in opp.OpportunityContactRoles.records:
            print(f"    - {role.FirstName} {role.LastName} ({role.Role})")
```

## Record Updates with .patch()

The `.patch()` method provides a clean way to update records.

### Direct Endpoint Updates

```python
# Update single record
sf.Account[account_id].patch(
    Phone='555-1234',
    Industry='Technology',
    Website='https://example.com'
)

# With custom timeout
sf.Case[case_id].patch(
    Status='Closed',
    Resolution='Resolved by customer',
    timeout=60
)
```

### Update from Object Instance

```python
# Fetch and update
account = sf.Account.get(Name='Acme Corp')
account.patch(sf, 
    AnnualRevenue=5000000,
    NumberOfEmployees=250
)
```

### Bulk Updates

```python
# Update multiple records from query
high_priority_cases = sf.query("""
    SELECT Id FROM Case 
    WHERE Priority = 'High' 
    AND Status = 'New'
    AND CreatedDate = TODAY
""")

new_owner_id = '005xx0000012345'
for case in high_priority_cases:
    sf.Case[case.Id].patch(
        Status='In Progress',
        OwnerId=new_owner_id
    )

print(f"Updated {len(high_priority_cases)} cases")
```

### Conditional Updates

```python
# Update based on conditions
accounts = sf.query("""
    SELECT Id, Name, AnnualRevenue, Industry
    FROM Account
    WHERE Industry = 'Technology'
""")

for account in accounts:
    # Categorize by revenue
    if account.AnnualRevenue and account.AnnualRevenue > 10000000:
        sf.Account[account.Id].patch(AccountTier__c='Enterprise')
    elif account.AnnualRevenue and account.AnnualRevenue > 1000000:
        sf.Account[account.Id].patch(AccountTier__c='Mid-Market')
    else:
        sf.Account[account.Id].patch(AccountTier__c='SMB')
```

## SOQL Helper Functions

Forcepy provides helper functions for formatting Python values in SOQL queries.

### DATE Helper

```python
from forcepy import DATE
from datetime import datetime, timedelta

# Recent records
last_week = DATE(datetime.now() - timedelta(days=7))
recent_cases = sf.query(f"""
    SELECT Id, CaseNumber, Subject, CreatedDate
    FROM Case
    WHERE CreatedDate >= {last_week}
""")

# Date ranges
thirty_days_ago = DATE(datetime.now() - timedelta(days=30))
seven_days_ago = DATE(datetime.now() - timedelta(days=7))

cases_in_range = sf.query(f"""
    SELECT Id, CaseNumber
    FROM Case
    WHERE CreatedDate >= {thirty_days_ago}
    AND CreatedDate < {seven_days_ago}
""")

# Specific dates
start_of_year = DATE(datetime(2025, 1, 1))
opportunities = sf.query(f"""
    SELECT Id, Name, CloseDate
    FROM Opportunity
    WHERE CloseDate >= {start_of_year}
""")
```

### IN Helper

```python
from forcepy import IN

# Filter by list of values
account_ids = ['001xx0001', '001xx0002', '001xx0003']
accounts = sf.query(f"""
    SELECT Id, Name
    FROM Account
    WHERE Id IN {IN(account_ids)}
""")

# Multiple field filters
industries = ['Technology', 'Healthcare', 'Finance']
high_value_accounts = sf.query(f"""
    SELECT Id, Name, Industry, AnnualRevenue
    FROM Account
    WHERE Industry IN {IN(industries)}
    AND AnnualRevenue > 1000000
""")

# With owner IDs
owner_ids = ['005xx0001', '005xx0002']
cases = sf.query(f"""
    SELECT Id, CaseNumber, OwnerId
    FROM Case
    WHERE OwnerId IN {IN(owner_ids)}
    AND IsClosed = false
""")
```

### BOOL Helper

```python
from forcepy import BOOL

# Boolean fields
is_active = True
active_accounts = sf.query(f"""
    SELECT Id, Name
    FROM Account
    WHERE IsActive__c = {BOOL(is_active)}
""")

# In conditions
include_closed = False
if include_closed:
    cases = sf.query(f"""
        SELECT Id, CaseNumber
        FROM Case
    """)
else:
    cases = sf.query(f"""
        SELECT Id, CaseNumber
        FROM Case
        WHERE IsClosed = {BOOL(False)}
    """)
```

### Combining Helpers

```python
from forcepy import DATE, IN, BOOL
from datetime import datetime, timedelta

# Complex query with all helpers
regions = ['US-WEST', 'US-EAST']
last_month = DATE(datetime.now() - timedelta(days=30))
is_active = True

accounts = sf.query(f"""
    SELECT Id, Name, Region__c, CreatedDate
    FROM Account
    WHERE Region__c IN {IN(regions)}
    AND CreatedDate >= {last_month}
    AND IsActive__c = {BOOL(is_active)}
""")
```

## Multi-Instance Management

Manage connections to multiple Salesforce orgs (production, sandbox, different business units).

### Basic Multi-Instance Setup

```python
from forcepy import Salesforce

# Production org
prod = Salesforce(
    username='prod@example.com',
    password='prod_password',
    security_token='prod_token'
)

# Sandbox org
sandbox = Salesforce(
    username='sandbox@example.com.sandbox',
    password='sandbox_password',
    sandbox=True
)

# Query each independently
prod_accounts = prod.query("SELECT Id, Name FROM Account LIMIT 10")
sandbox_accounts = sandbox.query("SELECT Id, Name FROM Account LIMIT 10")
```

### Multi-Org Data Sync

```python
# Fetch from production
prod_accounts = prod.query("""
    SELECT Id, Name, Industry, AnnualRevenue
    FROM Account
    WHERE Industry = 'Technology'
    LIMIT 100
""")

# Create in sandbox for testing
for account in prod_accounts:
    sandbox.Account.post(
        Name=f"TEST - {account.Name}",
        Industry=account.Industry,
        AnnualRevenue=account.AnnualRevenue,
        IsTestData__c=True
    )
```

### Environment-Aware Client

```python
import os

def get_salesforce_client(environment='production'):
    """Get Salesforce client for specified environment."""
    config = {
        'production': {
            'username': os.getenv('PROD_SF_USERNAME'),
            'password': os.getenv('PROD_SF_PASSWORD'),
            'security_token': os.getenv('PROD_SF_TOKEN'),
            'sandbox': False
        },
        'sandbox': {
            'username': os.getenv('SANDBOX_SF_USERNAME'),
            'password': os.getenv('SANDBOX_SF_PASSWORD'),
            'security_token': os.getenv('SANDBOX_SF_TOKEN'),
            'sandbox': True
        },
        'dev': {
            'username': os.getenv('DEV_SF_USERNAME'),
            'password': os.getenv('DEV_SF_PASSWORD'),
            'security_token': os.getenv('DEV_SF_TOKEN'),
            'sandbox': True
        }
    }
    
    return Salesforce(**config[environment])

# Usage
sf = get_salesforce_client('production')
sandbox_sf = get_salesforce_client('sandbox')
```

## Query Timeouts

Configure timeouts for long-running queries or production stability.

### Basic Timeout Usage

```python
# Default timeout (uses requests default)
accounts = sf.query("SELECT Id, Name FROM Account")

# Custom timeout for long query
large_dataset = sf.query(
    "SELECT Id, Name, (SELECT Id FROM Contacts) FROM Account",
    timeout=120  # 120 seconds
)

# Short timeout for health checks
try:
    health_check = sf.query("SELECT Id FROM Account LIMIT 1", timeout=5)
    print("Salesforce connection OK")
except Exception as e:
    print(f"Salesforce connection failed: {e}")
```

### Timeout Best Practices

```python
# Production queries - reasonable timeout
def fetch_daily_cases(sf, timeout=60):
    """Fetch today's cases with production-safe timeout."""
    from forcepy import DATE
    from datetime import datetime
    
    today = DATE(datetime.now().replace(hour=0, minute=0, second=0))
    return sf.query(
        f"SELECT Id, CaseNumber, Status FROM Case WHERE CreatedDate >= {today}",
        timeout=timeout
    )

# Report queries - longer timeout
def generate_monthly_report(sf, timeout=300):
    """Generate monthly report with longer timeout."""
    from forcepy import DATE
    from datetime import datetime, timedelta
    
    month_start = DATE(datetime.now().replace(day=1))
    return sf.query(
        f"""
        SELECT Id, Name, Amount, CloseDate,
               Account.Name, Account.Industry,
               Owner.Name
        FROM Opportunity
        WHERE CloseDate >= {month_start}
        """,
        timeout=timeout
    )
```

## Error Handling and Retries

Forcepy includes automatic retry logic, but you can add your own for specific scenarios.

### Basic Error Handling

```python
from forcepy.exceptions import APIError, QueryError, AuthenticationError

try:
    accounts = sf.query("SELECT Id, Name FROM Account")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Re-authenticate or alert
except QueryError as e:
    print(f"Query failed: {e}")
    # Log and handle malformed query
except APIError as e:
    print(f"API error: {e}")
    # General API errors
```

### Custom Retry Logic

```python
import time
from forcepy.exceptions import APIError

def query_with_retry(sf, soql, max_retries=3, wait_seconds=2, timeout=60):
    """Execute query with custom retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            return sf.query(soql, timeout=timeout)
        except APIError as e:
            if attempt == max_retries:
                raise
            print(f"Attempt {attempt} failed: {e}. Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            wait_seconds *= 2  # Exponential backoff
    
    raise Exception(f"Query failed after {max_retries} retries")

# Usage
accounts = query_with_retry(
    sf,
    "SELECT Id, Name FROM Account LIMIT 1000",
    max_retries=3,
    timeout=60
)
```

### Graceful Degradation

```python
def get_account_with_contacts(sf, account_id):
    """Fetch account with contacts, gracefully degrade if child query fails."""
    try:
        # Try with child relationship
        result = sf.query(f"""
            SELECT Id, Name, Industry,
                   (SELECT Id, FirstName, LastName FROM Contacts)
            FROM Account
            WHERE Id = '{account_id}'
        """)
        return result.records[0] if result else None
    except QueryError:
        # Fall back to simple query
        print("Child query failed, fetching account only")
        result = sf.query(f"""
            SELECT Id, Name, Industry
            FROM Account
            WHERE Id = '{account_id}'
        """)
        return result.records[0] if result else None
```

## Pagination and Large Datasets

Handle large result sets efficiently with pagination.

### Automatic Pagination Check

```python
# Query with pagination awareness
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 2000")

print(f"Retrieved {len(accounts)} accounts")
print(f"Total available: {accounts.total_size}")

if not accounts.done:
    print(f"More records available at: {accounts.next_records_url}")
    # Fetch next batch
    next_batch = sf.http("GET", accounts.next_records_url)
```

### Manual Pagination

```python
def fetch_all_records(sf, soql):
    """Fetch all records using manual pagination."""
    all_records = []
    result = sf.query(soql)
    
    all_records.extend(result.records)
    
    while not result.done:
        # Fetch next page
        next_result = sf.http("GET", result.next_records_url)
        
        # Convert to SobjectSet
        from forcepy.sobject import Sobject, SobjectSet
        records = SobjectSet()
        for record_data in next_result.get("records", []):
            records.append(Sobject(record_data))
        
        all_records.extend(records)
        
        # Update pagination metadata
        result.next_records_url = next_result.get("nextRecordsUrl")
        result.done = next_result.get("done", True)
    
    return all_records

# Usage
all_accounts = fetch_all_records(sf, "SELECT Id, Name, Industry FROM Account")
print(f"Fetched {len(all_accounts)} total accounts")
```

### Bulk API for Large Datasets

For truly large datasets (>50K records), use Bulk API 2.0:

```python
# Query 1M+ records efficiently
job = sf.bulk.query("SELECT Id, Name, Industry FROM Account")

# Process results in batches
for batch in job.results():
    for record in batch:
        process_record(record)
```

## Performance Optimization

### Query Optimization

```python
# BAD: Query in loop (N+1 problem)
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 100")
for account in accounts:
    contacts = sf.query(f"SELECT Id FROM Contact WHERE AccountId = '{account.Id}'")  # N queries!

# GOOD: Use child relationship query
accounts = sf.query("""
    SELECT Id, Name,
           (SELECT Id, FirstName, LastName FROM Contacts)
    FROM Account
    LIMIT 100
""")
for account in accounts:
    if account.Contacts:
        print(f"{account.Name} has {len(account.Contacts.records)} contacts")
```

### Select Only Needed Fields

```python
# BAD: Select all fields (slow, wasteful)
accounts = sf.query("SELECT FIELDS(ALL) FROM Account LIMIT 100")

# GOOD: Select only what you need
accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 100")
```

### Use Filters to Reduce Results

```python
# BAD: Filter client-side
all_accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 10000")
tech_accounts = [a for a in all_accounts if a.Industry == 'Technology']

# GOOD: Filter server-side
tech_accounts = sf.query("""
    SELECT Id, Name, Industry
    FROM Account
    WHERE Industry = 'Technology'
""")
```

### Batch Operations

```python
# BAD: Individual creates
for i in range(100):
    sf.Contact.post(FirstName=f"Test{i}", LastName="User", Email=f"test{i}@example.com")

# GOOD: Composite API (25 operations per call)
with sf as batch:
    for i in range(100):
        batch.sobjects.Contact.post(
            FirstName=f"Test{i}",
            LastName="User",
            Email=f"test{i}@example.com"
        )
```

### Caching Metadata

```python
# Cache describes for repeated access
account_describe = sf.describe.Account

# Use cached metadata
for field_name, field_info in account_describe.fields.items():
    if field_info.get('type') == 'picklist':
        print(f"{field_name}: {field_info['picklistValues']}")
```

## Next Steps

- [Bulk API Guide](./BULK_API.md) - For very large datasets
- [Token Caching Guide](./TOKEN_CACHING.md) - Optimize authentication
- [Chatter Features](./CHATTER_FEATURES.md) - Social collaboration
- [Authentication Patterns](./AUTHENTICATION.md) - All auth methods

Need help? [Open an issue](https://github.com/sanjan/forcepy/issues) or [start a discussion](https://github.com/sanjan/forcepy/discussions).

