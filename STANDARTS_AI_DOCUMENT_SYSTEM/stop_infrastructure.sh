#!/bin/bash

# Stop Infrastructure Script for DocumentsSystem

echo "🛑 Stopping DocumentsSystem Infrastructure..."

# Stop containers
docker-compose -f docker-compose.minimal.yml down

echo "✅ Infrastructure stopped"