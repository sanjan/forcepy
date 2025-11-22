<div align="center">
  <img src="https://raw.githubusercontent.com/sanjan/forcepy/main/docs/images/force_py_header.png" alt="forcepy" width="600"/>
</div>

<h1 align="center">forcepy ⚡</h1>

<p align="center">
  <strong>A faster way to work with Salesforce data.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/forcepy/"><img src="https://img.shields.io/pypi/v/forcepy.svg" alt="PyPI version"/></a>
  <a href="https://pypi.org/project/forcepy/"><img src="https://img.shields.io/pypi/pyversions/forcepy.svg" alt="Python versions"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://github.com/sanjan/forcepy"><img src="https://img.shields.io/badge/tests-349%20passing-brightgreen.svg" alt="Tests"/></a>
  <a href="https://github.com/sanjan/forcepy"><img src="https://img.shields.io/badge/coverage-78%25-brightgreen.svg" alt="Code coverage"/></a>
</p>

<p align="center">
  Forcepy transforms the way you interact with Salesforce APIs - turning complex operations into simple, Pythonic code. Build integrations, automate workflows, or migrate data with minimal effort and maximum power.
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#-core-features">Features</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#examples">Examples</a>
</p>

<hr/>

## ⚡ Core Features

- Transform your Salesforce workflow with **ZERO BOILERPLATE** (almost)! 🚀
- Build with **ANY** Salesforce use case (REST API, Bulk API 2.0, Composite API, Chatter, Metadata); or even **WITHOUT** complexity (just import and go). You name it! 🔥
- **🎯 Simple and Pythonic** - Write beautiful, easy-to-read code that feels native to Python
- **⚡ Lightning fast** - Smart caching, connection pooling, and auto-retry logic built-in
- **🔐 Multiple auth methods** - SOAP, OAuth2, and JWT Bearer Flow all supported
- **🚀 Advanced query building** - Q objects, client-side filtering, and SOQL helpers
- **📦 Bulk operations** - Handle millions of records with Bulk API 2.0
- **📊 Developer-friendly** - Full type hints, comprehensive docs, and 349 passing tests

## Installation

```bash
# Basic installation
pip install forcepy

# With JWT support
pip install forcepy[jwt]

# Using uv (recommended)
uv add forcepy
```

## Quickstart

### A little example

Create a file `my_script.py`:

```python
from forcepy import Salesforce

# Production org (default)
sf = Salesforce(
    username='user@example.com',
    password='password'
)

# With security token (if required)
sf = Salesforce(
    username='user@example.com',
    password='password',
    security_token='yourSecurityToken123'
)

# Sandbox org
sf = Salesforce(
    username='user@example.com',
    password='password',
    sandbox=True
)

# Query data with dot notation
accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 5")
for account in accounts.records:
    print(f"{account.Name} - {account.Industry}")
```

Run it:

```bash
python my_script.py
```

That's it! You're already querying Salesforce data. 🎉

### Get more power!

Forcepy comes packed with advanced features:

#### 🔍 Advanced Query Building

```python
from forcepy import Q

# Build complex queries with Q objects
high_value = Q(AnnualRevenue__gt=1000000) | Q(NumberOfEmployees__gt=500)
tech_companies = Q(Industry='Technology') & high_value

accounts = sf.query(f"SELECT Id, Name FROM Account WHERE {tech_companies.compile()}")
```

#### 🎛️ Client-Side Filtering

```python
# Query once, filter many times
cases = sf.query("SELECT Id, Status, Priority FROM Case LIMIT 1000")

# Filter client-side
urgent = cases.records.filter(Priority='High', Status='New')

# Group and aggregate
by_status = cases.records.group_by('Status').count()
# {'New': 450, 'In Progress': 300, 'Closed': 250}
```

#### ⚙️ Composite API (Batch Operations)

