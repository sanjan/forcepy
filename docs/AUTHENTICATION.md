# forcepy Authentication Guide

Complete guide to authentication patterns in forcepy.

## Key Feature: Auto-Authentication

**forcepy** automatically authenticates when credentials are provided to the constructor, making authentication seamless and intuitive.

## Authentication Patterns

### Pattern 1: Auto-Authentication (Recommended)

```python
from forcepy import Salesforce

# Production org (default)
sf = Salesforce(
    username='user@example.com',
    password='password'
)

# With security token (required when connecting outside trusted IP ranges)
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

# Ready to use immediately!
accounts = sf.query("SELECT Id, Name FROM Account")
```

**Benefits:**
- Simple and intuitive
- Reduces boilerplate code
- Prevents forgot-to-authenticate errors
- Works with token caching automatically

**Security Token:**
When connecting to Salesforce from outside trusted IP ranges, you need to append your security token to your password. Forcepy makes this easy with a dedicated parameter:

```python
# Option 1: Separate security_token parameter (recommended - clearer)
sf = Salesforce(
    username='user@example.com',
    password='password',
    security_token='yourSecurityToken123'
)

# Option 2: Manually append to password (traditional approach)
sf = Salesforce(
    username='user@example.com',
    password='password' + 'yourSecurityToken123'
)
```

**How to get your security token:**
1. Log in to Salesforce
2. Go to **Setup** > **My Personal Information** > **Reset Security Token**
3. Click **Reset Security Token**
4. Check your email for the new token

### Pattern 2: Deferred Authentication

For scenarios where you need more control:

```python
from forcepy import Salesforce

# Create client without authenticating
sf = Salesforce()

# Authenticate later when needed
sf.login(username='user@example.com', password='password')

# Now ready to use
accounts = sf.query("SELECT Id FROM Account")
```

**Use cases:**
- Dynamic credential selection
- Conditional authentication
- Testing scenarios

### Pattern 3: JWT Authentication

For production environments and server-to-server integrations:

```python
from forcepy import Salesforce

# Create client first
sf = Salesforce()

# Authenticate with JWT Bearer Flow
sf.login_with_jwt(
    client_id='your-connected-app-client-id',
    private_key='/path/to/private.key',
    username='integration@company.com',
    audience='https://login.salesforce.com'  # or https://test.salesforce.com for sandbox
)

# Ready for API calls
accounts = sf.query("SELECT Id FROM Account")
```

**Requirements:**
- Install JWT dependencies: `pip install forcepy[jwt]`
- Configure Connected App in Salesforce
- Generate SSL certificate/key pair

**Benefits:**
- More secure than password authentication
- Certificate-based authentication
- Ideal for CI/CD and automated processes
- No password storage needed

## Authentication Methods Comparison

| Method | Use Case | Security | Setup Complexity |
|--------|----------|----------|------------------|
| **SOAP (username/password)** | Development, scripts | ⚠️ Moderate | ✅ Simple |
| **JWT Bearer Flow** | Production, CI/CD | ✅ High | ⚠️ Moderate |
| **OAuth2** | Web apps, user auth | ✅ High | ⚠️ Complex |

## Sandbox vs Production

Forcepy automatically detects sandbox environments:

```python
# Production
sf = Salesforce(
    username='user@example.com',
    password='password',
    base_url='https://login.salesforce.com'
)

# Sandbox
sf = Salesforce(
    username='user@example.com.sandbox',
    password='password',
    base_url='https://test.salesforce.com'
)

# Auto-detection from username
sf = Salesforce(
    username='user@example.com.sandbox',  # Automatically uses test.salesforce.com
    password='password'
)
```

## Token Caching

Forcepy includes automatic token caching to improve performance:

### Default (Memory Cache)

```python
# Automatic in-memory caching
sf = Salesforce(username='user@example.com', password='password')

# Second instance reuses cached token
sf2 = Salesforce(username='user@example.com', password='password')
# No API call made! Token reused from cache
```

### Redis Cache (Production)

```python
# Redis cache for multi-pod/container deployments
sf = Salesforce(
    username='user@example.com',
    password='password',
    cache_backend='redis',
    redis_url='redis://redis-service:6379',
    prefix='myapp:sf:'
)
```

### Disable Caching

```python
# Disable caching for testing
sf = Salesforce(
    username='user@example.com',
    password='password',
    cache_backend='null'
)
```

See [TOKEN_CACHING.md](TOKEN_CACHING.md) for detailed caching strategies.

## Best Practices

