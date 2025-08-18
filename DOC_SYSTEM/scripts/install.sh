#!/bin/bash

# GalaxyDevSystem AutoDoc Installation Script
# Скрипт установки системы автоматической документации

set -e

echo "========================================="
echo "GalaxyDevSystem AutoDoc Installation"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOC_SYSTEM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DOC_SYSTEM_DIR")"

echo -e "${GREEN}Installation directory: ${DOC_SYSTEM_DIR}${NC}"
echo -e "${GREEN}Project root: ${PROJECT_ROOT}${NC}"

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
cd "$DOC_SYSTEM_DIR"
python3 -m venv venv
echo -e "${GREEN}Virtual environment created${NC}"

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed${NC}"

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p metadata logs docs templates
echo -e "${GREEN}Directories created${NC}"

# Install Git hooks
echo -e "\n${YELLOW}Installing Git hooks...${NC}"
if [ -d "$PROJECT_ROOT/.git" ]; then
    # Create hooks directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/.git/hooks"
    
    # Create pre-commit hook
    cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# GalaxyDevSystem AutoDoc pre-commit hook

# Activate virtual environment
source /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOC_SYSTEM/venv/bin/activate

# Run validation
python /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOC_SYSTEM/hooks/pre_commit.py

# Exit with the validation result
exit $?
EOF
    
    # Create post-commit hook
    cat > "$PROJECT_ROOT/.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# GalaxyDevSystem AutoDoc post-commit hook

# Activate virtual environment
source /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOC_SYSTEM/venv/bin/activate

# Update documentation
python /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOC_SYSTEM/hooks/post_commit.py &

# Don't block commit
exit 0
EOF
    
    # Make hooks executable
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
    chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
    
    echo -e "${GREEN}Git hooks installed${NC}"
else
    echo -e "${YELLOW}Git repository not found. Skipping Git hooks installation.${NC}"
fi

# Create systemd service (optional, for Linux systems)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "\n${YELLOW}Creating systemd service...${NC}"
    
    SERVICE_FILE="/etc/systemd/system/galaxy-autodoc.service"
    
    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=GalaxyDevSystem AutoDoc Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DOC_SYSTEM_DIR
Environment="PATH=$DOC_SYSTEM_DIR/venv/bin:/usr/bin:/bin"
ExecStart=$DOC_SYSTEM_DIR/venv/bin/python $DOC_SYSTEM_DIR/api/server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable galaxy-autodoc.service
    
    echo -e "${GREEN}Systemd service created${NC}"
    echo -e "${YELLOW}Start the service with: sudo systemctl start galaxy-autodoc${NC}"
fi

# Create launchd plist for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "\n${YELLOW}Creating launchd service for macOS...${NC}"
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.galaxydevelopers.autodoc.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.galaxydevelopers.autodoc</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DOC_SYSTEM_DIR/venv/bin/python</string>
        <string>$DOC_SYSTEM_DIR/api/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DOC_SYSTEM_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$DOC_SYSTEM_DIR/logs/autodoc.log</string>
    <key>StandardErrorPath</key>
    <string>$DOC_SYSTEM_DIR/logs/autodoc.error.log</string>
</dict>
</plist>
EOF
    
    echo -e "${GREEN}Launchd service created${NC}"
    echo -e "${YELLOW}Load the service with: launchctl load $PLIST_FILE${NC}"
fi

# Create activation script
echo -e "\n${YELLOW}Creating activation script...${NC}"
cat > "$DOC_SYSTEM_DIR/activate.sh" << 'EOF'
#!/bin/bash

# Activate GalaxyDevSystem AutoDoc

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the API server
echo "Starting GalaxyDevSystem AutoDoc API server..."
python "$SCRIPT_DIR/api/server.py"
EOF

chmod +x "$DOC_SYSTEM_DIR/activate.sh"
echo -e "${GREEN}Activation script created${NC}"

# Create deactivation script
cat > "$DOC_SYSTEM_DIR/deactivate.sh" << 'EOF'
#!/bin/bash

# Deactivate GalaxyDevSystem AutoDoc

echo "Stopping GalaxyDevSystem AutoDoc..."

# Find and kill the API server process
pkill -f "api/server.py"

echo "GalaxyDevSystem AutoDoc stopped"
EOF

chmod +x "$DOC_SYSTEM_DIR/deactivate.sh"

# Summary
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${GREEN}=========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Review and update configuration: $DOC_SYSTEM_DIR/config/system.config.yaml"
echo "2. Start the service:"
echo "   - Manual: $DOC_SYSTEM_DIR/activate.sh"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   - Systemd: sudo systemctl start galaxy-autodoc"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   - Launchd: launchctl load $HOME/Library/LaunchAgents/com.galaxydevelopers.autodoc.plist"
fi
echo "3. Access API at: http://localhost:37777/api/status"
echo ""
echo -e "${GREEN}Documentation system is ready to use!${NC}"