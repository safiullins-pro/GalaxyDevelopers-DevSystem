#!/usr/bin/env python3
"""
📝 COMPOSER AGENT
Агент для генерации документации
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import textwrap

class ComposerAgent:
    """Агент генерации документации"""
    
    def __init__(self):
        self.name = "ComposerAgent"
        self.priority = 3
        self.status = "idle"
        self.current_task = None
        
        # Шаблоны документации
        self.templates = {
            "readme": self._get_readme_template(),
            "api": self._get_api_template(),
            "class": self._get_class_template(),
            "function": self._get_function_template(),
            "project": self._get_project_template()
        }
        
        # Статистика
        self.stats = {
            "docs_generated": 0,
            "files_documented": 0,
            "lines_written": 0,
            "execution_time": 0
        }
    
    def generate_documentation(self, file_path: str, doc_type: str = "auto") -> Dict[str, Any]:
        """Генерация документации для файла"""
        self.status = "documenting"
        start_time = datetime.now()
        
        result = {
            "file": file_path,
            "doc_type": doc_type,
            "timestamp": datetime.now().isoformat(),
            "documentation": "",
            "sections": []
        }
        
        try:
            if not os.path.exists(file_path):
                result["error"] = "File not found"
                return result
            
            # Автоопределение типа документации
            if doc_type == "auto":
                doc_type = self._detect_doc_type(file_path)
            
            # Генерация в зависимости от типа файла
            if file_path.endswith('.py'):
                result = self._document_python(file_path, result)
            elif file_path.endswith(('.js', '.ts')):
                result = self._document_javascript(file_path, result)
            elif file_path.endswith('.json'):
                result = self._document_json(file_path, result)
            elif os.path.isdir(file_path):
                result = self._document_project(file_path, result)
            else:
                result["documentation"] = self._generate_generic_doc(file_path)
            
            # Обновление статистики
            self.stats["docs_generated"] += 1
            self.stats["files_documented"] += 1
            self.stats["lines_written"] += len(result["documentation"].split('\n'))
            self.stats["execution_time"] = (datetime.now() - start_time).total_seconds()
            
            result["execution_time"] = self.stats["execution_time"]
            
        except Exception as e:
            result["error"] = str(e)
        finally:
            self.status = "idle"
        
        return result
    
    def _document_python(self, file_path: str, result: Dict) -> Dict:
        """Документирование Python файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result["error"] = "Syntax error in Python file"
            return result
        
        doc_parts = []
        file_name = Path(file_path).name
        
        # Заголовок
        doc_parts.append(f"# {file_name}")
        doc_parts.append("")
        
        # Описание модуля
        module_doc = ast.get_docstring(tree)
        if module_doc:
            doc_parts.append("## Module Description")
            doc_parts.append(module_doc)
            doc_parts.append("")
        
        # Импорты
        imports = self._extract_imports(tree)
        if imports:
            doc_parts.append("## Dependencies")
            doc_parts.append("```python")
            for imp in imports:
                doc_parts.append(imp)
            doc_parts.append("```")
            doc_parts.append("")
        
        # Классы
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        if classes:
            doc_parts.append("## Classes")
            doc_parts.append("")
            for cls in classes:
                doc_parts.append(self._document_class(cls))
                doc_parts.append("")
        
        # Функции
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        if functions:
            doc_parts.append("## Functions")
            doc_parts.append("")
            for func in functions:
                doc_parts.append(self._document_function(func))
                doc_parts.append("")
        
        # Примеры использования
        doc_parts.append("## Usage Example")
        doc_parts.append("```python")
        doc_parts.append(self._generate_usage_example(tree, file_name))
        doc_parts.append("```")
        
        result["documentation"] = "\n".join(doc_parts)
        result["sections"] = ["Module Description", "Dependencies", "Classes", "Functions", "Usage Example"]
        
        return result
    
    def _document_javascript(self, file_path: str, result: Dict) -> Dict:
        """Документирование JavaScript/TypeScript файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        doc_parts = []
        file_name = Path(file_path).name
        
        # Заголовок
        doc_parts.append(f"# {file_name}")
        doc_parts.append("")
        
        # Извлечение компонентов
        imports = re.findall(r'import.*from.*[\'"].*[\'"];?', content)
        exports = re.findall(r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', content)
        functions = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)|[\w\s]*)\s*=>)', content)
        classes = re.findall(r'class\s+(\w+)', content)
        
        # Импорты
        if imports:
            doc_parts.append("## Dependencies")
            doc_parts.append("```javascript")
            for imp in imports[:10]:  # Ограничиваем количество
                doc_parts.append(imp)
            doc_parts.append("```")
            doc_parts.append("")
        
        # Экспорты
        if exports:
            doc_parts.append("## Exports")
            for exp in exports:
                doc_parts.append(f"- `{exp}`")
            doc_parts.append("")
        
        # Классы
        if classes:
            doc_parts.append("## Classes")
            for cls in classes:
                doc_parts.append(f"### {cls}")
                doc_parts.append(f"Class implementation in {file_name}")
                doc_parts.append("")
        
        # Функции
        if functions:
            doc_parts.append("## Functions")
            for func in functions:
                func_name = func[0] or func[1] if isinstance(func, tuple) else func
                if func_name:
                    doc_parts.append(f"### {func_name}()")
                    doc_parts.append(f"Function implementation in {file_name}")
                    doc_parts.append("")
        
        result["documentation"] = "\n".join(doc_parts)
        return result
    
    def _document_json(self, file_path: str, result: Dict) -> Dict:
        """Документирование JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_parts = []
        file_name = Path(file_path).name
        
        doc_parts.append(f"# {file_name}")
        doc_parts.append("")
        doc_parts.append("## Structure")
        doc_parts.append("```json")
        doc_parts.append(json.dumps(self._get_json_structure(data), indent=2))
        doc_parts.append("```")
        doc_parts.append("")
        
        if isinstance(data, dict):
            doc_parts.append("## Root Keys")
            for key in data.keys():
                value_type = type(data[key]).__name__
                doc_parts.append(f"- `{key}`: {value_type}")
            doc_parts.append("")
        
        result["documentation"] = "\n".join(doc_parts)
        return result
    
    def _document_project(self, project_path: str, result: Dict) -> Dict:
        """Документирование проекта"""
        doc_parts = []
        project_name = Path(project_path).name
        
        doc_parts.append(f"# {project_name}")
        doc_parts.append("")
        doc_parts.append("## Project Structure")
        doc_parts.append("```")
        doc_parts.append(self._generate_tree_structure(project_path, max_depth=3))
        doc_parts.append("```")
        doc_parts.append("")
        
        # Поиск основных файлов
        main_files = self._find_main_files(project_path)
        if main_files:
            doc_parts.append("## Main Files")
            for file in main_files:
                doc_parts.append(f"- `{file}`")
            doc_parts.append("")
        
        # Технологии
        technologies = self._detect_technologies(project_path)
        if technologies:
            doc_parts.append("## Technologies")
            for tech in technologies:
                doc_parts.append(f"- {tech}")
            doc_parts.append("")
        
        result["documentation"] = "\n".join(doc_parts)
        return result
    
    def _document_class(self, node: ast.ClassDef) -> str:
        """Документирование класса"""
        parts = []
        parts.append(f"### class {node.name}")
        
        # Docstring
        docstring = ast.get_docstring(node)
        if docstring:
            parts.append(docstring)
        
        # Базовые классы
        if node.bases:
            bases = [base.id for base in node.bases if hasattr(base, 'id')]
            if bases:
                parts.append(f"**Inherits from:** {', '.join(bases)}")
        
        # Методы
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if methods:
            parts.append("")
            parts.append("**Methods:**")
            for method in methods:
                args = [arg.arg for arg in method.args.args if arg.arg != 'self']
                args_str = ', '.join(args) if args else ''
                parts.append(f"- `{method.name}({args_str})`")
        
        return "\n".join(parts)
    
    def _document_function(self, node: ast.FunctionDef) -> str:
        """Документирование функции"""
        parts = []
        
        # Сигнатура
        args = [arg.arg for arg in node.args.args]
        args_str = ', '.join(args) if args else ''
        parts.append(f"### {node.name}({args_str})")
        
        # Docstring
        docstring = ast.get_docstring(node)
        if docstring:
            parts.append(docstring)
        else:
            parts.append(f"Function `{node.name}` - no description available")
        
        # Параметры
        if args:
            parts.append("")
            parts.append("**Parameters:**")
            for arg in args:
                parts.append(f"- `{arg}`: parameter")
        
        # Возвращаемое значение
        has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
        if has_return:
            parts.append("")
            parts.append("**Returns:** value")
        
        return "\n".join(parts)
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Извлечение импортов"""
        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                items = ', '.join(alias.name for alias in node.names)
                imports.append(f"from {module} import {items}")
        return imports
    
    def _generate_usage_example(self, tree: ast.AST, file_name: str) -> str:
        """Генерация примера использования"""
        module_name = file_name.replace('.py', '')
        examples = [f"from {module_name} import *"]
        
        # Находим основные классы и функции
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                examples.append(f"\n# Create instance of {node.name}")
                examples.append(f"obj = {node.name}()")
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                args = [f"arg{i}" for i in range(len(node.args.args))]
                args_str = ', '.join(args) if args else ''
                examples.append(f"\n# Call {node.name}")
                examples.append(f"result = {node.name}({args_str})")
        
        return "\n".join(examples)
    
    def _get_json_structure(self, obj: Any, depth: int = 0, max_depth: int = 3) -> Any:
        """Получение структуры JSON"""
        if depth > max_depth:
            return "..."
        
        if isinstance(obj, dict):
            if not obj:
                return {}
            return {k: self._get_json_structure(v, depth + 1, max_depth) 
                   for k, v in list(obj.items())[:5]}
        elif isinstance(obj, list):
            if not obj:
                return []
            return [self._get_json_structure(obj[0], depth + 1, max_depth)]
        else:
            return f"<{type(obj).__name__}>"
    
    def _generate_tree_structure(self, path: str, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        """Генерация древовидной структуры"""
        if current_depth > max_depth:
            return ""
        
        lines = []
        path_obj = Path(path)
        
        try:
            items = sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items[:20]):  # Ограничиваем количество
                if item.name.startswith('.'):
                    continue
                    
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and current_depth < max_depth:
                    extension = "    " if is_last else "│   "
                    subtree = self._generate_tree_structure(
                        str(item), prefix + extension, max_depth, current_depth + 1
                    )
                    if subtree:
                        lines.append(subtree)
        except PermissionError:
            pass
        
        return "\n".join(lines)
    
    def _find_main_files(self, project_path: str) -> List[str]:
        """Поиск основных файлов проекта"""
        main_files = []
        important_names = ['README.md', 'setup.py', 'package.json', 'requirements.txt',
                          'Dockerfile', 'docker-compose.yml', 'Makefile', '.env.example']
        
        for name in important_names:
            file_path = Path(project_path) / name
            if file_path.exists():
                main_files.append(name)
        
        return main_files
    
    def _detect_technologies(self, project_path: str) -> List[str]:
        """Определение используемых технологий"""
        technologies = []
        
        # Проверка по файлам
        checks = {
            'package.json': 'Node.js/JavaScript',
            'requirements.txt': 'Python',
            'Gemfile': 'Ruby',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'Cargo.toml': 'Rust',
            'go.mod': 'Go',
            'composer.json': 'PHP',
            'Dockerfile': 'Docker',
            '.github/workflows': 'GitHub Actions'
        }
        
        for file_name, tech in checks.items():
            if (Path(project_path) / file_name).exists():
                technologies.append(tech)
        
        return technologies
    
    def _detect_doc_type(self, file_path: str) -> str:
        """Автоопределение типа документации"""
        if os.path.isdir(file_path):
            return "project"
        elif file_path.endswith('.py'):
            return "python"
        elif file_path.endswith(('.js', '.ts')):
            return "javascript"
        elif file_path.endswith('.json'):
            return "json"
        else:
            return "generic"
    
    def _generate_generic_doc(self, file_path: str) -> str:
        """Генерация базовой документации"""
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path)
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        doc = f"""# {file_name}

