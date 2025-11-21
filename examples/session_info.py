"""Session info properties example."""

import datetime
import time

from forcepy import Salesforce

# Initialize client (auto-authenticates if username/password provided)
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

print("=== Session Info Properties ===\n")

# User ID
if sf.user_id:
    print(f"Logged in as user ID: {sf.user_id}")
else:
    print("User ID not available (may require userinfo endpoint access)")

# Session expiration
if sf.session_expires:
    expires = datetime.datetime.fromtimestamp(sf.session_expires)
    time_until_expiry = sf.session_expires - time.time()

    print(f"\nSession expires: {expires}")
    print(f"Time until expiry: {time_until_expiry / 60:.1f} minutes")

    # Check if session is about to expire
    if time_until_expiry < 300:  # 5 minutes
        print("⚠️  Session expiring soon! Consider re-authenticating.")
    else:
        print("✅ Session is still valid")
else:
    print("\nSession expiry not tracked")

# Last request time
print("\n=== Making API Request ===")
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 5")
print(f"Retrieved {len(accounts)} accounts")

if sf.last_request_time:
    last = datetime.datetime.fromtimestamp(sf.last_request_time)
    print(f"\nLast API request: {last}")
    print(f"Time since last request: {time.time() - sf.last_request_time:.2f} seconds")

# Debugging aid - check session health
print("\n=== Session Health Check ===")
print(f"Instance URL: {sf.instance_url}")
print(f"Is sandbox: {sf.is_sandbox}")
print(f"API version: {sf.version}")

if sf.session_expires and sf.last_request_time:
    session_age = time.time() - (sf.session_expires - 7200)  # Assuming 2-hour sessions
    print(f"Session age: {session_age / 60:.1f} minutes")

    # Calculate request frequency
    requests_per_minute = 1 / ((time.time() - sf.last_request_time) / 60)
    print(f"Approximate request rate: {requests_per_minute:.2f} requests/minute")

