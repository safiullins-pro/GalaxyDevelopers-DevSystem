#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import subprocess
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_monitor import FileMonitor
from analyzers.dependency_analyzer import DependencyAnalyzer
from generators.doc_generator import DocumentationGenerator

def get_committed_files():
    """Get list of files in the last commit"""
    result = subprocess.run(
        ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return []
    
    return [f.strip() for f in result.stdout.strip().split('\n') if f]

def update_documentation():
    """Update documentation after commit"""
    
    print("📚 GalaxyDevSystem AutoDoc: Updating documentation...")
    
    try:
        # Initialize components
        file_monitor = FileMonitor()
        dependency_analyzer = DependencyAnalyzer()
        doc_generator = DocumentationGenerator()
        
        # Get committed files
        committed_files = get_committed_files()
        
        if not committed_files:
            print("ℹ️  No files in commit to document")
            return
        
        print(f"📝 Processing {len(committed_files)} committed files...")
        
        # Scan for changes
        file_monitor.scan_directory()
        
        # Rebuild dependency graph
        print("🔗 Analyzing dependencies...")
        dependency_analyzer.build_dependency_graph()
        
        # Generate documentation
        print("📄 Generating documentation...")
        file_metadata = file_monitor.get_all_metadata()
        
        # Add dependency information to metadata
        for file_path in file_metadata:
            file_metadata[file_path]['dependencies'] = list(
                dependency_analyzer.get_file_dependencies(file_path)
            )
            file_metadata[file_path]['dependents'] = list(
                dependency_analyzer.get_file_dependents(file_path)
            )
        
        # Add orphaned files information
        file_metadata['orphaned_files'] = list(dependency_analyzer.orphaned_files)
        file_metadata['circular_dependencies'] = dependency_analyzer.circular_dependencies
        
        # Generate project documentation
        project_doc = doc_generator.generate_project_documentation(file_metadata)
        
        # Save documentation in all formats
        doc_generator.save_documentation(project_doc)
        
        # Update Claude context
        if doc_generator.config['claude_integration']['enabled']:
            doc_generator.update_claude_context(project_doc)
            print("🤖 Claude context updated")
        
        # Save dependency analysis
        dependency_analyzer.save_analysis()
        
        print("✅ Documentation updated successfully!")
        
        # Report any issues found
        if dependency_analyzer.orphaned_files:
            print(f"⚠️  Found {len(dependency_analyzer.orphaned_files)} orphaned files")
        
        if dependency_analyzer.circular_dependencies:
            print(f"⚠️  Found {len(dependency_analyzer.circular_dependencies)} circular dependencies")
    
    except Exception as e:
        print(f"❌ Error updating documentation: {e}")

def main():
    """Post-commit hook main function"""
    
    # Run documentation update in background thread
    thread = threading.Thread(target=update_documentation)
    thread.daemon = True
    thread.start()
    
    # Don't wait for completion - let commit finish
    print("🚀 Documentation update started in background...")
    return 0

if __name__ == '__main__':
    sys.exit(main())