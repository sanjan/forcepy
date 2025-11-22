# Migrating from simple-salesforce to forcepy

A practical guide to migrating your existing `simple-salesforce` code to `forcepy`.

## Why Migrate?

**forcepy** offers everything `simple-salesforce` has, plus:
- 🎯 **Q objects** for complex queries
- ⚡ **Client-side filtering** with Django-style syntax
- 🔐 **JWT authentication** and **token caching**
- 📦 **Bulk API 2.0** (newer, faster than v1.0)
- 🤝 **Composite API** for batch operations
- 💬 **Enhanced Chatter** with entity linking
- 🛠️ **Developer tools** (metadata caching, SOQL formatting, etc.)
- ✅ **Full type hints** for better IDE support

## Quick Migration Checklist

- [ ] Update imports
- [ ] Update authentication code
- [ ] Update query methods (optional improvements)
- [ ] Update CRUD operations (mostly compatible)
- [ ] Update Bulk API calls (if using)
- [ ] Test everything!

## Import Changes

### Before (simple-salesforce):
```python
from simple_salesforce import Salesforce
```

### After (forcepy):
```python
from forcepy import Salesforce
```

That's it! Most basic code will work without changes. 🎉

## Authentication

### Basic Username/Password

**simple-salesforce:**
```python
from simple_salesforce import Salesforce

sf = Salesforce(username='user@example.com',
                password='password',
                security_token='token')
```

**forcepy (identical):**
```python
from forcepy import Salesforce

sf = Salesforce(username='user@example.com',
                password='password',
                security_token='token')
```

✅ **No changes needed!**

### Sandbox Login

**simple-salesforce:**
```python
sf = Salesforce(username='user@example.com',
                password='password',
                domain='test')  # domain parameter
```

**forcepy:**
```python
sf = Salesforce(username='user@example.com',
                password='password',
                sandbox=True)  # sandbox parameter
```

⚠️ **Change**: `domain='test'` → `sandbox=True`

### Session ID

**simple-salesforce:**
```python
sf = Salesforce(session_id='00D...', instance='https://na1.salesforce.com')
```

**forcepy:**
```python
sf = Salesforce(session_id='00D...', instance_url='https://na1.salesforce.com')
```

⚠️ **Change**: `instance` → `instance_url`

### JWT Authentication (New!)

**simple-salesforce:**
```python
# Not supported ❌
```

**forcepy:**
```python
from forcepy import Salesforce

sf = Salesforce()
sf.login_with_jwt(
    client_id='your_connected_app_id',
    private_key='/path/to/server.key',
    username='user@example.com'
)
```

✅ **New feature!** Perfect for production automation.

## Queries

### Basic Queries

**simple-salesforce:**
```python
result = sf.query("SELECT Id, Name FROM Account LIMIT 10")
for record in result['records']:
    print(record['Name'])
```

**forcepy (compatible):**
```python
result = sf.query("SELECT Id, Name FROM Account LIMIT 10")
for record in result.records:  # .records instead of ['records']
    print(record.Name)  # dot notation!
```

✅ **Works both ways!** But dot notation is cleaner.

### Query All (Including Deleted)

**simple-salesforce:**
```python
sf.query_all("SELECT Id, Name FROM Account")
```

**forcepy:**
```python
# Not needed - sf.query() automatically fetches all records via pagination
# But if you want to include deleted records:
sf.query("SELECT Id, Name FROM Account", include_deleted=True)
```

### Query More (Pagination)

**simple-salesforce:**
```python
result = sf.query("SELECT Id FROM Account")
while not result['done']:
    result = sf.query_more(result['nextRecordsUrl'], identifier_is_url=True)
```

**forcepy (automatic):**
```python
# Automatic pagination - all records returned
result = sf.query("SELECT Id FROM Account")

# Or manual control:
result = sf.query("SELECT Id FROM Account LIMIT 2000")
if result.next_records_url:
    more = sf.query_more(result.next_records_url)
```

✅ **Improvement**: Pagination is automatic by default!

### Iterator Pattern

**simple-salesforce:**
```python
# Not supported - manual pagination only
```

**forcepy:**
```python
# Generator pattern - memory efficient for large datasets
for batch in sf.iterquery("SELECT Id, Name FROM Account", batch_size=2000):
    for record in batch.records:
        print(record.Name)

# Or with threading for performance:
for batch in sf.iterquery("SELECT Id FROM Account", threaded=True):
    process(batch.records)
```

