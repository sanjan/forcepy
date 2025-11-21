# forcepy vs Public Salesforce Libraries

Comprehensive comparison between **forcepy** and the two most popular public Python Salesforce libraries: **simple-salesforce** and **salesforce-python** (beatbox).

## Library Overview

### forcepy (New!)
Modern Python client with advanced query building, filtering, and developer-friendly features. Built with beginners and power users in mind.

### simple-salesforce
The most popular Python Salesforce library. Lightweight, straightforward REST API client with basic functionality.
- **PyPI**: `simple-salesforce`
- **GitHub**: ~1.7k stars
- **Status**: Actively maintained

### salesforce-python (beatbox)
XML-based SOAP API client. Older library using Salesforce's SOAP/XML interface.
- **PyPI**: `beatbox`
- **GitHub**: ~150 stars  
- **Status**: Less actively maintained

---

## Feature Comparison Matrix

| Feature | forcepy | simple-salesforce | beatbox |
|---------|---------|-------------------|---------|
| **Authentication** |
| Username/Password | ✅ | ✅ | ✅ |
| OAuth2 | ✅ | ✅ | ❌ |
| JWT Bearer Flow | ✅ | ❌ | ❌ |
| Token Caching | ✅ (Memory/Redis) | ❌ | ❌ |
| **Query Building** |
| SOQL Queries | ✅ | ✅ | ✅ |
| Q Objects (Complex WHERE) | ✅ | ❌ | ❌ |
| Query Helpers (IN, DATE, BOOL) | ✅ | ❌ | ❌ |
| compile_where_clause | ✅ | ❌ | ❌ |
| SELECT * Expansion | ✅ | ❌ | ❌ |
| **Result Handling** |
| Dot Notation Access | ✅ | ✅ | ❌ |
| Client-Side Filtering | ✅ | ❌ | ❌ |
| Group By / Order By | ✅ | ❌ | ❌ |
| Result Transforms | ✅ | ❌ | ❌ |
| **Pagination** |
| Basic Pagination | ✅ | ✅ | ✅ |
| Manual Control (query_more) | ✅ | ❌ | ❌ |
| Iterquery (Generator) | ✅ | ❌ | ❌ |
| Threaded Prefetching | ✅ | ❌ | ❌ |
| **Batch Operations** |
| Bulk API v1.0 | ❌ | ✅ | ✅ |
| Bulk API v2.0 | ✅ | ❌ | ❌ |
| Composite API | ✅ | ❌ | ❌ |
| Composite Context Manager | ✅ | ❌ | ❌ |
| **Metadata & Discovery** |
| Describe Objects | ✅ | ✅ | ✅ |
| Describe Caching | ✅ | ❌ | ❌ |
| Picklist Values | ✅ | ✅ | ✅ |
| Dependent Picklists | ✅ | ❌ | ❌ |
| Object Listing/Filtering | ✅ | ❌ | ❌ |
| ID to Object Type | ✅ | ❌ | ❌ |
| **Chatter Integration** |
| Post Messages | ✅ | Limited | ❌ |
| Entity Tagging (@mentions) | ✅ | ❌ | ❌ |
| HTML Formatting | ✅ | ❌ | ❌ |
| **Advanced Features** |
| Auto-Retry Logic | ✅ | ❌ | ❌ |
| Session Info Tracking | ✅ | ❌ | ❌ |
| Workbench URL Generation | ✅ | ❌ | ❌ |
| ID Comparison Utilities | ✅ | ❌ | ❌ |
| SOQL Formatting | ✅ | ❌ | ❌ |
| Sobject Refresh | ✅ | ❌ | ❌ |
| **Developer Experience** |
| Type Hints | ✅ | Limited | ❌ |
| Beginner-Friendly Helpers | ✅ | ❌ | ❌ |
| Interactive Exploration | ✅ | ❌ | ❌ |
| Convenience Methods (.first(), .last()) | ✅ | ❌ | ❌ |
| Case-Insensitive Filters | ✅ | ❌ | ❌ |
| CSV Export/Import | ✅ | ❌ | ❌ |
| Modern Python (3.9+) | ✅ | ✅ | ❌ |
| API Style | REST | REST | SOAP/XML |

