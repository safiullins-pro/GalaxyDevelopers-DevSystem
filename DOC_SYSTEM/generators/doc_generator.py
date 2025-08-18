#!/usr/bin/env python3

import os
import json
import yaml
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import hashlib
from jinja2 import Template, Environment, FileSystemLoader

class DocumentationGenerator:
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.templates_dir = self.project_root / 'DOC_SYSTEM' / 'templates'
        self.docs_output_dir = self.project_root / 'DOC_SYSTEM' / 'docs'
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False
        )
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directories exist
        self.docs_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Documentation cache
        self.doc_cache: Dict[str, Dict] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def generate_file_documentation(self, file_path: Path, metadata: Dict = None) -> Dict:
        """Generate documentation for a single file"""
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return {}
        
        relative_path = file_path.relative_to(self.project_root)
        
        doc_data = {
            'file_path': str(relative_path),
            'file_name': file_path.name,
            'extension': file_path.suffix,
            'size': file_path.stat().st_size,
            'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'hash': self._calculate_file_hash(file_path),
            'metadata': metadata or {},
            'content_analysis': self._analyze_file_content(file_path),
            'ai_description': None,
            'dependencies': [],
            'dependents': [],
            'tags': self._generate_tags(file_path),
            'complexity_metrics': self._calculate_complexity(file_path)
        }
        
        # Generate AI-powered description if enabled
        if self.config['documentation']['ai_powered']:
            doc_data['ai_description'] = self._generate_ai_description(file_path, doc_data)
        
        # Cache the documentation
        self.doc_cache[str(relative_path)] = doc_data
        
        return doc_data
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash"""
        algorithm = self.config['hashing']['algorithm']
        hasher = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _analyze_file_content(self, file_path: Path) -> Dict:
        """Analyze file content for documentation"""
        analysis = {
            'lines_of_code': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'functions': [],
            'classes': [],
            'imports': [],
            'exports': [],
            'docstrings': [],
            'todos': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            file_type = self._get_file_type(file_path)
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Count line types
                if not line_stripped:
                    analysis['blank_lines'] += 1
                elif self._is_comment(line_stripped, file_type):
                    analysis['comment_lines'] += 1
                else:
                    analysis['lines_of_code'] += 1
                
                # Extract functions/methods
                if file_type == 'python':
                    if line_stripped.startswith('def '):
                        func_name = re.match(r'def\s+(\w+)', line_stripped)
                        if func_name:
                            analysis['functions'].append({
                                'name': func_name.group(1),
                                'line': i
                            })
                    elif line_stripped.startswith('class '):
                        class_name = re.match(r'class\s+(\w+)', line_stripped)
                        if class_name:
                            analysis['classes'].append({
                                'name': class_name.group(1),
                                'line': i
                            })
                    elif line_stripped.startswith('import ') or line_stripped.startswith('from '):
                        analysis['imports'].append(line_stripped)
                
                elif file_type in ['javascript', 'typescript']:
                    # Function declarations
                    func_match = re.match(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', line_stripped)
                    if func_match:
                        analysis['functions'].append({
                            'name': func_match.group(1),
                            'line': i
                        })
                    
                    # Arrow functions
                    arrow_match = re.match(r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', line_stripped)
                    if arrow_match:
                        analysis['functions'].append({
                            'name': arrow_match.group(1),
                            'line': i
                        })
                    
                    # Classes
                    class_match = re.match(r'(?:export\s+)?class\s+(\w+)', line_stripped)
                    if class_match:
                        analysis['classes'].append({
                            'name': class_match.group(1),
                            'line': i
                        })
                    
                    # Imports
                    if line_stripped.startswith('import '):
                        analysis['imports'].append(line_stripped)
                    
                    # Exports
                    if line_stripped.startswith('export '):
                        analysis['exports'].append(line_stripped)
                
                # Find TODOs and FIXMEs
                if 'TODO' in line or 'FIXME' in line:
                    analysis['todos'].append({
                        'type': 'TODO' if 'TODO' in line else 'FIXME',
                        'line': i,
                        'text': line_stripped
                    })
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
        
        return analysis
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension"""
        ext = file_path.suffix.lower()
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.css': 'css',
            '.scss': 'css',
            '.html': 'html',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.sh': 'shell',
            '.bash': 'shell'
        }
        return type_map.get(ext, 'unknown')
    
    def _is_comment(self, line: str, file_type: str) -> bool:
        """Check if line is a comment"""
        comment_markers = {
            'python': ['#'],
            'javascript': ['//', '/*', '*/', '*'],
            'typescript': ['//', '/*', '*/', '*'],
            'css': ['/*', '*/', '*'],
            'html': ['<!--', '-->'],
            'shell': ['#'],
            'yaml': ['#']
        }
        
        markers = comment_markers.get(file_type, [])
        return any(line.startswith(marker) for marker in markers)
    
    def _generate_tags(self, file_path: Path) -> List[str]:
        """Generate tags for the file"""
        tags = []
        
        # Add extension as tag
        if file_path.suffix:
            tags.append(file_path.suffix[1:])
        
        # Add directory as tag
        parent_dir = file_path.parent.name
        if parent_dir and parent_dir != '.':
            tags.append(parent_dir)
        
        # Add file type
        file_type = self._get_file_type(file_path)
        if file_type != 'unknown':
            tags.append(file_type)
        
        # Add special tags based on file name
        file_name_lower = file_path.name.lower()
        if 'test' in file_name_lower:
            tags.append('test')
        if 'config' in file_name_lower:
            tags.append('configuration')
        if 'main' in file_name_lower or 'index' in file_name_lower:
            tags.append('entry-point')
        if 'util' in file_name_lower or 'helper' in file_name_lower:
            tags.append('utility')
        
        return list(set(tags))
    
    def _calculate_complexity(self, file_path: Path) -> Dict:
        """Calculate complexity metrics for the file"""
        metrics = {
            'cyclomatic_complexity': 0,
            'cognitive_complexity': 0,
            'nesting_depth': 0,
            'coupling': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_type = self._get_file_type(file_path)
            
            if file_type == 'python':
                # Count decision points for cyclomatic complexity
                metrics['cyclomatic_complexity'] = (
                    content.count('if ') +
                    content.count('elif ') +
                    content.count('for ') +
                    content.count('while ') +
                    content.count('except ') +
                    content.count('with ') +
                    1  # Base complexity
                )
                
                # Calculate nesting depth
                max_indent = 0
                for line in content.split('\n'):
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        max_indent = max(max_indent, indent // 4)
                metrics['nesting_depth'] = max_indent
            
            elif file_type in ['javascript', 'typescript']:
                metrics['cyclomatic_complexity'] = (
                    content.count('if (') +
                    content.count('if(') +
                    content.count('else if') +
                    content.count('for (') +
                    content.count('for(') +
                    content.count('while (') +
                    content.count('while(') +
                    content.count('catch') +
                    content.count('case ') +
                    1
                )
        
        except Exception as e:
            self.logger.error(f"Error calculating complexity for {file_path}: {e}")
        
        return metrics
    
    def _generate_ai_description(self, file_path: Path, doc_data: Dict) -> str:
        """Generate AI-powered description using Gemini"""
        
        if not self.config['gemini_integration']['enabled']:
            return "AI description generation disabled"
        
        try:
            # Prepare prompt for Gemini
            prompt = f"""Analyze this file and provide a concise technical description:
            
File: {doc_data['file_path']}
Type: {doc_data['extension']}
Size: {doc_data['size']} bytes
Functions: {len(doc_data['content_analysis']['functions'])}
Classes: {len(doc_data['content_analysis']['classes'])}
Lines of code: {doc_data['content_analysis']['lines_of_code']}

Provide a 2-3 sentence description of what this file does and its purpose in the project."""

            # Use Gemini trigger script if available
            gemini_script = Path(self.config['gemini_integration']['trigger_path']).expanduser() / 'simple-gemini-process.sh'
            
            if gemini_script.exists():
                result = subprocess.run(
                    [str(gemini_script), file_path, prompt],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "AI description generation not available"
        
        except Exception as e:
            self.logger.error(f"Error generating AI description: {e}")
            return "Error generating AI description"
    
    def generate_project_documentation(self, file_metadata: Dict[str, Dict]) -> Dict:
        """Generate documentation for entire project"""
        
        self.logger.info("Generating project documentation")
        
        project_doc = {
            'project_name': self.config['system']['name'],
            'generated_at': datetime.now().isoformat(),
            'total_files': len(file_metadata),
            'file_types': {},
            'statistics': {
                'total_lines': 0,
                'total_code_lines': 0,
                'total_comment_lines': 0,
                'total_functions': 0,
                'total_classes': 0
            },
            'files': {},
            'orphaned_files': [],
            'circular_dependencies': []
        }
        
        # Process each file
        for file_path_str, metadata in file_metadata.items():
            file_path = self.project_root / file_path_str
            
            if file_path.exists():
                file_doc = self.generate_file_documentation(file_path, metadata)
                project_doc['files'][file_path_str] = file_doc
                
                # Update statistics
                analysis = file_doc['content_analysis']
                project_doc['statistics']['total_lines'] += (
                    analysis['lines_of_code'] +
                    analysis['comment_lines'] +
                    analysis['blank_lines']
                )
                project_doc['statistics']['total_code_lines'] += analysis['lines_of_code']
                project_doc['statistics']['total_comment_lines'] += analysis['comment_lines']
                project_doc['statistics']['total_functions'] += len(analysis['functions'])
                project_doc['statistics']['total_classes'] += len(analysis['classes'])
                
                # Count file types
                ext = file_doc['extension']
                if ext:
                    project_doc['file_types'][ext] = project_doc['file_types'].get(ext, 0) + 1
        
        return project_doc
    
    def render_documentation(self, doc_data: Dict, format: str = 'markdown') -> str:
        """Render documentation in specified format"""
        
        if format == 'markdown':
            return self._render_markdown(doc_data)
        elif format == 'html':
            return self._render_html(doc_data)
        elif format == 'json':
            return json.dumps(doc_data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _render_markdown(self, doc_data: Dict) -> str:
        """Render documentation as Markdown"""
        
        # Create default template if it doesn't exist
        template_path = self.templates_dir / 'project_doc.md.j2'
        if not template_path.exists():
            self._create_default_templates()
        
        try:
            template = self.env.get_template('project_doc.md.j2')
            return template.render(doc=doc_data)
        except Exception as e:
            self.logger.error(f"Error rendering markdown: {e}")
            
            # Fallback to simple markdown
            lines = [
                f"# {doc_data.get('project_name', 'Project')} Documentation",
                f"\nGenerated: {doc_data.get('generated_at', 'Unknown')}",
                f"\nTotal Files: {doc_data.get('total_files', 0)}",
                "\n## Statistics",
                f"- Total Lines: {doc_data['statistics']['total_lines']}",
                f"- Code Lines: {doc_data['statistics']['total_code_lines']}",
                f"- Comment Lines: {doc_data['statistics']['total_comment_lines']}",
                f"- Functions: {doc_data['statistics']['total_functions']}",
                f"- Classes: {doc_data['statistics']['total_classes']}",
                "\n## Files"
            ]
            
            for file_path, file_doc in doc_data.get('files', {}).items():
                lines.append(f"\n### {file_path}")
                if file_doc.get('ai_description'):
                    lines.append(f"\n{file_doc['ai_description']}")
                lines.append(f"\n- Size: {file_doc.get('size', 0)} bytes")
                lines.append(f"- Modified: {file_doc.get('modified', 'Unknown')}")
                lines.append(f"- Tags: {', '.join(file_doc.get('tags', []))}")
            
            return '\n'.join(lines)
    
    def _render_html(self, doc_data: Dict) -> str:
        """Render documentation as HTML"""
        
        template_path = self.templates_dir / 'project_doc.html.j2'
        if not template_path.exists():
            self._create_default_templates()
        
        try:
            template = self.env.get_template('project_doc.html.j2')
            return template.render(doc=doc_data)
        except Exception as e:
            self.logger.error(f"Error rendering HTML: {e}")
            
            # Fallback to simple HTML
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{doc_data.get('project_name', 'Project')} Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .stats {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
        .file {{ margin: 20px 0; padding: 10px; border-left: 3px solid #007bff; }}
    </style>
</head>
<body>
    <h1>{doc_data.get('project_name', 'Project')} Documentation</h1>
    <p>Generated: {doc_data.get('generated_at', 'Unknown')}</p>
    <div class="stats">
        <h2>Statistics</h2>
        <ul>
            <li>Total Files: {doc_data.get('total_files', 0)}</li>
            <li>Code Lines: {doc_data['statistics']['total_code_lines']}</li>
            <li>Functions: {doc_data['statistics']['total_functions']}</li>
            <li>Classes: {doc_data['statistics']['total_classes']}</li>
        </ul>
    </div>
    <h2>Files</h2>
    {''.join([f'<div class="file"><h3>{path}</h3><p>{data.get("ai_description", "")}</p></div>' 
              for path, data in doc_data.get('files', {}).items()])}
</body>
</html>
"""
    
    def _create_default_templates(self):
        """Create default documentation templates"""
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Markdown template
        markdown_template = """# {{ doc.project_name }} Documentation

Generated: {{ doc.generated_at }}

## Project Overview

- **Total Files**: {{ doc.total_files }}
- **Code Lines**: {{ doc.statistics.total_code_lines }}
- **Comment Lines**: {{ doc.statistics.total_comment_lines }}
- **Functions**: {{ doc.statistics.total_functions }}
- **Classes**: {{ doc.statistics.total_classes }}

## File Types Distribution

{% for ext, count in doc.file_types.items() %}
- **{{ ext }}**: {{ count }} files
{% endfor %}

## Files Documentation

{% for file_path, file_doc in doc.files.items() %}
### {{ file_path }}

{% if file_doc.ai_description %}
{{ file_doc.ai_description }}
{% endif %}

**Details:**
- Size: {{ file_doc.size }} bytes
- Modified: {{ file_doc.modified }}
- Hash: {{ file_doc.hash[:8] }}...
- Tags: {{ file_doc.tags | join(', ') }}

**Code Metrics:**
- Lines of Code: {{ file_doc.content_analysis.lines_of_code }}
- Comment Lines: {{ file_doc.content_analysis.comment_lines }}
- Functions: {{ file_doc.content_analysis.functions | length }}
- Classes: {{ file_doc.content_analysis.classes | length }}
- Complexity: {{ file_doc.complexity_metrics.cyclomatic_complexity }}

{% if file_doc.content_analysis.functions %}
**Functions:**
{% for func in file_doc.content_analysis.functions %}
- `{{ func.name }}` (line {{ func.line }})
{% endfor %}
{% endif %}

{% if file_doc.content_analysis.classes %}
**Classes:**
{% for cls in file_doc.content_analysis.classes %}
- `{{ cls.name }}` (line {{ cls.line }})
{% endfor %}
{% endif %}

---
{% endfor %}

{% if doc.orphaned_files %}
## Orphaned Files

These files are not referenced by any other files in the project:
{% for file in doc.orphaned_files %}
- {{ file }}
{% endfor %}
{% endif %}

{% if doc.circular_dependencies %}
## Circular Dependencies

Warning: The following circular dependencies were detected:
{% for cycle in doc.circular_dependencies %}
- {{ cycle | join(' → ') }}
{% endfor %}
{% endif %}
"""
        
        with open(self.templates_dir / 'project_doc.md.j2', 'w') as f:
            f.write(markdown_template)
        
        # HTML template
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ doc.project_name }} Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card h4 { margin: 0 0 10px 0; color: #3498db; }
        .stat-card .value { font-size: 24px; font-weight: bold; }
        .file-card {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .file-header { display: flex; justify-content: space-between; align-items: center; }
        .tags { display: flex; gap: 5px; flex-wrap: wrap; margin: 10px 0; }
        .tag {
            background: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .metric { background: #ecf0f1; padding: 8px; border-radius: 4px; }
        code { background: #2c3e50; color: #ecf0f1; padding: 2px 5px; border-radius: 3px; }
        .warning { background: #f39c12; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .error { background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>{{ doc.project_name }} Documentation</h1>
    <p>Generated: {{ doc.generated_at }}</p>
    
    <h2>Project Statistics</h2>
    <div class="stats">
        <div class="stat-card">
            <h4>Total Files</h4>
            <div class="value">{{ doc.total_files }}</div>
        </div>
        <div class="stat-card">
            <h4>Code Lines</h4>
            <div class="value">{{ doc.statistics.total_code_lines }}</div>
        </div>
        <div class="stat-card">
            <h4>Functions</h4>
            <div class="value">{{ doc.statistics.total_functions }}</div>
        </div>
        <div class="stat-card">
            <h4>Classes</h4>
            <div class="value">{{ doc.statistics.total_classes }}</div>
        </div>
    </div>
    
    <h2>Files Documentation</h2>
    {% for file_path, file_doc in doc.files.items() %}
    <div class="file-card">
        <div class="file-header">
            <h3>{{ file_path }}</h3>
            <span>{{ file_doc.size }} bytes</span>
        </div>
        
        {% if file_doc.ai_description %}
        <p>{{ file_doc.ai_description }}</p>
        {% endif %}
        
        <div class="tags">
            {% for tag in file_doc.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        
        <div class="metrics">
            <div class="metric">Lines: {{ file_doc.content_analysis.lines_of_code }}</div>
            <div class="metric">Functions: {{ file_doc.content_analysis.functions | length }}</div>
            <div class="metric">Classes: {{ file_doc.content_analysis.classes | length }}</div>
            <div class="metric">Complexity: {{ file_doc.complexity_metrics.cyclomatic_complexity }}</div>
        </div>
        
        {% if file_doc.content_analysis.functions %}
        <h4>Functions:</h4>
        <ul>
        {% for func in file_doc.content_analysis.functions %}
            <li><code>{{ func.name }}</code> (line {{ func.line }})</li>
        {% endfor %}
        </ul>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if doc.orphaned_files %}
    <div class="warning">
        <h3>Orphaned Files</h3>
        <ul>
        {% for file in doc.orphaned_files %}
            <li>{{ file }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if doc.circular_dependencies %}
    <div class="error">
        <h3>Circular Dependencies</h3>
        <ul>
        {% for cycle in doc.circular_dependencies %}
            <li>{{ cycle | join(' → ') }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
</body>
</html>"""
        
        with open(self.templates_dir / 'project_doc.html.j2', 'w') as f:
            f.write(html_template)
        
        self.logger.info("Default templates created")
    
    def save_documentation(self, doc_data: Dict, formats: List[str] = None):
        """Save documentation in specified formats"""
        
        if formats is None:
            formats = self.config['documentation']['formats']
        
        for format in formats:
            try:
                rendered = self.render_documentation(doc_data, format)
                
                if format == 'markdown':
                    output_file = self.docs_output_dir / 'project_documentation.md'
                elif format == 'html':
                    output_file = self.docs_output_dir / 'project_documentation.html'
                elif format == 'json':
                    output_file = self.docs_output_dir / 'project_documentation.json'
                else:
                    continue
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(rendered)
                
                self.logger.info(f"Documentation saved to {output_file}")
                
            except Exception as e:
                self.logger.error(f"Error saving documentation in {format} format: {e}")
    
    def update_claude_context(self, doc_data: Dict):
        """Update CLAUDE.md file with project context - ЕДИНСТВЕННЫЙ РАЗРЕШЕННЫЙ ФАЙЛ ВНЕ DOC_SYSTEM"""
        
        if not self.config['claude_integration']['enabled']:
            return
        
        # СТРОГАЯ ПРОВЕРКА: только CLAUDE.md разрешено создавать в корне
        claude_file = self.project_root / 'CLAUDE.md'
        
        try:
            content = [
                "# GalaxyDevelopers DevSystem - AI Context",
                "## ⚠️ АВТОМАТИЧЕСКИ СГЕНЕРИРОВАННЫЙ ФАЙЛ - НЕ РЕДАКТИРОВАТЬ",
                f"Generated: {datetime.now().isoformat()}",
                "\n## 🚫 ИЗОЛЯЦИЯ DOC_SYSTEM",
                "DOC_SYSTEM работает в режиме READ-ONLY и НЕ изменяет основной проект!",
                "Единственное исключение - этот файл для контекста AI.",
                "\n## 📊 Обзор проекта",
                f"- Всего файлов: {doc_data['total_files']}",
                f"- Строк кода: {doc_data['statistics']['total_code_lines']}",
                f"- Функций: {doc_data['statistics']['total_functions']}",
                f"- Классов: {doc_data['statistics']['total_classes']}",
                "\n## 🗂️ Ключевые файлы проекта"
            ]
            
            # Добавляем только ключевые файлы (не все)
            key_files = 0
            for file_path, file_doc in doc_data.get('files', {}).items():
                if key_files >= 20:  # Ограничиваем количество
                    break
                    
                # Показываем только важные файлы
                if (file_doc.get('ai_description') and 
                    any(important in file_path.lower() for important in ['main', 'index', 'app', 'server', 'api', 'config'])):
                    
                    content.append(f"\n### {file_path}")
                    content.append(file_doc['ai_description'])
                    
                    if file_doc['content_analysis']['functions']:
                        funcs = [f['name'] for f in file_doc['content_analysis']['functions'][:3]]
                        content.append(f"Основные функции: {', '.join(funcs)}")
                    
                    key_files += 1
            
            # Добавляем проблемы только если они есть
            if 'orphaned_files' in doc_data and doc_data['orphaned_files']:
                content.append(f"\n## ⚠️ Неиспользуемые файлы ({len(doc_data['orphaned_files'])})")
                # Показываем только первые 10
                for file in list(doc_data['orphaned_files'])[:10]:
                    content.append(f"- {file}")
            
            content.extend([
                "\n## 🔧 DOC_SYSTEM API",
                "http://localhost:37777/api/status - статус системы документации",
                "\n---",
                f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])
            
            # ЕДИНСТВЕННАЯ РАЗРЕШЕННАЯ ОПЕРАЦИЯ ЗАПИСИ ВНЕ DOC_SYSTEM
            with open(claude_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Claude context updated (READ-ONLY mode active)")
            
        except Exception as e:
            self.logger.error(f"Error updating Claude context: {e}")


if __name__ == "__main__":
    generator = DocumentationGenerator()
    
    # Test with a sample file
    test_file = Path(__file__)
    doc = generator.generate_file_documentation(test_file)
    
    print("File Documentation:")
    print(json.dumps(doc, indent=2))
    
    # Generate project documentation
    project_doc = generator.generate_project_documentation({str(test_file.relative_to(test_file.parent.parent.parent)): {}})
    
    # Save in all formats
    generator.save_documentation(project_doc)
    
    # Update Claude context
    generator.update_claude_context(project_doc)