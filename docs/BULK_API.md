# Bulk API 2.0 Guide

The Bulk API in forcepy provides efficient handling of large-scale data operations. It's built on Salesforce's Bulk API 2.0, offering improved performance and simplified usage compared to the older Bulk API v1.

## Overview

### When to Use Bulk API

Use the Bulk API when you need to:

- **Insert, update, upsert, or delete** thousands of records
- **Query** large datasets (>2,000 records)
- **Minimize API limits** by processing records in batches
- **Handle long-running operations** asynchronously

### Quick Comparison

| Operation Type | Standard REST API | Bulk API 2.0 |
|----------------|------------------|--------------|
| Record Limit | ~200 per request | Up to 150 million |
| Processing | Synchronous | Asynchronous |
| Best For | < 2,000 records | > 2,000 records |
| API Calls | Multiple | Single job |

## Getting Started

### Basic Usage

```python
from forcepy import Salesforce

sf = Salesforce(username='user@example.com', password='password')

# Insert records
job = sf.bulk.Account.insert([
    {'Name': 'Account 1', 'Industry': 'Technology'},
    {'Name': 'Account 2', 'Industry': 'Finance'}
])

# Wait for completion
job.wait_for_completion()

# Get results
results = job.get_results()
print(f"Successful: {len(results['successful'])}")
print(f"Failed: {len(results['failed'])}")
```

## Core Concepts

### Jobs

A **job** represents a bulk operation. Jobs are asynchronous - they're created, data is uploaded, and then Salesforce processes them in the background.

**Job States:**

- `Open` - Job created, ready for data
- `UploadComplete` - Data uploaded, processing started
- `InProgress` - Job is processing
- `JobComplete` - Job finished successfully
- `Failed` - Job encountered an error
- `Aborted` - Job was manually aborted

### Job Monitoring

There are two ways to monitor job progress:

#### 1. Automatic Waiting (Recommended)

```python
job = sf.bulk.Account.insert(records)

# Block until complete
job.wait_for_completion(poll_interval=5)
```

#### 2. Manual Polling

```python
job = sf.bulk.Account.insert(records)

while job.state not in ('JobComplete', 'Failed', 'Aborted'):
    job.refresh()
    print(f"State: {job.state}, Processed: {job.number_records_processed}")
    time.sleep(5)
```

## Operations

### Insert

Create new records.

```python
records = [
    {'Name': 'Acme Corp', 'Industry': 'Technology', 'NumberOfEmployees': 500},
    {'Name': 'Global Industries', 'Industry': 'Manufacturing', 'NumberOfEmployees': 1200},
]

job = sf.bulk.Account.insert(records)
job.wait_for_completion()

results = job.get_results()
for record in results['successful']:
    print(f"Created: {record['sf__Id']}")
```

### Update

Update existing records (requires `Id` field).

```python
records = [
    {'Id': '001xx000003DGbQAAW', 'Description': 'Updated via Bulk API'},
    {'Id': '001xx000003DGbRAAW', 'Industry': 'Finance'},
]

job = sf.bulk.Account.update(records)
job.wait_for_completion()
```

### Upsert

Insert new records or update existing ones based on an external ID field.

```python
records = [
    {'External_Id__c': 'EXT001', 'Name': 'Account 1', 'Industry': 'Energy'},
    {'External_Id__c': 'EXT002', 'Name': 'Account 2', 'Industry': 'Utilities'},
]

job = sf.bulk.Account.upsert(records, external_id_field='External_Id__c')
job.wait_for_completion()
```

**Note:** The external ID field must exist on the object and be marked as "External ID" in Salesforce.

### Delete

Delete records (requires `Id` field).

```python
records = [
    {'Id': '001xx000003DGbQAAW'},
    {'Id': '001xx000003DGbRAAW'},
]

job = sf.bulk.Account.delete(records)
job.wait_for_completion()
```

### Query

Execute SOQL queries for large result sets.

```python
soql = "SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology'"

results = sf.bulk.Account.query(soql)
print(f"Found {len(results)} records")

for record in results:
    print(f"{record['Name']} - {record['Industry']}")
```

**Note:** Query operations are automatically waited on and return results directly.

## Advanced Features

### Callbacks

