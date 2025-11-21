# Changelog

All notable changes to forcepy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Streaming API integration
- Platform Events support
- Enhanced async/await patterns

## [0.1.2] - 2024-11-22

### Added
- Beautiful header image to README
- Modern, centered layout inspired by Agent Lightning
- Improved navigation with quick links

### Fixed
- Image now uses absolute GitHub URL for PyPI compatibility

## [0.1.1] - 2024-11-21

### Fixed
- Updated README to correctly show Bulk API 2.0 as available (not "Coming Soon")
- Updated comparison table to show Bulk API 2.0 support
- Corrected example count from 12 to 13 examples
- Added working Bulk API code examples to README

### Changed
- Code formatting improvements with ruff (24 files)
- Enhanced examples section with more detail

## [0.1.0] - 2024-11-21

### Added - Initial Release

#### Core Features
- **SOQL Query Support** - Full Salesforce Object Query Language support
- **Q Objects** - Build complex WHERE clauses with boolean logic (AND, OR, NOT)
- **Query Helpers** - IN(), DATE(), BOOL() functions for cleaner SOQL
- **Dot Notation Access** - Intuitive access to nested fields and relationships
- **Dynamic Endpoints** - Chain attributes to build API paths dynamically

#### Authentication & Security
- **SOAP Login** - Username/password authentication with auto-detection
- **JWT Bearer Flow** - Certificate-based authentication for production
- **OAuth2 Support** - Full OAuth 2.0 authentication flow
- **Auto-Authentication** - Automatic login when credentials provided
- **Token Caching** - Multiple backends (memory, Redis, null, custom)
- **Session Tracking** - Monitor user_id, session expiry, request times

#### Query & Data Operations
- **Client-Side Filtering** - filter(), exclude(), group_by(), order_by() on results
- **SELECT * Expansion** - Automatically expand queries to all fields
- **Manual Pagination** - Full control with query_more() and next_records_url
- **Threaded Iterquery** - Efficient pagination with background prefetching
- **Workbench URLs** - Generate shareable query links for debugging

#### Batch Operations
- **Composite API** - Batch up to 25 operations in single API call
- **Context Manager** - Pythonic `with` statement for automatic batching
- **Reference Support** - Link operations with @{referenceId} syntax
- **All-or-None Mode** - Atomic transaction support

#### Metadata & Schema
- **Cached Describe** - Fast metadata access with automatic caching
- **Field Information** - Required fields, picklist values, field properties
- **Dependent Picklists** - Filter picklist values by controlling field
- **Object Discovery** - List, filter, and explore Salesforce objects
- **Org Limits** - Check API usage and limits

#### Chatter Integration
- **Post to Feeds** - Post to user, group, and record feeds
- **@Mentions** - Tag users with @[userId] syntax
- **Entity Links** - Link records with $[recordId] syntax
- **HTML Formatting** - Bold, italic, underline, code formatting
- **Comments & Likes** - Full comment and like functionality
- **Feed Management** - Get, delete feed elements and comments

#### Performance & Reliability
- **Auto-Retry Logic** - Configurable retries on 503, 502, 500, 429 errors
- **UNABLE_TO_LOCK_ROW Handling** - Automatic retry on row locking conflicts
- **Exponential Backoff** - Smart retry timing to avoid rate limits
- **Connection Pooling** - Efficient HTTP session management
- **Request Tracking** - Monitor last request time for debugging

#### Developer Experience
- **Full Type Hints** - Complete type annotation for better IDE support
- **ID Utilities** - Compare 15/18 char IDs, determine object type from ID
- **Pretty Print** - Format SOQL queries for readability
- **Sobject Refresh** - Reload record from server
- **Sandbox Detection** - Auto-detect sandbox from username
- **Comprehensive Documentation** - Guides for all features
- **12 Code Examples** - Ready-to-run examples for common use cases

#### Testing
- **321 Tests** - Comprehensive test coverage
- **78% Code Coverage** - High confidence in code quality
- **Mock Support** - Easy testing with mocked clients
- **Fixtures** - Reusable test patterns

### Technical Details

#### Dependencies
- `requests>=2.25.0` - HTTP client
- `python-dateutil>=2.8.0` - Date/time handling
- `cachetools>=5.3.0` - Caching utilities

#### Optional Dependencies
- `PyJWT>=2.0.0` - JWT authentication (install with `pip install forcepy[jwt]`)
- `cryptography>=3.0.0` - Certificate handling for JWT
- `redis>=4.0.0` - Redis cache backend (install with `pip install forcepy[redis]`)

#### Python Support
- Python 3.9+
- Tested on Python 3.9, 3.10, 3.11, 3.12

#### Code Quality
- **Linting**: ruff with strict rules
- **Type Checking**: mypy in strict mode
- **Formatting**: ruff format
- **Testing**: pytest with coverage reporting

### Documentation

#### Guides Created
- README.md - Comprehensive getting started guide
- CONTRIBUTING.md - Contribution guidelines and development setup
- CHANGELOG.md - This file
- CODE_OF_CONDUCT.md - Community standards
- docs/AUTHENTICATION.md - Authentication patterns and best practices
- docs/TOKEN_CACHING.md - Token caching strategies
- docs/CHATTER_FEATURES.md - Chatter API reference
- docs/PUBLIC_LIBRARY_COMPARISON.md - Comparison with other libraries

#### Examples
- basic_query.py - Simple query operations
- advanced_query.py - Advanced query features
- advanced_filters.py - Client-side filtering
- jwt_auth.py - JWT authentication
- token_caching.py - Token caching examples
- composite_api.py - Batch operations
- context_manager.py - Context manager usage
- chatter_integration.py - Chatter features
- metadata_describe.py - Metadata operations
- object_discovery.py - Object discovery features
- session_info.py - Session tracking
- bulk_operations.py - Bulk API examples (coming in v0.2.0)

### Known Limitations

- **Bulk API**: Not yet implemented (coming in v0.2.0)
- **Streaming API**: Not yet implemented
- **Platform Events**: Not yet implemented
- **Reports API**: Limited support

### Migration Notes

This is the initial public release of forcepy, designed as a modern, professional Python client for Salesforce with comprehensive features and no external platform dependencies.

---

## Release Schedule

### v0.2.0 (Planned Q1 2025)
- Bulk API 2.0 support
- Enhanced async/await patterns
- Performance optimizations

### v0.3.0 (Planned Q2 2025)
- Streaming API support
- Platform Events integration
- Real-time data subscriptions

### v1.0.0 (Planned Q3 2025)
- Production-ready stable release
- Performance benchmarks
- Enterprise support options

---

## Links

- **GitHub Repository**: https://github.com/sanjan/forcepy
- **PyPI**: https://pypi.org/project/forcepy/
- **Documentation**: https://github.com/sanjan/forcepy/tree/main/docs
- **Issues**: https://github.com/sanjan/forcepy/issues
- **Discussions**: https://github.com/sanjan/forcepy/discussions

[Unreleased]: https://github.com/sanjan/forcepy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sanjan/forcepy/releases/tag/v0.1.0

