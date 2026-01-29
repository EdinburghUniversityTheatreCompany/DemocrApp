# DemocrApp API - Testing Guide

## Environment Setup

This project uses Python 3.12 with a virtual environment for testing.

### Prerequisites

- Python 3.12 (managed via mise)
- MySQL 8 (mysql8 Docker container)
- Redis (for WebSocket tests)

### Virtual Environment

The virtual environment is located at `venv/` and includes all dependencies from `requirements.txt`.

**To activate manually:**
```bash
source venv/bin/activate
```

**To install/update dependencies:**
```bash
./venv/bin/pip install -r requirements.txt
```

## Running Tests

### Quick Start

Use the provided test runner script which handles environment setup automatically:

```bash
# Run all tests
./run_tests.sh

# Run with verbose output
./run_tests.sh -v

# Run specific test file
./run_tests.sh Meeting/test_views.py

# Run specific test class
./run_tests.sh Meeting/test_views.py::ManagementInterfaceCases

# Run specific test
./run_tests.sh Meeting/test_views.py::ManagementInterfaceCases::test_announcement

# Run tests matching a pattern
./run_tests.sh -k "test_create"
```

### Manual Test Execution

If you need to run tests without the script:

```bash
# Set up environment variables
export $(grep -v '^#' ../.env | tr -d '\r' | xargs)
export DATABASE_HOST=127.0.0.1

# Run pytest
./venv/bin/pytest
```

## Database Configuration

### MySQL Container Setup

The tests use the `mysql8` Docker container on `127.0.0.1:3306`.

**Database:** `democrapp`
**User:** `django`
**Password:** (from `.env` file)
**Host:** `127.0.0.1` (not `localhost` - this forces TCP connection)

The django user has full privileges for creating/dropping test databases.

### Test Database

Django automatically creates a `test_democrapp` database for each test run and destroys it afterward.

## Test Structure

### Test Files

- `Meeting/test_views.py` - HTTP endpoint tests for the management interface
- `Meeting/test_voterws.py` - WebSocket consumer tests for real-time voting

### Test Configuration

Configuration is in `pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = democrapp_api.settings
```

## Common Issues

### Can't connect to MySQL socket

**Error:** `Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock'`

**Solution:** Use `DATABASE_HOST=127.0.0.1` instead of `localhost` to force TCP connection.

### Permission denied creating test database

**Error:** `Access denied for user 'django'@'%' to database 'test_democrapp'`

**Solution:** Grant full privileges:
```bash
docker exec mysql8 mysql -u root -e "GRANT ALL PRIVILEGES ON *.* TO 'django'@'%'; FLUSH PRIVILEGES;"
```

### WebSocket tests failing

WebSocket tests require a Redis connection at `localhost:6379`. Ensure the Redis Docker container is running:
```bash
docker ps | grep redis
```

### Carriage return in environment variables

If you get authentication errors with usernames ending in `\r`, the `.env` file has Windows line endings.

The `run_tests.sh` script handles this automatically with `tr -d '\r'`.

## Test Coverage

Current test suite includes:
- 23 view/endpoint tests
- 15 WebSocket tests

Run with coverage:
```bash
./run_tests.sh --cov=Meeting --cov-report=html
```

## Debugging Tests

### Run with more verbosity
```bash
./run_tests.sh -vv
```

### Stop on first failure
```bash
./run_tests.sh -x
```

### Drop into debugger on failure
```bash
./run_tests.sh --pdb
```

### Show print statements
```bash
./run_tests.sh -s
```

## Development Workflow

1. **Activate virtual environment** (if running commands manually)
2. **Write your test** following existing patterns
3. **Run the specific test** to verify it works
4. **Run full test suite** to ensure no regressions
5. **Check coverage** if implementing new features
