# forcepy - Modern Task Runner
# Install just: https://github.com/casey/just

# List all available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Install with all extras
install-dev:
    uv sync --all-extras

# Run tests
test *ARGS:
    uv run pytest {{ARGS}}

# Run tests with coverage
test-cov:
    uv run pytest --cov=forcepy --cov-report=html --cov-report=term

# Quick test
test-fast:
    uv run pytest -q --tb=short

# Lint code
lint:
    uv run ruff check src/ tests/

# Fix linting issues
lint-fix:
    uv run ruff check --fix src/ tests/

# Format code
format:
    uv run ruff format src/ tests/

# Check formatting
format-check:
    uv run ruff format --check src/ tests/

# Type check
typecheck:
    uv run mypy src/forcepy/

# Run all quality checks
quality: lint typecheck test-fast
    @echo "✅ All quality checks passed!"

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info
    rm -rf .pytest_cache .ruff_cache .mypy_cache
    rm -rf htmlcov .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Build package
build: clean
    uv build
    @ls -lh dist/

# Pre-release checks
pre-release: format lint typecheck test-cov build
    @echo "✅ Ready for release!"

# Publish to TestPyPI
publish-test: build
    uv run twine upload --repository testpypi dist/*

# Publish to PyPI
publish: build
    @echo "⚠️  Publishing to PyPI (PRODUCTION)"
    @echo "Press Ctrl+C to cancel..."
    @sleep 3
    uv run twine upload dist/*

# Run in watch mode for development
watch:
    uv run pytest-watch

# Show current version
version:
    @grep '^version = ' pyproject.toml | cut -d '"' -f 2