✅ **New feature!** Great for processing millions of records.

## CRUD Operations

### Create Records

**simple-salesforce:**
```python
sf.Account.create({'Name': 'Test Account', 'Industry': 'Technology'})
```

**forcepy (identical):**
```python
sf.sobjects.Account.create({'Name': 'Test Account', 'Industry': 'Technology'})
```

⚠️ **Change**: `sf.Account` → `sf.sobjects.Account`

### Read Records

**simple-salesforce:**
```python
account = sf.Account.get('001xx000003DGb2AAG')
print(account['Name'])
```

**forcepy:**
```python
account = sf.sobjects.Account.get('001xx000003DGb2AAG')
print(account.Name)  # dot notation
```

✅ **Compatible**, but dot notation is nicer!

### Update Records

**simple-salesforce:**
```python
sf.Account.update('001xx000003DGb2AAG', {'Name': 'Updated Name'})
```

**forcepy (identical):**
```python
sf.sobjects.Account.update('001xx000003DGb2AAG', {'Name': 'Updated Name'})
```

### Delete Records

**simple-salesforce:**
```python
sf.Account.delete('001xx000003DGb2AAG')
```

**forcepy (identical):**
```python
sf.sobjects.Account.delete('001xx000003DGb2AAG')
```

### Upsert

**simple-salesforce:**
```python
sf.Account.upsert('External_Id__c/12345', {'Name': 'Test'})
```

**forcepy (identical):**
```python
sf.sobjects.Account.upsert('External_Id__c/12345', {'Name': 'Test'})
```

## Describe & Metadata

### Describe Object

**simple-salesforce:**
```python
metadata = sf.Account.describe()
print(metadata['fields'])
```

**forcepy:**
```python
# Same, but also cached!
metadata = sf.describe('Account')  # automatically cached
print(metadata.fields)

# Or access via sobjects:
metadata = sf.sobjects.Account.describe()
```

✅ **Improvement**: Results are cached automatically!

### Describe Global

**simple-salesforce:**
```python
sf.describe()
```

**forcepy:**
```python
sf.describe_global()
```

⚠️ **Change**: `describe()` → `describe_global()`

## Bulk API

### Bulk API v1.0 (simple-salesforce)

**simple-salesforce:**
```python
from simple_salesforce import Salesforce

sf = Salesforce(username='...', password='...')

# Bulk insert
sf.bulk.Account.insert([
    {'Name': 'Account 1'},
    {'Name': 'Account 2'}
])

# Bulk query
results = sf.bulk.Account.query("SELECT Id, Name FROM Account")
```

### Bulk API v2.0 (forcepy)

**forcepy:**
```python
from forcepy import Salesforce, BulkAPI

sf = Salesforce(username='...', password='...')
bulk = BulkAPI(sf)

# Create job and insert
job = bulk.create_job('Account', 'insert')
bulk.upload_data(job['id'], [
    {'Name': 'Account 1'},
    {'Name': 'Account 2'}
])
bulk.wait_for_job(job['id'])

# Or use simpler methods:
bulk.insert('Account', [{'Name': 'Account 1'}, {'Name': 'Account 2'}])
```

⚠️ **Different API**: Bulk v2.0 is faster but different syntax. See [BULK_API.md](BULK_API.md) for details.

## Chatter

### Post to Chatter

**simple-salesforce:**
```python
# Limited support
```

**forcepy:**
```python
from forcepy import Chatter

chatter = Chatter(sf)
chatter.post("Hello Chatter!")

# With mentions and entity links
chatter.post("Hey @[005xx0000012345]! Check out $[001xx0000012345]")

# With HTML formatting
chatter.post("<b>Important:</b> <i>Please review</i>")
```

✅ **New feature!** Full Chatter support with entity tagging. See [CHATTER_FEATURES.md](CHATTER_FEATURES.md).

## Advanced Query Features (New in forcepy)

### Q Objects for Complex Queries

**simple-salesforce:**
```python
# Manual string building ❌
query = f"SELECT Id FROM Account WHERE Name = '{name}' AND Industry = '{industry}'"
```

