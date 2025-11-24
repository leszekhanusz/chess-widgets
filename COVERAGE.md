# Code Coverage Setup Guide

This document explains how code coverage is configured in this project and how to set it up for automatic verification on GitHub.

## Overview

This project uses:
- **pytest-cov**: For collecting code coverage during test runs
- **Codecov**: For tracking coverage over time and posting coverage reports on pull requests
- **Coverage.py**: The underlying coverage measurement tool

## Local Usage

### Running Tests with Coverage

```bash
# Run tests with coverage report in terminal
make coverage

# Run tests with coverage and open HTML report
make coverage-html

# Or use pytest directly
pytest tests/ -v
```

The coverage configuration in `pyproject.toml` ensures that coverage is automatically collected when running pytest.

### Coverage Reports

Three types of coverage reports are generated:

1. **Terminal Report**: Shows missing lines directly in the terminal
2. **HTML Report**: Interactive report in `htmlcov/index.html`
3. **XML Report**: `coverage.xml` for CI/CD integration

### Coverage Requirements

- **Minimum Coverage**: 80% (configured in `pyproject.toml`)
- Tests will fail if coverage drops below this threshold
- You can adjust this in `[tool.pytest.ini_options]` section

## GitHub Actions Integration

### What's Already Configured

The `.github/workflows/test.yml` workflow:
1. Runs tests with coverage on all supported Python versions (3.10-3.14)
2. Generates coverage reports in XML format
3. Uploads coverage to Codecov (only for Python 3.12 to avoid duplicates)
4. Fails the build if coverage is below 80%

### Setting Up Codecov on GitHub

To enable automatic coverage verification on GitHub:

#### Step 1: Sign up for Codecov

1. Go to [codecov.io](https://codecov.io)
2. Click "Sign up with GitHub"
3. Authorize Codecov to access your GitHub repositories

#### Step 2: Add Your Repository

1. In Codecov dashboard, click "Add new repository"
2. Find and select `leszekhanusz/chess-widgets`
3. Codecov will generate a **CODECOV_TOKEN** for your repository

#### Step 3: Add the Token to GitHub Secrets

1. Go to your GitHub repository: `https://github.com/leszekhanusz/chess-widgets`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `CODECOV_TOKEN`
5. Value: Paste the token from Codecov
6. Click **Add secret**

#### Step 4: Verify Setup

1. Push a commit or create a pull request
2. The GitHub Actions workflow will run automatically
3. Coverage will be uploaded to Codecov
4. Codecov will post a comment on the PR with coverage details

## Codecov Features

Once configured, Codecov provides:

### 1. Coverage Badge
Add this to your README.md:
```markdown
[![codecov](https://codecov.io/gh/leszekhanusz/chess-widgets/branch/main/graph/badge.svg)](https://codecov.io/gh/leszekhanusz/chess-widgets)
```

### 2. Pull Request Comments
Codecov automatically comments on PRs with:
- Overall coverage percentage
- Coverage change compared to base branch
- Line-by-line coverage in the diff view

### 3. Coverage Trends
- Track coverage over time
- See which files/functions have low coverage
- Visualize coverage across branches

### 4. Status Checks
The workflow will:
- ✅ Pass if coverage meets the 80% threshold
- ❌ Fail if coverage drops below 80%
- ⚠️ Warn if coverage decreases by more than 1%

## Configuration Files

### pyproject.toml
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src/chess_widgets",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--cov-fail-under=80",  # Minimum coverage threshold
]

[tool.coverage.run]
source = ["src/chess_widgets"]
omit = ["*/tests/*", "*/__pycache__/*", "*/.venv/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

### codecov.yml
- **Project coverage target**: 80%
- **Patch coverage target**: 80% (for new code in PRs)
- **Threshold**: 1% (allowed decrease)

## Troubleshooting

### Coverage Not Uploading to Codecov

1. **Check the token**: Ensure `CODECOV_TOKEN` is correctly set in GitHub Secrets
2. **Check the workflow**: Look at the Actions tab for error messages
3. **Verify coverage.xml exists**: The file should be generated after tests run

### Coverage Below Threshold

1. Add more tests to cover untested code
2. Check `htmlcov/index.html` to see which lines are missing coverage
3. Consider excluding certain lines with `# pragma: no cover` if appropriate

### Local vs CI Coverage Differences

- Ensure you're using the same Python version locally as in CI
- Run `pip install -e .[dev]` to get the same dependencies
- Clear coverage data: `rm -rf .coverage htmlcov/ coverage.xml`

## Alternative: Coverage Without Codecov

If you prefer not to use Codecov:

1. Remove the "Upload coverage to Codecov" step from `.github/workflows/test.yml`
2. Coverage will still be measured and enforced locally and in CI
3. The build will fail if coverage drops below 80%
4. You won't get PR comments or historical tracking

## Customization

### Adjusting Coverage Threshold

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=90",  # Change to desired percentage
]
```

In `codecov.yml`:
```yaml
coverage:
  status:
    project:
      default:
        target: 90%  # Change to desired percentage
```

### Excluding Files from Coverage

In `pyproject.toml`:
```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",  # Add patterns here
    "*/__init__.py",
]
```

### Excluding Lines from Coverage

Use `# pragma: no cover` comment:
```python
def debug_only():  # pragma: no cover
    """This function is only used during debugging"""
    ...
```

## Best Practices

1. **Write tests first**: Aim for high coverage from the start
2. **Focus on meaningful tests**: 100% coverage doesn't guarantee bug-free code
3. **Review coverage reports**: Regularly check `htmlcov/` to find gaps
4. **Don't game the metrics**: Coverage should reflect actual test quality
5. **Update threshold gradually**: If coverage is low, increase it incrementally

## Summary

✅ **Local setup**: Ready to use with `make coverage`  
⚠️ **GitHub setup**: Requires Codecov token configuration  
📊 **Threshold**: 80% minimum coverage enforced  
🔄 **Automatic**: Runs on every push and pull request  
