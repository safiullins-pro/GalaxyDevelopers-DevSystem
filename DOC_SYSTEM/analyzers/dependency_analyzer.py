#!/usr/bin/env python3

import os
import re
import ast
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import networkx as nx
import logging
from datetime import datetime

class DependencyAnalyzer:
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.dependency_graph = nx.DiGraph()
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.orphaned_files: Set[str] = set()
        self.circular_dependencies: List[List[str]] = []
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for different languages
        self.import_patterns = {
            'python': [
                r'^import\s+(\S+)',
                r'^from\s+(\S+)\s+import',
            ],
            'javascript': [
                r'^import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'^const\s+.*\s+=\s+require\([\'"]([^\'"]+)[\'"]\)',
                r'^import\s+[\'"]([^\'"]+)[\'"]',
            ],
            'typescript': [
                r'^import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'^import\s+type\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'^import\s+[\'"]([^\'"]+)[\'"]',
            ],
            'css': [
                r'@import\s+[\'"]([^\'"]+)[\'"]',
                r'@import\s+url\([\'"]([^\'"]+)[\'"]\)',
            ],
            'html': [
                r'<script\s+.*src=[\'"]([^\'"]+)[\'"]',
                r'<link\s+.*href=[\'"]([^\'"]+)[\'"]',
                r'<img\s+.*src=[\'"]([^\'"]+)[\'"]',
            ]
        }
    
    def _load_config(self, config_path: str) -> Dict:
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def analyze_file(self, file_path: Path) -> Set[str]:
        """Analyze a single file for dependencies"""
        dependencies = set()
        
        if not file_path.exists():
            return dependencies
        
        file_type = self._get_file_type(file_path)
        
        if file_type == 'python':
            dependencies = self._analyze_python_file(file_path)
        elif file_type in ['javascript', 'typescript']:
            dependencies = self._analyze_js_file(file_path, file_type)
        elif file_type == 'css':
            dependencies = self._analyze_css_file(file_path)
        elif file_type == 'html':
            dependencies = self._analyze_html_file(file_path)
        
        return dependencies
    
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
            '.sass': 'css',
            '.html': 'html',
            '.htm': 'html',
        }
        return type_map.get(ext, 'unknown')
    
    def _analyze_python_file(self, file_path: Path) -> Set[str]:
        """Analyze Python file for imports"""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_path = self._resolve_python_import(alias.name, file_path)
                        if module_path:
                            dependencies.add(str(module_path))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_path = self._resolve_python_import(node.module, file_path)
                        if module_path:
                            dependencies.add(str(module_path))
        
        except Exception as e:
            self.logger.error(f"Error analyzing Python file {file_path}: {e}")
        
        return dependencies
    
    def _resolve_python_import(self, module_name: str, from_file: Path) -> Optional[Path]:
        """Resolve Python import to actual file path"""
        # Convert module name to path
        module_parts = module_name.split('.')
        
        # Check relative to current file
        current_dir = from_file.parent
        possible_paths = [
            current_dir / Path(*module_parts).with_suffix('.py'),
            current_dir / Path(*module_parts) / '__init__.py',
        ]
        
        # Check relative to project root
        possible_paths.extend([
            self.project_root / Path(*module_parts).with_suffix('.py'),
            self.project_root / Path(*module_parts) / '__init__.py',
        ])
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                return path.relative_to(self.project_root)
        
        return None
    
    def _analyze_js_file(self, file_path: Path, file_type: str) -> Set[str]:
        """Analyze JavaScript/TypeScript file for imports"""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = self.import_patterns.get(file_type, [])
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    resolved_path = self._resolve_js_import(match, file_path)
                    if resolved_path:
                        dependencies.add(str(resolved_path))
        
        except Exception as e:
            self.logger.error(f"Error analyzing JS/TS file {file_path}: {e}")
        
        return dependencies
    
    def _resolve_js_import(self, import_path: str, from_file: Path) -> Optional[Path]:
        """Resolve JavaScript/TypeScript import to actual file path"""
        # Skip node_modules and external packages
        if import_path.startswith('@') or not import_path.startswith('.'):
            return None
        
        current_dir = from_file.parent
        import_path_obj = current_dir / import_path
        
        # Try different extensions
        possible_paths = [
            import_path_obj.with_suffix('.js'),
            import_path_obj.with_suffix('.jsx'),
            import_path_obj.with_suffix('.ts'),
            import_path_obj.with_suffix('.tsx'),
            import_path_obj / 'index.js',
            import_path_obj / 'index.jsx',
            import_path_obj / 'index.ts',
            import_path_obj / 'index.tsx',
        ]
        
        # If already has extension
        if import_path_obj.suffix:
            possible_paths.insert(0, import_path_obj)
        
        for path in possible_paths:
            resolved = path.resolve()
            if resolved.exists() and resolved.is_file():
                try:
                    return resolved.relative_to(self.project_root)
                except ValueError:
                    return None
        
        return None
    
    def _analyze_css_file(self, file_path: Path) -> Set[str]:
        """Analyze CSS file for imports"""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = self.import_patterns.get('css', [])
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    resolved_path = self._resolve_css_import(match, file_path)
                    if resolved_path:
                        dependencies.add(str(resolved_path))
        
        except Exception as e:
            self.logger.error(f"Error analyzing CSS file {file_path}: {e}")
        
        return dependencies
    
    def _resolve_css_import(self, import_path: str, from_file: Path) -> Optional[Path]:
        """Resolve CSS import to actual file path"""
        if import_path.startswith('http'):
            return None
        
        current_dir = from_file.parent
        resolved = (current_dir / import_path).resolve()
        
        if resolved.exists() and resolved.is_file():
            try:
                return resolved.relative_to(self.project_root)
            except ValueError:
                return None
        
        return None
    
    def _analyze_html_file(self, file_path: Path) -> Set[str]:
        """Analyze HTML file for resource references"""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = self.import_patterns.get('html', [])
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if not match.startswith('http'):
                        resolved_path = self._resolve_html_import(match, file_path)
                        if resolved_path:
                            dependencies.add(str(resolved_path))
        
        except Exception as e:
            self.logger.error(f"Error analyzing HTML file {file_path}: {e}")
        
        return dependencies
    
    def _resolve_html_import(self, import_path: str, from_file: Path) -> Optional[Path]:
        """Resolve HTML resource reference to actual file path"""
        if import_path.startswith('http') or import_path.startswith('//'):
            return None
        
        current_dir = from_file.parent
        
        if import_path.startswith('/'):
            resolved = (self.project_root / import_path[1:]).resolve()
        else:
            resolved = (current_dir / import_path).resolve()
        
        if resolved.exists() and resolved.is_file():
            try:
                return resolved.relative_to(self.project_root)
            except ValueError:
                return None
        
        return None
    
    def build_dependency_graph(self, files: List[Path] = None):
        """Build complete dependency graph for project"""
        if files is None:
            files = list(self.project_root.rglob('*'))
            files = [f for f in files if f.is_file() and not self._should_ignore(f)]
        
        self.logger.info(f"Building dependency graph for {len(files)} files")
        
        # Clear existing data
        self.dependency_graph.clear()
        self.file_dependencies.clear()
        self.reverse_dependencies.clear()
        
        # Analyze each file
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            dependencies = self.analyze_file(file_path)
            
            self.file_dependencies[str(relative_path)] = dependencies
            self.dependency_graph.add_node(str(relative_path))
            
            for dep in dependencies:
                self.dependency_graph.add_edge(str(relative_path), dep)
                self.reverse_dependencies[dep].add(str(relative_path))
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        # Find orphaned files
        self._find_orphaned_files()
        
        self.logger.info("Dependency graph built successfully")
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = self.config['monitoring']['file_watcher']['ignore_patterns']
        path_str = str(path)
        
        for pattern in ignore_patterns:
            if pattern.replace('**', '').replace('*', '') in path_str:
                return True
        
        return False
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies in the graph"""
        self.circular_dependencies = list(nx.simple_cycles(self.dependency_graph))
        
        if self.circular_dependencies:
            self.logger.warning(f"Found {len(self.circular_dependencies)} circular dependencies")
            for cycle in self.circular_dependencies:
                self.logger.warning(f"Circular dependency: {' -> '.join(cycle)}")
    
    def _find_orphaned_files(self):
        """Find files that are not referenced by any other file"""
        all_files = set(self.file_dependencies.keys())
        referenced_files = set()
        
        for deps in self.file_dependencies.values():
            referenced_files.update(deps)
        
        # Files with no incoming dependencies (except entry points)
        entry_points = self._identify_entry_points()
        self.orphaned_files = all_files - referenced_files - entry_points
        
        if self.orphaned_files:
            self.logger.info(f"Found {len(self.orphaned_files)} orphaned files")
    
    def _identify_entry_points(self) -> Set[str]:
        """Identify entry point files"""
        entry_points = set()
        
        # Common entry point patterns
        entry_patterns = [
            'main.py', 'app.py', 'index.js', 'index.html',
            'server.py', 'server.js', 'setup.py', 'package.json',
            '__main__.py', 'start.py', 'run.py'
        ]
        
        for file_path in self.file_dependencies.keys():
            file_name = Path(file_path).name
            if file_name in entry_patterns:
                entry_points.add(file_path)
        
        return entry_points
    
    def get_file_dependencies(self, file_path: str) -> Set[str]:
        """Get direct dependencies of a file"""
        return self.file_dependencies.get(file_path, set())
    
    def get_file_dependents(self, file_path: str) -> Set[str]:
        """Get files that depend on this file"""
        return self.reverse_dependencies.get(file_path, set())
    
    def get_dependency_chain(self, file_path: str, max_depth: int = None) -> Dict[str, Any]:
        """Get full dependency chain for a file"""
        if max_depth is None:
            max_depth = self.config['dependency_analysis']['depth_limit']
        
        chain = {'file': file_path, 'dependencies': {}}
        visited = set()
        
        def traverse(path: str, current_chain: Dict, depth: int):
            if depth >= max_depth or path in visited:
                return
            
            visited.add(path)
            deps = self.get_file_dependencies(path)
            
            for dep in deps:
                current_chain[dep] = {'file': dep, 'dependencies': {}}
                traverse(dep, current_chain[dep]['dependencies'], depth + 1)
        
        traverse(file_path, chain['dependencies'], 0)
        
        return chain
    
    def export_graph(self, format: str = None) -> str:
        """Export dependency graph in specified format"""
        if format is None:
            format = self.config['dependency_analysis']['graph_format']
        
        if format == 'json':
            return self._export_json()
        elif format == 'dot':
            return self._export_dot()
        elif format == 'mermaid':
            return self._export_mermaid()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self) -> str:
        """Export graph as JSON"""
        graph_data = {
            'nodes': list(self.dependency_graph.nodes()),
            'edges': list(self.dependency_graph.edges()),
            'orphaned_files': list(self.orphaned_files),
            'circular_dependencies': self.circular_dependencies,
            'statistics': {
                'total_files': len(self.file_dependencies),
                'total_dependencies': sum(len(deps) for deps in self.file_dependencies.values()),
                'orphaned_count': len(self.orphaned_files),
                'circular_count': len(self.circular_dependencies)
            }
        }
        
        return json.dumps(graph_data, indent=2)
    
    def _export_dot(self) -> str:
        """Export graph as DOT format"""
        lines = ['digraph dependencies {']
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box];')
        
        # Add nodes
        for node in self.dependency_graph.nodes():
            color = 'red' if node in self.orphaned_files else 'black'
            lines.append(f'  "{node}" [color={color}];')
        
        # Add edges
        for source, target in self.dependency_graph.edges():
            lines.append(f'  "{source}" -> "{target}";')
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def _export_mermaid(self) -> str:
        """Export graph as Mermaid format"""
        lines = ['graph LR']
        
        # Add edges
        for source, target in self.dependency_graph.edges():
            source_id = source.replace('/', '_').replace('.', '_')
            target_id = target.replace('/', '_').replace('.', '_')
            lines.append(f'  {source_id}[{source}] --> {target_id}[{target}]')
        
        # Mark orphaned files
        for orphan in self.orphaned_files:
            orphan_id = orphan.replace('/', '_').replace('.', '_')
            lines.append(f'  style {orphan_id} fill:#f9f,stroke:#333,stroke-width:2px')
        
        return '\n'.join(lines)
    
    def get_statistics(self) -> Dict:
        """Get statistics about the dependency graph"""
        return {
            'total_files': len(self.file_dependencies),
            'total_dependencies': sum(len(deps) for deps in self.file_dependencies.values()),
            'orphaned_files': len(self.orphaned_files),
            'circular_dependencies': len(self.circular_dependencies),
            'average_dependencies': sum(len(deps) for deps in self.file_dependencies.values()) / max(len(self.file_dependencies), 1),
            'max_depth': self._calculate_max_depth()
        }
    
    def _calculate_max_depth(self) -> int:
        """Calculate maximum dependency depth in the graph"""
        if not self.dependency_graph.nodes():
            return 0
        
        max_depth = 0
        for node in self.dependency_graph.nodes():
            try:
                # Find all paths from this node
                paths = nx.single_source_shortest_path_length(self.dependency_graph, node)
                if paths:
                    depth = max(paths.values())
                    max_depth = max(max_depth, depth)
            except:
                continue
        
        return max_depth
    
    def save_analysis(self, output_path: Path = None):
        """Save dependency analysis to file"""
        if output_path is None:
            output_path = self.project_root / 'DOC_SYSTEM' / 'metadata' / 'dependencies.json'
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'graph': json.loads(self._export_json()),
            'file_dependencies': {k: list(v) for k, v in self.file_dependencies.items()},
            'reverse_dependencies': {k: list(v) for k, v in self.reverse_dependencies.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2)
        
        self.logger.info(f"Analysis saved to {output_path}")


if __name__ == "__main__":
    analyzer = DependencyAnalyzer()
    
    # Build dependency graph for entire project
    analyzer.build_dependency_graph()
    
    # Export in different formats
    print("Dependency Graph (JSON):")
    print(analyzer.export_graph('json'))
    
    # Find orphaned files
    if analyzer.orphaned_files:
        print(f"\nOrphaned files: {analyzer.orphaned_files}")
    
    # Save analysis
    analyzer.save_analysis()