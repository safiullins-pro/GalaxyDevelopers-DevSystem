#!/usr/bin/env python3

import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
from enum import Enum

class ValidationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationRule:
    def __init__(self, name: str, level: ValidationLevel, check_func, message: str):
        self.name = name
        self.level = level
        self.check_func = check_func
        self.message = message

class ValidationAgent:
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.rules: List[ValidationRule] = []
        self.validation_results: Dict[str, List[Dict]] = {}
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize default rules
        self._initialize_rules()
    
    def _load_config(self, config_path: str) -> Dict:
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _initialize_rules(self):
        """Initialize validation rules based on configuration"""
        
        validation_config = self.config.get('validation', {})
        rules_config = validation_config.get('rules', [])
        
        # Documentation requirement rule
        if any(r == 'require_documentation' or (isinstance(r, dict) and r.get('require_documentation')) for r in rules_config):
            self.add_rule(
                name="require_documentation",
                level=ValidationLevel.WARNING,
                check_func=self._check_documentation,
                message="File lacks proper documentation"
            )
        
        # File size limit rule
        max_size = next((r.get('max_file_size') for r in rules_config if isinstance(r, dict) and 'max_file_size' in r), None)
        if max_size:
            self.add_rule(
                name="max_file_size",
                level=ValidationLevel.ERROR,
                check_func=lambda f, m: self._check_file_size(f, m, max_size),
                message=f"File exceeds maximum size of {max_size} bytes"
            )
        
        # Forbidden patterns rule
        forbidden = next((r.get('forbidden_patterns') for r in rules_config if isinstance(r, dict) and 'forbidden_patterns' in r), [])
        if forbidden:
            self.add_rule(
                name="forbidden_patterns",
                level=ValidationLevel.WARNING,
                check_func=lambda f, m: self._check_forbidden_patterns(f, m, forbidden),
                message=f"File contains forbidden patterns: {', '.join(forbidden)}"
            )
        
        # Test requirement rule
        if any(r == 'require_tests' or (isinstance(r, dict) and r.get('require_tests')) for r in rules_config):
            self.add_rule(
                name="require_tests",
                level=ValidationLevel.INFO,
                check_func=self._check_test_coverage,
                message="File lacks corresponding test file"
            )
        
        # Add custom validation rules
        self.add_rule(
            name="orphaned_file",
            level=ValidationLevel.WARNING,
            check_func=self._check_orphaned,
            message="File is orphaned (not referenced by any other file)"
        )
        
        self.add_rule(
            name="circular_dependency",
            level=ValidationLevel.ERROR,
            check_func=self._check_circular_dependency,
            message="File is part of a circular dependency"
        )
        
        self.add_rule(
            name="missing_imports",
            level=ValidationLevel.ERROR,
            check_func=self._check_missing_imports,
            message="File has missing or broken imports"
        )
        
        self.add_rule(
            name="code_complexity",
            level=ValidationLevel.INFO,
            check_func=self._check_complexity,
            message="File has high code complexity"
        )
        
        self.add_rule(
            name="naming_convention",
            level=ValidationLevel.WARNING,
            check_func=self._check_naming_convention,
            message="File or its contents violate naming conventions"
        )
    
    def add_rule(self, name: str, level: ValidationLevel, check_func, message: str):
        """Add a validation rule"""
        rule = ValidationRule(name, level, check_func, message)
        self.rules.append(rule)
        self.logger.debug(f"Added validation rule: {name}")
    
    def validate_file(self, file_path: Path, metadata: Dict = None) -> List[Dict]:
        """Validate a single file against all rules"""
        
        if not file_path.exists():
            return [{
                'rule': 'file_exists',
                'level': ValidationLevel.CRITICAL.value,
                'message': f"File does not exist: {file_path}",
                'passed': False
            }]
        
        results = []
        relative_path = file_path.relative_to(self.project_root)
        
        for rule in self.rules:
            try:
                passed = rule.check_func(file_path, metadata or {})
                
                if not passed:
                    results.append({
                        'rule': rule.name,
                        'level': rule.level.value,
                        'message': rule.message,
                        'passed': False,
                        'file': str(relative_path)
                    })
                    
                    self.logger.log(
                        getattr(logging, rule.level.value.upper()),
                        f"{relative_path}: {rule.message}"
                    )
                
            except Exception as e:
                self.logger.error(f"Error running rule {rule.name} on {file_path}: {e}")
                results.append({
                    'rule': rule.name,
                    'level': ValidationLevel.ERROR.value,
                    'message': f"Error running validation: {e}",
                    'passed': False,
                    'file': str(relative_path)
                })
        
        # Store results
        self.validation_results[str(relative_path)] = results
        
        return results
    
    def _check_documentation(self, file_path: Path, metadata: Dict) -> bool:
        """Check if file has proper documentation"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_type = self._get_file_type(file_path)
            
            # Check for docstrings in Python files
            if file_type == 'python':
                # Check for module docstring
                if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                    return False
                
                # Check for function/class docstrings
                import ast
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        if not ast.get_docstring(node):
                            return False
            
            # Check for JSDoc in JavaScript/TypeScript files
            elif file_type in ['javascript', 'typescript']:
                # Look for JSDoc comments
                if not re.search(r'/\*\*[\s\S]*?\*/', content):
                    # No JSDoc comments found
                    functions = re.findall(r'(?:export\s+)?(?:async\s+)?function\s+\w+', content)
                    classes = re.findall(r'(?:export\s+)?class\s+\w+', content)
                    if functions or classes:
                        return False
            
            # Check for comments in other files
            else:
                comment_ratio = self._calculate_comment_ratio(content, file_type)
                if comment_ratio < 0.05:  # Less than 5% comments
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking documentation for {file_path}: {e}")
            return True  # Don't fail on error
    
    def _check_file_size(self, file_path: Path, metadata: Dict, max_size: int) -> bool:
        """Check if file size is within limits"""
        file_size = file_path.stat().st_size
        return file_size <= max_size
    
    def _check_forbidden_patterns(self, file_path: Path, metadata: Dict, patterns: List[str]) -> bool:
        """Check for forbidden patterns in file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in patterns:
                if pattern in content:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking forbidden patterns in {file_path}: {e}")
            return True
    
    def _check_test_coverage(self, file_path: Path, metadata: Dict) -> bool:
        """Check if file has corresponding test file"""
        
        # Skip test files themselves
        if 'test' in file_path.name.lower() or 'spec' in file_path.name.lower():
            return True
        
        # Skip non-code files
        if file_path.suffix not in ['.py', '.js', '.jsx', '.ts', '.tsx']:
            return True
        
        # Look for corresponding test file
        test_patterns = [
            file_path.parent / f"test_{file_path.name}",
            file_path.parent / f"{file_path.stem}_test{file_path.suffix}",
            file_path.parent / f"{file_path.stem}.test{file_path.suffix}",
            file_path.parent / f"{file_path.stem}.spec{file_path.suffix}",
            file_path.parent.parent / 'tests' / f"test_{file_path.name}",
            file_path.parent.parent / 'test' / f"test_{file_path.name}",
        ]
        
        for test_file in test_patterns:
            if test_file.exists():
                return True
        
        return False
    
    def _check_orphaned(self, file_path: Path, metadata: Dict) -> bool:
        """Check if file is orphaned"""
        
        # Entry points are never orphaned
        entry_patterns = ['main.py', 'app.py', 'index.js', 'index.html', 'setup.py']
        if file_path.name in entry_patterns:
            return True
        
        # Check metadata for dependency information
        if metadata.get('dependents'):
            return True
        
        # If we have orphaned_files list in metadata
        relative_path = str(file_path.relative_to(self.project_root))
        if metadata.get('orphaned_files') and relative_path in metadata['orphaned_files']:
            return False
        
        return True
    
    def _check_circular_dependency(self, file_path: Path, metadata: Dict) -> bool:
        """Check if file is part of circular dependency"""
        
        relative_path = str(file_path.relative_to(self.project_root))
        
        # Check if file is in any circular dependency cycle
        circular_deps = metadata.get('circular_dependencies', [])
        for cycle in circular_deps:
            if relative_path in cycle:
                return False
        
        return True
    
    def _check_missing_imports(self, file_path: Path, metadata: Dict) -> bool:
        """Check for missing or broken imports"""
        
        try:
            file_type = self._get_file_type(file_path)
            
            if file_type == 'python':
                return self._check_python_imports(file_path)
            elif file_type in ['javascript', 'typescript']:
                return self._check_js_imports(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking imports in {file_path}: {e}")
            return True
    
    def _check_python_imports(self, file_path: Path) -> bool:
        """Check Python imports"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import ast
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Check if it's a local import
                        if not self._is_standard_library(alias.name):
                            module_path = self._resolve_python_import(alias.name, file_path)
                            if module_path and not (self.project_root / module_path).exists():
                                return False
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._is_standard_library(node.module):
                        module_path = self._resolve_python_import(node.module, file_path)
                        if module_path and not (self.project_root / module_path).exists():
                            return False
            
            return True
            
        except SyntaxError:
            return False  # Syntax error means broken imports
        except Exception:
            return True
    
    def _check_js_imports(self, file_path: Path) -> bool:
        """Check JavaScript/TypeScript imports"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all import statements
            import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)
            
            for import_path in imports:
                # Skip node_modules
                if not import_path.startswith('.'):
                    continue
                
                # Resolve relative import
                resolved = (file_path.parent / import_path).resolve()
                
                # Check with various extensions
                extensions = ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.jsx', '/index.ts', '/index.tsx']
                found = False
                
                for ext in extensions:
                    check_path = Path(str(resolved) + ext)
                    if check_path.exists():
                        found = True
                        break
                
                if not found:
                    return False
            
            return True
            
        except Exception:
            return True
    
    def _check_complexity(self, file_path: Path, metadata: Dict) -> bool:
        """Check code complexity"""
        
        # Get complexity from metadata if available
        if metadata.get('complexity_metrics'):
            complexity = metadata['complexity_metrics'].get('cyclomatic_complexity', 0)
            return complexity <= 20  # Threshold for high complexity
        
        # Calculate complexity if not in metadata
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple complexity check based on control flow statements
            complexity = 1  # Base complexity
            complexity += content.count('if ')
            complexity += content.count('elif ')
            complexity += content.count('else:')
            complexity += content.count('for ')
            complexity += content.count('while ')
            complexity += content.count('except ')
            complexity += content.count('case ')
            
            return complexity <= 20
            
        except Exception:
            return True
    
    def _check_naming_convention(self, file_path: Path, metadata: Dict) -> bool:
        """Check naming conventions"""
        
        file_name = file_path.stem
        file_type = self._get_file_type(file_path)
        
        # Check file naming
        if file_type == 'python':
            # Python files should be snake_case
            if not re.match(r'^[a-z_][a-z0-9_]*$', file_name) and file_name != '__init__':
                return False
        
        elif file_type in ['javascript', 'typescript']:
            # JS/TS files can be camelCase or kebab-case
            if not re.match(r'^[a-z][a-zA-Z0-9]*$', file_name) and not re.match(r'^[a-z]+(-[a-z]+)*$', file_name):
                # Allow index and special files
                if file_name not in ['index', 'app', 'App', 'main', 'Main']:
                    return False
        
        # Check content naming conventions
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_type == 'python':
                # Check function names (should be snake_case)
                functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                for func in functions:
                    if not re.match(r'^[a-z_][a-z0-9_]*$', func):
                        # Allow special methods
                        if not func.startswith('__') and not func.endswith('__'):
                            return False
                
                # Check class names (should be PascalCase)
                classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                for cls in classes:
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', cls):
                        return False
            
            return True
            
        except Exception:
            return True
    
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
            '.html': 'html',
        }
        return type_map.get(ext, 'unknown')
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is from Python standard library"""
        standard_libs = {
            'os', 'sys', 'json', 'yaml', 're', 'ast', 'pathlib', 'datetime',
            'logging', 'typing', 'collections', 'enum', 'hashlib', 'subprocess',
            'threading', 'queue', 'time', 'math', 'random', 'itertools', 'functools'
        }
        
        # Check if it's a standard library module
        base_module = module_name.split('.')[0]
        return base_module in standard_libs
    
    def _resolve_python_import(self, module_name: str, from_file: Path) -> Optional[str]:
        """Resolve Python import to file path"""
        module_parts = module_name.split('.')
        
        # Try relative to current file
        current_dir = from_file.parent
        possible_paths = [
            current_dir / Path(*module_parts).with_suffix('.py'),
            current_dir / Path(*module_parts) / '__init__.py',
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.relative_to(self.project_root))
        
        return None
    
    def _calculate_comment_ratio(self, content: str, file_type: str) -> float:
        """Calculate ratio of comment lines to total lines"""
        
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = 0
        
        for line in lines:
            line_stripped = line.strip()
            if self._is_comment(line_stripped, file_type):
                comment_lines += 1
        
        return comment_lines / total_lines if total_lines > 0 else 0
    
    def _is_comment(self, line: str, file_type: str) -> bool:
        """Check if line is a comment"""
        comment_markers = {
            'python': ['#'],
            'javascript': ['//', '/*', '*/', '*'],
            'typescript': ['//', '/*', '*/', '*'],
            'css': ['/*', '*/', '*'],
            'html': ['<!--', '-->'],
        }
        
        markers = comment_markers.get(file_type, [])
        return any(line.startswith(marker) for marker in markers)
    
    def validate_project(self, file_metadata: Dict[str, Dict]) -> Dict:
        """Validate entire project"""
        
        self.logger.info("Starting project validation")
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(file_metadata),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': 0,
            'critical': 0,
            'files': {}
        }
        
        for file_path_str, metadata in file_metadata.items():
            file_path = self.project_root / file_path_str
            
            if file_path.exists():
                results = self.validate_file(file_path, metadata)
                all_results['files'][file_path_str] = results
                
                # Count issues by level
                for result in results:
                    if not result['passed']:
                        level = result['level']
                        if level == 'warning':
                            all_results['warnings'] += 1
                        elif level == 'error':
                            all_results['errors'] += 1
                        elif level == 'critical':
                            all_results['critical'] += 1
                
                # Count files that passed all validations
                if all(r.get('passed', True) for r in results):
                    all_results['passed'] += 1
                else:
                    all_results['failed'] += 1
        
        self.logger.info(f"Validation complete: {all_results['passed']} passed, {all_results['failed']} failed")
        
        return all_results
    
    def should_block_operation(self, validation_results: List[Dict]) -> bool:
        """Determine if operation should be blocked based on validation results"""
        
        if not self.config['validation'].get('blocking_mode', False):
            return False
        
        # Block on critical or error level issues
        for result in validation_results:
            if not result['passed'] and result['level'] in ['critical', 'error']:
                return True
        
        return False
    
    def generate_report(self, validation_results: Dict) -> str:
        """Generate validation report"""
        
        lines = [
            "# Validation Report",
            f"\nGenerated: {validation_results['timestamp']}",
            f"\n## Summary",
            f"- Total Files: {validation_results['total_files']}",
            f"- Passed: {validation_results['passed']}",
            f"- Failed: {validation_results['failed']}",
            f"- Warnings: {validation_results['warnings']}",
            f"- Errors: {validation_results['errors']}",
            f"- Critical: {validation_results['critical']}",
            "\n## Issues by File\n"
        ]
        
        for file_path, results in validation_results['files'].items():
            issues = [r for r in results if not r['passed']]
            if issues:
                lines.append(f"\n### {file_path}")
                for issue in issues:
                    level_emoji = {
                        'info': 'ℹ️',
                        'warning': '⚠️',
                        'error': '❌',
                        'critical': '🚨'
                    }.get(issue['level'], '•')
                    lines.append(f"- {level_emoji} **{issue['rule']}**: {issue['message']}")
        
        return '\n'.join(lines)
    
    def save_report(self, validation_results: Dict, output_path: Path = None):
        """Save validation report to file"""
        
        if output_path is None:
            output_path = self.project_root / 'DOC_SYSTEM' / 'docs' / 'validation_report.md'
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report(validation_results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Also save JSON version
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
        
        self.logger.info(f"Validation report saved to {output_path}")


if __name__ == "__main__":
    validator = ValidationAgent()
    
    # Test validation on this file
    test_file = Path(__file__)
    results = validator.validate_file(test_file)
    
    print("Validation Results:")
    for result in results:
        if not result['passed']:
            print(f"- {result['level']}: {result['rule']} - {result['message']}")
    
    # Test blocking logic
    if validator.should_block_operation(results):
        print("\n⛔ Operation would be BLOCKED due to validation failures")
    else:
        print("\n✅ Operation would be ALLOWED")