**Legend:**
- ✅ Fully supported
- Limited: Basic support only
- 🔜 Planned/Coming soon
- ❌ Not supported

---

## Detailed Comparison

### 1. Authentication

#### forcepy ⭐
```python
# Multiple auth methods with caching
sf = Salesforce(username='user', password='pass')  # SOAP (auto-caches)
sf.login_with_jwt(client_id, private_key, username)  # JWT
# Redis caching for production
sf = Salesforce(username='user', password='pass', cache_backend='redis', redis_url='...')
```

**Advantages:**
- JWT authentication for serverless/CI environments
- Automatic token caching (memory or Redis)
- Session info tracking (expiry, last request)

#### simple-salesforce
```python
from simple_salesforce import Salesforce
sf = Salesforce(username='user', password='pass', security_token='token')
# OAuth2 supported but no JWT
```

**Limitations:**
- No JWT support
- No token caching
- No session tracking

#### beatbox
```python
from beatbox import PythonClient
svc = PythonClient()
svc.login('username', 'password+token')
```

**Limitations:**
- Only basic username/password
- SOAP-based (XML heavy)
- No modern auth methods

---

### 2. Query Building & Execution

#### forcepy ⭐
```python
from forcepy import Salesforce, Q

sf = Salesforce(username='user', password='pass')

# Complex WHERE clauses with Q objects
q = (Q(Status='New') | Q(Status='In Progress')) & Q(Priority='High')
results = sf.query(f"SELECT Id FROM Case WHERE {q.compile()}")

# Query helpers
where = sf.compile_where_clause(
    Status='New',
    Priority__in=['High', 'Critical'],
    CreatedDate__gte='2024-01-01'
)

# SELECT * expansion
results = sf.query("SELECT * FROM Account LIMIT 10", expand_select_star=True)

# Iterquery with pagination
for page in sf.iterquery("SELECT Id FROM Account", threaded=True):
    process(page)  # Next page prefetches in background
```

**Advantages:**
- Q objects for complex boolean logic
- Django-style __ operators (\_\_in, \_\_gte, \_\_contains, etc.)
- SELECT * auto-expansion
- Threaded pagination for performance
- Manual pagination control

#### simple-salesforce
```python
from simple_salesforce import Salesforce
sf = Salesforce(username='user', password='pass', security_token='token')

# Basic SOQL only
results = sf.query("SELECT Id, Name FROM Account WHERE Status = 'Active'")
```

**Limitations:**
- No query building helpers
- Manual WHERE clause construction
- No SELECT * expansion
- Basic pagination only

#### beatbox
```python
from beatbox import PythonClient
svc = PythonClient()
svc.login('username', 'password+token')

# Basic SOQL
results = svc.query("SELECT Id, Name FROM Account")
```

**Limitations:**
- Returns XML structures
- No query helpers
- Limited result handling

---

### 3. Result Manipulation

#### forcepy ⭐
```python
# Query once, filter multiple times
cases = sf.query("SELECT Id, Status, Priority FROM Case LIMIT 1000")

# Client-side filtering
high_priority = cases.filter(Priority='High')
new_cases = cases.filter(Status='New', Priority='High')

# Grouping
by_status = cases.group_by('Status').count()
# {'New': 450, 'In Progress': 300, 'Closed': 250}

# Ordering
sorted_cases = cases.order_by('CreatedDate', asc=False)

# Get earliest/latest
oldest = cases.earliest('CreatedDate')
newest = cases.latest('CreatedDate')

# Transformations
case_numbers = cases.values_list('CaseNumber', flat=True)
```

**Advantages:**
- Rich client-side operations
- Reduce API calls with local filtering
- Django-style ResultSet API
- Memory-efficient chaining

#### simple-salesforce
```python
results = sf.query("SELECT Id, Name FROM Account")
# Manual iteration only
for record in results['records']:
    print(record['Name'])
```

**Limitations:**
- No client-side filtering
- No grouping or ordering
- Manual dict access
- Must re-query for filtering

#### beatbox
```python
results = svc.query("SELECT Id, Name FROM Account")
# XML/dict structures, manual processing
```

**Limitations:**
- No helper methods
- Manual XML/dict navigation
- No result transformations