Execute custom code when a job completes:

```python
def on_complete(job):
    results = job.get_results()
    print(f"✓ Processed {job.number_records_processed} records")
    print(f"✗ Failed {job.number_records_failed} records")

    # Send notification, update database, etc.
    send_notification(f"Bulk job {job.job_id} completed")

job = sf.bulk.Account.insert(large_dataset)
job.wait_for_completion(callback=on_complete, poll_interval=10)
```

### Timeouts

Prevent indefinite waiting:

```python
from forcepy.exceptions import BulkJobTimeout

try:
    job = sf.bulk.Account.insert(records)
    job.wait_for_completion(timeout=300)  # 5 minutes max
except BulkJobTimeout:
    print("Job took too long, aborting...")
    job.abort()
```

### Error Handling

Handle failures gracefully:

```python
from forcepy.exceptions import BulkJobError

try:
    job = sf.bulk.Account.insert(records)
    job.wait_for_completion()

    results = job.get_results()

    # Check for partial failures
    if results['failed']:
        print(f"Warning: {len(results['failed'])} records failed")
        for failed_record in results['failed']:
            print(f"Error: {failed_record.get('sf__Error', 'Unknown')}")

except BulkJobError as e:
    print(f"Bulk job failed: {e}")
```

### Aborting Jobs

Stop a running job:

```python
job = sf.bulk.Account.insert(large_dataset)

# Something went wrong, abort
job.abort()

print(f"Job state: {job.state}")  # 'Aborted'
```

## Data Formats

### Python Dictionaries (Recommended)

The easiest way to work with the Bulk API is using Python dictionaries:

```python
records = [
    {'Name': 'Account 1', 'Industry': 'Technology'},
    {'Name': 'Account 2', 'Industry': 'Finance'},
]

job = sf.bulk.Account.insert(records)
```

