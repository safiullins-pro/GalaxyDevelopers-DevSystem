# GalaxyDevelopers AI DevSystem

Stateless AI chat system with automatic API key rotation for Google Gemini, web interface, and macOS system integrations.

## Features

- **Stateless Architecture** - Each request is independent, no sessions saved
- **Auto-rotation of 14 API keys** - Switches on each request
- **11 Gemini models** to choose from (versions 1.5, 2.0, 2.5)
- **macOS System Service** - Auto-starts on boot
- **MCP Integration** - API for AI agents
- **Screenshot Functionality** - Interface state capture

## Quick Start

### Web Interface
Open http://127.0.0.1:37777 in your browser

### API Usage
```bash
curl -X POST http://127.0.0.1:37777/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your question here",
    "model": "gemini-2.5-flash"
  }'
```

## Project Structure

```
├── docs/           # Documentation
├── scripts/        # Utility scripts
├── resources/      # Models, configs, dependencies
├── server/         # Backend server
├── interface/      # Web interface
├── connectors/     # Integrations (iTerm2, screenshots)
└── validators/     # Test utilities
```

## System Service

The backend runs as a macOS launchd service on port 37777.

### Service Management
```bash
# Restart
launchctl kickstart -k gui/$(id -u)/com.galaxydevelopers.ai.backend

# Stop
launchctl unload ~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist

# Start
launchctl load ~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist
```

## Development

See [docs/CLAUDE.md](docs/CLAUDE.md) for detailed documentation.

---
GalaxyDevelopers © 2025