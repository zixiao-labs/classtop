# ClassTop Testing Guide

This guide explains how to run tests for the ClassTop application.

## Test Organization

ClassTop uses pytest for testing with three types of tests:

1. **Unit Tests** - Test individual components in isolation with mocked dependencies
2. **Integration Tests** - Test components working together with real services
3. **Manual Tests** - End-to-end testing through the UI

## Prerequisites

### Install Test Dependencies

```bash
cd src-tauri
uv pip install -e ".[dev]"
```

This installs:
- pytest >= 8.0.0
- pytest-asyncio >= 0.23.0
- pytest-cov >= 4.1.0
- pytest-mock >= 3.12.0
- responses >= 0.24.0
- httpx >= 0.26.0

## Running Tests

### Run All Unit Tests

```bash
cd src-tauri
pytest
```

### Run Specific Test Files

```bash
# Test sync client
pytest tests/test_sync_client.py -v

# Test schedule manager
pytest tests/test_schedule_manager.py -v

# Test settings manager
pytest tests/test_settings_manager.py -v

# Test commands
pytest tests/test_commands.py -v
```

### Run Tests by Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests only (requires Management Server)
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Windows-specific tests only
pytest -m windows_only
```

### Run with Coverage Report

```bash
# Terminal output
pytest --cov=tauri_app --cov-report=term-missing

# Generate HTML report
pytest --cov=tauri_app --cov-report=html

# Then open htmlcov/index.html in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Integration Tests

Integration tests require a running Management Server instance.

### Setup for Integration Tests

1. **Start PostgreSQL Database**
   ```bash
   # macOS with Homebrew
   brew services start postgresql@14

   # Linux
   sudo systemctl start postgresql

   # Windows
   # Use pgAdmin or start PostgreSQL service
   ```

2. **Clone and Setup Management Server** (if not already done)
   ```bash
   cd ../  # Go to parent directory
   git clone https://github.com/Zixiao-System/Classtop-Management-Server.git
   cd Classtop-Management-Server

   # Configure database
   cp .env.example .env
   # Edit .env and set DATABASE_URL

   # Build frontend
   cd frontend
   npm install
   npm run build
   cd ..

   # Run migrations
   diesel migration run
   ```

3. **Start Management Server**
   ```bash
   cd ../Classtop-Management-Server
   cargo run --release
   ```

   Server will start at http://localhost:8765

4. **Verify Server is Running**
   ```bash
   curl http://localhost:8765/api/health
   # Should return: {"success":true,"data":{"status":"healthy","version":"1.2.0"}}
   ```

### Run Integration Tests

```bash
cd ../classtop/src-tauri

# Run all integration tests
pytest -m integration -v

# Run specific integration test file
pytest tests/test_sync_integration.py -v

# Skip integration tests (run only unit tests)
pytest -m "not integration"
```

### What Integration Tests Cover

- Server health check
- Client registration workflow
- Data upload (courses and schedule)
- Data download from server
- Bidirectional sync with conflict resolution
- Conflict detection logic
- Auto-sync start/stop
- Multi-client synchronization
- Error handling (invalid URLs, network failures)
- Sync history logging

## Test File Organization

```
src-tauri/tests/
├── conftest.py                    # Shared fixtures
├── test_commands.py               # Tauri command tests
├── test_db.py                     # Database operations
├── test_events.py                 # Event system tests
├── test_schedule_manager.py       # Schedule CRUD tests
├── test_settings_manager.py       # Settings management tests
├── test_sync_client.py           # Sync client unit tests (790 lines, 38 tests)
├── test_sync_history.py          # Sync history tracking tests
└── test_sync_integration.py      # Integration tests (NEW)
```

## Writing New Tests

### Unit Test Template

```python
"""Test module for feature X."""
import pytest
from tauri_app.feature import Feature

@pytest.fixture
def feature_instance():
    """Create a Feature instance for testing."""
    return Feature()

class TestFeature:
    """Tests for Feature class."""

    def test_basic_functionality(self, feature_instance):
        """Test basic functionality."""
        result = feature_instance.do_something()
        assert result is not None
```

