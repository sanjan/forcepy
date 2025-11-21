"""Token caching for Salesforce authentication.

Provides pluggable cache backends for session token persistence:
- TTLCache (default): In-memory cache with TTL, thread-safe
- RedisCache: Shared cache across processes/pods (requires redis package)
- NullCache: No caching (always re-authenticate)
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class TokenCache(ABC):
    """Abstract base class for token cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get cached token data.

        Args:
            key: Cache key (typically username)

        Returns:
            Dict with session_id, instance_url, expires_at, or None if not cached
        """
        pass

    @abstractmethod
    def set(self, key: str, value: dict[str, Any], ttl: int = 7200) -> None:
        """Cache token data.

        Args:
            key: Cache key (typically username)
            value: Dict with session_id, instance_url, expires_at
            ttl: Time to live in seconds (default: 2 hours)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete cached token.

        Args:
            key: Cache key to delete
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached tokens."""
        pass


class MemoryCache(TokenCache):
    """In-memory token cache using TTLCache (thread-safe, automatic expiration).

    This is the default cache backend. Tokens are stored in memory and
    automatically expire after the TTL. Cache is lost on process restart.

    Good for: Single process, development, testing
    """

    def __init__(self, maxsize: int = 100, default_ttl: int = 7200):
        """Initialize memory cache.

        Args:
            maxsize: Maximum number of tokens to cache (default: 100)
            default_ttl: Default TTL in seconds (default: 2 hours)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get cached token data."""
        try:
            value = self._cache.get(key)
            if value:
                logger.debug(f"Cache hit for key: {self._hash_key(key)}")
                return value
            logger.debug(f"Cache miss for key: {self._hash_key(key)}")
            return None
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
            return None

    def set(self, key: str, value: dict[str, Any], ttl: int = 7200) -> None:
        """Cache token data."""
        try:
            # TTLCache handles expiration automatically
            self._cache[key] = value
            logger.debug(f"Cached token for key: {self._hash_key(key)} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")

    def delete(self, key: str) -> None:
        """Delete cached token."""
        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache key: {self._hash_key(key)}")
        except Exception as e:
            logger.warning(f"Error deleting from cache: {e}")

    def clear(self) -> None:
        """Clear all cached tokens."""
        self._cache.clear()
        logger.debug("Cleared all cached tokens")

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash key for logging (don't log usernames)."""
        return hashlib.sha256(key.encode()).hexdigest()[:8]


class NullCache(TokenCache):
    """No-op cache that never stores tokens.

    Use this to disable caching entirely. Every authentication will
    result in a fresh login to Salesforce.

    Good for: Testing, security-sensitive environments
    """

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Always returns None (no cache)."""
        return None

    def set(self, key: str, value: dict[str, Any], ttl: int = 7200) -> None:
        """No-op (doesn't cache)."""
        pass

    def delete(self, key: str) -> None:
        """No-op (nothing to delete)."""
        pass

    def clear(self) -> None:
        """No-op (nothing to clear)."""
        pass


class RedisCache(TokenCache):
    """Redis-backed token cache for shared caching across processes/pods.

    Requires the `redis` package to be installed.

    Good for: Production, multiple pods, Kubernetes deployments
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "forcepy:token:",
        default_ttl: int = 7200,
        **redis_kwargs: Any,
    ):
        """Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for all cached tokens
            default_ttl: Default TTL in seconds (default: 2 hours)
            **redis_kwargs: Additional arguments for redis.from_url()

        Raises:
            ImportError: If redis package not installed
        """
        try:
            import redis
        except ImportError as e:
            raise ImportError(
                "Redis cache requires the redis package. Install with: pip install redis or pip install forcepy[redis]"
            ) from e

        self._client = redis.from_url(redis_url, decode_responses=True, **redis_kwargs)
        self._prefix = prefix
        self._default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get cached token data from Redis."""
        try:
            value = self._client.get(self._make_key(key))
            if value:
                logger.debug(f"Redis cache hit for key: {self._hash_key(key)}")
                return json.loads(value)
            logger.debug(f"Redis cache miss for key: {self._hash_key(key)}")
            return None
        except Exception as e:
            logger.warning(f"Error reading from Redis: {e}")
            return None

    def set(self, key: str, value: dict[str, Any], ttl: int = 7200) -> None:
        """Cache token data in Redis."""
        try:
            redis_key = self._make_key(key)
            self._client.setex(redis_key, ttl or self._default_ttl, json.dumps(value))
            logger.debug(f"Cached token in Redis for key: {self._hash_key(key)} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Error writing to Redis: {e}")

    def delete(self, key: str) -> None:
        """Delete cached token from Redis."""
        try:
            self._client.delete(self._make_key(key))
            logger.debug(f"Deleted Redis cache key: {self._hash_key(key)}")
        except Exception as e:
            logger.warning(f"Error deleting from Redis: {e}")

    def clear(self) -> None:
        """Clear all cached tokens (with prefix)."""
        try:
            # Scan for all keys with our prefix
            for key in self._client.scan_iter(match=f"{self._prefix}*"):
                self._client.delete(key)
            logger.debug("Cleared all cached tokens from Redis")
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash key for logging (don't log usernames)."""
        return hashlib.sha256(key.encode()).hexdigest()[:8]


def create_cache(backend: Optional[str | TokenCache] = None, **kwargs: Any) -> TokenCache:
    """Create a token cache backend.

    Args:
        backend: Cache backend type or instance:
            - None or "memory": In-memory cache (default)
            - "null" or "none": No caching
            - "redis": Redis-backed cache
            - TokenCache instance: Use provided cache
        **kwargs: Additional arguments for cache backend

    Returns:
        TokenCache instance

    Example:
        >>> cache = create_cache("memory", maxsize=200)
        >>> cache = create_cache("redis", redis_url="redis://redis:6379")
        >>> cache = create_cache()  # Uses default memory cache
    """
    if isinstance(backend, TokenCache):
        return backend

    backend_str = (backend or "memory").lower()

    if backend_str in ("memory", "default"):
        return MemoryCache(**kwargs)
    elif backend_str in ("null", "none", "disabled"):
        return NullCache()
    elif backend_str == "redis":
        return RedisCache(**kwargs)
    else:
        raise ValueError(
            f"Unknown cache backend: {backend}. Valid options: 'memory', 'null', 'redis', or a TokenCache instance"
        )


def get_cache_key(username: str, base_url: str) -> str:
    """Generate cache key from username and base URL.

    Args:
        username: Salesforce username
        base_url: Salesforce base URL

    Returns:
        Cache key string
    """
    # Normalize base URL (remove protocol and trailing slash)
    base_url = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    return f"{username}@{base_url}"