**forcepy:**
```python
from forcepy import Q

# Type-safe query building
conditions = Q(Name=name) & Q(Industry=industry)
query = f"SELECT Id FROM Account WHERE {conditions}"
```

### Client-Side Filtering

**simple-salesforce:**
```python
# Query everything, filter in Python ❌
accounts = sf.query("SELECT Id, Name, Industry FROM Account")
filtered = [a for a in accounts['records'] if a['Industry'] == 'Technology']
```

**forcepy:**
```python
# Filter on query results (Django-style)
accounts = sf.query("SELECT Id, Name, Industry FROM Account")
tech_accounts = accounts.filter(Industry='Technology')
high_revenue = accounts.filter(AnnualRevenue__gte=1000000)
```

### SOQL Helpers

**forcepy only:**
```python
from forcepy import IN, DATE, BOOL

# IN clause helper
industries = ['Technology', 'Healthcare']
query = f"SELECT Id FROM Account WHERE Industry IN {IN(industries)}"

# Date helpers
query = f"SELECT Id FROM Opportunity WHERE CloseDate = {DATE('LAST_N_DAYS', 30)}"

# Boolean helper
query = f"SELECT Id FROM Lead WHERE IsConverted = {BOOL(True)}"
```

## Composite API (New in forcepy)

**simple-salesforce:**
```python
# Not supported ❌
```

**forcepy:**
```python
# Batch multiple operations in a single API call
with sf.composite() as batch:
    batch.sobjects.Account.create({'Name': 'Account 1'})
    batch.sobjects.Account.create({'Name': 'Account 2'})
    batch.sobjects.Contact.create({'LastName': 'Smith'})
# All executed in one round-trip!
```

## Token Caching (New in forcepy)

**simple-salesforce:**
```python
# No caching - authenticates every time ❌
```

**forcepy:**
```python
# Memory cache (default)
sf = Salesforce(username='...', password='...', cache_backend='memory')

# Redis cache for production
sf = Salesforce(
    username='...', 
    password='...',
    cache_backend='redis',
    redis_url='redis://localhost:6379'
)
```

See [TOKEN_CACHING.md](TOKEN_CACHING.md) for details.

## Error Handling

### Authentication Errors

**simple-salesforce:**
```python
from simple_salesforce import SalesforceAuthenticationFailed

try:
    sf = Salesforce(...)
except SalesforceAuthenticationFailed:
    print("Login failed")
```

**forcepy:**
```python
from forcepy import AuthenticationError

try:
    sf = Salesforce(...)
except AuthenticationError:
    print("Login failed")
```

### API Errors

**simple-salesforce:**
```python
from simple_salesforce import SalesforceMalformedRequest

try:
    result = sf.query("INVALID SOQL")
except SalesforceMalformedRequest as e:
    print(f"Error: {e}")
```

**forcepy:**
```python
from forcepy import QueryError, APIError

try:
    result = sf.query("INVALID SOQL")
except QueryError as e:
    print(f"Query error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Migration Strategy

### Step 1: Side-by-Side Testing

Install both libraries and test in parallel:

```bash
pip install simple-salesforce forcepy
```

```python
# Test file
import simple_salesforce
import forcepy

# Compare results
sf_old = simple_salesforce.Salesforce(...)
sf_new = forcepy.Salesforce(...)

# Test queries
result_old = sf_old.query("SELECT Id FROM Account LIMIT 10")
result_new = sf_new.query("SELECT Id FROM Account LIMIT 10")

assert len(result_old['records']) == len(result_new.records)
```

### Step 2: Gradual Migration

Migrate one module at a time:

1. **Start with read-only operations** (queries)
2. **Move to CRUD operations**
3. **Migrate Bulk API** (if used)
4. **Add new features** (Q objects, filters, etc.)

### Step 3: Update Tests

Update your test fixtures:

```python
# Old
from simple_salesforce import Salesforce

