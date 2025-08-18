#!/bin/bash

# Activate GalaxyDevSystem AutoDoc

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the API server
echo "Starting GalaxyDevSystem AutoDoc API server..."
python "$SCRIPT_DIR/api/server.py"
