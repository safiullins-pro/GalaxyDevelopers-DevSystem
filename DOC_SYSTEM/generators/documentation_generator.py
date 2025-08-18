#!/usr/bin/env python3

import os
import ast
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import logging
from jinja2 import Template

class DocumentationGenerator:
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.templates = {}
        self.logger = self._setup_logger()
        self._load_templates()
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocumentationGenerator')
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        handler = logging.FileHandler(
            Path(self.project_root) / 'DOC_SYSTEM' / self.config['logging']['file']
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def _load_templates(self):
        self.templates['file'] = """# {{ file_name }}

## Описание
{{ description }}

## Путь
`{{ file_path }}`

## Метаданные
- **Размер**: {{ size }} байт
- **Создан**: {{ created }}
- **Изменен**: {{ modified }}
- **Хеш**: {{ hash }}

## Зависимости

### Внутренние зависимости
{% for dep in dependencies.internal %}
- `{{ dep }}`
{% endfor %}

### Внешние зависимости
{% for dep in dependencies.external %}
- `{{ dep }}`
{% endfor %}

## Функции и классы
{% for item in code_elements %}
### {{ item.type }}: `{{ item.name }}`
{{ item.description }}
{% if item.params %}
**Параметры:**
{% for param in item.params %}
- `{{ param.name }}`: {{ param.description }}
{% endfor %}
{% endif %}
{% endfor %}

## Статус
- **Orphaned**: {{ is_orphan }}
- **Покрыт тестами**: {{ has_tests }}
- **Документирован**: {{ is_documented }}

---
*Сгенерировано автоматически системой GalaxyDevSystem AutoDoc*
"""

        self.templates['overview'] = """# Обзор проекта GalaxyDevelopers DevSystem

## Статистика
- **Всего файлов**: {{ total_files }}
- **Всего зависимостей**: {{ total_dependencies }}
- **Orphaned файлов**: {{ orphaned_files }}
- **Циклических зависимостей**: {{ circular_dependencies }}

## Структура проекта
```
{{ project_structure }}
```

## Ключевые компоненты
{% for component in key_components %}
### {{ component.name }}
- **Путь**: `{{ component.path }}`
- **Описание**: {{ component.description }}
- **Зависимости**: {{ component.dependency_count }}
{% endfor %}

## Проблемы требующие внимания
{% for issue in issues %}
- {{ issue }}
{% endfor %}

---
*Обновлено: {{ updated_at }}*
"""

    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        code_elements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'type': 'Класс',
                        'name': node.name,
                        'description': ast.get_docstring(node) or 'Нет описания',
                        'params': []
                    }
                    
                    # Find __init__ method
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                            class_info['params'] = self._extract_params(item)
                            break
                            
                    code_elements.append(class_info)
                    
                elif isinstance(node, ast.FunctionDef):
                    # Skip methods inside classes
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                        func_info = {
                            'type': 'Функция',
                            'name': node.name,
                            'description': ast.get_docstring(node) or 'Нет описания',
                            'params': self._extract_params(node)
                        }
                        code_elements.append(func_info)
                        
        except Exception as e:
            self.logger.error(f"Error analyzing Python file {file_path}: {e}")
            
        return {'code_elements': code_elements}
        
    def _extract_params(self, func_node: ast.FunctionDef) -> List[Dict]:
        params = []
        for arg in func_node.args.args:
            if arg.arg != 'self':
                params.append({
                    'name': arg.arg,
                    'description': 'Параметр функции'
                })
        return params
        
    def analyze_javascript_file(self, file_path: Path) -> Dict[str, Any]:
        code_elements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract functions
            func_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
            for match in re.finditer(func_pattern, content):
                func_name = match.group(1) or match.group(2)
                code_elements.append({
                    'type': 'Функция',
                    'name': func_name,
                    'description': 'JavaScript функция',
                    'params': []
                })
                
            # Extract classes
            class_pattern = r'class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                code_elements.append({
                    'type': 'Класс',
                    'name': match.group(1),
                    'description': 'JavaScript класс',
                    'params': []
                })
                
        except Exception as e:
            self.logger.error(f"Error analyzing JavaScript file {file_path}: {e}")
            
        return {'code_elements': code_elements}
        
    def generate_ai_description(self, file_path: Path, content: str = None) -> str:
        if not self.config['documentation']['ai_powered']:
            return "Автоматическое описание недоступно"
            
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:1000]  # First 1000 chars
            except:
                return "Не удалось прочитать файл"
                
        # Integration with Gemini
        if self.config['gemini_integration']['enabled']:
            try:
                prompt = f"Опиши назначение этого файла в 2-3 предложениях:\n{content[:500]}"
                result = self._call_gemini_api(prompt)
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"Gemini API error: {e}")
                
        # Fallback to simple analysis
        if 'class' in content.lower() or 'def' in content.lower():
            return "Файл содержит определения классов и функций"
        elif 'import' in content.lower() or 'require' in content.lower():
            return "Модуль с импортами и зависимостями"
        else:
            return "Файл кода проекта"
            
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        try:
            gemini_script = Path.home() / "Scripts/gemini-triggers/simple-gemini-process.sh"
            if gemini_script.exists():
                result = subprocess.run(
                    [str(gemini_script), "-", prompt],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error calling Gemini: {e}")
        return None
        
    def generate_file_documentation(self, file_path: Path, metadata: Dict) -> str:
        relative_path = file_path.relative_to(self.project_root)
        
        # Analyze code structure
        code_analysis = {}
        if file_path.suffix == '.py':
            code_analysis = self.analyze_python_file(file_path)
        elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            code_analysis = self.analyze_javascript_file(file_path)
            
        # Get AI description
        description = self.generate_ai_description(file_path)
        
        # Check for tests
        has_tests = self._check_has_tests(file_path)
        
        # Prepare template data
        template_data = {
            'file_name': file_path.name,
            'file_path': str(relative_path),
            'description': description,
            'size': metadata.get('size', 0),
            'created': metadata.get('created', ''),
            'modified': metadata.get('modified', ''),
            'hash': metadata.get('hash', ''),
            'dependencies': metadata.get('dependencies', {'internal': [], 'external': []}),
            'code_elements': code_analysis.get('code_elements', []),
            'is_orphan': metadata.get('is_orphan', False),
            'has_tests': has_tests,
            'is_documented': bool(description and description != "Автоматическое описание недоступно")
        }
        
        # Render template
        template = Template(self.templates['file'])
        return template.render(**template_data)
        
    def _check_has_tests(self, file_path: Path) -> bool:
        test_patterns = ['test_', '_test.', '.test.', '.spec.']
        file_name = file_path.stem.lower()
        
        # Check if this is a test file
        if any(pattern in file_name for pattern in test_patterns):
            return True
            
        # Check if test file exists for this file
        test_dir = file_path.parent / 'tests'
        if test_dir.exists():
            for pattern in test_patterns:
                test_file = test_dir / f"{pattern}{file_path.name}"
                if test_file.exists():
                    return True
                    
        return False
        
    def generate_project_overview(self, statistics: Dict, files_metadata: Dict) -> str:
        # Find key components
        key_components = self._identify_key_components(files_metadata)
        
        # Find issues
        issues = self._identify_issues(statistics, files_metadata)
        
        # Generate project structure
        project_structure = self._generate_tree_structure()
        
        template_data = {
            'total_files': statistics.get('total_files', 0),
            'total_dependencies': statistics.get('total_dependencies', 0),
            'orphaned_files': statistics.get('orphaned_files', 0),
            'circular_dependencies': statistics.get('circular_dependencies', 0),
            'project_structure': project_structure,
            'key_components': key_components,
            'issues': issues,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        template = Template(self.templates['overview'])
        return template.render(**template_data)
        
    def _identify_key_components(self, files_metadata: Dict) -> List[Dict]:
        components = []
        
        # Find main entry points
        for path, metadata in files_metadata.items():
            if any(pattern in path.lower() for pattern in ['main.', 'index.', 'app.', 'server.']):
                components.append({
                    'name': Path(path).name,
                    'path': path,
                    'description': metadata.get('description', 'Точка входа приложения'),
                    'dependency_count': len(metadata.get('dependencies', {}).get('internal', []))
                })
                
        return components[:10]  # Top 10 components
        
    def _identify_issues(self, statistics: Dict, files_metadata: Dict) -> List[str]:
        issues = []
        
        if statistics.get('orphaned_files', 0) > 0:
            issues.append(f"Обнаружено {statistics['orphaned_files']} неиспользуемых файлов")
            
        if statistics.get('circular_dependencies', 0) > 0:
            issues.append(f"Обнаружено {statistics['circular_dependencies']} циклических зависимостей")
            
        # Check for undocumented files
        undocumented = sum(1 for m in files_metadata.values() if not m.get('documentation'))
        if undocumented > 0:
            issues.append(f"{undocumented} файлов без документации")
            
        # Check for files without tests
        untested = sum(1 for path in files_metadata.keys() if not self._check_has_tests(Path(self.project_root) / path))
        if untested > 0:
            issues.append(f"{untested} файлов без тестов")
            
        return issues
        
    def _generate_tree_structure(self) -> str:
        try:
            result = subprocess.run(
                ['tree', '-L', '3', '-I', 'node_modules|__pycache__|.git', str(self.project_root)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
            
        # Fallback to simple listing
        lines = []
        for root, dirs, files in os.walk(self.project_root):
            level = root.replace(str(self.project_root), '').count(os.sep)
            if level < 3:
                indent = ' ' * 2 * level
                lines.append(f'{indent}{os.path.basename(root)}/')
                sub_indent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # Show first 5 files
                    lines.append(f'{sub_indent}{file}')
                    
        return '\n'.join(lines)
        
    def generate_all_documentation(self, files_metadata: Dict, statistics: Dict):
        self.logger.info("Starting documentation generation...")
        
        docs_dir = Path(self.project_root) / 'DOC_SYSTEM' / 'docs'
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate overview
        overview = self.generate_project_overview(statistics, files_metadata)
        with open(docs_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(overview)
            
        # Generate file documentation
        for file_path_str, metadata in files_metadata.items():
            file_path = Path(self.project_root) / file_path_str
            if file_path.exists():
                doc = self.generate_file_documentation(file_path, metadata)
                
                # Save documentation
                doc_path = docs_dir / f"{file_path_str.replace('/', '_')}.md"
                doc_path.parent.mkdir(parents=True, exist_ok=True)
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(doc)
                    
                # Update metadata with documentation
                metadata['documentation'] = doc
                
        self.logger.info(f"Documentation generated for {len(files_metadata)} files")
        
    def export_to_claude_context(self, files_metadata: Dict, statistics: Dict) -> str:
        context = f"""# GalaxyDevelopers DevSystem - Контекст проекта

## Обзор системы
- Всего файлов: {statistics.get('total_files', 0)}
- Зависимостей: {statistics.get('total_dependencies', 0)}
- Orphaned файлов: {statistics.get('orphaned_files', 0)}

## Структура файлов
"""
        
        for path, metadata in files_metadata.items():
            context += f"\n### {path}\n"
            context += f"- Размер: {metadata.get('size', 0)} байт\n"
            context += f"- Зависимости: {len(metadata.get('dependencies', {}).get('internal', []))}\n"
            context += f"- Orphaned: {metadata.get('is_orphan', False)}\n"
            
        return context

if __name__ == "__main__":
    generator = DocumentationGenerator()
    
    # Example usage
    test_metadata = {
        'test.py': {
            'size': 1024,
            'created': '2024-01-01',
            'modified': '2024-01-02',
            'hash': 'abc123',
            'dependencies': {'internal': ['module1.py'], 'external': ['requests']},
            'is_orphan': False
        }
    }
    
    stats = {
        'total_files': 100,
        'total_dependencies': 250,
        'orphaned_files': 5,
        'circular_dependencies': 2
    }
    
    generator.generate_all_documentation(test_metadata, stats)