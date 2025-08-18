#!/bin/bash

# Deactivate GalaxyDevSystem AutoDoc

echo "Stopping GalaxyDevSystem AutoDoc..."

# Find and kill the API server process
pkill -f "api/server.py"

echo "GalaxyDevSystem AutoDoc stopped"
