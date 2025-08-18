#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- SETTING UP DATABASES ---"

# --- DIRECTORY CREATION ---
echo "Creating database directories..."
mkdir -p MEMORY/chromadb
mkdir -p MEMORY/vector_memory

# --- SQLITE DATABASE SETUP ---
DB_FILE="MEMORY/unified_memory.db"
echo "Creating SQLite database and tables in $DB_FILE..."

# Create tables
sqlite3 $DB_FILE <<EOF
CREATE TABLE IF NOT EXISTS conversations (id TEXT, user_message TEXT, ai_response TEXT, timestamp TEXT);
CREATE TABLE IF NOT EXISTS knowledge (id TEXT, key TEXT, value TEXT, importance REAL, timestamp TEXT);
CREATE TABLE IF NOT EXISTS prompts (id TEXT, name TEXT, content TEXT, category TEXT);
CREATE TABLE IF NOT EXISTS vector_embeddings (id TEXT, text TEXT, embedding TEXT, metadata TEXT);
EOF

echo "--- DATABASE SETUP COMPLETE ---"