## File Information
- **Path:** {file_path}
- **Size:** {file_size} bytes
- **Modified:** {modified.isoformat()}
- **Type:** {Path(file_path).suffix}

## Description
Documentation for {file_name}
"""
        return doc
    
    def _get_readme_template(self) -> str:
        return """# Project Name

## Description
Brief description of the project

## Installation
```bash
# Installation commands
```

## Usage
```python
# Usage example
```

## Features
- Feature 1
- Feature 2

## License
MIT"""
    
    def _get_api_template(self) -> str:
        return """# API Documentation

## Endpoints

### GET /endpoint
Description

**Parameters:**
- param1: description

**Response:**
```json
{
  "status": "success"
}
```"""
    
    def _get_class_template(self) -> str:
        return """## Class: ClassName

### Description
Class description

### Methods
- method1(): description
- method2(param): description

### Properties
- property1: description"""
    
    def _get_function_template(self) -> str:
        return """### function_name(param1, param2)

**Description:** Function description

**Parameters:**
- param1 (type): description
- param2 (type): description

**Returns:** type - description

**Example:**
```python
result = function_name(value1, value2)
```"""
    
    def _get_project_template(self) -> str:
        return """# Project Documentation

## Overview
Project overview

## Architecture
System architecture description

## Components
- Component 1
- Component 2

## Getting Started
Setup instructions"""
    
    def generate_readme(self, project_path: str) -> str:
        """Генерация README для проекта"""
        self.status = "generating_readme"
        
        try:
            result = self.generate_documentation(project_path, "project")
            readme_content = result.get("documentation", self.templates["readme"])
            
            # Сохранение README
            readme_path = Path(project_path) / "README_GENERATED.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            return str(readme_path)
            
        finally:
            self.status = "idle"
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса агента"""
        return {
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "current_task": self.current_task,
            "stats": self.stats
        }
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи"""
        self.current_task = task
        task_type = task.get("type", "document")
        
        try:
            if task_type == "document":
                return self.generate_documentation(
                    task.get("file_path", ""),
                    task.get("doc_type", "auto")
                )
            elif task_type == "readme":
                readme_path = self.generate_readme(task.get("project_path", ""))
                return {"readme_path": readme_path}
            else:
                return {"error": f"Unknown task type: {task_type}"}
        finally:
            self.current_task = None