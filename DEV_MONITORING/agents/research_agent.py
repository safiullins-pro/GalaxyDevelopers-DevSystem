#!/usr/bin/env python3
"""
🔍 RESEARCH AGENT
Агент для поиска и анализа информации в коде
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import subprocess

class ResearchAgent:
    """Исследовательский агент - ищет информацию в кодовой базе"""
    
    def __init__(self, base_paths: List[str] = None):
        self.name = "ResearchAgent"
        self.priority = 1
        self.status = "idle"
        self.current_task = None
        
        # Пути для поиска
        self.base_paths = base_paths or [
            "/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/",
            "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/"
        ]
        
        # Статистика
        self.stats = {
            "searches_performed": 0,
            "files_analyzed": 0,
            "patterns_found": 0,
            "execution_time": 0
        }
    
    def search_code(self, query: str, file_types: List[str] = None) -> Dict[str, Any]:
        """Поиск кода по запросу"""
        self.status = "searching"
        start_time = datetime.now()
        results = {
            "query": query,
            "matches": [],
            "files_scanned": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        file_types = file_types or ['.py', '.js', '.ts', '.json', '.md']
        
        try:
            for base_path in self.base_paths:
                if not os.path.exists(base_path):
                    continue
                    
                for root, dirs, files in os.walk(base_path):
                    # Пропускаем системные директории
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'node_modules']
                    
                    for file in files:
                        if any(file.endswith(ft) for ft in file_types):
                            file_path = Path(root) / file
                            results["files_scanned"] += 1
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                # Ищем паттерн
                                if re.search(query, content, re.IGNORECASE):
                                    matches = self._extract_matches(content, query, str(file_path))
                                    if matches:
                                        results["matches"].extend(matches)
                                        
                            except Exception as e:
                                pass  # Пропускаем нечитаемые файлы
            
            # Обновляем статистику
            self.stats["searches_performed"] += 1
            self.stats["files_analyzed"] += results["files_scanned"]
            self.stats["patterns_found"] += len(results["matches"])
            self.stats["execution_time"] = (datetime.now() - start_time).total_seconds()
            
            results["execution_time"] = self.stats["execution_time"]
            
        finally:
            self.status = "idle"
            
        return results
    
    def _extract_matches(self, content: str, query: str, file_path: str) -> List[Dict]:
        """Извлечение совпадений с контекстом"""
        matches = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if re.search(query, line, re.IGNORECASE):
                context_start = max(0, i - 3)
                context_end = min(len(lines), i + 3)
                
                matches.append({
                    "file": file_path,
                    "line": i,
                    "text": line.strip(),
                    "context": '\n'.join(lines[context_start:context_end])
                })
        
        return matches[:10]  # Максимум 10 совпадений на файл
    
    def analyze_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Анализ зависимостей файла"""
        self.status = "analyzing"
        result = {
            "file": file_path,
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "dependencies": []
        }
        
        try:
            if file_path.endswith('.py'):
                result = self._analyze_python(file_path)
            elif file_path.endswith(('.js', '.ts')):
                result = self._analyze_javascript(file_path)
            elif file_path.endswith('.json'):
                result = self._analyze_json(file_path)
                
        except Exception as e:
            result["error"] = str(e)
        finally:
            self.status = "idle"
            
        return result
    
    def _analyze_python(self, file_path: str) -> Dict[str, Any]:
        """Анализ Python файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {"file": file_path, "error": f"Syntax error: {e}"}
        
        result = {
            "file": file_path,
            "imports": [],
            "functions": [],
            "classes": [],
            "global_vars": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    result["imports"].append(f"{module}.{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                result["functions"].append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "line": node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                result["classes"].append({
                    "name": node.name,
                    "bases": [base.id for base in node.bases if hasattr(base, 'id')],
                    "line": node.lineno
                })
        
        return result
    
    def _analyze_javascript(self, file_path: str) -> Dict[str, Any]:
        """Анализ JavaScript/TypeScript файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = {
            "file": file_path,
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": []
        }
        
        # Простой regex анализ
        import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        export_pattern = r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
        function_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)|[\w\s]*)\s*=>)'
        class_pattern = r'class\s+(\w+)'
        
        result["imports"] = re.findall(import_pattern, content)
        result["exports"] = re.findall(export_pattern, content)
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2)
            if func_name:
                result["functions"].append(func_name)
        
        result["classes"] = re.findall(class_pattern, content)
        
        return result
    
    def _analyze_json(self, file_path: str) -> Dict[str, Any]:
        """Анализ JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def get_structure(obj, depth=0, max_depth=3):
            if depth > max_depth:
                return "..."
            
            if isinstance(obj, dict):
                return {k: get_structure(v, depth + 1, max_depth) for k, v in list(obj.items())[:10]}
            elif isinstance(obj, list):
                if obj:
                    return [get_structure(obj[0], depth + 1, max_depth)]
                return []
            else:
                return type(obj).__name__
        
        return {
            "file": file_path,
            "structure": get_structure(data),
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "length": len(data) if isinstance(data, (list, dict)) else None
        }
    
    def find_similar_code(self, code_snippet: str, threshold: float = 0.7) -> List[Dict]:
        """Поиск похожего кода"""
        self.status = "searching_similar"
        results = []
        
        # Нормализация кода для сравнения
        normalized_snippet = self._normalize_code(code_snippet)
        
        try:
            for base_path in self.base_paths:
                if not os.path.exists(base_path):
                    continue
                    
                for root, dirs, files in os.walk(base_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                    
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts')):
                            file_path = Path(root) / file
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                similarity = self._calculate_similarity(normalized_snippet, content)
                                if similarity >= threshold:
                                    results.append({
                                        "file": str(file_path),
                                        "similarity": similarity,
                                        "preview": content[:500]
                                    })
                                    
                            except:
                                pass
        finally:
            self.status = "idle"
            
        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:10]
    
    def _normalize_code(self, code: str) -> str:
        """Нормализация кода для сравнения"""
        # Удаляем комментарии и пустые строки
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'\n\s*\n', '\n', code)
        code = code.strip()
        return code
    
    def _calculate_similarity(self, snippet1: str, content: str) -> float:
        """Расчет схожести кода"""
        snippet1 = self._normalize_code(snippet1)
        content = self._normalize_code(content)
        
        if not snippet1 or not content:
            return 0.0
        
        # Простое сравнение по совпадающим строкам
        lines1 = set(snippet1.split('\n'))
        lines2 = set(content.split('\n'))
        
        if not lines1:
            return 0.0
            
        common = lines1.intersection(lines2)
        return len(common) / len(lines1)
    
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
        task_type = task.get("type", "search")
        
        try:
            if task_type == "search":
                return self.search_code(task.get("query", ""), task.get("file_types"))
            elif task_type == "analyze":
                return self.analyze_dependencies(task.get("file_path", ""))
            elif task_type == "find_similar":
                return {"similar": self.find_similar_code(task.get("code", ""))}
            else:
                return {"error": f"Unknown task type: {task_type}"}
        finally:
            self.current_task = None