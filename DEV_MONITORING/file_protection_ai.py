#!/usr/bin/env python3
"""
GALAXY FILE PROTECTION WITH AI
Система защиты файлов с AI проверкой прав доступа
"""

import os
import stat
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess
import re
from datetime import datetime
import sqlite3

class AIFileProtection:
    """AI-powered система защиты файлов"""
    
    def __init__(self):
        self.protected_paths = [
            '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/',
            '/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/'
        ]
        
        # Критические файлы - НИКТО не может изменять
        self.critical_files = [
            'monitoring_server_fixed.py',
            'file_protection_ai.py',
            'monitoring_config.json',
            '.env',
            'credentials.json'
        ]
        
        # Паттерны опасных операций
        self.danger_patterns = [
            r'rm\s+-rf\s+/',  # Удаление корневой директории
            r'chmod\s+777',   # Открытие всех прав
            r'eval\(',         # Выполнение произвольного кода
            r'exec\(',         # Выполнение команд
            r'__import__',     # Динамический импорт
            r'os\.system',     # Системные вызовы
            r'subprocess\.',   # Запуск процессов
            r'open\(.*[\'"]w', # Запись в файлы
        ]
        
        # База данных для хранения хешей и прав
        self.db_path = Path(__file__).parent / 'file_protection.db'
        self.init_database()
        
        # AI модель для анализа (эмуляция)
        self.ai_threat_levels = {
            'safe': 0,
            'low': 25,
            'medium': 50,
            'high': 75,
            'critical': 100
        }
        
    def init_database(self):
        """Инициализация базы данных защиты"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                path TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                permissions TEXT NOT NULL,
                owner TEXT NOT NULL,
                last_check REAL NOT NULL,
                threat_level INTEGER DEFAULT 0,
                locked BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                path TEXT NOT NULL,
                action TEXT NOT NULL,
                user TEXT NOT NULL,
                allowed BOOLEAN NOT NULL,
                threat_level INTEGER,
                reason TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                file_path TEXT NOT NULL,
                operation TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                decision TEXT NOT NULL,
                factors TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, filepath: str) -> str:
        """Вычисление хеша файла"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return ""
    
    def get_file_permissions(self, filepath: str) -> Dict:
        """Получение прав доступа к файлу"""
        try:
            st = os.stat(filepath)
            return {
                'mode': oct(st.st_mode),
                'owner': st.st_uid,
                'group': st.st_gid,
                'size': st.st_size,
                'modified': st.st_mtime,
                'permissions': {
                    'owner': {
                        'read': bool(st.st_mode & stat.S_IRUSR),
                        'write': bool(st.st_mode & stat.S_IWUSR),
                        'execute': bool(st.st_mode & stat.S_IXUSR)
                    },
                    'group': {
                        'read': bool(st.st_mode & stat.S_IRGRP),
                        'write': bool(st.st_mode & stat.S_IWGRP),
                        'execute': bool(st.st_mode & stat.S_IXGRP)
                    },
                    'others': {
                        'read': bool(st.st_mode & stat.S_IROTH),
                        'write': bool(st.st_mode & stat.S_IWOTH),
                        'execute': bool(st.st_mode & stat.S_IXOTH)
                    }
                }
            }
        except:
            return {}
    
    def ai_analyze_threat(self, filepath: str, operation: str, content: str = None) -> Tuple[int, str, Dict]:
        """
        AI анализ угрозы операции над файлом
        Возвращает: (уровень_угрозы, решение, факторы)
        """
        threat_score = 0
        factors = []
        
        # 1. Проверка критических файлов
        filename = Path(filepath).name
        if filename in self.critical_files:
            threat_score += 50
            factors.append("CRITICAL_FILE")
        
        # 2. Проверка расширения
        ext = Path(filepath).suffix
        dangerous_extensions = ['.sh', '.py', '.js', '.exe', '.dll', '.so']
        if ext in dangerous_extensions:
            threat_score += 20
            factors.append(f"DANGEROUS_EXT:{ext}")
        
        # 3. Проверка операции
        dangerous_operations = {
            'delete': 30,
            'chmod': 25,
            'write': 15,
            'execute': 35,
            'move': 20
        }
        if operation in dangerous_operations:
            threat_score += dangerous_operations[operation]
            factors.append(f"DANGEROUS_OP:{operation}")
        
        # 4. Анализ содержимого (если есть)
        if content:
            for pattern in self.danger_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    threat_score += 30
                    factors.append(f"DANGEROUS_PATTERN:{pattern}")
        
        # 5. Проверка прав доступа
        perms = self.get_file_permissions(filepath)
        if perms and perms.get('permissions', {}).get('others', {}).get('write'):
            threat_score += 25
            factors.append("WORLD_WRITABLE")
        
        # 6. Проверка целостности (если файл уже отслеживается)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT hash FROM file_hashes WHERE path = ?', (filepath,))
        row = cursor.fetchone()
        if row:
            current_hash = self.calculate_file_hash(filepath)
            if current_hash and row[0] != current_hash:
                threat_score += 40
                factors.append("INTEGRITY_VIOLATION")
        conn.close()
        
        # AI решение
        if threat_score >= 80:
            decision = "BLOCK"
        elif threat_score >= 50:
            decision = "REQUIRE_CONFIRMATION"
        elif threat_score >= 25:
            decision = "WARN"
        else:
            decision = "ALLOW"
        
        # Сохраняем решение AI
        self.log_ai_decision(filepath, operation, threat_score, decision, factors)
        
        return threat_score, decision, {
            'factors': factors,
            'score': threat_score,
            'recommendation': self.get_recommendation(threat_score)
        }
    
    def get_recommendation(self, threat_score: int) -> str:
        """Получение рекомендации на основе уровня угрозы"""
        if threat_score >= 80:
            return "🚨 КРИТИЧЕСКАЯ УГРОЗА! Операция заблокирована. Требуется проверка администратора."
        elif threat_score >= 50:
            return "⚠️ ВЫСОКИЙ РИСК! Требуется подтверждение для выполнения операции."
        elif threat_score >= 25:
            return "⚡ СРЕДНИЙ РИСК. Рекомендуется проверить операцию."
        else:
            return "✅ Операция безопасна."
    
    def check_permission(self, filepath: str, operation: str, user: str = None) -> Tuple[bool, str]:
        """
        Проверка разрешения на операцию с файлом
        """
        # Получаем текущего пользователя
        if not user:
            user = os.environ.get('USER', 'unknown')
        
        # AI анализ
        threat_score, decision, analysis = self.ai_analyze_threat(filepath, operation)
        
        # Логируем попытку доступа
        allowed = decision in ['ALLOW', 'WARN']
        reason = f"{decision}: {analysis['recommendation']}"
        
        self.log_access(filepath, operation, user, allowed, threat_score, reason)
        
        return allowed, reason
    
    def protect_file(self, filepath: str, lock: bool = False) -> bool:
        """
        Добавление файла под защиту
        """
        try:
            # Вычисляем хеш
            file_hash = self.calculate_file_hash(filepath)
            if not file_hash:
                return False
            
            # Получаем права
            perms = self.get_file_permissions(filepath)
            
            # Сохраняем в БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO file_hashes 
                (path, hash, permissions, owner, last_check, locked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                filepath,
                file_hash,
                json.dumps(perms),
                os.environ.get('USER', 'unknown'),
                time.time(),
                lock
            ))
            
            conn.commit()
            conn.close()
            
            # Устанавливаем безопасные права (если lock=True)
            if lock:
                os.chmod(filepath, 0o600)  # Только владелец может читать/писать
            
            return True
        except Exception as e:
            print(f"Error protecting file: {e}")
            return False
    
    def verify_integrity(self, filepath: str) -> Tuple[bool, str]:
        """
        Проверка целостности файла
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT hash, permissions FROM file_hashes WHERE path = ?', (filepath,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False, "File not protected"
        
        stored_hash = row[0]
        current_hash = self.calculate_file_hash(filepath)
        
        if current_hash != stored_hash:
            return False, f"INTEGRITY VIOLATION! Hash mismatch"
        
        return True, "File integrity verified"
    
    def scan_directory(self, directory: str) -> Dict:
        """
        Сканирование директории на угрозы
        """
        results = {
            'total_files': 0,
            'protected_files': 0,
            'threats_found': [],
            'integrity_violations': [],
            'permission_issues': []
        }
        
        for root, dirs, files in os.walk(directory):
            # Пропускаем системные директории
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                filepath = os.path.join(root, file)
                results['total_files'] += 1
                
                # Проверяем целостность
                is_valid, message = self.verify_integrity(filepath)
                if not is_valid and "INTEGRITY VIOLATION" in message:
                    results['integrity_violations'].append(filepath)
                
                # AI анализ угроз
                threat_score, decision, analysis = self.ai_analyze_threat(filepath, 'scan')
                if threat_score >= 50:
                    results['threats_found'].append({
                        'file': filepath,
                        'score': threat_score,
                        'factors': analysis['factors']
                    })
                
                # Проверка прав
                perms = self.get_file_permissions(filepath)
                if perms and perms.get('permissions', {}).get('others', {}).get('write'):
                    results['permission_issues'].append({
                        'file': filepath,
                        'issue': 'World writable'
                    })
        
        return results
    
    def log_access(self, filepath: str, action: str, user: str, allowed: bool, threat_level: int, reason: str):
        """Логирование попыток доступа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO access_log 
            (timestamp, path, action, user, allowed, threat_level, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (time.time(), filepath, action, user, allowed, threat_level, reason))
        
        conn.commit()
        conn.close()
    
    def log_ai_decision(self, filepath: str, operation: str, risk_score: int, decision: str, factors: List):
        """Логирование решений AI"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_decisions 
            (timestamp, file_path, operation, risk_score, decision, factors)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (time.time(), filepath, operation, risk_score, decision, json.dumps(factors)))
        
        conn.commit()
        conn.close()
    
    def get_protection_status(self) -> Dict:
        """Получение общего статуса защиты"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Количество защищенных файлов
        cursor.execute('SELECT COUNT(*) FROM file_hashes')
        protected_count = cursor.fetchone()[0]
        
        # Количество заблокированных файлов
        cursor.execute('SELECT COUNT(*) FROM file_hashes WHERE locked = 1')
        locked_count = cursor.fetchone()[0]
        
        # Последние попытки доступа
        cursor.execute('''
            SELECT timestamp, path, action, user, allowed, threat_level 
            FROM access_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_access = cursor.fetchall()
        
        # Последние решения AI
        cursor.execute('''
            SELECT timestamp, file_path, risk_score, decision 
            FROM ai_decisions 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_decisions = cursor.fetchall()
        
        conn.close()
        
        return {
            'protected_files': protected_count,
            'locked_files': locked_count,
            'recent_access_attempts': [
                {
                    'time': datetime.fromtimestamp(r[0]).isoformat(),
                    'file': r[1],
                    'action': r[2],
                    'user': r[3],
                    'allowed': r[4],
                    'threat_level': r[5]
                } for r in recent_access
            ],
            'recent_ai_decisions': [
                {
                    'time': datetime.fromtimestamp(r[0]).isoformat(),
                    'file': r[1],
                    'risk_score': r[2],
                    'decision': r[3]
                } for r in recent_decisions
            ]
        }
    
    def quarantine_file(self, filepath: str) -> bool:
        """
        Карантин опасного файла
        """
        try:
            quarantine_dir = Path(__file__).parent / 'quarantine'
            quarantine_dir.mkdir(exist_ok=True)
            
            # Создаем уникальное имя
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = Path(filepath).name
            quarantine_path = quarantine_dir / f"{timestamp}_{filename}"
            
            # Перемещаем файл
            import shutil
            shutil.move(filepath, quarantine_path)
            
            # Убираем все права
            os.chmod(quarantine_path, 0o000)
            
            # Логируем
            self.log_access(
                filepath, 
                'QUARANTINE', 
                os.environ.get('USER', 'unknown'),
                True,
                100,
                f"File quarantined to {quarantine_path}"
            )
            
            return True
        except Exception as e:
            print(f"Quarantine failed: {e}")
            return False


# API для интеграции с мониторингом
class FileProtectionAPI:
    """API для интеграции с системой мониторинга"""
    
    def __init__(self):
        self.protection = AIFileProtection()
    
    async def check_file_operation(self, filepath: str, operation: str) -> Dict:
        """Проверка операции над файлом"""
        allowed, reason = self.protection.check_permission(filepath, operation)
        
        return {
            'allowed': allowed,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    async def protect_files(self, files: List[str], lock: bool = False) -> Dict:
        """Защита списка файлов"""
        results = []
        for filepath in files:
            success = self.protection.protect_file(filepath, lock)
            results.append({
                'file': filepath,
                'protected': success,
                'locked': lock
            })
        
        return {
            'protected_count': sum(1 for r in results if r['protected']),
            'results': results
        }
    
    async def scan_for_threats(self, directory: str) -> Dict:
        """Сканирование на угрозы"""
        return self.protection.scan_directory(directory)
    
    async def get_status(self) -> Dict:
        """Получение статуса защиты"""
        return self.protection.get_protection_status()
    
    async def verify_file(self, filepath: str) -> Dict:
        """Проверка целостности файла"""
        is_valid, message = self.protection.verify_integrity(filepath)
        
        return {
            'file': filepath,
            'valid': is_valid,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # Тестирование
    protection = AIFileProtection()
    
    print("🛡️ GALAXY FILE PROTECTION WITH AI")
    print("=" * 50)
    
    # Защищаем критические файлы
    critical_files = [
        'monitoring_server_fixed.py',
        'monitoring_config.json'
    ]
    
    for file in critical_files:
        if Path(file).exists():
            if protection.protect_file(file, lock=False):
                print(f"✅ Protected: {file}")
    
    # Проверяем операцию
    test_file = "test.txt"
    allowed, reason = protection.check_permission(test_file, 'write')
    print(f"\n📝 Write to {test_file}: {'✅ Allowed' if allowed else '❌ Blocked'}")
    print(f"   Reason: {reason}")
    
    # Статус защиты
    status = protection.get_protection_status()
    print(f"\n📊 Protection Status:")
    print(f"   Protected files: {status['protected_files']}")
    print(f"   Locked files: {status['locked_files']}")