# Contributing to phi-redactor

Thank you for your interest in contributing to phi-redactor! This project helps healthcare organizations safely use LLMs without risking PHI exposure, and every contribution makes that mission stronger.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)
- [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your changes
4. **Make your changes** with tests
5. **Submit a pull request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/phi-redactor.git
cd phi-redactor

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Download the spaCy model
python -m spacy download en_core_web_lg

# Verify everything works
pytest
```

### Requirements

- Python 3.11+
- Git

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feat/add-azure-adapter` — new features
- `fix/vault-session-cleanup` — bug fixes
- `docs/improve-quickstart` — documentation
- `test/add-streaming-tests` — test additions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(detection): add custom recognizer for DEA numbers
fix(vault): prevent FK constraint error on session creation
test(proxy): add streaming round-trip tests for Anthropic
docs: update API endpoint table in README
```

## Pull Request Process

1. **Update tests** — all new features need tests; bug fixes need regression tests
2. **Run the full test suite** — `pytest` must pass
3. **Run linting** — `ruff check src/ tests/` must pass
4. **Run formatting** — `ruff format src/ tests/`
5. **Update documentation** if your change affects the public API or CLI
6. **Keep PRs focused** — one feature or fix per PR; avoid unrelated changes
7. **Fill out the PR template** — describe what changed and why

### PR Review Criteria

- All CI checks pass (tests on Python 3.11, 3.12, 3.13)
- No decrease in test coverage for changed files
- Code follows existing patterns and conventions
- PHI safety invariants are preserved (see below)

## Code Standards

### PHI Safety Invariants

These are **non-negotiable** — any PR that violates these will be rejected:

1. **PHI must never be logged** — use the PHI-safe log formatter
2. **PHI must never leave the local machine unredacted** — fail-safe: block, never leak
3. **Vault entries must be encrypted at rest** — Fernet encryption required
4. **Audit trail must be append-only** — hash-chain integrity must be preserved
5. **Sessions must be isolated** — no cross-session data leakage

### Style

- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type hints**: Use type annotations for all public functions
- **Docstrings**: Required for public APIs; use Google style

### Project Structure

```
src/phi_redactor/
├── detection/      # PHI detection engine and recognizers
├── masking/        # Semantic masking and identity generation
├── vault/          # Encrypted storage for PHI mappings
├── proxy/          # FastAPI reverse proxy and adapters
├── audit/          # Tamper-evident audit trail
├── cli/            # Click-based CLI commands
├── dashboard/      # Real-time monitoring web UI
├── plugins/        # Plugin loader and examples
├── config.py       # Configuration management
└── models.py       # Shared data models
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_detection.py

# Run tests matching a pattern
pytest -k "test_ssn"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use `pytest` fixtures for shared setup
- Use `pytest-asyncio` for async tests
- Use `pytest-httpx` for HTTP mocking
- Test both happy paths and error cases
- For PHI detection tests, include realistic but synthetic examples

## Reporting Issues

### Bug Reports

Use the [bug report template](https://github.com/DilawarShafiq/phi-redactor/issues/new?template=bug_report.yml) and include:

- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (ensure no real PHI is included!)

### Feature Requests

Use the [feature request template](https://github.com/DilawarShafiq/phi-redactor/issues/new?template=feature_request.yml) and describe:

- The problem you're trying to solve
- Your proposed solution
- Alternatives you've considered

## Security Vulnerabilities

**Do NOT open a public issue for security vulnerabilities.**

See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
