# Token Caching in forcepy

Efficient authentication token management for Salesforce APIs.

## Overview

forcepy includes **automatic token caching** to:
- **Reduce API calls** to Salesforce authentication endpoints
- **Speed up initialization** by reusing valid session tokens  
- **Support production deployments** with Redis-backed shared caching
- **Work in read-only filesystems** (Kubernetes, containers)

### Key Benefits

✅ **Thread-safe** - Uses `cachetools.TTLCache` with automatic expiration  
✅ **Automatic** - Works out of the box with zero configuration  
✅ **Pluggable** - Swap backends for your environment  
✅ **Production-ready** - Redis support for multi-pod Kubernetes deployments

---

## Quick Start

### Default Behavior (Recommended)

```python
from forcepy import Salesforce

# First call - performs login, caches token
sf1 = Salesforce(username='user@example.com', password='password')

# Second call - reuses cached token (no API call!)
sf2 = Salesforce(username='user@example.com', password='password')

# Tokens are cached for 2 hours (Salesforce default)
```

**That's it!** Token caching works automatically with sensible defaults.

---

## Cache Backends

### 1. Memory Cache (Default) ⭐

In-memory cache using `cachetools.TTLCache`. Thread-safe, automatic expiration.

**Best for:**
- Development
- Single-process applications
- Kubernetes (single pod)
- CI/CD pipelines

```python
# Explicit (same as default)
sf = Salesforce(
    username='...',
    password='...',
    cache_backend='memory',
    maxsize=100  # Max tokens to cache (default: 100)
)
```

**Pros:**
- Zero external dependencies (just `cachetools`)
- Fast - in-process memory access
- Thread-safe with TTL
- Automatic cleanup

**Cons:**
- Lost on process restart
- Not shared across pods/processes

---

### 2. Redis Cache (Production) 🚀

Shared cache across multiple processes/pods using Redis.

**Best for:**
- Kubernetes multi-pod deployments
- Microservices
- High-traffic production environments
- Serverless functions (with Redis)

```python
sf = Salesforce(
    username='...',
    password='...',
    cache_backend='redis',
    redis_url='redis://redis-service:6379',
    prefix='myapp:sf:'  # Optional key prefix
)
```

**Kubernetes Example:**

```yaml
# k8s deployment with Redis cache
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

```python
import os
from forcepy import Salesforce

sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD'],
    cache_backend='redis',
    redis_url=os.environ['REDIS_URL']
)
```

**Pros:**
- Shared across all pods/processes
- Survives pod restarts
- Centralized token management
- Automatic expiration

**Cons:**
- Requires Redis deployment
- Network latency (minimal)

**Installation:**

```bash
pip install forcepy[redis]
# or
pip install redis
```

---

### 3. Null Cache (No Caching)

Disables caching entirely. Every login performs fresh authentication.

**Best for:**
- Testing
- Security-sensitive environments
- Very short-lived processes

```python
sf = Salesforce(
    username='...',
    password='...',
    cache_backend='null'
)
```

---

### 4. Custom Cache Backend

Implement your own cache for special requirements.

```python
from forcepy import TokenCache, Salesforce

class DatabaseCache(TokenCache):
    """Store tokens in PostgreSQL."""
    
    def get(self, key):
        # Fetch from database
        pass
    
    def set(self, key, value, ttl=7200):
        # Store in database
        pass
    
    def delete(self, key):
        # Delete from database
        pass
    
    def clear(self):
        # Clear all tokens
        pass

sf = Salesforce(
    username='...',
    password='...',
    cache_backend=DatabaseCache()
)
```

---

## Configuration Examples

### Development (Simple)

```python
# Use defaults
sf = Salesforce(username='dev@example.com', password='devpass')
```

### Kubernetes (Single Pod)

```python
# Memory cache works great
sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD']
)
```

### Kubernetes (Multiple Pods)

```python
# Redis for shared caching
sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD'],
    cache_backend='redis',
    redis_url=os.environ['REDIS_URL']
)
```

### CI/CD (Short-lived)

```python
# Consider disabling cache for very short runs
sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD'],
    cache_backend='null'
)
```

### Custom Cache Size

```python
# Limit memory usage
sf = Salesforce(
    username='...',
    password='...',
    cache_backend='memory',
    maxsize=50  # Cache only 50 tokens
)
```

---

## How It Works

### Cache Key Generation

Tokens are cached by `username@base_url`:

```python
# These get separate cache entries
sf1 = Salesforce(username='user@example.com', ...)  # user@example.com@login.salesforce.com
sf2 = Salesforce(username='admin@example.com', ...) # admin@example.com@login.salesforce.com
sf3 = Salesforce(username='user@example.com.sandbox', ...)  # user@example.com.sandbox@test.salesforce.com
```

### Token Lifetime

- Tokens cached for **2 hours** (Salesforce default)
- Automatic expiration via TTL
- Re-authentication on expiry

### Thread Safety

Memory cache uses `cachetools.TTLCache` which is thread-safe for:
- Concurrent reads
- Concurrent writes
- Automatic cleanup

---

## Advanced Usage

### Manual Cache Management

```python
sf = Salesforce(username='...', password='...')

# Access cache instance
cache = sf._token_cache

# Clear all cached tokens
cache.clear()

# Force re-authentication
sf.login()
```

### Cache Inspection

```python
from forcepy import Salesforce, MemoryCache

# Create with explicit cache
cache = MemoryCache(maxsize=100)
sf = Salesforce(username='...', password='...', cache_backend=cache)

# Inspect cache (for debugging)
print(f"Cache type: {type(sf._token_cache).__name__}")
```

### Custom Cache with Logging

```python
from forcepy import MemoryCache, Salesforce
import logging