---

### 4. Metadata & Object Discovery

#### forcepy ⭐ (Beginner-Friendly!)
```python
# Interactive object exploration
sf.print_objects(custom_only=True, limit=20)

# Filter objects
custom = sf.list_objects(custom_only=True, queryable_only=True)
account_related = sf.list_objects(pattern='.*account.*')

# Identify object from ID (super helpful!)
obj_type = sf.get_object_type_from_id('001B00000123456')
print(obj_type)  # 'Account'

# Dependent picklists
values = sf.get_dependent_picklist_values(
    'Case', 'Sub_Category__c', controlling_value='Hardware'
)

# Cached describe
describe = sf.describe('Account', use_cache=True)
required = describe.required_fields
```

**Advantages:**
- Beginner-friendly discovery tools
- ID to object type lookup
- Dependent picklist support
- Automatic caching
- Interactive exploration

#### simple-salesforce
```python
# Basic describe
describe = sf.Account.describe()

# Global describe
metadata = sf.describe()
```

**Limitations:**
- No filtering or search
- No ID lookup
- No dependent picklists
- No caching
- Not beginner-friendly

#### beatbox
```python
# Basic describe via SOAP
desc = svc.describeSObject('Account')
```

**Limitations:**
- XML responses
- Limited functionality
- No discovery helpers

---

### 5. Batch Operations

#### forcepy ⭐
```python
# Composite API (up to 25 operations)
composite = sf.composite(all_or_none=True)
composite.post('/services/data/v53.0/sobjects/Account', 'NewAccount', 
               body={'Name': 'Test'})
composite.patch('/services/data/v53.0/sobjects/Contact/003xxx', 'UpdateContact',
                body={'Phone': '555-1234'})
response = composite.execute()

# Or use context manager (Pythonic!)
with sf as batch:
    batch.sobjects.Account.post(Name='Account 1')
    batch.sobjects.Account.post(Name='Account 2')
# Auto-executes on exit

# Bulk API 2.0 (for millions of records)
job = sf.bulk.Account.insert([
    {'Name': 'Account 1', 'Industry': 'Technology'},
    {'Name': 'Account 2', 'Industry': 'Finance'},
    # ... thousands/millions more
])

# Async monitoring
def on_complete(job):
    print(f"Done! Processed {job.number_records_processed}")

job.wait_for_completion(poll_interval=5, callback=on_complete)

# Get results
results = job.get_results()
print(f"Successful: {len(results['successful'])}")
print(f"Failed: {len(results['failed'])}")

# Other bulk operations
update_job = sf.bulk.Account.update(update_data)
upsert_job = sf.bulk.Account.upsert(data, external_id_field='External_Id__c')
delete_job = sf.bulk.Account.delete(delete_data)
query_results = sf.bulk.Account.query("SELECT Id, Name FROM Account")
```

**Advantages:**
- Composite API (up to 25 operations)
- Bulk API 2.0 (millions of records)
- Context manager for clean syntax
- Async job monitoring with callbacks
- Reference support between requests
- All-or-none option

#### simple-salesforce
```python
from simple_salesforce import Salesforce
sf = Salesforce(username='user', password='pass', security_token='token')

# Bulk API v1.0 for large datasets
from simple_salesforce import bulk
bulk = sf.bulk
results = bulk.Account.insert([{'Name': 'Test1'}, {'Name': 'Test2'}])
```

**Advantages:**
- Bulk API v1.0 support

**Limitations:**
- No Composite API
- No Bulk API v2.0 (older API only)
- No context manager

#### beatbox
```python
# Basic SOAP batch operations
svc.create([obj1, obj2, obj3])
```

**Limitations:**
- SOAP-based (slower)
- Limited batch functionality
- No Bulk API

---

### 6. Advanced Features

