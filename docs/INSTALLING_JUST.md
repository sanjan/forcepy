# Installing just

Quick guide to installing the `just` command runner on different platforms.

## What is just?

`just` is a modern command runner (like Make but better) that we use for development tasks. It's cross-platform, fast, and has a simple syntax.

- **Website**: https://github.com/casey/just
- **Documentation**: https://just.systems/

## Installation

### macOS (Homebrew)

```bash
brew install just
```

### Linux

**Using Homebrew on Linux**:
```bash
brew install just
```

**Using cargo (Rust)**:
```bash
cargo install just
```

**Debian/Ubuntu (from package)**:
```bash
wget -qO - 'https://proget.makedeb.org/debian-feeds/prebuilt-mpr.pub' | gpg --dearmor | sudo tee /usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg 1> /dev/null
echo "deb [arch=all,$(dpkg --print-architecture) signed-by=/usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg] https://proget.makedeb.org prebuilt-mpr $(lsb_release -cs)" | sudo tee /etc/apt/sources.list.d/prebuilt-mpr.list
sudo apt update
sudo apt install just
```

### Windows

**Using Scoop**:
```bash
scoop install just
```

**Using Chocolatey**:
```bash
choco install just
```

**Using cargo (Rust)**:
```bash
cargo install just
```

### Any Platform (Binary Download)

Download pre-built binaries from the releases page:

1. Go to: https://github.com/casey/just/releases
2. Download the binary for your platform
3. Extract and add to your PATH

**Example for macOS/Linux**:
```bash
# Download (replace version and platform as needed)
wget https://github.com/casey/just/releases/download/1.25.2/just-1.25.2-x86_64-unknown-linux-musl.tar.gz

# Extract
tar -xzf just-*.tar.gz

# Move to PATH
sudo mv just /usr/local/bin/

# Verify
just --version
```

## Verify Installation

```bash
just --version
```

You should see something like: `just 1.25.2`

## Quick Start

Once installed, navigate to the forcepy directory and run:

```bash
# See all available commands
just --list

# Run tests
just test

# Run all quality checks
just quality

# See help for a specific command
just --show test
```

## Alternative: Use uv directly

If you prefer not to install `just`, you can always use `uv run` commands directly:

```bash
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/forcepy/
```

But we recommend `just` for a better developer experience! 🚀

