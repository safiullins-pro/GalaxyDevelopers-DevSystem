#!/bin/bash

echo "--- RESTARTING GALAXY DEVELOPERS SYSTEM ---"

# Stop all services
./galaxy-stop.sh

# Wait a moment before starting again
sleep 2

# Start all services
./galaxy-start.sh