### ✅ Do

- **Use JWT in production** for better security
- **Enable token caching** to reduce API calls
- **Use environment variables** for credentials
- **Handle authentication errors** gracefully
- **Auto-detect sandbox** from username patterns

### ❌ Don't

- Don't hardcode credentials in code
- Don't commit credentials to version control
- Don't disable SSL verification in production
- Don't share session tokens between users
- Don't store passwords in plain text

## Environment Variables Pattern

```python
import os
from forcepy import Salesforce

sf = Salesforce(
    username=os.environ['SF_USERNAME'],
    password=os.environ['SF_PASSWORD'],
    base_url=os.environ.get('SF_BASE_URL', 'https://login.salesforce.com')
)
```

## Error Handling

```python
from forcepy import Salesforce
from forcepy.exceptions import AuthenticationError

try:
    sf = Salesforce(username='user@example.com', password='wrong_password')
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle error - retry, log, alert, etc.
```

## Session Management

Track session information for debugging:

```python
sf = Salesforce(username='user@example.com', password='password')

# Access session info
print(f"User ID: {sf.user_id}")
print(f"Session expires: {sf.session_expires}")
print(f"Last request: {sf.last_request_time}")
print(f"Instance URL: {sf.instance_url}")
print(f"Sandbox: {sf.is_sandbox}")
```

## JWT Setup Guide

### Step 1: Generate SSL Certificate

```bash
# Generate private key
openssl genrsa -out private.key 2048

# Generate certificate signing request
openssl req -new -key private.key -out request.csr

# Generate self-signed certificate
openssl x509 -req -days 365 -in request.csr -signkey private.key -out certificate.crt
```

### Step 2: Configure Connected App

1. In Salesforce Setup, go to App Manager
2. Create new Connected App
3. Enable OAuth Settings
4. Upload `certificate.crt`
5. Add OAuth scopes (api, refresh_token, etc.)
6. Save and note the Consumer Key (client_id)

### Step 3: Use in Code

```python
from forcepy import Salesforce

sf = Salesforce()
sf.login_with_jwt(
    client_id='3MVG9...consumer.key.here',
    private_key='private.key',  # Path to private key file
    username='integration@company.com'
)
```

## Testing Strategies

### Mock Authentication

```python
from unittest.mock import Mock, patch
from forcepy import Salesforce

# Mock authentication for tests
with patch.object(Salesforce, 'login'):
    sf = Salesforce(username='test@example.com', password='test')
    sf.session_id = 'mock_session_id'
    sf.instance_url = 'https://test.salesforce.com'
    
    # Run tests...
```

### Fixture-Based Authentication

```python
import pytest
from forcepy import Salesforce

@pytest.fixture
def sf_client():
    """Reusable Salesforce client for tests."""
    client = Salesforce(
        username='test@example.com',
        password='test_password',
        cache_backend='null'  # Disable caching in tests
    )
    yield client
    # Cleanup if needed

def test_query_accounts(sf_client):
    accounts = sf_client.query("SELECT Id FROM Account LIMIT 1")
    assert len(accounts.records) <= 1
```

## Advanced: Custom Authentication

For custom authentication flows:

```python
from forcepy import Salesforce

sf = Salesforce()

# Set session details manually
sf.session_id = 'your_session_id'
sf.instance_url = 'https://your-instance.salesforce.com'
sf.session.headers['Authorization'] = f'Bearer {sf.session_id}'

# Ready to use
accounts = sf.query("SELECT Id FROM Account")
```

## Troubleshooting

### "Invalid username, password, security token"

- Verify credentials are correct
- Check if security token is required (append to password)
- Ensure account is not locked
- Verify IP restrictions in Salesforce

### "JWT validation failed"

- Check certificate is uploaded to Connected App
- Verify client_id matches Consumer Key
- Ensure username exists and has access
- Check certificate hasn't expired

### "Session expired"

- Forcepy automatically handles this with token caching
- Check session_expires property
- Re-authenticate if needed

### Connection Issues

```python
# Increase timeout for slow connections
sf = Salesforce(
    username='user@example.com',
    password='password',
    timeout=60  # seconds
)

# Configure retries
sf = Salesforce(
    username='user@example.com',
    password='password',
    max_retries=5,
    retry_delay=10
)
```

## Related Documentation

- [Token Caching Guide](TOKEN_CACHING.md) - Caching strategies
- [Examples](../examples/jwt_auth.py) - JWT authentication example
- [API Reference](README.md) - Complete API documentation
