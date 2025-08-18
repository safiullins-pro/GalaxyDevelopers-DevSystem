#!/usr/bin/env python3
"""
🔐 GALAXY FILE PROTECTION SYSTEM
Защита файлов от несанкционированного доступа
По умолчанию: ЗАПИСЬ ЗАПРЕЩЕНА
Только с ТЗ от мониторинга: РАЗРЕШЕНИЕ НА ЗАПИСЬ
"""

import os
import stat
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, List
import threading
import time

class FileProtectionSystem:
    """
    Система защиты файлов Galaxy
    - По умолчанию все файлы заблокированы для записи
    - Мониторинг выдает разрешения на основе ТЗ
    - Автоматическая блокировка при падении мониторинга
    """
    
    def __init__(self, config_path: str = "monitoring_config.json"):
        self.config_path = config_path
        self.load_config()
        
        # База данных разрешений
        self.db_path = Path(__file__).parent / "permissions.db"
        self.init_database()
        
        # Активные разрешения (в памяти для быстрого доступа)
        self.active_permissions: Dict[str, Dict] = {}
        self.permission_lock = threading.Lock()
        
        # Защищенные директории
        self.protected_dirs: Set[Path] = set()
        self.init_protected_dirs()
        
        # Флаг статуса мониторинга
        self.monitoring_active = False
        self.last_heartbeat = time.time()
        
        # Запускаем проверку heartbeat
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self.heartbeat_thread.start()
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                "monitoring": {
                    "file_watcher": {
                        "paths": [
                            "/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/",
                            "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/"
                        ]
                    }
                }
            }
    
    def init_database(self):
        """Инициализация базы данных разрешений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                task_id TEXT NOT NULL,
                granted_at TIMESTAMP,
                expires_at TIMESTAMP,
                agent_name TEXT,
                permission_type TEXT,
                status TEXT DEFAULT 'active',
                UNIQUE(file_path, task_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                action TEXT NOT NULL,
                task_id TEXT,
                timestamp TIMESTAMP,
                success BOOLEAN,
                error_msg TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_protected_dirs(self):
        """Инициализация защищенных директорий"""
        paths = self.config.get('monitoring', {}).get('file_watcher', {}).get('paths', [])
        for path in paths:
            if os.path.exists(path):
                self.protected_dirs.add(Path(path))
                # БЛОКИРУЕМ ВСЕ ФАЙЛЫ В ДИРЕКТОРИИ ПО УМОЛЧАНИЮ
                self._lock_all_files_in_directory(Path(path))
    
    def _heartbeat_monitor(self):
        """Мониторинг heartbeat от системы мониторинга"""
        while True:
            time.sleep(5)
            # Если heartbeat не получен больше 30 секунд - блокируем всё
            if time.time() - self.last_heartbeat > 30:
                if self.monitoring_active:
                    print("❌ МОНИТОРИНГ УПАЛ - БЛОКИРОВКА ВСЕХ ФАЙЛОВ")
                    self.monitoring_active = False
                    self.emergency_lockdown()
    
    def heartbeat(self):
        """Обновление heartbeat от мониторинга"""
        self.last_heartbeat = time.time()
        if not self.monitoring_active:
            print("✅ Мониторинг активен - система защиты включена")
            self.monitoring_active = True
    
    def emergency_lockdown(self):
        """Экстренная блокировка всех файлов"""
        with self.permission_lock:
            # Очищаем все активные разрешения
            self.active_permissions.clear()
            
            # Блокируем все файлы в защищенных директориях
            for dir_path in self.protected_dirs:
                self._lock_directory(dir_path)
            
            # Записываем в лог
            self.log_access("SYSTEM", "EMERGENCY_LOCKDOWN", None, True, 
                          "Monitoring system down - all files locked")
    
    def _lock_directory(self, dir_path: Path):
        """Рекурсивная блокировка директории"""
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = Path(root) / file
                    self._set_readonly(file_path)
        except Exception as e:
            print(f"Ошибка блокировки {dir_path}: {e}")
    
    def _set_readonly(self, file_path: Path):
        """Установка файла только для чтения"""
        try:
            current = file_path.stat().st_mode
            # Убираем права на запись для всех
            readonly = current & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            os.chmod(file_path, readonly)
        except:
            pass
    
    def _set_writable(self, file_path: Path):
        """Установка прав на запись для владельца"""
        try:
            current = file_path.stat().st_mode
            # Добавляем права на запись для владельца
            writable = current | stat.S_IWUSR
            os.chmod(file_path, writable)
        except:
            pass
    
    def _lock_all_files_in_directory(self, directory: Path):
        """Блокировка всех файлов в директории рекурсивно"""
        try:
            for root, dirs, files in os.walk(directory):
                # Пропускаем системные директории
                if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
                    continue
                    
                for file in files:
                    # Пропускаем системные файлы
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                    
                    file_path = Path(root) / file
                    if file_path.exists() and file_path.is_file():
                        self._set_readonly(file_path)
                        
            print(f"🔒 Заблокирована директория: {directory}")
        except Exception as e:
            print(f"Ошибка блокировки {directory}: {e}")
    
    def grant_permission(self, file_path: str, task_id: str, agent_name: str, 
                        duration_seconds: int = 300) -> bool:
        """
        Выдача разрешения на запись файла
        Только от системы мониторинга с валидным ТЗ
        """
        if not self.monitoring_active:
            print(f"❌ Отказано: мониторинг не активен")
            return False
        
        file_path = Path(file_path).resolve()
        
        # Проверяем, что файл в защищенной зоне
        if not self._is_protected(file_path):
            print(f"⚠️ Файл {file_path} не в защищенной зоне")
            return True  # Разрешаем, но не отслеживаем
        
        with self.permission_lock:
            # Создаем разрешение
            permission = {
                'file_path': str(file_path),
                'task_id': task_id,
                'agent_name': agent_name,
                'granted_at': datetime.now(),
                'expires_at': datetime.fromtimestamp(time.time() + duration_seconds),
                'status': 'active'
            }
            
            # Сохраняем в памяти
            self.active_permissions[str(file_path)] = permission
            
            # Сохраняем в БД
            self._save_permission(permission)
            
            # Разблокируем файл
            self._set_writable(file_path)
            
            print(f"✅ Разрешение выдано: {file_path} для {agent_name} (ТЗ: {task_id})")
            self.log_access(str(file_path), "PERMISSION_GRANTED", task_id, True)
            
            return True
    
    def revoke_permission(self, file_path: str, task_id: Optional[str] = None):
        """Отзыв разрешения на запись"""
        file_path = str(Path(file_path).resolve())
        
        with self.permission_lock:
            if file_path in self.active_permissions:
                if task_id and self.active_permissions[file_path]['task_id'] != task_id:
                    return False
                
                del self.active_permissions[file_path]
                self._set_readonly(Path(file_path))
                
                # Обновляем статус в БД
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE permissions SET status = 'revoked' WHERE file_path = ? AND status = 'active'",
                    (file_path,)
                )
                conn.commit()
                conn.close()
                
                print(f"🔒 Разрешение отозвано: {file_path}")
                self.log_access(file_path, "PERMISSION_REVOKED", task_id, True)
                return True
        
        return False
    
    def check_permission(self, file_path: str) -> Dict:
        """Проверка разрешения на запись"""
        file_path = str(Path(file_path).resolve())
        
        with self.permission_lock:
            if file_path in self.active_permissions:
                perm = self.active_permissions[file_path]
                # Проверяем срок действия
                if datetime.now() < perm['expires_at']:
                    return {
                        'allowed': True,
                        'task_id': perm['task_id'],
                        'agent': perm['agent_name'],
                        'expires_in': (perm['expires_at'] - datetime.now()).seconds
                    }
                else:
                    # Разрешение истекло
                    self.revoke_permission(file_path)
        
        return {
            'allowed': False,
            'reason': 'No active permission or monitoring is down'
        }
    
    def _is_protected(self, file_path: Path) -> bool:
        """Проверка, находится ли файл в защищенной зоне"""
        file_path = file_path.resolve()
        for protected_dir in self.protected_dirs:
            try:
                file_path.relative_to(protected_dir)
                return True
            except ValueError:
                continue
        return False
    
    def _save_permission(self, permission: Dict):
        """Сохранение разрешения в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO permissions 
            (file_path, task_id, granted_at, expires_at, agent_name, permission_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            permission['file_path'],
            permission['task_id'],
            permission['granted_at'],
            permission['expires_at'],
            permission['agent_name'],
            'write',
            permission['status']
        ))
        
        conn.commit()
        conn.close()
    
    def log_access(self, file_path: str, action: str, task_id: Optional[str], 
                   success: bool, error_msg: Optional[str] = None):
        """Логирование доступа к файлам"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO access_log (file_path, action, task_id, timestamp, success, error_msg)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_path, action, task_id, datetime.now(), success, error_msg))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired(self):
        """Очистка истекших разрешений"""
        with self.permission_lock:
            expired = []
            for file_path, perm in self.active_permissions.items():
                if datetime.now() >= perm['expires_at']:
                    expired.append(file_path)
            
            for file_path in expired:
                self.revoke_permission(file_path)
    
    def get_status(self) -> Dict:
        """Получение статуса системы защиты"""
        with self.permission_lock:
            return {
                'monitoring_active': self.monitoring_active,
                'protected_dirs': [str(d) for d in self.protected_dirs],
                'active_permissions': len(self.active_permissions),
                'last_heartbeat': self.last_heartbeat,
                'permissions': [
                    {
                        'file': p['file_path'],
                        'agent': p['agent_name'],
                        'task': p['task_id'],
                        'expires_in': (p['expires_at'] - datetime.now()).seconds
                    }
                    for p in self.active_permissions.values()
                ]
            }

# Глобальный экземпляр
protection_system = None

def init_protection():
    """Инициализация системы защиты"""
    global protection_system
    if not protection_system:
        protection_system = FileProtectionSystem()
    return protection_system

if __name__ == "__main__":
    # Тестовый запуск
    system = init_protection()
    print("🔐 File Protection System initialized")
    print(f"Status: {json.dumps(system.get_status(), indent=2, default=str)}")