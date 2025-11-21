# Publishing forcepy to PyPI

Complete guide to publishing forcepy to the Python Package Index.

## Prerequisites

### 1. Create PyPI Accounts

- **PyPI (Production)**: https://pypi.org/account/register/
- **TestPyPI (Testing)**: https://test.pypi.org/account/register/

### 2. Create API Tokens

After registering, create API tokens for authentication:

1. **TestPyPI Token**:
   - Go to: https://test.pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "forcepy-test"
   - Scope: "Entire account" (or specific to forcepy once published)
   - Copy and save the token (starts with `pypi-`)

2. **PyPI Token**:
   - Go to: https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "forcepy"
   - Scope: "Entire account" (or specific to forcepy once published)
   - Copy and save the token

### 3. Configure Credentials

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

**Important**: Never commit this file! Add `~/.pypirc` to your global gitignore.

## Publishing Process

### Step 1: Pre-Release Checklist

Run comprehensive checks before publishing:

```bash
just pre-release
```

This will:
- ✅ Format code with ruff
- ✅ Run linting checks
- ✅ Run type checking
- ✅ Run full test suite with coverage
- ✅ Build distribution packages

**Manual checks**:
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Ensure all tests pass (321 tests)
- [ ] Verify coverage is ≥78%
- [ ] Check README looks good
- [ ] Verify no internal references (sfdcutils, etc.)
- [ ] All GitHub URLs point to correct repo

### Step 2: Test on TestPyPI

Always test on TestPyPI first:

```bash
just publish-test
```

This will:
1. Clean old builds
2. Build fresh distribution
3. Upload to TestPyPI

**Verify the test upload**:

```bash
# View on TestPyPI
open https://test.pypi.org/project/forcepy/

# Test installation in a clean environment
python -m venv test-env
source test-env/bin/activate
pip install --index-url https://test.pypi.org/simple/ forcepy

# Test it works
python -c "from forcepy import Salesforce; print('✅ Import successful')"

# Deactivate and clean up
deactivate
rm -rf test-env
```

### Step 3: Publish to Production PyPI

Once TestPyPI looks good:

```bash
just publish
```

This will:
1. Clean old builds
2. Build fresh distribution
3. Prompt for confirmation (safety check)
4. Upload to production PyPI

**Alternative**: Manual publish with twine:

```bash
# Build
just build

# Upload to PyPI
uv run twine upload dist/*

# Or specify repository
uv run twine upload --repository pypi dist/*
```

### Step 4: Verify Production Release

```bash
# View on PyPI
open https://pypi.org/project/forcepy/

# Test installation
pip install forcepy

# Verify it works
python -c "from forcepy import Salesforce; print('✅ forcepy installed!')"
```

### Step 5: Create GitHub Release

1. Tag the release:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

2. Create GitHub release:
   - Go to: https://github.com/sanjan/forcepy/releases/new
   - Select tag: v0.1.0
   - Title: "forcepy v0.1.0"
   - Copy release notes from CHANGELOG.md
   - Attach distribution files from `dist/`
   - Publish release

## Quick Reference

### Common Commands

```bash
# Install dev dependencies
just install-dev

# Run all quality checks
just quality

# Pre-release checks
just pre-release

# Test publish
just publish-test

# Production publish
just publish

# Clean builds
just clean

# View version
just version

# See all commands
just --list
```

### Version Bumping

Update version in `pyproject.toml`:

```toml
[project]
name = "forcepy"
version = "0.1.0"  # ← Update this
```

Version scheme (Semantic Versioning):
- **Patch** (0.1.0 → 0.1.1): Bug fixes, no breaking changes
- **Minor** (0.1.0 → 0.2.0): New features, no breaking changes
- **Major** (0.1.0 → 1.0.0): Breaking changes

### Troubleshooting

#### "403 Forbidden" error
- Check your API token is correct in `~/.pypirc`
- Ensure token has correct permissions
- For first upload, use account-wide token

#### "400 Bad Request: File already exists"
- Version already published to PyPI
- Bump version number in `pyproject.toml`
- Rebuild with `make build`

#### "Invalid distribution file"
- Clean and rebuild: `make clean && make build`
- Check `pyproject.toml` syntax

#### Package name already taken
- Choose a different name
- Check availability: https://pypi.org/project/YOUR_NAME/

## Security Best Practices

1. **Never commit credentials**
   - Add `~/.pypirc` to global gitignore
   - Never commit API tokens to git

2. **Use API tokens, not passwords**
   - Tokens are more secure
   - Can be scoped to specific packages
   - Can be revoked easily

3. **Limit token scope**
   - After first publish, create package-specific token
   - Update `~/.pypirc` with scoped token

4. **Enable 2FA**
   - Enable two-factor authentication on PyPI account
   - Protects against unauthorized access

## Post-Release Checklist

After successful release:

- [ ] Verify package on PyPI: https://pypi.org/project/forcepy/
- [ ] Test pip install: `pip install forcepy`
- [ ] Create GitHub release with tag
- [ ] Update documentation with new version
- [ ] Announce on relevant channels (Twitter, Reddit, etc.)
- [ ] Close milestone on GitHub (if applicable)
- [ ] Start next version in CHANGELOG.md

## Release Schedule

Based on planned roadmap:

- **v0.1.0** - Initial release (current)
- **v0.2.0** - Bulk API 2.0 (Q1 2025)
- **v0.3.0** - Streaming API (Q2 2025)
- **v1.0.0** - Stable release (Q3 2025)

## Support

Questions about publishing?
- **Documentation**: https://packaging.python.org/
- **PyPI Help**: https://pypi.org/help/
- **Issues**: https://github.com/sanjan/forcepy/issues

