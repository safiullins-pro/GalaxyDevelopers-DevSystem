#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.validation_agent import ValidationAgent
from core.file_monitor import FileMonitor
import subprocess
import json

def get_staged_files():
    """Get list of staged files from git"""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return []
    
    return [f.strip() for f in result.stdout.strip().split('\n') if f]

def main():
    """Pre-commit hook main function"""
    
    print("🔍 GalaxyDevSystem AutoDoc: Running pre-commit validation...")
    
    # Get staged files
    staged_files = get_staged_files()
    
    if not staged_files:
        print("✅ No staged files to validate")
        return 0
    
    print(f"📝 Validating {len(staged_files)} staged files...")
    
    # Initialize validation agent
    validator = ValidationAgent()
    
    # Track validation results
    has_errors = False
    has_warnings = False
    blocked_files = []
    
    # Validate each staged file
    for file_path in staged_files:
        full_path = Path.cwd() / file_path
        
        if not full_path.exists():
            continue
        
        # Run validation
        results = validator.validate_file(full_path)
        
        # Check results
        for result in results:
            if not result.get('passed', True):
                level = result.get('level', 'info')
                
                if level == 'critical' or level == 'error':
                    has_errors = True
                    blocked_files.append(file_path)
                    print(f"❌ {file_path}: {result['rule']} - {result['message']}")
                elif level == 'warning':
                    has_warnings = True
                    print(f"⚠️  {file_path}: {result['rule']} - {result['message']}")
    
    # Determine if commit should be blocked
    if has_errors and validator.config['validation'].get('blocking_mode', False):
        print("\n🚫 Commit blocked due to validation errors!")
        print(f"   Files with errors: {', '.join(blocked_files)}")
        print("\n   Fix the errors and try again.")
        return 1
    
    if has_warnings:
        print(f"\n⚠️  Commit proceeding with {len([f for f in staged_files if f not in blocked_files])} warnings")
    else:
        print("\n✅ All validations passed!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())