```python
# Execute up to 25 operations in a single API call
with sf as batch:
    batch.sobjects.Account.post(Name='Acme Corp', Industry='Technology')
    batch.sobjects.Account.post(Name='Global Inc', Industry='Finance')
    batch.sobjects.Contact['003xx000004TmiQQAS'].patch(LastName='Smith')
# All operations execute atomically on exit
```

#### 💬 Chatter Integration

```python
from forcepy import Chatter

chatter = Chatter(sf)

# Post with @mentions and $record links (entity tagging)
chatter.post("Hey @[005xx0000012345]! Please review $[001xx0000012345]")

# HTML formatting
chatter.post("<b>Important:</b> <i>Q4 goals achieved!</i>")

# Post to groups
chatter.post_to_group("0F9xx000000abcd", "Team meeting at 2pm!")
```

**Entity Tagging:**
- `@[userId]` - Mention users (e.g., `@[005xx0000012345]`)
- `$[recordId]` - Link to records (e.g., `$[001xx0000012345]`)

#### 🎁 Developer Experience Features

```python
# Convenience methods - cleaner code
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 10")
first = accounts.records.first()  # Instead of [0]
last = accounts.records.last()    # Instead of [-1]

# Case-insensitive filtering - more flexible
cases = sf.query("SELECT Id, Subject, Status FROM Case")
urgent = cases.records.filter(Subject__icontains='urgent')  # Matches "URGENT", "Urgent", etc.
new_cases = cases.records.filter(Status__iexact='new')      # Case-insensitive exact match

# CSV export/import - easy data exchange
accounts.records.to_csv('accounts.csv')
from forcepy.results import ResultSet
imported = ResultSet.from_csv('accounts.csv')
```

#### 🗄️ Bulk API 2.0

```python
# Handle millions of records efficiently
records = [{'Name': f'Account {i}', 'Industry': 'Technology'} for i in range(10000)]
job = sf.bulk.Account.insert(records)

# Wait for completion and get results
results = job.wait()
print(f"Processed: {results['numberRecordsProcessed']}")
print(f"Failed: {results['numberRecordsFailed']}")

# Or query large datasets
job = sf.bulk.Account.query("SELECT Id, Name FROM Account")
for batch in job.get_results():
    for record in batch:
        print(record['Name'])
```

## Key Features

### 🎯 Query & Filtering
- **Q Objects** - Build complex WHERE clauses with boolean logic
- **Query helpers** - IN(), DATE(), BOOL() for clean SOQL
- **SELECT * expansion** - Automatically expand to all fields
- **Client-side filtering** - filter(), group_by(), order_by() on results
- **Iterquery** - Efficient pagination with optional threading

### 🔐 Authentication & Security
- **SOAP login** - Username/password authentication (auto-detects sandbox)
- **JWT Bearer Flow** - Certificate-based authentication for production
- **OAuth2** - Full OAuth2 support
- **Token caching** - Automatic caching (memory/Redis) for performance
- **Session tracking** - Monitor user_id, session expiry, last request time

### ⚡ Performance & Reliability
- **Auto-retry** - Configurable retries on 503, 502, 500, UNABLE_TO_LOCK_ROW, 429
- **Connection pooling** - Efficient HTTP session management
- **Smart caching** - Describe/metadata results cached automatically
- **Manual pagination** - Full control with query_more() and next_records_url

### 🛠️ Developer Experience
- **Full type hints** - Better IDE autocomplete and type checking
- **Dot notation** - Access nested fields intuitively
- **Dynamic endpoints** - Chain attributes to build API paths
- **Workbench URLs** - Generate shareable query links
- **Pretty print** - Format SOQL for readability
- **Object discovery** - List and explore Salesforce objects
- **ID utilities** - Compare 15/18 char IDs, determine object type from ID
- **Convenience methods** - `.first()`, `.last()` for cleaner code
- **Case-insensitive filters** - `__icontains`, `__iexact` for flexible searching
- **CSV export/import** - Easy data exchange with `.to_csv()` and `.from_csv()`