Internally, forcepy converts these to JSON format (Bulk API 2.0's native format).

### Field Types

All standard Salesforce field types are supported:

```python
record = {
    'Name': 'Test Account',                    # Text
    'NumberOfEmployees': 100,                  # Number
    'AnnualRevenue': 1000000.50,              # Currency
    'IsActive__c': True,                       # Checkbox
    'FoundedDate__c': '2020-01-15',           # Date (YYYY-MM-DD)
    'LastMeetingTime__c': '2020-01-15T10:30:00Z',  # DateTime (ISO 8601)
    'OwnerId': '005xx000001Sv5OAAS',          # Lookup
    'Description': None,                       # Null value (clears field)
}
```

## Best Practices

### 1. Batch Size Recommendations

| Record Count | Recommendation |
|--------------|----------------|
| < 2,000 | Use standard REST API (`sf.sobjects.Account.post()`) |
| 2,000 - 10,000 | Bulk API (single job) |
| 10,000+ | Bulk API (consider splitting into multiple jobs) |

### 2. Field Selection for Queries

Be specific with fields to improve performance:

```python
# Good - specific fields
results = sf.bulk.Account.query("SELECT Id, Name, Industry FROM Account")

# Avoid - select all
results = sf.bulk.Account.query("SELECT Id, Name, Industry, ... FROM Account")
```

### 3. Error Recovery

Always check for failed records:

```python
job = sf.bulk.Account.insert(records)
job.wait_for_completion()

results = job.get_results()

if results['failed']:
    # Retry failed records
    failed_records = [...]  # Extract and fix failed records
    retry_job = sf.bulk.Account.insert(failed_records)
```

### 4. Polling Intervals

Choose appropriate polling intervals:

```python
# Small jobs (< 10,000 records): check every 2-5 seconds
job.wait_for_completion(poll_interval=3)

# Medium jobs (10,000 - 100,000): check every 10-30 seconds
job.wait_for_completion(poll_interval=15)

# Large jobs (100,000+): check every 60 seconds
job.wait_for_completion(poll_interval=60)
```

### 5. Concurrent Jobs

You can run multiple jobs concurrently:

```python
# Start multiple jobs
account_job = sf.bulk.Account.insert(account_records)
contact_job = sf.bulk.Contact.insert(contact_records)
opportunity_job = sf.bulk.Opportunity.insert(opp_records)

# Wait for all
account_job.wait_for_completion()
contact_job.wait_for_completion()
opportunity_job.wait_for_completion()
```

**Note:** Salesforce limits the number of concurrent jobs per org (typically 10-20).

## Performance Tips

### 1. Use JSON Format (Default)

Bulk API 2.0 uses JSON by default, which is faster than CSV and handles complex data types better.

### 2. Minimize Field Count

Only include fields you need to update:

```python
# Good - only necessary fields
records = [{'Id': id, 'Status__c': 'Active'} for id in account_ids]

# Avoid - unnecessary fields
records = [{'Id': id, 'Name': name, 'Status__c': 'Active', ...} for ...]
```

### 3. Pre-validate Data

Validate records before submitting to avoid job failures:

```python
from forcepy.bulk import validate_records

try:
    validate_records(records, 'update')
    job = sf.bulk.Account.update(records)
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Comparison with simple-salesforce

If you're migrating from `simple-salesforce`, here's the equivalent syntax:

### simple-salesforce

```python
from simple_salesforce import Salesforce

sf = Salesforce(username='user', password='pass', security_token='token')

# Insert
job = sf.bulk.Account.insert(data)
sf.bulk.Account.wait_for_batch(job.id)
results = sf.bulk.Account.get_batch_results(job.id)
```

### forcepy

```python
from forcepy import Salesforce

sf = Salesforce(username='user', password='pass')

# Insert (simpler API)
job = sf.bulk.Account.insert(data)
job.wait_for_completion()
results = job.get_results()
```

**Key Differences:**

- forcepy uses Bulk API 2.0 (simpler, faster)
- No manual batch management needed
- Job object encapsulates all operations
- Automatic token handling (no security token needed)

## Troubleshooting

### Job Stuck in InProgress

If a job stays in `InProgress` for a long time:

```python
# Check job details
job.refresh()
print(f"Processed: {job.number_records_processed}")
print(f"State: {job.state}")

# If truly stuck, abort and retry
if job.state == 'InProgress' and time_elapsed > threshold:
    job.abort()
    new_job = sf.bulk.Account.insert(records)
```

### High Failure Rate

If many records fail:

```python
results = job.get_results()

# Analyze failures
for failed in results['failed']:
    error = failed.get('sf__Error', '')
    if 'REQUIRED_FIELD_MISSING' in error:
        print(f"Missing required field: {failed}")
    elif 'DUPLICATE_VALUE' in error:
        print(f"Duplicate record: {failed}")
```

### Timeout Errors

Increase timeout or poll interval:

```python
# Longer timeout
job.wait_for_completion(timeout=600, poll_interval=30)

# Or disable timeout
job.wait_for_completion(timeout=None, poll_interval=10)
```

## API Reference

### BulkJob Class

```python
class BulkJob:
    job_id: str                      # Unique job identifier
    state: str                       # Current state
    object_name: str                 # Salesforce object
    operation: str                   # Operation type
    created_date: str                # Creation timestamp
    number_records_processed: int    # Records processed
    number_records_failed: int       # Records failed

    def refresh() -> None:
        """Refresh job status from Salesforce."""

    def wait_for_completion(
        poll_interval: int = 5,
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> BulkJob:
        """Wait for job to complete."""

    def get_results() -> dict:
        """Get successful and failed records."""

    def abort() -> None:
        """Abort the job."""
```

### BulkAPI Class

```python
class BulkAPI:
    def __getattr__(object_name: str) -> BulkObjectOperations:
        """Access object operations (e.g., bulk.Account)."""

class BulkObjectOperations:
    def insert(records: list[dict]) -> BulkJob:
        """Insert records."""

    def update(records: list[dict]) -> BulkJob:
        """Update records."""

    def upsert(records: list[dict], external_id_field: str) -> BulkJob:
        """Upsert records."""

    def delete(records: list[dict]) -> BulkJob:
        """Delete records."""

    def query(soql: str) -> list[dict]:
        """Execute bulk query."""
```

## Examples

See `examples/bulk_operations.py` for complete working examples.

## Further Reading

- [Salesforce Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_bulk_v2.meta/api_bulk_v2/)
- [forcepy Documentation](../README.md)
- [Feature Comparison](FEATURE_COMPARISON.md)

