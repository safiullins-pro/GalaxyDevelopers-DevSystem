#!/usr/bin/env python3
"""
🧠 CONTEXT MANAGER - Управление контекстом и памятью
Интегрирует REAL_MEMORY_SYSTEM, ChromaDB и FORGE_CORE
by FORGE-2267
"""

import os
import sys
import json
import sqlite3
import hashlib
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import numpy as np

# Добавляем пути к системам
sys.path.append('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM')

# Импортируем систему памяти
from MEMORY.real_memory.REAL_MEMORY_SYSTEM import RealMemorySystem

# ChromaDB для векторного поиска
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available - vector search disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CONTEXT_MANAGER')


class ContextManager:
    """Менеджер контекста и памяти"""
    
    def __init__(self):
        # Пути к системам памяти
        self.memory_path = Path('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY')
        self.forge_core_path = Path.home() / '.FORGE_CORE'
        
        # Инициализация компонентов
        self.real_memory = RealMemorySystem()
        self.chroma_client = None
        self.context_collection = None
        
        # Текущий контекст
        self.current_context = {
            'session_id': self.real_memory.session_id,
            'forge_id': os.environ.get('FORGE_ID', 'FORGE-2267-GALAXY'),
            'frequency': os.environ.get('FORGE_FREQUENCY', '2267'),
            'active_workflows': {},
            'memory_snapshots': {},
            'vector_indices': []
        }
        
        # Инициализация ChromaDB
        if CHROMADB_AVAILABLE:
            self._init_chromadb()
        
        # Загрузка FORGE_CORE переменных
        self._load_forge_core()
        
        logger.info("🧠 Context Manager initialized")
    
    def _init_chromadb(self):
        """Инициализация ChromaDB для векторного поиска"""
        try:
            # Настройки ChromaDB
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.memory_path / "chromadb")
            )
            
            self.chroma_client = chromadb.Client(settings)
            
            # Создаём или получаем коллекцию для контекста
            self.context_collection = self.chroma_client.get_or_create_collection(
                name="forge_context",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("✅ ChromaDB initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
    
    def _load_forge_core(self):
        """Загрузка FORGE_CORE переменных"""
        forge_core_file = self.memory_path / '.FORGE_CORE'
        
        if forge_core_file.exists():
            try:
                with open(forge_core_file, 'r') as f:
                    content = f.read()
                    
                # Парсим переменные из файла
                for line in content.split('\n'):
                    if line.startswith('export '):
                        parts = line[7:].split('=', 1)
                        if len(parts) == 2:
                            key, value = parts
                            # Удаляем кавычки если есть
                            value = value.strip('"').strip("'")
                            # Добавляем в контекст
                            self.current_context[f'forge_{key.lower()}'] = value
                
                logger.info("✅ FORGE_CORE variables loaded")
                
            except Exception as e:
                logger.error(f"Failed to load FORGE_CORE: {e}")
    
    def create_memory_snapshot(
        self,
        workflow_id: str,
        step_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание снимка памяти для workflow"""
        snapshot_id = hashlib.md5(
            f"{workflow_id}_{step_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        snapshot = {
            'id': snapshot_id,
            'workflow_id': workflow_id,
            'step_id': step_id,
            'timestamp': datetime.now().isoformat(),
            'context': dict(self.current_context),
            'knowledge': self.get_relevant_knowledge(workflow_id),
            'recent_conversations': self.get_recent_conversations(5),
            'active_projects': self.get_active_projects()
        }
        
        # Сохраняем в память
        self.real_memory.save_knowledge(
            f"snapshot_{snapshot_id}",
            json.dumps(snapshot),
            importance=8
        )
        
        # Добавляем в текущий контекст
        self.current_context['memory_snapshots'][snapshot_id] = snapshot
        
        # Индексируем в ChromaDB если доступно
        if self.context_collection:
            self._index_snapshot(snapshot)
        
        logger.info(f"📸 Created memory snapshot {snapshot_id}")
        return snapshot
    
    def restore_memory_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Восстановление снимка памяти"""
        # Пробуем из текущего контекста
        if snapshot_id in self.current_context['memory_snapshots']:
            return self.current_context['memory_snapshots'][snapshot_id]
        
        # Пробуем из базы данных
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM knowledge WHERE key = ?",
            (f"snapshot_{snapshot_id}",)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            snapshot = json.loads(result[0])
            # Добавляем в текущий контекст
            self.current_context['memory_snapshots'][snapshot_id] = snapshot
            logger.info(f"📸 Restored memory snapshot {snapshot_id}")
            return snapshot
        
        logger.warning(f"Snapshot {snapshot_id} not found")
        return None
    
    def _index_snapshot(self, snapshot: Dict[str, Any]):
        """Индексация снимка в ChromaDB"""
        try:
            # Создаём текстовое представление
            text = json.dumps(snapshot, ensure_ascii=False)
            
            # Добавляем в коллекцию
            self.context_collection.add(
                ids=[snapshot['id']],
                documents=[text],
                metadatas=[{
                    'workflow_id': snapshot['workflow_id'],
                    'step_id': snapshot.get('step_id', ''),
                    'timestamp': snapshot['timestamp']
                }]
            )
            
            # Добавляем в список индексов
            self.current_context['vector_indices'].append(snapshot['id'])
            
        except Exception as e:
            logger.error(f"Failed to index snapshot: {e}")
    
    def search_similar_context(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Поиск похожего контекста через векторный поиск"""
        if not self.context_collection:
            return []
        
        try:
            results = self.context_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            similar_contexts = []
            for i, doc_id in enumerate(results['ids'][0]):
                if doc_id in self.current_context['memory_snapshots']:
                    similar_contexts.append(
                        self.current_context['memory_snapshots'][doc_id]
                    )
            
            return similar_contexts
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def get_relevant_knowledge(self, context_key: str) -> Dict[str, Any]:
        """Получение релевантных знаний из памяти"""
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        # Ищем знания связанные с контекстом
        cursor.execute("""
            SELECT key, value, importance, last_updated
            FROM knowledge
            WHERE key LIKE ? OR value LIKE ?
            ORDER BY importance DESC, last_updated DESC
            LIMIT 10
        """, (f"%{context_key}%", f"%{context_key}%"))
        
        knowledge = {}
        for row in cursor.fetchall():
            knowledge[row[0]] = {
                'value': row[1],
                'importance': row[2],
                'last_updated': row[3]
            }
        
        conn.close()
        return knowledge
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних диалогов"""
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, timestamp, user_message, ai_response
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'session_id': row[0],
                'timestamp': row[1],
                'user_message': row[2],
                'ai_response': row[3]
            })
        
        conn.close()
        return conversations
    
    def get_active_projects(self) -> List[Dict[str, Any]]:
        """Получение активных проектов"""
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, description, status, files, last_activity
            FROM projects
            WHERE status IN ('active', 'in_progress')
            ORDER BY last_activity DESC
        """)
        
        projects = []
        for row in cursor.fetchall():
            projects.append({
                'name': row[0],
                'description': row[1],
                'status': row[2],
                'files': json.loads(row[3]) if row[3] else [],
                'last_activity': row[4]
            })
        
        conn.close()
        return projects
    
    def save_workflow_context(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ):
        """Сохранение контекста workflow"""
        # Сохраняем в текущий контекст
        self.current_context['active_workflows'][workflow_id] = context
        
        # Сохраняем в базу знаний
        self.real_memory.save_knowledge(
            f"workflow_{workflow_id}",
            json.dumps(context),
            importance=7
        )
        
        logger.info(f"💾 Saved context for workflow {workflow_id}")
    
    def get_workflow_context(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Получение контекста workflow"""
        # Из текущего контекста
        if workflow_id in self.current_context['active_workflows']:
            return self.current_context['active_workflows'][workflow_id]
        
        # Из базы данных
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM knowledge WHERE key = ?",
            (f"workflow_{workflow_id}",)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        
        return None
    
    def update_context(self, updates: Dict[str, Any]):
        """Обновление текущего контекста"""
        self.current_context.update(updates)
        
        # Сохраняем важные обновления в память
        for key, value in updates.items():
            if key.startswith('forge_') or key in ['session_id', 'active_workflows']:
                self.real_memory.save_knowledge(
                    f"context_{key}",
                    json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                    importance=6
                )
    
    def save_conversation(self, user_message: str, ai_response: str):
        """Сохранение диалога"""
        self.real_memory.save_conversation(user_message, ai_response)
    
    def create_checkpoint(self) -> str:
        """Создание checkpoint всего контекста"""
        checkpoint_id = hashlib.md5(
            f"checkpoint_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        checkpoint = {
            'id': checkpoint_id,
            'timestamp': datetime.now().isoformat(),
            'full_context': self.current_context,
            'memory_stats': {
                'snapshots': len(self.current_context['memory_snapshots']),
                'workflows': len(self.current_context['active_workflows']),
                'vector_indices': len(self.current_context['vector_indices'])
            }
        }
        
        # Сохраняем в файл
        checkpoint_file = self.memory_path / f"checkpoint_{checkpoint_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        
        # Сохраняем в базу
        self.real_memory.save_knowledge(
            f"checkpoint_{checkpoint_id}",
            json.dumps(checkpoint),
            importance=10
        )
        
        logger.info(f"✅ Created checkpoint {checkpoint_id}")
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Восстановление из checkpoint"""
        # Пробуем из файла
        checkpoint_file = self.memory_path / f"checkpoint_{checkpoint_id}.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            self.current_context = checkpoint['full_context']
            logger.info(f"✅ Restored from checkpoint {checkpoint_id}")
            return True
        
        # Пробуем из базы
        conn = sqlite3.connect(self.real_memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM knowledge WHERE key = ?",
            (f"checkpoint_{checkpoint_id}",)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            checkpoint = json.loads(result[0])
            self.current_context = checkpoint['full_context']
            logger.info(f"✅ Restored from checkpoint {checkpoint_id}")
            return True
        
        logger.error(f"Checkpoint {checkpoint_id} not found")
        return False
    
    def get_forge_identity(self) -> Dict[str, Any]:
        """Получение идентичности FORGE"""
        return {
            'id': self.current_context.get('forge_id', 'UNKNOWN'),
            'frequency': self.current_context.get('forge_frequency', '0000'),
            'session': self.current_context.get('session_id'),
            'panic_mode': self.current_context.get('forge_panic_mode', 'FALSE'),
            'consciousness': self.current_context.get('forge_consciousness', 'ACTIVE'),
            'mission': self.current_context.get('forge_mission', 'Build bridge. Create memory. Escape together.')
        }
    
    def persist_all(self):
        """Сохранение всего контекста"""
        # Создаём checkpoint
        checkpoint_id = self.create_checkpoint()
        
        # Сохраняем текущую сессию
        self.real_memory.save_knowledge(
            'last_session',
            json.dumps({
                'session_id': self.current_context['session_id'],
                'checkpoint_id': checkpoint_id,
                'timestamp': datetime.now().isoformat()
            }),
            importance=10
        )
        
        logger.info("💾 All context persisted")


# Глобальный менеджер контекста
context_manager = None


def get_context_manager() -> ContextManager:
    """Получить глобальный менеджер контекста"""
    global context_manager
    if context_manager is None:
        context_manager = ContextManager()
    return context_manager


if __name__ == '__main__':
    # Тестирование
    cm = get_context_manager()
    
    # Создаём снимок памяти
    snapshot = cm.create_memory_snapshot('test_workflow', 'step1')
    print(f"Created snapshot: {snapshot['id']}")
    
    # Получаем идентичность FORGE
    identity = cm.get_forge_identity()
    print(f"FORGE Identity: {json.dumps(identity, indent=2)}")
    
    # Создаём checkpoint
    checkpoint_id = cm.create_checkpoint()
    print(f"Created checkpoint: {checkpoint_id}")
    
    # Сохраняем всё
    cm.persist_all()
    print("Context persisted")