### 📦 Batch Operations
- **Composite API** - Batch up to 25 operations with reference support
- **Context manager** - Pythonic `with` statement for batching
- **All-or-none** - Atomic transactions option

### 📊 Metadata & Schema
- **Cached describe** - Fast metadata access with automatic caching
- **Field information** - Required fields, picklist values, field properties
- **Dependent picklists** - Filter picklist values by controlling field
- **Org limits** - Check API usage and limits

## Get Inspired

Here's what you can build with forcepy:

### 🔄 Data Migration
Migrate millions of records between orgs with bulk operations and smart error handling.

### 🤖 Automation & Integration
Build workflows that sync Salesforce with external systems - CRMs, ERPs, databases, and more.

### 📊 Analytics & Reporting
Extract Salesforce data for custom analytics, dashboards, and business intelligence.

### 🧪 Testing & CI/CD
Populate test orgs, validate deployments, and automate quality assurance.

### 📱 Custom Applications
Build custom apps that extend Salesforce capabilities beyond the platform.

## Documentation

- 🔄 **[Migration from simple-salesforce](docs/MIGRATION_FROM_SIMPLE_SALESFORCE.md)** - Step-by-step migration guide
- 📖 **[Token Caching Guide](docs/TOKEN_CACHING.md)** - Production caching strategies
- 🔐 **[Authentication Guide](docs/AUTHENTICATION.md)** - All auth methods explained
- 💬 **[Chatter Features](docs/CHATTER_FEATURES.md)** - Complete Chatter reference
- 💡 **[Examples](examples/)** - 13 ready-to-run code examples (including bulk operations!)

## Resources

- **Documentation:**
  - [Migration from simple-salesforce](docs/MIGRATION_FROM_SIMPLE_SALESFORCE.md) - Step-by-step guide
  - [Authentication Guide](docs/AUTHENTICATION.md) - All auth methods explained
  - [Token Caching Guide](docs/TOKEN_CACHING.md) - Production caching strategies
  - [Chatter Features](docs/CHATTER_FEATURES.md) - Complete Chatter reference
  - [Bulk API Guide](docs/BULK_API.md) - Handle large-scale operations
  - [Library Comparison](docs/PUBLIC_LIBRARY_COMPARISON.md) - vs simple-salesforce
- **Examples:** [13 ready-to-run code examples](examples/)
  - Basic queries and CRUD operations
  - Advanced filtering with Q objects
  - **Bulk API 2.0** for large-scale operations
  - JWT and OAuth authentication
  - Chatter integration
  - Composite API batch operations
  - Token caching strategies
  - And more!
