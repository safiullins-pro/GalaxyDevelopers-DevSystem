#!/usr/bin/env python3

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import threading
from pathlib import Path
from datetime import datetime
import sys
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_monitor import FileMonitor
from analyzers.dependency_analyzer import DependencyAnalyzer
from generators.doc_generator import DocumentationGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global instances
monitor = None
analyzer = None
generator = None

def init_system():
    global monitor, analyzer, generator
    
    logger.info("Initializing system components...")
    
    config_path = Path(__file__).parent.parent / "config" / "system.config.yaml"
    
    try:
        monitor = FileMonitor(str(config_path))
        analyzer = DependencyAnalyzer(str(config_path))
        generator = DocumentationGenerator(str(config_path))
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor.start_monitoring, daemon=True)
        monitor_thread.start()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'components': {
            'monitor': monitor is not None,
            'analyzer': analyzer is not None,
            'generator': generator is not None
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get all monitored files"""
    if not monitor:
        return jsonify({'error': 'System not initialized'}), 500
        
    metadata = monitor.get_all_metadata()
    return jsonify({
        'total': len(metadata),
        'files': metadata
    })

@app.route('/api/file/<path:file_path>', methods=['GET'])
def get_file_info(file_path):
    """Get detailed information about a specific file"""
    if not monitor:
        return jsonify({'error': 'System not initialized'}), 500
        
    metadata = monitor.get_file_metadata(file_path)
    if not metadata:
        return jsonify({'error': 'File not found'}), 404
        
    return jsonify(metadata)

@app.route('/api/analyze', methods=['POST'])
def analyze_project():
    """Analyze project dependencies"""
    if not analyzer:
        return jsonify({'error': 'Analyzer not initialized'}), 500
        
    try:
        # Build dependency graph
        analyzer.build_dependency_graph()
        
        # Get statistics
        stats = analyzer.get_statistics()
        
        # Export analysis
        analysis = json.loads(analyzer.export_graph('json'))
        
        return jsonify({
            'statistics': stats,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-docs', methods=['POST'])
def generate_documentation():
    """Generate project documentation"""
    if not generator or not monitor:
        return jsonify({'error': 'System not initialized'}), 500
        
    try:
        # Get all metadata
        files_metadata = monitor.get_all_metadata()
        
        # Generate documentation
        project_doc = generator.generate_project_documentation(files_metadata)
        
        # Save documentation
        generator.save_documentation(project_doc)
        
        # Update Claude context
        generator.update_claude_context(project_doc)
        
        return jsonify({
            'status': 'success',
            'files_documented': len(files_metadata),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orphans', methods=['GET'])
def get_orphaned_files():
    """Get list of orphaned files"""
    if not analyzer:
        return jsonify({'error': 'Analyzer not initialized'}), 500
        
    try:
        # Build dependency graph if not already built
        if not analyzer.dependency_graph.nodes():
            analyzer.build_dependency_graph()
        
        orphans = list(analyzer.orphaned_files)
        
        return jsonify({
            'total': len(orphans),
            'files': orphans
        })
        
    except Exception as e:
        logger.error(f"Failed to get orphaned files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dependencies/<path:file_path>', methods=['GET'])
def get_dependencies(file_path):
    """Get dependencies for a specific file"""
    if not analyzer:
        return jsonify({'error': 'Analyzer not initialized'}), 500
        
    try:
        # Build dependency graph if not already built
        if not analyzer.dependency_graph.nodes():
            analyzer.build_dependency_graph()
        
        dependencies = list(analyzer.get_file_dependencies(file_path))
        dependents = list(analyzer.get_file_dependents(file_path))
        
        return jsonify({
            'file': file_path,
            'dependencies': dependencies,
            'dependents': dependents
        })
        
    except Exception as e:
        logger.error(f"Failed to get dependencies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_files():
    """Validate files"""
    try:
        # Import validator only when needed
        from validators.validation_agent import ValidationAgent
        validator = ValidationAgent()
        
        # Get file list from request
        data = request.get_json() or {}
        files = data.get('files', [])
        
        if not files and monitor:
            # Validate all files if none specified
            files = list(monitor.get_all_metadata().keys())
        
        results = []
        for file_path_str in files:
            file_path = Path(validator.project_root) / file_path_str
            if file_path.exists():
                validation = validator.validate_file(file_path)
                results.extend(validation)
        
        return jsonify({
            'validated': len(files),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger a project scan"""
    if not monitor:
        return jsonify({'error': 'Monitor not initialized'}), 500
        
    try:
        # Run scan in background
        scan_thread = threading.Thread(
            target=lambda: monitor.scan_directory(),
            daemon=True
        )
        scan_thread.start()
        
        return jsonify({
            'status': 'scanning',
            'message': 'Project scan started'
        })
        
    except Exception as e:
        logger.error(f"Failed to start scan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_documentation():
    """Export documentation in various formats"""
    if not generator or not monitor:
        return jsonify({'error': 'System not initialized'}), 500
        
    format = request.args.get('format', 'markdown')
    
    try:
        files_metadata = monitor.get_all_metadata()
        project_doc = generator.generate_project_documentation(files_metadata)
        
        if format == 'json':
            return jsonify(project_doc)
        elif format == 'html':
            html = generator.render_documentation(project_doc, 'html')
            return Response(html, mimetype='text/html')
        else:  # Default to markdown
            markdown = generator.render_documentation(project_doc, 'markdown')
            return Response(markdown, mimetype='text/markdown')
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/')
def index():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'GalaxyDevelopers DOC_SYSTEM API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/status': 'System status',
            'GET /api/files': 'List all files',
            'GET /api/file/<path>': 'Get file information',
            'POST /api/analyze': 'Analyze project',
            'POST /api/generate-docs': 'Generate documentation',
            'GET /api/orphans': 'Get orphaned files',
            'GET /api/dependencies/<path>': 'Get file dependencies',
            'POST /api/validate': 'Validate files',
            'POST /api/scan': 'Trigger project scan',
            'GET /api/export': 'Export documentation',
            'GET /health': 'Health check'
        }
    })

def run_server():
    """Run the API server"""
    try:
        init_system()
        
        host = '127.0.0.1'
        port = 37777
        
        logger.info(f"Starting API server on {host}:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()