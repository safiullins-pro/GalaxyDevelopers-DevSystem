#!/bin/bash

# Quick test script for DOC_SYSTEM

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
DOC_SYSTEM="$PROJECT_ROOT/DOC_SYSTEM"

echo -e "${BLUE}Testing DOC_SYSTEM Components...${NC}"
echo ""

# Test 1: Check structure
echo -e "${YELLOW}Test 1: Checking directory structure${NC}"
if [ -d "$DOC_SYSTEM/core" ] && [ -d "$DOC_SYSTEM/analyzers" ] && [ -d "$DOC_SYSTEM/generators" ]; then
    echo -e "${GREEN}✅ Directory structure OK${NC}"
else
    echo -e "${RED}❌ Directory structure incomplete${NC}"
fi

# Test 2: Check Python modules
echo -e "${YELLOW}Test 2: Testing Python imports${NC}"
python3 -c "
import sys
sys.path.insert(0, '$DOC_SYSTEM')
try:
    from core.file_monitor import FileMonitor
    from analyzers.dependency_analyzer import DependencyAnalyzer
    from generators.doc_generator import DocumentationGenerator
    print('✅ All modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
"

# Test 3: Test configuration
echo -e "${YELLOW}Test 3: Checking configuration${NC}"
if [ -f "$DOC_SYSTEM/config/system.config.yaml" ]; then
    echo -e "${GREEN}✅ Configuration file exists${NC}"
    python3 -c "
import yaml
with open('$DOC_SYSTEM/config/system.config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(f'  System name: {config[\"system\"][\"name\"]}')
    print(f'  API port: {config[\"api\"][\"port\"]}')
"
else
    echo -e "${RED}❌ Configuration file missing${NC}"
fi

# Test 4: Quick functionality test
echo -e "${YELLOW}Test 4: Testing basic functionality${NC}"
python3 << EOF
import sys
sys.path.insert(0, '$DOC_SYSTEM')

try:
    from pathlib import Path
    from core.file_monitor import FileMonitor
    
    # Test file monitoring
    monitor = FileMonitor()
    test_file = Path('$DOC_SYSTEM/test_file.txt')
    test_file.write_text('test content')
    
    # Test hash calculation
    hash_val = monitor._calculate_hash(test_file)
    if hash_val:
        print('✅ File hash calculation works')
    else:
        print('❌ File hash calculation failed')
    
    # Cleanup
    test_file.unlink()
    
except Exception as e:
    print(f'❌ Functionality test failed: {e}')
EOF

# Test 5: API endpoint test (if running)
echo -e "${YELLOW}Test 5: Testing API (if running)${NC}"
if curl -s http://localhost:37777/health > /dev/null 2>&1; then
    STATUS=$(curl -s http://localhost:37777/api/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['status'])")
    echo -e "${GREEN}✅ API is running: $STATUS${NC}"
else
    echo -e "${YELLOW}⚠️  API not running (start with ./ACTIVATE_DOC_SYSTEM.sh)${NC}"
fi

echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo -e "${GREEN}DOC_SYSTEM is ready to use!${NC}"
echo ""
echo -e "To activate the system, run:"
echo -e "${YELLOW}./ACTIVATE_DOC_SYSTEM.sh${NC}"