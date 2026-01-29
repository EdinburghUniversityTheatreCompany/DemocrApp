# DemocrApp API - Testing Guide

## Recent Updates (January 2026)

**Major Version Upgrades:**
- Python: 3.12 → **3.14.2**
- Django: 5.0.4 → **6.0.1**
- pytest: 8.2.0 → **9.0.2**
- pytest-asyncio: 0.23.6 → **1.3.0**
- channels: 4.1.0 → **4.3.2**
- All other dependencies updated to latest versions

**Breaking Changes Addressed:**
- Django 6.0: Updated `format_html()` usage in template tags to require args/kwargs
- pytest-asyncio: Added `asyncio_mode = auto` configuration for mixed sync/async tests

## Environment Setup

This project uses Python 3.14 with a virtual environment for testing.

### Prerequisites

- Python 3.14 (managed via mise - configured in `.mise.toml`)
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
asyncio_mode = auto
```

**Note:** `asyncio_mode = auto` is required for pytest-asyncio 1.3.0+ to support mixed sync/async test classes.

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

WebSocket tests currently have known issues with channel layer mocking - they try to connect to real Redis and timeout. This is a pre-existing issue not related to the Python/Django upgrade.

**Current status:**
- 5/9 WebSocket async tests fail with database lock timeouts or async context errors
- Issue: Tests need proper channel layer mocking instead of real Redis connections
- Workaround: Run non-WebSocket tests separately with `./run_tests.sh Meeting/test_views.py`

Ensure Redis is running for other functionality:
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

## Docker Deployment

### Docker Compose Setup

The project uses `democrapp-compose.yml` (located in the project root, one directory above DemocrApp-API) with the following services:

- **web** - Django API server (uWSGI) on port 8001
- **websocket** - WebSocket server (Daphne) on port 8002
- **nginx** - Reverse proxy on port 80
- **redis** - Redis for Django Channels
- **database** - MySQL 8.3

### Rebuild Entire Docker Setup

From the project root:

```bash
# Stop all services
docker compose -f democrapp-compose.yml down

# Rebuild everything without cache 
docker compose -f democrapp-compose.yml build --no-cache

# Start services
docker compose -f democrapp-compose.yml up -d

# View logs
docker compose -f democrapp-compose.yml logs -f
```

### Quick Commands

```bash
# Restart services after code changes
docker compose -f democrapp-compose.yml restart web websocket

# Run migrations in container
docker compose -f democrapp-compose.yml exec web python manage.py migrate

# Access Django shell in container
docker compose -f democrapp-compose.yml exec web python manage.py shell

# View service status
docker compose -f democrapp-compose.yml ps
```

### Development Watch Mode

The compose file includes development watch configuration that automatically:
- Syncs code changes from `./DemocrApp-API` to the container
- Rebuilds on `requirements.txt` or settings changes

Start in watch mode:
```bash
docker compose -f democrapp-compose.yml watch
```

## Development Workflow

1. **Activate virtual environment** (if running commands manually)
2. **Write your test** following existing patterns
3. **Run the specific test** to verify it works
4. **Run full test suite** to ensure no regressions
5. **Check coverage** if implementing new features
