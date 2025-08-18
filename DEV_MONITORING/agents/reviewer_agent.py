#!/usr/bin/env python3
"""
✅ REVIEWER AGENT
Агент для проверки качества кода
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pylint.lint
from pylint.reporters.json_reporter import JSONReporter
from io import StringIO

class ReviewerAgent:
    """Агент проверки качества кода"""
    
    def __init__(self):
        self.name = "ReviewerAgent"
        self.priority = 2
        self.status = "idle"
        self.current_task = None
        
        # Правила проверки
        self.rules = {
            "naming": {
                "functions": r'^[a-z_][a-z0-9_]*$',
                "classes": r'^[A-Z][a-zA-Z0-9]*$',
                "constants": r'^[A-Z][A-Z0-9_]*$',
                "variables": r'^[a-z_][a-z0-9_]*$'
            },
            "complexity": {
                "max_function_length": 50,
                "max_file_length": 500,
                "max_line_length": 120,
                "max_complexity": 10
            },
            "security": {
                "dangerous_functions": ['eval', 'exec', '__import__', 'compile'],
                "sql_injection_patterns": [r'SELECT.*FROM.*WHERE.*%s', r'INSERT.*VALUES.*%s'],
                "hardcoded_secrets": [r'password\s*=\s*["\'].*["\']', r'api_key\s*=\s*["\'].*["\']']
            }
        }
        
        # Статистика
        self.stats = {
            "reviews_performed": 0,
            "issues_found": 0,
            "critical_issues": 0,
            "files_reviewed": 0
        }
    
    def review_code(self, file_path: str) -> Dict[str, Any]:
        """Полная проверка качества кода"""
        self.status = "reviewing"
        start_time = datetime.now()
        
        result = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "metrics": {},
            "score": 100,
            "recommendations": []
        }
        
        try:
            if not os.path.exists(file_path):
                result["error"] = "File not found"
                return result
            
            # Определяем тип файла
            if file_path.endswith('.py'):
                result = self._review_python(file_path, result)
            elif file_path.endswith(('.js', '.ts')):
                result = self._review_javascript(file_path, result)
            elif file_path.endswith('.json'):
                result = self._review_json(file_path, result)
            else:
                result["error"] = "Unsupported file type"
            
            # Подсчет финального скора
            result["score"] = self._calculate_score(result["issues"])
            
            # Генерация рекомендаций
            result["recommendations"] = self._generate_recommendations(result)
            
            # Обновление статистики
            self.stats["reviews_performed"] += 1
            self.stats["files_reviewed"] += 1
            self.stats["issues_found"] += len(result["issues"])
            self.stats["critical_issues"] += len([i for i in result["issues"] if i["severity"] == "critical"])
            
            result["execution_time"] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            result["error"] = str(e)
        finally:
            self.status = "idle"
        
        return result
    
    def _review_python(self, file_path: str, result: Dict) -> Dict:
        """Проверка Python кода"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Синтаксический анализ
        try:
            tree = ast.parse(content)
            result["metrics"]["valid_syntax"] = True
        except SyntaxError as e:
            result["issues"].append({
                "type": "syntax_error",
                "severity": "critical",
                "line": e.lineno,
                "message": str(e)
            })
            result["metrics"]["valid_syntax"] = False
            return result
        
        # 2. PyLint анализ
        pylint_issues = self._run_pylint(file_path)
        for issue in pylint_issues:
            result["issues"].append({
                "type": "pylint",
                "severity": self._map_pylint_severity(issue.get("type", "warning")),
                "line": issue.get("line", 0),
                "message": issue.get("message", ""),
                "symbol": issue.get("symbol", "")
            })
        
        # 3. Проверка сложности
        complexity_issues = self._check_complexity(tree, content)
        result["issues"].extend(complexity_issues)
        
        # 4. Проверка безопасности
        security_issues = self._check_security(content)
        result["issues"].extend(security_issues)
        
        # 5. Проверка стиля
        style_issues = self._check_style(tree, content)
        result["issues"].extend(style_issues)
        
        # Метрики
        result["metrics"].update({
            "lines_of_code": len(content.split('\n')),
            "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
            "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
        })
        
        return result
    
    def _review_javascript(self, file_path: str, result: Dict) -> Dict:
        """Проверка JavaScript/TypeScript кода"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Базовые проверки для JS
        lines = content.split('\n')
        
        # 1. Проверка длины строк
        for i, line in enumerate(lines, 1):
            if len(line) > self.rules["complexity"]["max_line_length"]:
                result["issues"].append({
                    "type": "line_too_long",
                    "severity": "minor",
                    "line": i,
                    "message": f"Line exceeds {self.rules['complexity']['max_line_length']} characters"
                })
        
        # 2. Проверка console.log
        console_pattern = r'console\.(log|error|warn|info)'
        for i, line in enumerate(lines, 1):
            if re.search(console_pattern, line):
                result["issues"].append({
                    "type": "console_statement",
                    "severity": "warning",
                    "line": i,
                    "message": "Console statement found in production code"
                })
        
        # 3. Проверка безопасности
        security_issues = self._check_security(content)
        result["issues"].extend(security_issues)
        
        # Метрики
        result["metrics"] = {
            "lines_of_code": len(lines),
            "functions": len(re.findall(r'function\s+\w+|=>\s*{', content)),
            "classes": len(re.findall(r'class\s+\w+', content))
        }
        
        return result
    
    def _review_json(self, file_path: str, result: Dict) -> Dict:
        """Проверка JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            result["metrics"]["valid_json"] = True
            
            # Проверка на секреты
            json_str = json.dumps(data)
            security_issues = self._check_security(json_str)
            result["issues"].extend(security_issues)
            
        except json.JSONDecodeError as e:
            result["issues"].append({
                "type": "json_error",
                "severity": "critical",
                "line": e.lineno if hasattr(e, 'lineno') else 0,
                "message": str(e)
            })
            result["metrics"]["valid_json"] = False
        
        return result
    
    def _run_pylint(self, file_path: str) -> List[Dict]:
        """Запуск PyLint"""
        try:
            output = StringIO()
            reporter = JSONReporter(output)
            
            # Запускаем pylint с базовыми проверками
            pylint.lint.Run(
                [file_path, '--disable=all', '--enable=W,E,C', '--output-format=json'],
                reporter=reporter,
                exit=False
            )
            
            output.seek(0)
            results = json.loads(output.getvalue() or '[]')
            return results
        except:
            return []
    
    def _check_complexity(self, tree: ast.AST, content: str) -> List[Dict]:
        """Проверка сложности кода"""
        issues = []
        lines = content.split('\n')
        
        # Проверка длины файла
        if len(lines) > self.rules["complexity"]["max_file_length"]:
            issues.append({
                "type": "file_too_long",
                "severity": "warning",
                "line": 0,
                "message": f"File exceeds {self.rules['complexity']['max_file_length']} lines"
            })
        
        # Проверка длины функций
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > self.rules["complexity"]["max_function_length"]:
                    issues.append({
                        "type": "function_too_long",
                        "severity": "warning",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' exceeds {self.rules['complexity']['max_function_length']} lines"
                    })
                
                # Циклматическая сложность (упрощенная)
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.rules["complexity"]["max_complexity"]:
                    issues.append({
                        "type": "high_complexity",
                        "severity": "major",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has high cyclomatic complexity: {complexity}"
                    })
        
        return issues
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Расчет циклматической сложности"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _check_security(self, content: str) -> List[Dict]:
        """Проверка безопасности"""
        issues = []
        lines = content.split('\n')
        
        # Проверка опасных функций
        for dangerous in self.rules["security"]["dangerous_functions"]:
            pattern = rf'\b{dangerous}\s*\('
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append({
                        "type": "dangerous_function",
                        "severity": "critical",
                        "line": i,
                        "message": f"Dangerous function '{dangerous}' detected"
                    })
        
        # Проверка хардкод паролей
        for pattern in self.rules["security"]["hardcoded_secrets"]:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "type": "hardcoded_secret",
                        "severity": "critical",
                        "line": i,
                        "message": "Possible hardcoded secret detected"
                    })
        
        return issues
    
    def _check_style(self, tree: ast.AST, content: str) -> List[Dict]:
        """Проверка стиля кода"""
        issues = []
        
        # Проверка именования
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(self.rules["naming"]["functions"], node.name):
                    issues.append({
                        "type": "naming_convention",
                        "severity": "minor",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' doesn't follow naming convention"
                    })
            elif isinstance(node, ast.ClassDef):
                if not re.match(self.rules["naming"]["classes"], node.name):
                    issues.append({
                        "type": "naming_convention",
                        "severity": "minor",
                        "line": node.lineno,
                        "message": f"Class '{node.name}' doesn't follow naming convention"
                    })
        
        return issues
    
    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Маппинг severity из PyLint"""
        mapping = {
            "error": "critical",
            "warning": "major",
            "convention": "minor",
            "refactor": "minor",
            "info": "info"
        }
        return mapping.get(pylint_type.lower(), "warning")
    
    def _calculate_score(self, issues: List[Dict]) -> int:
        """Расчет финального скора"""
        score = 100
        penalties = {
            "critical": 20,
            "major": 10,
            "warning": 5,
            "minor": 2,
            "info": 0
        }
        
        for issue in issues:
            severity = issue.get("severity", "warning")
            score -= penalties.get(severity, 5)
        
        return max(0, score)
    
    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        if result["score"] < 50:
            recommendations.append("⚠️ Code quality is below acceptable level. Major refactoring needed.")
        
        critical_count = len([i for i in result["issues"] if i["severity"] == "critical"])
        if critical_count > 0:
            recommendations.append(f"🔴 Fix {critical_count} critical issues immediately")
        
        if result["metrics"].get("lines_of_code", 0) > 300:
            recommendations.append("📦 Consider splitting this file into smaller modules")
        
        security_issues = [i for i in result["issues"] if i["type"] in ["dangerous_function", "hardcoded_secret"]]
        if security_issues:
            recommendations.append("🔐 Security vulnerabilities detected. Review and fix immediately")
        
        return recommendations
    
    def compare_versions(self, file1: str, file2: str) -> Dict[str, Any]:
        """Сравнение двух версий файла"""
        self.status = "comparing"
        
        try:
            review1 = self.review_code(file1)
            review2 = self.review_code(file2)
            
            comparison = {
                "file1": file1,
                "file2": file2,
                "score_change": review2["score"] - review1["score"],
                "issues_change": len(review2["issues"]) - len(review1["issues"]),
                "improvements": [],
                "regressions": []
            }
            
            # Анализ улучшений и регрессий
            if comparison["score_change"] > 0:
                comparison["improvements"].append(f"Code quality improved by {comparison['score_change']} points")
            elif comparison["score_change"] < 0:
                comparison["regressions"].append(f"Code quality decreased by {abs(comparison['score_change'])} points")
            
            return comparison
            
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
        task_type = task.get("type", "review")
        
        try:
            if task_type == "review":
                return self.review_code(task.get("file_path", ""))
            elif task_type == "compare":
                return self.compare_versions(task.get("file1", ""), task.get("file2", ""))
            else:
                return {"error": f"Unknown task type: {task_type}"}
        finally:
            self.current_task = None