# New
from forcepy import Salesforce
```

Run your test suite frequently!

### Step 4: Remove simple-salesforce

Once everything works:

```bash
pip uninstall simple-salesforce
```

Update `requirements.txt` or `pyproject.toml`:

```diff
- simple-salesforce==1.12.0
+ forcepy==0.1.2
```

## Common Pitfalls

### 1. Instance vs Instance URL

**Wrong:**
```python
sf = Salesforce(session_id='...', instance='na1')
```

**Right:**
```python
sf = Salesforce(session_id='...', instance_url='https://na1.salesforce.com')
```

### 2. Domain vs Sandbox

**Wrong:**
```python
sf = Salesforce(username='...', password='...', domain='test')
```

**Right:**
```python
sf = Salesforce(username='...', password='...', sandbox=True)
```

### 3. Direct Object Access

**Wrong:**
```python
sf.Account.create({'Name': 'Test'})
```

**Right:**
```python
sf.sobjects.Account.create({'Name': 'Test'})
```

### 4. Result Dictionary Access

**Old style still works:**
```python
for record in result['records']:
    print(record['Name'])
```

**But prefer:**
```python
for record in result.records:
    print(record.Name)
```

## Feature Upgrade Opportunities

Once migrated, consider using these forcepy-exclusive features:

### 1. Query Building

```python
from forcepy import Q, IN, DATE

# Complex conditions
conditions = (
    (Q(Industry='Technology') | Q(Industry='Healthcare')) &
    Q(AnnualRevenue__gte=1000000)
)
query = f"SELECT Id, Name FROM Account WHERE {conditions}"
```

### 2. Client-Side Filtering

```python
# Filter after query
results = sf.query("SELECT Id, Name, Industry, AnnualRevenue FROM Account")
tech = results.filter(Industry='Technology')
high_value = results.filter(AnnualRevenue__gte=1000000)
sorted_results = results.order_by('-AnnualRevenue')
```

### 3. Developer Tools

```python
# Pretty-print SOQL
print(sf.prettyprint("SELECT Id, Name, (SELECT FirstName FROM Contacts) FROM Account"))

# Generate Workbench URL
url = sf.get_workbench_url("SELECT Id FROM Account")

# Get object type from ID
obj_type = sf.get_object_type_from_id('001xx000003DGb2AAG')
print(obj_type)  # 'Account'
```

### 4. Bulk Operations

```python
from forcepy import BulkAPI

bulk = BulkAPI(sf)

# Simple insert
bulk.insert('Account', [
    {'Name': 'Account 1'},
    {'Name': 'Account 2'}
])

# Monitor progress
job = bulk.create_job('Account', 'insert')
bulk.upload_data(job['id'], data)
bulk.wait_for_job(job['id'])  # Blocks until complete
```

## Performance Improvements

### Token Caching

**Before (simple-salesforce):**
```python
# Authenticates every time script runs ❌
sf = Salesforce(username='...', password='...')
```

**After (forcepy):**
```python
# Cached for 2 hours ✅
sf = Salesforce(
    username='...', 
    password='...',
    cache_backend='memory'
)
```

### Threaded Query Iteration

**Before:**
```python
# Synchronous pagination
result = sf.query("SELECT Id FROM Account")
process(result['records'])
while not result['done']:
    result = sf.query_more(result['nextRecordsUrl'])
    process(result['records'])
```

**After:**
```python
# Prefetches next batch while processing current
for batch in sf.iterquery("SELECT Id FROM Account", threaded=True):
    process(batch.records)
```

## Support & Resources

- **Migration Issues**: https://github.com/sanjan/forcepy/issues
- **Documentation**: https://github.com/sanjan/forcepy/tree/main/docs
- **Examples**: https://github.com/sanjan/forcepy/tree/main/examples
- **Comparison Guide**: [PUBLIC_LIBRARY_COMPARISON.md](PUBLIC_LIBRARY_COMPARISON.md)

## Quick Reference

| Operation | simple-salesforce | forcepy |
|-----------|------------------|---------|
| Import | `from simple_salesforce import Salesforce` | `from forcepy import Salesforce` |
| Sandbox | `domain='test'` | `sandbox=True` |
| Session | `instance='url'` | `instance_url='url'` |
| CRUD | `sf.Account.create()` | `sf.sobjects.Account.create()` |
| Results | `result['records'][0]['Name']` | `result.records[0].Name` |
| Describe | `sf.Account.describe()` | `sf.describe('Account')` |
| Global Describe | `sf.describe()` | `sf.describe_global()` |

---

**Questions?** Open an issue: https://github.com/sanjan/forcepy/issues

**Ready to migrate?** Start with a small module and gradually expand! 🚀