### Integration Test Template

```python
"""Integration tests for feature X."""
import pytest

pytestmark = pytest.mark.integration

class TestFeatureIntegration:
    """Integration tests for feature X."""

    def test_with_real_service(self):
        """Test with actual service running."""
        # Test code here
        pass
```

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd src-tauri
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          cd src-tauri
          pytest -m "not integration" --cov=tauri_app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'tauri_app'`

**Solution**:
```bash
cd src-tauri
pip install -e .
```

#### 2. Integration Tests Skipped

**Problem**: "Management Server is not running at http://localhost:8765"

**Solution**:
```bash
# Check if server is running
curl http://localhost:8765/api/health

# If not, start it
cd ../Classtop-Management-Server
cargo run --release
```

#### 3. Database Locked Errors

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close ClassTop application
- Kill any orphaned Python processes
- Tests use temporary databases to avoid conflicts

#### 4. Test Failures After Code Changes

**Solution**:
```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall package
cd src-tauri
pip install -e . --force-reinstall
```

## Test Coverage Goals

- **Overall**: > 80%
- **Critical paths** (sync, schedule, settings): > 90%
- **New features**: 100%

### Current Coverage

Run to see current coverage:
```bash
pytest --cov=tauri_app --cov-report=term-missing
```

Expected output:
```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
tauri_app/__init__.py                  45      2    96%   23-24
tauri_app/commands.py                 156      8    95%
tauri_app/db.py                        87      4    95%
tauri_app/events.py                    42      1    98%
tauri_app/schedule_manager.py         198     10    95%
tauri_app/settings_manager.py         112      5    96%
tauri_app/sync_client.py              287     15    95%
-----------------------------------------------------------------
TOTAL                                 927     45    95%
```

## Manual Testing Checklist

Before release, manually test these workflows:

### Sync Functionality

- [ ] Configure server URL in Settings
- [ ] Test connection to Management Server
- [ ] Register client
- [ ] Add courses locally
- [ ] Manual sync upload (should succeed)
- [ ] Verify courses appear in Management Server UI
- [ ] Modify course on server
- [ ] Download sync (should update local)
- [ ] Enable auto-sync
- [ ] Wait for auto-sync to trigger (check logs)
- [ ] Create conflict (modify same course locally and on server)
- [ ] Test bidirectional sync with different strategies
- [ ] Verify sync history in database

### Multi-Client Sync

- [ ] Set up two ClassTop instances with different UUIDs
- [ ] Both register to same server
- [ ] Client 1: Add course and sync
- [ ] Client 2: Download sync (should get Course)
- [ ] Client 2: Modify course and sync
- [ ] Client 1: Download sync (should get updates)
- [ ] Verify no data loss or duplication

### Error Scenarios

- [ ] Test with server offline
- [ ] Test with invalid server URL
- [ ] Test with network timeout
- [ ] Test with malformed responses
- [ ] Verify graceful error handling and user feedback

## Performance Testing

### Sync Performance

Test sync with large datasets:

```python
# Generate test data
for i in range(100):
    schedule_manager.add_course(f"Course {i}", f"Teacher {i}")

# Time sync operation
import time
start = time.time()
sync_client.sync_to_server()
duration = time.time() - start
print(f"Sync completed in {duration:.2f} seconds")
```

Target: < 5 seconds for 100 courses with 500 schedule entries

## Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Debug Specific Test

```python
# Add breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    # Test code
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [ClassTop CLAUDE.md](../CLAUDE.md) - Architecture and development guide
- [Management Server Testing Guide](../docs/MANAGEMENT_SERVER_TESTING.md)
- [Quick Start Sync Guide](../docs/QUICK_START_SYNC.md)

## Getting Help

- Check [GitHub Issues](https://github.com/Zixiao-System/classtop/issues)
- Review test output carefully
- Enable verbose logging in tests
- Check Management Server logs if integration tests fail
