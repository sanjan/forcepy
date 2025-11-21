"""JWT authentication example."""

from forcepy import Salesforce

# Path to your private key file
PRIVATE_KEY_PATH = "/path/to/your/private.key"

# Or private key content as string
PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...your private key here...
-----END RSA PRIVATE KEY-----
"""

# Initialize client
sf = Salesforce()

# Login with JWT
sf.login_with_jwt(
    client_id="your-connected-app-consumer-key",
    private_key=PRIVATE_KEY_PATH,  # or use PRIVATE_KEY variable
    username="your-username@example.com",
    audience="https://login.salesforce.com",  # or https://test.salesforce.com for sandbox
)

print(f"Logged in successfully!")
print(f"Instance URL: {sf.instance_url}")

# Now you can use the client normally
accounts = sf.query("SELECT Id, Name FROM Account LIMIT 5")
for account in accounts:
    print(f"Account: {account.Name}")

# Sandbox example
sf_sandbox = Salesforce()
sf_sandbox.login_with_jwt(
    client_id="your-connected-app-consumer-key",
    private_key=PRIVATE_KEY_PATH,
    username="your-username@example.com.sandboxname",
    audience="https://test.salesforce.com",
)

print(f"Logged into sandbox: {sf_sandbox.instance_url}")