logger = logging.getLogger(__name__)

class LoggingCache(MemoryCache):
    """Memory cache with detailed logging."""
    
    def get(self, key):
        result = super().get(key)
        logger.info(f"Cache {'HIT' if result else 'MISS'}: {key[:20]}...")
        return result
    
    def set(self, key, value, ttl=7200):
        logger.info(f"Caching token: {key[:20]}... (TTL: {ttl}s)")
        super().set(key, value, ttl)

sf = Salesforce(username='...', password='...', cache_backend=LoggingCache())
```

---

## Kubernetes Deployment Guide

### Option 1: Memory Cache (Single Pod)

**When to use:** Single replica deployments

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 1  # Single pod
  template:
    spec:
      containers:
      - name: app
        env:
        - name: SF_USER
          valueFrom:
            secretKeyRef:
              name: salesforce-creds
              key: username
        - name: SF_PASSWORD
          valueFrom:
            secretKeyRef:
              name: salesforce-creds
              key: password
```

```python
# app.py - memory cache works great
from forcepy import Salesforce
import os

sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD']
    # cache_backend='memory' is the default
)
```

### Option 2: Redis Cache (Multi-Pod)

**When to use:** Multiple replicas, shared caching

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

```yaml
# app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3  # Multiple pods share Redis cache
  template:
    spec:
      containers:
      - name: app
        env:
        - name: SF_USER
          valueFrom:
            secretKeyRef:
              name: salesforce-creds
              key: username
        - name: SF_PASSWORD
          valueFrom:
            secretKeyRef:
              name: salesforce-creds
              key: password
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

```python
# app.py - Redis cache for multi-pod
from forcepy import Salesforce
import os

sf = Salesforce(
    username=os.environ['SF_USER'],
    password=os.environ['SF_PASSWORD'],
    cache_backend='redis',
    redis_url=os.environ.get('REDIS_URL', 'redis://localhost:6379')
)
```

---

## Troubleshooting

### Issue: Token Not Cached

**Symptom:** Every call performs fresh login

**Causes:**
1. Different usernames/passwords
2. Cache disabled (`cache_backend='null'`)
3. Token expired (>2 hours old)

**Solution:**
```python
# Check cache type
print(f"Cache: {type(sf._token_cache).__name__}")

# Verify username consistency
print(f"Username: {sf.username}")
```

### Issue: Redis Connection Failed

**Symptom:** Falls back to fresh login on every call

**Causes:**
1. Redis not running
2. Wrong Redis URL
3. Network issues

**Solution:**
```python
# Test Redis connection
import redis
r = redis.from_url('redis://localhost:6379')
r.ping()  # Should return True

# Check logs for Redis errors
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Issue: Memory Usage Growing

**Symptom:** Memory usage increases over time

**Causes:**
1. Too many unique username/url combinations
2. Cache size too large

**Solution:**
```python
# Limit cache size
sf = Salesforce(
    username='...',
    password='...',
    cache_backend='memory',
    maxsize=50  # Reduce from default 100
)

# Or clear cache periodically
sf._token_cache.clear()
```

---

## Performance Impact

### Without Caching

- **Every login:** ~500-1000ms (API call to Salesforce)
- **100 logins:** ~50-100 seconds
- **Rate limit risk:** Frequent auth calls

### With Memory Cache

- **First login:** ~500-1000ms (initial auth)
- **Cached logins:** <1ms (in-memory lookup)
- **100 logins (same user):** ~1 second total
- **Rate limit risk:** Minimal

### With Redis Cache

- **First login (any pod):** ~500-1000ms
- **Cached logins:** ~5-10ms (Redis network)
- **Shared across pods:** All pods benefit
- **Rate limit risk:** Minimal

---

## Best Practices

✅ **Use default memory cache** for most applications  
✅ **Use Redis cache** in Kubernetes with multiple pods  
✅ **Don't disable caching** unless you have a specific reason  
✅ **Monitor cache hits** in production (add logging)  
✅ **Set appropriate maxsize** based on number of unique users  
✅ **Use secrets** for Redis URLs and credentials  
✅ **Test token expiration** in your integration tests

---

## Comparison with simple-salesforce

| Feature | forcepy | simple-salesforce |
|---------|---------|-------------------|
| Automatic caching | ✅ Default | ❌ No |
| In-memory cache | ✅ Thread-safe | ❌ Manual only |
| Redis cache | ✅ Built-in | ❌ No |
| Token expiration | ✅ Automatic | ❌ Manual |
| Pluggable backends | ✅ Yes | ❌ No |
| K8s-friendly | ✅ Yes | ⚠️ Requires workarounds |

---

## API Reference

### `TokenCache` (Abstract Base Class)

```python
class TokenCache(ABC):
    def get(self, key: str) -> Optional[dict]:
        """Get cached token."""
    
    def set(self, key: str, value: dict, ttl: int = 7200):
        """Cache token with TTL."""
    
    def delete(self, key: str):
        """Delete cached token."""
    
    def clear(self):
        """Clear all tokens."""
```

### `MemoryCache`

```python
MemoryCache(maxsize=100, default_ttl=7200)
```

### `RedisCache`

```python
RedisCache(
    redis_url='redis://localhost:6379',
    prefix='forcepy:token:',
    default_ttl=7200,
    **redis_kwargs
)
```

### `NullCache`

```python
NullCache()  # No arguments, no caching
```

---

## See Also

- [README.md](README.md) - Main documentation
- [examples/token_caching.py](examples/token_caching.py) - Full examples
- [tests/test_token_cache.py](tests/test_token_cache.py) - Test suite