- **Issues:** [Report bugs or request features](https://github.com/sanjan/forcepy/issues)
- **Discussions:** [Get help from the community](https://github.com/sanjan/forcepy/discussions)

## Comparison with simple-salesforce

Forcepy builds on the foundation of simple-salesforce with many powerful additions:

| Feature | forcepy | simple-salesforce |
|---------|---------|-------------------|
| Q Objects for complex queries | ✅ | ❌ |
| Query building helpers | ✅ | ❌ |
| Client-side filtering/grouping | ✅ | ❌ |
| JWT authentication | ✅ | ❌ |
| Token caching (automatic) | ✅ | ❌ |
| Redis cache support | ✅ | ❌ |
| Composite API | ✅ | ❌ |
| Dependent picklists | ✅ | ❌ |
| SELECT * expansion | ✅ | ❌ |
| Workbench URL generation | ✅ | ❌ |
| ID comparison utilities | ✅ | ❌ |
| Auto-retry on errors | ✅ | ❌ |
| Threaded iterquery | ✅ | ❌ |
| Session info properties | ✅ | ❌ |
| Composite context manager | ✅ | ❌ |
| Chatter integration | ✅ | Limited |
| Type hints | ✅ | Limited |
| Dot notation | ✅ | ✅ |
| SOQL queries | ✅ | ✅ |
| Bulk API 2.0 | ✅ | ✅ |

## Examples

### Basic Operations

```python
from forcepy import Salesforce

sf = Salesforce(username='user@example.com', password='password')

# Create (both styles work!)
result = sf.Account.post(Name='Acme Corp', Industry='Technology')
# or: sf.sobjects.Account.post(...)
account_id = result['id']

# Read
account = sf.Account[account_id].get()
print(account['Name'])

# Update
sf.Account[account_id].patch(Industry='Manufacturing')

# Delete
sf.Account[account_id].delete()
```

> **💡 Tip:** Both `sf.Account` and `sf.sobjects.Account` work! Use whichever style you prefer.

### Advanced Query with Q Objects

```python
from forcepy import Q

# Complex boolean logic
tech_or_finance = Q(Industry='Technology') | Q(Industry='Finance')
high_revenue = Q(AnnualRevenue__gte=1000000)
california = Q(BillingState='CA')

query = tech_or_finance & high_revenue & california

accounts = sf.query(f"SELECT Id, Name FROM Account WHERE {query.compile()}")
```

### Client-Side Data Manipulation

```python
# Query all opportunities
opps = sf.query("SELECT Id, Name, Amount, StageName FROM Opportunity LIMIT 1000")

# Filter to closed-won
won = opps.records.filter(StageName='Closed Won')

# Group by stage and sum amounts
pipeline = opps.records.group_by('StageName').count()

# Sort by amount
top_deals = won.order_by('Amount', asc=False)[:10]

# Extract field values
amounts = opps.records.values_list('Amount', flat=True)
total = sum(amounts)
```

### JWT Authentication (Production)

```python
sf = Salesforce()
sf.login_with_jwt(
    client_id='your-connected-app-id',
    private_key='/path/to/private.key',
    username='user@example.com'
)
```

### Token Caching for Performance

```python
# Redis cache for Kubernetes/multi-pod deployments
sf = Salesforce(
    username='user@example.com',
    password='password',
    cache_backend='redis',
    redis_url='redis://redis-service:6379'
)
# Second authentication reuses cached token - no API call!
```

### Object Discovery (Perfect for Beginners!)

```python
# List all custom objects
custom = sf.list_objects(custom_only=True)
for obj in custom:
    print(f"{obj['name']}: {obj['label']}")

# Find what object a record ID belongs to
obj_type = sf.get_object_type_from_id('006xx0000012345')
print(f"This is a {obj_type} record")
```

### Metadata & Describe

```python
# Get object metadata (cached)
describe = sf.describe('Account')

# Required fields
for field in describe.required_fields:
    print(field['name'])

# Picklist values
industries = describe.get_picklist_values('Industry')

# Dependent picklists
subcategories = describe.get_dependent_picklist_values(
    field_name='Sub_Category__c',
    controlling_value='Hardware'
)
```

## Contributing

We welcome contributions! Here's how you can help:

1. **Report bugs** - Open an issue with details and reproduction steps
2. **Suggest features** - Share your ideas for improvements
3. **Submit PRs** - See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
4. **Improve docs** - Help make our documentation better
5. **Share examples** - Contribute real-world usage examples

## Development

```bash
# Clone repository
git clone https://github.com/sanjan/forcepy.git
cd forcepy

# Install just (modern task runner)
brew install just  # Mac
cargo install just  # Any platform with Rust
# See docs/INSTALLING_JUST.md for other platforms

# Install dependencies
just install-dev

# Run tests
just test

# Run tests with coverage
just test-cov

# Lint and format
just format
just lint

# Run all quality checks
just quality

# Build package
just build

# See all commands
just --list
```

**Without just**: You can also use `uv run` directly:

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/forcepy/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug reports:** [GitHub Issues](https://github.com/sanjan/forcepy/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/sanjan/forcepy/discussions)
- 📧 **Email:** [sgrero@salesforce.com](mailto:sgrero@salesforce.com)

---

Made with ❤️ by developers, for developers.