#### forcepy ⭐
```python
# Auto-retry on transient errors
sf = Salesforce(
    username='user',
    password='pass',
    max_retries=3,
    retry_delay=6.0,
    retry_backoff=True
)
# Automatically retries 503, 502, 500, UNABLE_TO_LOCK_ROW, 429

# Session tracking
print(f"User: {sf.user_id}")
print(f"Expires: {sf.session_expires}")
print(f"Last request: {sf.last_request_time}")

# Workbench URL generation
url = sf.get_workbench_url("SELECT Id FROM Account")
# Share query with team for debugging

# ID comparison utilities
if sf.equal('005B0000000hMtx', '005B0000000hMtxIAI'):  # 15 vs 18 char
    print("Same record")

# SOQL formatting
formatted = sf.prettyprint("SELECT Id,Name FROM Account WHERE Status='Active'")
```

**Advantages:**
- Production-ready reliability (auto-retry)
- Developer tools (Workbench URLs, formatting)
- Session monitoring
- ID utilities

#### simple-salesforce & beatbox
```python
# No advanced features
# Manual retry logic required
# No developer tools
```

---

### 7. Developer Convenience Features

#### forcepy ⭐
```python
# Convenience methods - cleaner, safer code
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 10")
first = accounts.records.first()  # Returns None if empty (no IndexError!)
last = accounts.records.last()

# Case-insensitive filtering - flexible and intuitive
cases = sf.query("SELECT Id, Subject, Status FROM Case")
urgent = cases.records.filter(Subject__icontains='urgent')
# Matches "URGENT", "Urgent", "urgent", "URGENT ISSUE", etc.

new_cases = cases.records.filter(Status__iexact='new')
# Matches "New", "NEW", "new" - exact but case-insensitive

# More case-insensitive operators
api_issues = cases.records.filter(Subject__istartswith='api')
bug_reports = cases.records.filter(Subject__iendswith='bug')

# CSV export/import - easy data exchange
accounts.records.to_csv('accounts.csv')  # Export to file
csv_string = accounts.records.to_csv()   # Or get as string

from forcepy.results import ResultSet
imported = ResultSet.from_csv('accounts.csv')      # From file
imported = ResultSet.from_csv(csv_string)          # From string
imported = ResultSet.from_csv(io.StringIO(data))   # From buffer

# Round-trip preserves data
accounts.records.to_csv('data.csv')
loaded = ResultSet.from_csv('data.csv')
# All data preserved including None values
```

**Advantages:**
- **Convenience methods** prevent index errors and make code more readable
- **Case-insensitive filters** work better with real-world data (inconsistent capitalization)
- **CSV support** simplifies data import/export workflows
- **Chaining friendly** - all methods return ResultSets for further filtering
- **Safe for empty results** - `.first()` and `.last()` return None instead of raising exceptions

**Real-world benefits:**
```python
# Before: Risky code
if len(results.records) > 0:
    first = results.records[0]
else:
    first = None

# After: Clean and safe
first = results.records.first()

# Case-insensitive search is invaluable for user-entered data
user_search = "urgent"
cases = sf.query("SELECT Id, Subject FROM Case")
matches = cases.records.filter(Subject__icontains=user_search)
# Finds "URGENT", "Urgent Issue", "urgent problem", etc.
```

#### simple-salesforce
```python
# Manual approaches required
results = sf.query("SELECT Id, Name FROM Account")['records']

# Must handle index errors manually
first = results[0] if results else None
last = results[-1] if results else None

# Case-sensitive only - requires custom logic
matches = [r for r in results if 'urgent' in r['Name'].lower()]

# No built-in CSV support - must use csv module
import csv
with open('export.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['Id', 'Name'])
    writer.writeheader()
    for record in results:
        writer.writerow(record)
```

**Limitations:**
- No convenience methods
- No case-insensitive filters
- No CSV helpers
- More boilerplate code required

#### beatbox
```python
# XML-based results - even more manual
results = svc.query("SELECT Id, Name FROM Account")
records = results['records']
# All filtering/transformation is manual
```

**Limitations:**
- No convenience features
- XML parsing required
- Very manual approach

---

## Use Case Recommendations

### Choose forcepy if you want:
✅ **Modern, feature-rich client** with advanced capabilities  
✅ **Beginner-friendly** object discovery and exploration  
✅ **Power-user features** like Q objects, client-side filtering, iterquery  
✅ **Production reliability** with auto-retry and session tracking  
✅ **JWT authentication** for serverless/CI environments  
✅ **Token caching** for performance (Redis support)  
✅ **Type hints** and modern Python (3.9+)  
✅ **Composite API** for batch operations  

