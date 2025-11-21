"""Token caching examples for forcepy.

Demonstrates different caching backends for efficient authentication.
"""

from forcepy import MemoryCache, NullCache, Salesforce

print("=== Token Caching Examples ===\n")

# Example 1: Default (In-Memory Caching)
print("1. Default In-Memory Caching (Recommended)")
print("-" * 50)

# First call - performs login and caches token
sf1 = Salesforce(username="user@example.com", password="password123")
print("✓ First login - token cached in memory")

# Second call with same credentials - reuses cached token
sf2 = Salesforce(username="user@example.com", password="password123")
print("✓ Second login - token reused from cache (no API call!)")

# Third call with different credentials - new login
sf3 = Salesforce(username="other@example.com", password="password456")
print("✓ Different user - new login performed\n")

# Example 2: Disable Caching
print("2. Disable Token Caching")
print("-" * 50)

sf_no_cache = Salesforce(username="user@example.com", password="password123", cache_backend="null")
print("✓ Always performs fresh login (no caching)")

# Or explicitly pass NullCache
sf_no_cache2 = Salesforce(username="user@example.com", password="password123", cache_backend=NullCache())
print("✓ Explicit NullCache instance\n")

# Example 3: Custom Cache Size
print("3. Custom Memory Cache Size")
print("-" * 50)

sf_custom = Salesforce(username="user@example.com", password="password123", cache_backend="memory", maxsize=50)
print("✓ Memory cache limited to 50 tokens\n")

# Example 4: Redis Cache (Production)
print("4. Redis Cache (Multi-Pod/Production)")
print("-" * 50)

try:
    sf_redis = Salesforce(
        username="user@example.com",
        password="password123",
        cache_backend="redis",
        redis_url="redis://redis-service:6379",
        prefix="myapp:sf:",
    )
    print("✓ Token cached in Redis (shared across pods)")
except ImportError:
    print("⚠ Redis cache requires: pip install redis")
    print("  Or: pip install forcepy[redis]")
print()

# Example 5: Custom Cache Backend
print("5. Custom Cache Backend")
print("-" * 50)


# Implement your own cache
class MyCustomCache(MemoryCache):
    """Custom cache with logging."""

    def get(self, key):
        print(f"  → Cache lookup: {key[:20]}...")
        result = super().get(key)
        print(f"  → {'Hit' if result else 'Miss'}")
        return result

    def set(self, key, value, ttl=7200):
        print(f"  → Caching token: {key[:20]}... (TTL: {ttl}s)")
        super().set(key, value, ttl)


sf_custom_backend = Salesforce(username="user@example.com", password="password123", cache_backend=MyCustomCache())
print("✓ Custom cache with logging\n")

# Example 6: Manual Token Management
print("6. Manual Token Management")
print("-" * 50)

# Get initial connection
sf = Salesforce(username="user@example.com", password="password123")

# Extract session info
session_info = {"session_id": sf.session_id, "instance_url": sf.instance_url}

print(f"Session ID: {session_info['session_id'][:20]}...")
print(f"Instance: {session_info['instance_url']}")

# Reuse session manually (e.g., pass to another process)
sf_reused = Salesforce(session_id=session_info["session_id"], instance_url=session_info["instance_url"])
print("✓ Session reused manually\n")

# Example 7: Cache Behavior in Different Environments
print("7. Environment-Specific Patterns")
print("-" * 50)

print("Development:")
print("  - Use default memory cache")
print("  - Fast, simple, no dependencies")
print("  sf = Salesforce(username='...', password='...')")

print("\nKubernetes (read-only filesystem):")
print("  - Use memory cache (default) for single pod")
print("  - Use Redis cache for multi-pod")
print("  sf = Salesforce(..., cache_backend='redis', redis_url='redis://...')")

print("\nCI/CD (short-lived):")
print("  - Consider disabling cache if very short-lived")
print("  sf = Salesforce(..., cache_backend='null')")

print("\nProduction (multi-pod):")
print("  - Use Redis for shared caching")
print("  - Reduces auth API calls across fleet")
print("  sf = Salesforce(..., cache_backend='redis')\n")

# Example 8: Cache Inspection
print("8. Cache Inspection")
print("-" * 50)

sf = Salesforce(username="user@example.com", password="password123")

# Access the cache instance
cache = sf._token_cache
print(f"Cache type: {type(cache).__name__}")

# Clear cache if needed
cache.clear()
print("✓ Cache cleared")

# Force re-authentication
sf.login()
print("✓ Fresh login performed\n")

print("=== Best Practices ===")
print("-" * 50)
print("✓ Default memory cache works for most use cases")
print("✓ Use Redis cache in Kubernetes multi-pod deployments")
print("✓ Tokens are cached for 2 hours (Salesforce default)")
print("✓ Cache is automatic - no manual management needed")
print("✓ Thread-safe by default (uses cachetools.TTLCache)")
print("\nDone!")

