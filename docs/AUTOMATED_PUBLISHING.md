# Automated Publishing to PyPI

Guide to setting up automated publishing from GitHub to PyPI.

## Overview

We use **GitHub Actions + PyPI Trusted Publishing** for secure, automated releases.

**Benefits**:
- 🔒 No API tokens needed (more secure!)
- 🤖 Automatic publishing on GitHub releases
- ✅ Tests run before publishing
- 🚀 One-click releases

## Setup (One-Time Configuration)

### Step 1: Configure PyPI Trusted Publishing

1. **Go to PyPI**: https://pypi.org/manage/account/publishing/

2. **Add a new pending publisher**:
   - **PyPI Project Name**: `forcepy`
   - **Owner**: `sanjan`
   - **Repository name**: `forcepy`
   - **Workflow name**: `publish.yml`
   - **Environment name**: (leave empty)
   
3. Click **Add**

4. **Repeat for TestPyPI** (optional but recommended):
   - Go to: https://test.pypi.org/manage/account/publishing/
   - Same settings as above

### Step 2: Verify GitHub Actions Permissions

1. Go to: https://github.com/sanjan/forcepy/settings/actions
2. Under **Workflow permissions**, ensure:
   - ✅ "Read and write permissions" is selected
   - ✅ "Allow GitHub Actions to create and approve pull requests" is checked

## How to Publish

### Test Release (to TestPyPI)

```bash
# 1. Update version in pyproject.toml to include -rc
# Example: version = "0.1.0-rc1"

# 2. Commit and tag
git add pyproject.toml
git commit -m "Prepare v0.1.0-rc1"
git tag v0.1.0-rc1
git push origin v0.1.0-rc1

# 3. GitHub Actions automatically publishes to TestPyPI!
```

**Watch progress**: https://github.com/sanjan/forcepy/actions

**Verify**: https://test.pypi.org/project/forcepy/

### Production Release (to PyPI)

```bash
# 1. Update version in pyproject.toml (remove -rc)
# Example: version = "0.1.0"

# 2. Update CHANGELOG.md with release notes

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main
git push origin v0.1.0

# 4. Create GitHub Release
gh release create v0.1.0 \
  --title "forcepy v0.1.0" \
  --notes-file CHANGELOG.md

# 5. GitHub Actions automatically publishes to PyPI!
```

**Or create release via GitHub UI**:
1. Go to: https://github.com/sanjan/forcepy/releases/new
2. Choose tag: `v0.1.0`
3. Title: `forcepy v0.1.0`
4. Copy release notes from CHANGELOG.md
5. Click **Publish release**
6. ✨ Automatic publishing starts!

## Workflow Details

### What Happens on GitHub Release:

1. ✅ Checks out code
2. ✅ Installs dependencies
3. ✅ Runs full test suite (321 tests)
4. ✅ Builds distribution packages
5. ✅ Publishes to PyPI (using trusted publishing)
6. 🎉 Done!

### Manual Trigger (If Needed)

You can also trigger publishing manually:

1. Go to: https://github.com/sanjan/forcepy/actions
2. Select **Publish to PyPI** workflow
3. Click **Run workflow**
4. Choose branch (usually `main`)
5. Click **Run workflow**

## Troubleshooting

### "Publishing is not configured" error

**Cause**: Trusted publishing not set up on PyPI.

**Fix**: Complete Step 1 above. For first release, you may need to:
1. Publish manually once: `just publish`
2. Then configure trusted publishing
3. Future releases will be automatic

### "Workflow does not have required permission" error

**Cause**: GitHub Actions doesn't have OIDC permissions.

**Fix**: 
1. Go to repo Settings > Actions > General
2. Enable "Read and write permissions"
3. Re-run the workflow

### Tests fail during publishing

**Cause**: Code has failing tests.

**Fix**: 
1. Run tests locally: `just test`
2. Fix issues
3. Commit and push fixes
4. Create release again

### Want to skip tests?

Not recommended, but you can remove the test step from `.github/workflows/publish.yml`:

```yaml
# Comment out or remove:
# - name: Run tests
#   run: uv run pytest --cov=forcepy
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, backwards compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

**Pre-releases** (for TestPyPI):
- `0.1.0-rc1` - Release Candidate 1
- `0.1.0-rc2` - Release Candidate 2
- `0.1.0-alpha1` - Alpha release
- `0.1.0-beta1` - Beta release

## Security Benefits

**Trusted Publishing** is more secure than API tokens:

✅ No secrets stored in GitHub  
✅ Short-lived credentials (expires after each run)  
✅ Scoped to specific repository  
✅ Recommended by PyPI  
✅ Recommended by Python Packaging Authority (PyPA)

## Comparison: Manual vs Automated

| Feature | Manual (`just publish`) | Automated (GitHub Actions) |
|---------|------------------------|---------------------------|
| Setup complexity | ✅ Simple | ⚠️ One-time setup needed |
| Security | ⚠️ API token needed | ✅ No tokens needed |
| Speed | Fast | Depends on CI queue |
| Tests before publish | Manual | ✅ Automatic |
| Audit trail | Local only | ✅ Full GitHub history |
| Recommended for | Local dev, first release | Production releases |

## Best Practice Workflow

1. **Development**: Work on features, run `just test` frequently
2. **Release Candidate**: Tag as `v0.1.0-rc1`, auto-publish to TestPyPI
3. **Testing**: Install from TestPyPI, verify everything works
4. **Production**: Create GitHub Release, auto-publish to PyPI
5. **Verification**: Install from PyPI, verify installation

## Summary

**For your first release**: Use manual publishing (`just publish`)  
**For all future releases**: Set up trusted publishing and use GitHub Releases

This gives you a professional, secure, automated release pipeline! 🚀

