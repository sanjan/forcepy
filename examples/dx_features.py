"""
Developer Experience Features Examples

Demonstrates the convenience features that make working with forcepy easier:
- .first() and .last() convenience methods
- Case-insensitive filtering
- CSV export and import
"""

import io
from forcepy import Salesforce

# Initialize client (auto-authenticates)
sf = Salesforce(
    username="user@example.com",
    password="password",
    security_token="token"
)


def demo_convenience_methods():
    """Demonstrate .first() and .last() methods."""
    print("=== Convenience Methods Demo ===\n")
    
    # Query some accounts
    accounts = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 10")
    
    # Get first account (easier than accounts.records[0])
    first_account = accounts.records.first()
    print(f"First account: {first_account.Name}")
    
    # Get last account (easier than accounts.records[-1])
    last_account = accounts.records.last()
    print(f"Last account: {last_account.Name}")
    
    # Safe for empty results (returns None instead of IndexError)
    no_results = sf.query("SELECT Id FROM Account WHERE Name = 'DOESNOTEXIST'")
    first = no_results.records.first()  # Returns None, no error
    print(f"First of empty results: {first}")
    print()


def demo_case_insensitive_filtering():
    """Demonstrate case-insensitive filter lookups."""
    print("=== Case-Insensitive Filtering Demo ===\n")
    
    # Query all cases
    cases = sf.query("SELECT Id, Subject, Status, Priority FROM Case LIMIT 100")
    
    # Find urgent cases (case-insensitive)
    # Matches "urgent", "URGENT", "Urgent", etc.
    urgent_cases = cases.records.filter(Subject__icontains="urgent")
    print(f"Found {len(urgent_cases)} urgent cases:")
    for case in urgent_cases[:5]:
        print(f"  - {case.Subject}")
    
    # Find all "new" cases regardless of capitalization
    # Matches "New", "NEW", "new", etc.
    new_cases = cases.records.filter(Status__iexact="new")
    print(f"\nFound {len(new_cases)} new cases")
    
    # Case-insensitive startswith
    api_questions = cases.records.filter(Subject__istartswith="api")
    print(f"\nFound {len(api_questions)} cases starting with 'API'")
    
    # Case-insensitive endswith
    bug_reports = cases.records.filter(Subject__iendswith="bug")
    print(f"Found {len(bug_reports)} bug reports")
    print()


def demo_csv_export():
    """Demonstrate CSV export functionality."""
    print("=== CSV Export Demo ===\n")
    
    # Query accounts
    accounts = sf.query("SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 20")
    
    # Export to CSV string
    csv_string = accounts.records.to_csv()
    print("CSV Output (first 200 chars):")
    print(csv_string[:200] + "...\n")
    
    # Export to file
    accounts.records.to_csv("accounts_export.csv")
    print("Exported to accounts_export.csv")
    print()


def demo_csv_import():
    """Demonstrate CSV import functionality."""
    print("=== CSV Import Demo ===\n")
    
    # Import from file
    from forcepy.results import ResultSet
    accounts = ResultSet.from_csv("accounts_export.csv")
    print(f"Loaded {len(accounts)} accounts from CSV")
    print(f"First account: {accounts.first().Name}")
    
    # Import from string
    csv_data = """Id,Name,Industry
001xxx000001AAA,Acme Corp,Technology
001xxx000001AAB,Globe Inc,Finance"""
    
    accounts_from_string = ResultSet.from_csv(csv_data)
    print(f"\nLoaded {len(accounts_from_string)} accounts from string")
    for account in accounts_from_string:
        print(f"  - {account.Name} ({account.Industry})")
    
    # Import from StringIO (file-like object)
    csv_buffer = io.StringIO(csv_data)
    accounts_from_buffer = ResultSet.from_csv(csv_buffer)
    print(f"\nLoaded {len(accounts_from_buffer)} accounts from buffer")
    print()


def demo_combined_workflow():
    """Demonstrate combining multiple DX features."""
    print("=== Combined Workflow Demo ===\n")
    
    # Query opportunities
    opps = sf.query("""
        SELECT Id, Name, StageName, Amount, CloseDate 
        FROM Opportunity 
        WHERE CloseDate = THIS_QUARTER
    """)
    
    # Filter for closed won opportunities (case-insensitive)
    won_opps = opps.records.filter(StageName__iexact="closed won")
    
    # Get the first and last won opportunity
    first_win = won_opps.first()
    last_win = won_opps.last()
    
    if first_win:
        print(f"First win: {first_win.Name} - ${first_win.Amount}")
    if last_win:
        print(f"Last win: {last_win.Name} - ${last_win.Amount}")
    
    # Export won opportunities to CSV for reporting
    won_opps.to_csv("quarterly_wins.csv")
    print(f"\nExported {len(won_opps)} won opportunities to CSV")
    
    # Filter for opportunities with "enterprise" in name (case-insensitive)
    enterprise_opps = opps.records.filter(Name__icontains="enterprise")
    print(f"Found {len(enterprise_opps)} enterprise opportunities")
    
    # Get the biggest enterprise deal
    if enterprise_opps:
        biggest = enterprise_opps.order_by("Amount", asc=False).first()
        print(f"Biggest enterprise deal: {biggest.Name} - ${biggest.Amount}")
    print()


def demo_csv_round_trip():
    """Demonstrate CSV export and import round-trip."""
    print("=== CSV Round-Trip Demo ===\n")
    
    # Query contacts
    contacts = sf.query("SELECT Id, FirstName, LastName, Email FROM Contact LIMIT 10")
    print(f"Original: {len(contacts.records)} contacts")
    
    # Export to CSV
    csv_output = contacts.records.to_csv()
    
    # Import back from CSV
    from forcepy.results import ResultSet
    reimported = ResultSet.from_csv(csv_output)
    print(f"Reimported: {len(reimported)} contacts")
    
    # Verify data preserved
    original_first = contacts.records.first()
    reimported_first = reimported.first()
    
    print(f"\nOriginal first contact: {original_first.FirstName} {original_first.LastName}")
    print(f"Reimported first contact: {reimported_first.FirstName} {reimported_first.LastName}")
    print("Data preserved: ✓" if original_first.Email == reimported_first.Email else "Data lost: ✗")
    print()


if __name__ == "__main__":
    print("\nforcepy Developer Experience Features Demo")
    print("=" * 50)
    print()
    
    try:
        demo_convenience_methods()
        demo_case_insensitive_filtering()
        demo_csv_export()
        demo_csv_import()
        demo_combined_workflow()
        demo_csv_round_trip()
        
        print("\n" + "=" * 50)
        print("All demos completed successfully!")
        
    except Exception as e:
        print(f"\nError running demos: {e}")
        print("Note: You need valid Salesforce credentials to run these examples")

