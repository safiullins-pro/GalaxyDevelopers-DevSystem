#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- INSTALLING DEPENDENCIES ---"

# --- SYSTEM DEPENDENCIES (macOS with Homebrew) ---
if [[ "$(uname)" == "Darwin" ]]; then
    echo "Installing system dependencies with Homebrew..."
    brew install node python3 sqlite3 redis postgresql
fi

# --- Node.js DEPENDENCIES ---
echo "Installing Node.js dependencies..."
npm install express @google/generative-ai axios cors jsonwebtoken sqlite3

# --- Python DEPENDENCIES ---
echo "Installing Python dependencies..."
pip3 install flask flask-cors sqlite3 watchdog prometheus-client bandit requests openai anthropic

echo "--- DEPENDENCIES INSTALLATION COMPLETE ---"