**Best for:** New projects, complex queries, production deployments, beginners

### Choose simple-salesforce if you want:
✅ **Simple, lightweight** REST API client  
✅ **Bulk API v1.0** support (forcepy uses newer v2.0)  
✅ **Mature, stable** library with large community  
✅ **Basic CRUD** operations only  

**Best for:** Simple integrations, bulk data loads, quick prototypes

### Choose beatbox if you want:
✅ **SOAP API** access (legacy requirement)  
✅ **XML-based** integration  

**Best for:** Legacy systems, SOAP requirements (not recommended for new projects)

---

## Migration Guide

### From simple-salesforce to forcepy

#### Before (simple-salesforce)
```python
from simple_salesforce import Salesforce

sf = Salesforce(username='user', password='pass', security_token='token')
results = sf.query("SELECT Id, Name FROM Account WHERE Industry = 'Technology'")
for record in results['records']:
    print(record['Name'])
```

#### After (forcepy)
```python
from forcepy import Salesforce, Q

# Auto-authenticates (no security token needed with password)
sf = Salesforce(username='user', password='pass')

# Same basic query works
results = sf.query("SELECT Id, Name FROM Account WHERE Industry = 'Technology'")
for record in results:  # Cleaner iteration
    print(record.Name)  # Dot notation

# OR use Q objects for complex queries
q = Q(Industry='Technology') & (Q(AnnualRevenue__gte=1000000) | Q(NumberOfEmployees__gte=100))
results = sf.query(f"SELECT Id, Name FROM Account WHERE {q.compile()}")

# Client-side filtering (no extra API calls!)
large_accounts = results.filter(AnnualRevenue__gte=5000000)
by_state = results.group_by('BillingState').count()
```

**Key Differences:**
1. No `security_token` parameter (included in password for SOAP)
2. Cleaner result iteration (no `['records']`)
3. Dot notation for field access
4. Many more features available (Q objects, filtering, etc.)

---

## Performance Comparison

| Operation | forcepy | simple-salesforce | beatbox |
|-----------|---------|-------------------|---------|
| Authentication | Fast (cached) | Medium | Slow (SOAP) |
| Simple Query | Fast | Fast | Medium |
| Complex Query | Very Fast (Q objects) | Slow (manual) | Slow |
| Large Datasets | Very Fast (threaded iterquery) | Medium | Slow |
| Bulk Operations | 🔜 (planned) | Fast | Medium |
| Batch Operations | Fast (Composite) | N/A | Medium (SOAP) |
| API Calls Needed | Fewer (caching, filtering) | More | More |

---

## Community & Support

| Aspect | forcepy | simple-salesforce | beatbox |
|--------|---------|-------------------|---------|
| **GitHub Stars** | New! | ~1,700 | ~150 |
| **PyPI Downloads** | New! | ~500k/month | ~10k/month |
| **Last Update** | Active | Active | Less active |
| **Documentation** | Comprehensive | Good | Basic |
| **Issues Response** | Active | Active | Slow |
| **Python Version** | 3.9+ | 3.7+ | 2.7/3.x |

---

## Conclusion

**forcepy** is the **most feature-rich** and **beginner-friendly** Python Salesforce library available:

✅ **30+ unique features** not in other libraries  
✅ **Beginner-friendly** with object discovery and ID lookup  
✅ **Power-user** features like Q objects and client-side filtering  
✅ **Production-ready** with auto-retry and session tracking  
✅ **Modern Python** with full type hints  
✅ **Zero compromises** - works for beginners AND experts  

While **simple-salesforce** is great for basic use cases, **forcepy** is the better choice for:
- New projects
- Complex query requirements
- Production deployments
- Salesforce newcomers
- Teams needing advanced features

**simple-salesforce** is good for:
- **Bulk API v1.0** (forcepy uses newer v2.0)
- Maximum simplicity (if you only need basic CRUD)

**beatbox** is only recommended for legacy SOAP requirements.

---

**Try forcepy today!**
```bash
pip install forcepy
# or
uv add forcepy
```

See the [README](../README.md) for quick start guide and examples!

