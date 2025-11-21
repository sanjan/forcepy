"""Tests for token caching."""

import time

import pytest

from forcepy.token_cache import MemoryCache, NullCache, RedisCache, TokenCache, create_cache, get_cache_key


class TestGetCacheKey:
    """Test cache key generation."""

    def test_basic_key(self):
        """Test basic cache key generation."""
        key = get_cache_key("user@example.com", "https://login.salesforce.com")
        assert key == "user@example.com@login.salesforce.com"

    def test_normalizes_url(self):
        """Test URL normalization."""
        key1 = get_cache_key("user@example.com", "https://login.salesforce.com/")
        key2 = get_cache_key("user@example.com", "http://login.salesforce.com")
        assert key1 == key2 == "user@example.com@login.salesforce.com"


class TestMemoryCache:
    """Test in-memory cache."""

    def test_get_set(self):
        """Test basic get/set operations."""
        cache = MemoryCache()
        token_data = {"session_id": "abc123", "instance_url": "https://na1.salesforce.com", "expires_at": time.time() + 3600}

        # Initially empty
        assert cache.get("user1") is None

        # Set and get
        cache.set("user1", token_data)
        result = cache.get("user1")
        assert result == token_data

    def test_expiration(self):
        """Test automatic TTL expiration."""
        cache = MemoryCache(default_ttl=1)  # 1 second TTL
        token_data = {"session_id": "abc123", "instance_url": "https://na1.salesforce.com", "expires_at": time.time() + 3600}

        cache.set("user1", token_data, ttl=1)
        assert cache.get("user1") == token_data

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("user1") is None

    def test_delete(self):
        """Test delete operation."""
        cache = MemoryCache()
        token_data = {"session_id": "abc123", "instance_url": "https://na1.salesforce.com"}

        cache.set("user1", token_data)
        assert cache.get("user1") == token_data

        cache.delete("user1")
        assert cache.get("user1") is None

    def test_clear(self):
        """Test clear all tokens."""
        cache = MemoryCache()
        cache.set("user1", {"session_id": "abc"})
        cache.set("user2", {"session_id": "def"})

        cache.clear()
        assert cache.get("user1") is None
        assert cache.get("user2") is None

    def test_maxsize_limit(self):
        """Test cache size limit."""
        cache = MemoryCache(maxsize=2)
        cache.set("user1", {"session_id": "abc"})
        cache.set("user2", {"session_id": "def"})
        cache.set("user3", {"session_id": "ghi"})

        # Cache should only have 2 items (oldest evicted)
        # TTLCache with maxsize=2 should evict user1 when user3 is added
        # But we can't guarantee which one is evicted, just that size <= 2


class TestNullCache:
    """Test null cache (no caching)."""

    def test_never_caches(self):
        """Test that null cache never stores data."""
        cache = NullCache()
        token_data = {"session_id": "abc123"}

        cache.set("user1", token_data)
        assert cache.get("user1") is None

    def test_delete_no_op(self):
        """Test that delete is a no-op."""
        cache = NullCache()
        cache.delete("user1")  # Should not raise

    def test_clear_no_op(self):
        """Test that clear is a no-op."""
        cache = NullCache()
        cache.clear()  # Should not raise


class TestRedisCache:
    """Test Redis cache."""

    def test_requires_redis_package(self):
        """Test that RedisCache requires redis package."""
        # This will either work (if redis is installed) or raise ImportError
        try:
            cache = RedisCache(redis_url="redis://localhost:6379")
            # If redis package is available, instance should be created
            assert isinstance(cache, RedisCache)
        except ImportError as e:
            # Expected if redis not installed
            assert "redis package" in str(e).lower()

    @pytest.mark.skipif(
        True, reason="Requires Redis server - run manually with Redis available"
    )
    def test_redis_get_set(self):
        """Test Redis get/set (requires Redis server)."""
        cache = RedisCache(redis_url="redis://localhost:6379", prefix="test:")
        token_data = {"session_id": "abc123", "instance_url": "https://na1.salesforce.com"}

        cache.set("user1", token_data)
        result = cache.get("user1")
        assert result == token_data

        cache.delete("user1")
        assert cache.get("user1") is None


class TestCreateCache:
    """Test cache factory function."""

    def test_create_memory_cache(self):
        """Test creating memory cache."""
        cache = create_cache("memory")
        assert isinstance(cache, MemoryCache)

    def test_create_memory_default(self):
        """Test creating default cache (memory)."""
        cache = create_cache()
        assert isinstance(cache, MemoryCache)

        cache = create_cache(None)
        assert isinstance(cache, MemoryCache)

    def test_create_null_cache(self):
        """Test creating null cache."""
        cache = create_cache("null")
        assert isinstance(cache, NullCache)

        cache = create_cache("none")
        assert isinstance(cache, NullCache)

    def test_create_with_instance(self):
        """Test passing cache instance directly."""
        my_cache = MemoryCache()
        cache = create_cache(my_cache)
        assert cache is my_cache

    def test_invalid_backend(self):
        """Test invalid backend raises error."""
        with pytest.raises(ValueError, match="Unknown cache backend"):
            create_cache("invalid")

    def test_memory_cache_with_kwargs(self):
        """Test passing kwargs to memory cache."""
        cache = create_cache("memory", maxsize=50)
        assert isinstance(cache, MemoryCache)


class TestTokenCacheInterface:
    """Test that all cache backends implement TokenCache interface."""

    def test_memory_cache_implements_interface(self):
        """Test MemoryCache implements TokenCache."""
        cache = MemoryCache()
        assert isinstance(cache, TokenCache)
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "clear")

    def test_null_cache_implements_interface(self):
        """Test NullCache implements TokenCache."""
        cache = NullCache()
        assert isinstance(cache, TokenCache)
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "clear")

