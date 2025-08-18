#!/usr/bin/env python3

import os
import json
import time
import random
import hashlib
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from openai import OpenAI
import anthropic
import logging

class AIIntegration:
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.logger = self._setup_logger()
        
        # Load API keys from existing project
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        
        # Initialize AI clients
        self._init_ai_clients()
        
    def _load_config(self, config_path: str) -> dict:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AIIntegration')
        logger.setLevel(logging.INFO)
        return logger
        
    def _load_api_keys(self) -> Dict[str, List[str]]:
        keys = {
            'gemini': [],
            'openai': [],
            'claude': []
        }
        
        # Check for existing keys in project
        key_files = [
            self.project_root / 'config' / 'api_keys.json',
            self.project_root / '.env',
            self.project_root / 'keys' / 'gemini_keys.txt',
            Path.home() / '.galaxy' / 'api_keys.json'
        ]
        
        for key_file in key_files:
            if key_file.exists():
                if key_file.suffix == '.json':
                    with open(key_file, 'r') as f:
                        data = json.load(f)
                        keys.update(data)
                elif key_file.suffix == '.txt':
                    with open(key_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.strip():
                                keys['gemini'].append(line.strip())
                                
        # Get from environment
        if os.getenv('GEMINI_API_KEY'):
            keys['gemini'].append(os.getenv('GEMINI_API_KEY'))
        if os.getenv('OPENAI_API_KEY'):
            keys['openai'].append(os.getenv('OPENAI_API_KEY'))
        if os.getenv('ANTHROPIC_API_KEY'):
            keys['claude'].append(os.getenv('ANTHROPIC_API_KEY'))
            
        return keys
        
    def _init_ai_clients(self):
        # Initialize Gemini
        if self.api_keys['gemini']:
            genai.configure(api_key=self._get_next_key('gemini'))
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
            
        # Initialize OpenAI
        if self.api_keys['openai']:
            self.openai_client = OpenAI(api_key=self._get_next_key('openai'))
        else:
            self.openai_client = None
            
        # Initialize Claude
        if self.api_keys['claude']:
            self.claude_client = anthropic.Anthropic(api_key=self._get_next_key('claude'))
        else:
            self.claude_client = None
            
    def _get_next_key(self, service: str) -> str:
        keys = self.api_keys.get(service, [])
        if not keys:
            return ""
            
        # Rotate keys
        key = keys[self.current_key_index % len(keys)]
        self.current_key_index += 1
        return key
        
    def _rotate_api_key(self, service: str):
        if service == 'gemini' and self.api_keys['gemini']:
            genai.configure(api_key=self._get_next_key('gemini'))
        elif service == 'openai' and self.api_keys['openai']:
            self.openai_client = OpenAI(api_key=self._get_next_key('openai'))
        elif service == 'claude' and self.api_keys['claude']:
            self.claude_client = anthropic.Anthropic(api_key=self._get_next_key('claude'))
            
    def analyze_code_with_gemini(self, code: str, prompt: str) -> Optional[str]:
        if not self.gemini_model:
            return None
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.gemini_model.generate_content(
                    f"{prompt}\n\nКод:\n```\n{code[:4000]}\n```"
                )
                return response.text
            except Exception as e:
                self.logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if "quota" in str(e).lower():
                    self._rotate_api_key('gemini')
                time.sleep(2 ** attempt)
                
        return None
        
    def analyze_code_with_openai(self, code: str, prompt: str) -> Optional[str]:
        if not self.openai_client:
            return None
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a code documentation expert."},
                        {"role": "user", "content": f"{prompt}\n\nКод:\n```\n{code[:4000]}\n```"}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.warning(f"OpenAI attempt {attempt + 1} failed: {e}")
                if "rate_limit" in str(e).lower():
                    self._rotate_api_key('openai')
                time.sleep(2 ** attempt)
                
        return None
        
    def analyze_code_with_claude(self, code: str, prompt: str) -> Optional[str]:
        if not self.claude_client:
            return None
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    temperature=0.3,
                    messages=[
                        {
                            "role": "user",
                            "content": f"{prompt}\n\nКод:\n```\n{code[:4000]}\n```"
                        }
                    ]
                )
                return response.content[0].text
            except Exception as e:
                self.logger.warning(f"Claude attempt {attempt + 1} failed: {e}")
                if "rate_limit" in str(e).lower():
                    self._rotate_api_key('claude')
                time.sleep(2 ** attempt)
                
        return None
        
    def generate_documentation(self, file_path: Path, code: str) -> Dict[str, str]:
        prompt = f"""Проанализируй код файла {file_path.name} и создай документацию:
1. Краткое описание назначения (2-3 предложения)
2. Основные функции/классы и их назначение
3. Зависимости и связи с другими модулями
4. Потенциальные проблемы или улучшения

Ответ в формате JSON:
{{
    "description": "...",
    "functions": [...],
    "dependencies": [...],
    "issues": [...]
}}"""
        
        # Try different AI services with fallback
        result = None
        
        # Try Gemini first (usually has better quota)
        if self.api_keys['gemini']:
            result = self.analyze_code_with_gemini(code, prompt)
            if result:
                try:
                    return json.loads(result)
                except:
                    return {"description": result, "functions": [], "dependencies": [], "issues": []}
                    
        # Fallback to OpenAI
        if not result and self.api_keys['openai']:
            result = self.analyze_code_with_openai(code, prompt)
            if result:
                try:
                    return json.loads(result)
                except:
                    return {"description": result, "functions": [], "dependencies": [], "issues": []}
                    
        # Last resort - Claude
        if not result and self.api_keys['claude']:
            result = self.analyze_code_with_claude(code, prompt)
            if result:
                try:
                    return json.loads(result)
                except:
                    return {"description": result, "functions": [], "dependencies": [], "issues": []}
                    
        # If all fail, use local analysis
        return self._local_code_analysis(code, file_path)
        
    def _local_code_analysis(self, code: str, file_path: Path) -> Dict[str, str]:
        analysis = {
            "description": f"Файл {file_path.name} в проекте GalaxyDevelopers",
            "functions": [],
            "dependencies": [],
            "issues": []
        }
        
        # Simple pattern matching
        if file_path.suffix == '.py':
            import ast
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        analysis["functions"].append(node.name)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["dependencies"].append(alias.name)
            except:
                pass
                
        elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            import re
            # Find functions
            func_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=)'
            for match in re.finditer(func_pattern, code):
                func_name = match.group(1) or match.group(2)
                if func_name:
                    analysis["functions"].append(func_name)
                    
            # Find imports
            import_pattern = r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"
            for match in re.finditer(import_pattern, code):
                analysis["dependencies"].append(match.group(1))
                
        return analysis
        
    def find_code_issues(self, code: str, file_path: Path) -> List[Dict]:
        issues = []
        
        # Check for common issues
        patterns = {
            'console.log': 'Debug console.log оставлен в коде',
            'TODO': 'Незавершенная задача TODO',
            'FIXME': 'Требуется исправление FIXME',
            'hardcoded': 'Возможны захардкоженные значения',
            'password': 'Возможна утечка паролей',
            'api_key': 'Возможна утечка API ключей',
            'localhost': 'Захардкожен localhost',
            '127.0.0.1': 'Захардкожен IP адрес'
        }
        
        for pattern, description in patterns.items():
            if pattern.lower() in code.lower():
                line_num = code.lower().find(pattern.lower())
                line = code[:line_num].count('\n') + 1
                issues.append({
                    'type': 'warning',
                    'line': line,
                    'description': description
                })
                
        return issues
        
    def suggest_improvements(self, code: str, file_path: Path) -> List[str]:
        suggestions = []
        
        # Basic suggestions
        if len(code.splitlines()) > 500:
            suggestions.append("Файл слишком большой, рекомендуется разделить на модули")
            
        if file_path.suffix == '.py':
            if 'class' not in code and 'def' not in code:
                suggestions.append("Файл не содержит функций или классов")
            if not code.strip().startswith('#!/usr/bin/env python'):
                suggestions.append("Добавьте shebang для Python файлов")
                
        if not any(doc in code for doc in ['"""', "'''", '//', '/*']):
            suggestions.append("Отсутствуют комментарии и документация")
            
        return suggestions
        
    def batch_analyze_files(self, file_paths: List[Path], max_concurrent: int = 5) -> Dict[str, Dict]:
        results = {}
        
        for i in range(0, len(file_paths), max_concurrent):
            batch = file_paths[i:i + max_concurrent]
            
            for file_path in batch:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        
                    analysis = self.generate_documentation(file_path, code)
                    analysis['issues'] = self.find_code_issues(code, file_path)
                    analysis['suggestions'] = self.suggest_improvements(code, file_path)
                    
                    results[str(file_path)] = analysis
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {e}")
                    results[str(file_path)] = {
                        "description": f"Ошибка анализа: {e}",
                        "functions": [],
                        "dependencies": [],
                        "issues": [],
                        "suggestions": []
                    }
                    
            # Rate limiting
            time.sleep(1)
            
        return results

if __name__ == "__main__":
    ai = AIIntegration()
    
    # Test file analysis
    test_file = Path(__file__)
    with open(test_file, 'r') as f:
        code = f.read()
        
    result = ai.generate_documentation(test_file, code)
    print(json.dumps(result, indent=2, ensure_ascii=False))