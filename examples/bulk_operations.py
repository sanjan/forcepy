"""Examples of Bulk API usage in forcepy.

This script demonstrates how to use the Bulk API 2.0 for large-scale operations.
"""

import os
import time

from forcepy import Salesforce

# Initialize Salesforce client
sf = Salesforce(
    username=os.getenv('SF_USERNAME'),
    password=os.getenv('SF_PASSWORD')
)

print("=== Bulk API Examples ===\n")

# Example 1: Bulk Insert
print("1. Bulk Insert:")
print("-" * 50)

accounts = [
    {'Name': 'Bulk Account 1', 'Industry': 'Technology', 'NumberOfEmployees': 100},
    {'Name': 'Bulk Account 2', 'Industry': 'Finance', 'NumberOfEmployees': 250},
    {'Name': 'Bulk Account 3', 'Industry': 'Healthcare', 'NumberOfEmployees': 500},
    {'Name': 'Bulk Account 4', 'Industry': 'Retail', 'NumberOfEmployees': 75},
    {'Name': 'Bulk Account 5', 'Industry': 'Manufacturing', 'NumberOfEmployees': 150},
]

# Create bulk job
job = sf.bulk.Account.insert(accounts)
print(f"Created job: {job.job_id}")
print(f"Initial state: {job.state}")

# Wait for completion with callback
def on_complete(job):
    print(f"\n✓ Job completed!")
    print(f"  Processed: {job.number_records_processed}")
    print(f"  Failed: {job.number_records_failed}")

# Wait (synchronous with polling)
job.wait_for_completion(poll_interval=5, callback=on_complete)

# Get results
results = job.get_results()
print(f"\nSuccessful records: {len(results['successful'])}")
if results['successful']:
    print("Sample successful record:", results['successful'][0])

print(f"Failed records: {len(results['failed'])}")
if results['failed']:
    print("Failed record details:", results['failed'][0])

print("\n")

# Example 2: Bulk Update
print("2. Bulk Update:")
print("-" * 50)

# Get some account IDs first (in real usage, you'd have these)
accounts_to_update = sf.query("SELECT Id FROM Account ORDER BY CreatedDate DESC LIMIT 3")

update_data = [
    {'Id': acc['Id'], 'Description': 'Updated via Bulk API'}
    for acc in accounts_to_update['records']
]

if update_data:
    update_job = sf.bulk.Account.update(update_data)
    print(f"Created update job: {update_job.job_id}")

    # Wait with timeout
    update_job.wait_for_completion(poll_interval=3, timeout=60)
    print(f"✓ Update completed: {update_job.number_records_processed} records")

print("\n")

# Example 3: Bulk Upsert with External ID
print("3. Bulk Upsert (with External ID):")
print("-" * 50)

# Note: This assumes you have an External_Id__c field on Account
upsert_data = [
    {'External_Id__c': 'EXT001', 'Name': 'Upserted Account 1', 'Industry': 'Energy'},
    {'External_Id__c': 'EXT002', 'Name': 'Upserted Account 2', 'Industry': 'Utilities'},
]

try:
    upsert_job = sf.bulk.Account.upsert(upsert_data, external_id_field='External_Id__c')
    print(f"Created upsert job: {upsert_job.job_id}")

    upsert_job.wait_for_completion(poll_interval=3)
    print(f"✓ Upsert completed: {upsert_job.number_records_processed} records")
except Exception as e:
    print(f"Note: Upsert example requires External_Id__c field on Account")
    print(f"Error: {e}")

print("\n")

# Example 4: Bulk Query
print("4. Bulk Query:")
print("-" * 50)

# Bulk query is useful for large result sets
soql = "SELECT Id, Name, Industry, NumberOfEmployees FROM Account WHERE Industry = 'Technology' LIMIT 100"

query_results = sf.bulk.Account.query(soql)
print(f"Query returned {len(query_results)} records")

if query_results:
    print("\nFirst 3 records:")
    for record in query_results[:3]:
        print(f"  - {record['Name']} ({record.get('Industry', 'N/A')})")

print("\n")

# Example 5: Bulk Delete
print("5. Bulk Delete:")
print("-" * 50)

# Get test records to delete
test_accounts = sf.query("SELECT Id FROM Account WHERE Name LIKE 'Bulk Account%' LIMIT 5")

if test_accounts['records']:
    delete_data = [{'Id': acc['Id']} for acc in test_accounts['records']]

    delete_job = sf.bulk.Account.delete(delete_data)
    print(f"Created delete job: {delete_job.job_id}")

    delete_job.wait_for_completion(poll_interval=3)
    delete_results = delete_job.get_results()

    print(f"✓ Delete completed")
    print(f"  Successful: {len(delete_results['successful'])}")
    print(f"  Failed: {len(delete_results['failed'])}")
else:
    print("No test accounts to delete")

print("\n")

# Example 6: Error Handling
print("6. Error Handling:")
print("-" * 50)

try:
    # Intentionally cause an error - missing required field
    bad_data = [
        {'Industry': 'Technology'},  # Missing required 'Name' field
    ]

    error_job = sf.bulk.Account.insert(bad_data)
    error_job.wait_for_completion(poll_interval=2)

    # Check for failures
    error_results = error_job.get_results()
    if error_results['failed']:
        print("Failed records found:")
        for failed in error_results['failed']:
            print(f"  Error: {failed.get('sf__Error', 'Unknown error')}")
except Exception as e:
    print(f"Caught exception: {type(e).__name__}: {e}")

print("\n")

# Example 7: Monitoring Job Progress
print("7. Monitoring Job Progress:")
print("-" * 50)

large_dataset = [
    {'Name': f'Account {i}', 'Industry': 'Technology'}
    for i in range(20)
]

progress_job = sf.bulk.Account.insert(large_dataset)
print(f"Job ID: {progress_job.job_id}")

# Manual progress monitoring
while progress_job.state not in ('JobComplete', 'Failed', 'Aborted'):
    progress_job.refresh()
    print(f"State: {progress_job.state}, Processed: {progress_job.number_records_processed}")
    time.sleep(2)

print(f"\n✓ Final state: {progress_job.state}")
print(f"Total processed: {progress_job.number_records_processed}")

# Clean up
cleanup_ids = [{'Id': acc['Id']} for acc in sf.query("SELECT Id FROM Account WHERE Name LIKE 'Account %'")['records']]
if cleanup_ids:
    cleanup_job = sf.bulk.Account.delete(cleanup_ids)
    cleanup_job.wait_for_completion(poll_interval=2)
    print(f"Cleaned up {cleanup_job.number_records_processed} test records")

print("\n=== Bulk API Examples Complete ===")

