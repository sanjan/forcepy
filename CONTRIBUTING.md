# Contributing to forcepy

Thank you for your interest in contributing to forcepy! We welcome contributions from the community and are excited to have you involved.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/forcepy.git
   cd forcepy
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/sanjan/forcepy.git
   ```

## Development Setup

We use `uv` for dependency management and `just` for task running:

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install just (task runner)
brew install just  # Mac
cargo install just  # Any platform with Rust
# or download from https://github.com/casey/just/releases

# 3. Install project dependencies
just install-dev
# or manually: uv sync --all-extras

# 4. See all available commands
just --list
```

**No need to activate virtual environment** - `uv run` automatically uses the project's venv!

## Making Changes

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Add tests for new features
   - Update documentation as needed
   - Follow the code style guidelines (see below)

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```
   
   Write clear, descriptive commit messages. Good examples:
   - `Add support for Bulk API 2.0 queries`
   - `Fix token caching race condition in multi-threaded environments`
   - `Update authentication documentation with JWT examples`

## Code Style

### Python Code Standards

We use `ruff` for linting and formatting:

```bash
# Format code
uv run ruff format src/ tests/

# Check for linting issues
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/
```

### Code Style Guidelines

- **Follow PEP 8** Python style guide
- **Use type hints** for all function signatures
- **Write docstrings** for all public functions, classes, and methods
- **Keep functions focused** - one function, one purpose
- **Use descriptive names** - `calculate_annual_revenue()` not `calc_rev()`
- **Avoid magic numbers** - use named constants

### Type Hints

All code must include type hints:

```python
# Good
def query(self, soql: str, expand_select_star: bool = False) -> QueryResult:
    """Execute SOQL query."""
    pass

# Bad - missing type hints
def query(self, soql, expand_select_star=False):
    """Execute SOQL query."""
    pass
```

### Docstring Format

Use Google-style docstrings:

```python
def create_account(name: str, industry: str, annual_revenue: Optional[float] = None) -> dict[str, Any]:
    """Create a new Salesforce Account record.
    
    Args:
        name: Account name
        industry: Industry type
        annual_revenue: Optional annual revenue amount
        
    Returns:
        Dictionary with created account details including 'id'
        
    Raises:
        APIError: If account creation fails
        
    Example:
        >>> result = sf.create_account('Acme Corp', 'Technology', 1000000.0)
        >>> print(result['id'])
        '001xx000003DGbQQAW'
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just test-cov

# Quick test (minimal output)
just test-fast

# Run specific tests (pass args)
just test tests/test_query.py
just test tests/test_query.py::TestQObject::test_simple_q

# Or use uv directly if you prefer
uv run pytest
uv run pytest tests/test_query.py
```

### Writing Tests

- **Write tests for all new features**
- **Aim for high coverage** (we target 75%+)
- **Use descriptive test names**: `test_query_with_invalid_soql_raises_error`
- **Use fixtures** for common setup
- **Mock external API calls** - don't make real Salesforce API calls in tests

Example test:

```python
def test_q_object_with_and_operator():
    """Test Q object with AND operator."""
    q = Q(Industry='Technology') & Q(AnnualRevenue__gt=1000000)
    result = q.compile()
    
    assert "Industry = 'Technology'" in result
    assert "AnnualRevenue > 1000000" in result
    assert " AND " in result
```

### Test Coverage Requirements

- **New features**: Must include tests
- **Bug fixes**: Must include regression test
- **Minimum coverage**: 75% overall
- **Critical paths**: 90%+ coverage for authentication, query building, API calls

## Pull Request Process

1. **Update your branch** with latest upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run quality checks**:
   ```bash
   # Format code
   just format
   
   # Lint and fix issues
   just lint-fix
   
   # Type check
   just typecheck
   
   # Run all quality checks at once (recommended)
   just quality
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Go to https://github.com/sanjan/forcepy/pulls
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template with:
     - Clear description of changes
     - Motivation and context
     - Related issue numbers (if applicable)
     - Types of changes (bug fix, feature, docs, etc.)
     - Checklist items completed

5. **Address review feedback**:
   - Respond to review comments
   - Make requested changes
   - Push updates to your branch
   - Request re-review when ready

### PR Checklist

Before submitting, ensure:

- [ ] Code follows project style guidelines
- [ ] Code has been formatted with `ruff format`
- [ ] All linting issues resolved (`ruff check`)
- [ ] Type hints added and checked with `mypy`
- [ ] Tests added for new features
- [ ] All tests pass (`pytest`)
- [ ] Documentation updated (README, docstrings, guides)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

## Reporting Bugs

### Before Reporting

1. **Check existing issues** - your bug might already be reported
2. **Verify with latest version** - bug might be fixed
3. **Try to reproduce** - ensure bug is consistent

### Bug Report Template

Open an issue with:

- **Clear title**: "query() raises KeyError when result has no records"
- **Environment**:
  - forcepy version
  - Python version
  - Operating system
- **Steps to reproduce**:
  1. Do this
  2. Then do that
  3. Bug occurs
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Code sample**: Minimal reproducible example
- **Error message**: Full traceback if applicable

## Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing issues** - feature might be planned
2. **Open a discussion** before coding large features
3. **Provide use cases** - why is this feature useful?
4. **Consider scope** - keep features focused

### Feature Request Template

Open an issue with:

- **Clear title**: "Add support for Salesforce Bulk API 2.0"
- **Problem**: What problem does this solve?
- **Proposed solution**: How would this work?
- **Alternatives**: Other approaches considered?
- **Use cases**: Real-world examples

## Development Workflow

### Typical Workflow

```bash
# 1. Start with latest code
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/add-bulk-api

# 3. Make changes, test frequently
# ... code ...
just test tests/test_bulk.py

# 4. Commit incrementally
git add src/forcepy/bulk.py tests/test_bulk.py
git commit -m "Add Bulk API job creation"

# 5. Keep branch updated
git fetch upstream
git rebase upstream/main

# 6. Final quality check
just quality

# 7. Push and create PR
git push origin feature/add-bulk-api
```

### Tips for Success

- **Small, focused PRs** - easier to review and merge
- **Write tests first** - TDD helps design better APIs
- **Ask questions** - use Discussions for guidance
- **Be patient** - reviews take time
- **Stay positive** - we're all learning together!

## Recognition

Contributors will be:

- **Listed in AUTHORS.md** (coming soon)
- **Credited in release notes**
- **Recognized in project README**

Thank you for making forcepy better! 🎉

## Questions?

- **GitHub Discussions**: https://github.com/sanjan/forcepy/discussions
- **Issues**: https://github.com/sanjan/forcepy/issues
- **Email**: sgrero@salesforce.com

