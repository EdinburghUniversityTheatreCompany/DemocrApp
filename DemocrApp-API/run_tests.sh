#!/bin/bash
# Change to the script's directory
cd "$(dirname "$0")"

# Load environment variables from .env file (stripping carriage returns)
export $(grep -v '^#' ../.env | tr -d '\r' | xargs)

# Override DATABASE_HOST for local testing (use 127.0.0.1 for TCP instead of socket)
export DATABASE_HOST=127.0.0.1

# Run pytest with all arguments passed to this script
./venv/bin/pytest "$@"
