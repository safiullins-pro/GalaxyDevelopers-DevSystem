#!/bin/bash

echo "Setting up iTerm2 integration for GalaxyDevelopers DevSystem"
echo "============================================="
echo ""

# Check if iTerm2 is installed
if [ ! -d "/Applications/iTerm.app" ]; then
    echo "❌ iTerm2 not found. Please install iTerm2 first."
    exit 1
fi

# Enable Python API in iTerm2
echo "📝 To enable iTerm2 integration:"
echo ""
echo "1. Open iTerm2"
echo "2. Go to Preferences → General → Magic"
echo "3. Enable 'Enable Python API'"
echo ""
echo "4. Then run this script in iTerm2:"
echo "   python3 /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/iterm2-integration.py"
echo ""
echo "5. The script will:"
echo "   • Mark all DevSystem terminals with 💻"
echo "   • Mark Claude terminals with 🤖"
echo "   • Auto-insert screenshots into active Claude terminals"
echo ""
echo "Installation command for iTerm2 Python support:"
echo "pip3 install iterm2"
echo ""

# Install iterm2 python package if not installed
if ! python3 -c "import iterm2" 2>/dev/null; then
    echo "Installing iterm2 Python package..."
    pip3 install iterm2
fi

echo "✅ Setup complete!"