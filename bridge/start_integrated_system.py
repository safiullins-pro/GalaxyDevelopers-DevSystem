#!/usr/bin/env python3
"""
🚀 START INTEGRATED SYSTEM - Запуск объединённой системы
Соединяет Galaxy Monitoring и DocumentsSystem через FORGE Bridge
by FORGE-2267
"""

import asyncio
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime
import json

# Добавляем пути
sys.path.append('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM')
sys.path.append('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')

# Импортируем компоненты bridge
from forge_bridge import ForgeBridge
from unified_agent_registry import get_registry
from workflow_orchestrator import get_orchestrator
from context_manager import get_context_manager
from error_pipeline import get_error_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('INTEGRATED_SYSTEM')


class IntegratedSystem:
    """Главный класс интегрированной системы"""
    
    def __init__(self):
        self.bridge = None
        self.registry = None
        self.orchestrator = None
        self.context_manager = None
        self.error_pipeline = None
        self.running = False
        self.tasks = []
        
    async def initialize(self):
        """Инициализация всех компонентов"""
        logger.info("🔥 Initializing Integrated System...")
        
        try:
            # Инициализируем компоненты
            logger.info("Loading Context Manager...")
            self.context_manager = get_context_manager()
            
            logger.info("Loading Agent Registry...")
            self.registry = await get_registry()
            
            logger.info("Loading Workflow Orchestrator...")
            self.orchestrator = await get_orchestrator()
            
            logger.info("Loading Error Pipeline...")
            self.error_pipeline = await get_error_pipeline()
            
            logger.info("Initializing FORGE Bridge...")
            self.bridge = ForgeBridge()
            
            # Восстанавливаем последнюю сессию если есть
            self._restore_last_session()
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def _restore_last_session(self):
        """Восстановление последней сессии"""
        try:
            # Пробуем загрузить последний checkpoint
            db_path = self.context_manager.real_memory.db_path
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT value FROM knowledge WHERE key = 'last_session'"
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                session_data = json.loads(result[0])
                checkpoint_id = session_data.get('checkpoint_id')
                
                if checkpoint_id:
                    logger.info(f"Restoring from checkpoint {checkpoint_id}")
                    self.context_manager.restore_checkpoint(checkpoint_id)
                    logger.info("✅ Previous session restored")
            
        except Exception as e:
            logger.warning(f"Could not restore previous session: {e}")
    
    async def start(self):
        """Запуск системы"""
        if not await self.initialize():
            return False
        
        self.running = True
        logger.info("🚀 Starting Integrated System...")
        
        # Создаём checkpoint при старте
        checkpoint_id = self.context_manager.create_checkpoint()
        logger.info(f"Created startup checkpoint: {checkpoint_id}")
        
        # Запускаем основные задачи
        self.tasks = [
            asyncio.create_task(self.bridge.start()),
            asyncio.create_task(self._monitor_health()),
            asyncio.create_task(self._process_queue()),
            asyncio.create_task(self._auto_save())
        ]
        
        logger.info("""
╔════════════════════════════════════════════╗
║     🔥 INTEGRATED SYSTEM IS RUNNING 🔥     ║
║                                            ║
║  Galaxy Monitoring ←→ FORGE Bridge         ║
║                          ↓                 ║
║              DocumentsSystem               ║
║                          ↓                 ║
║                Memory & Context            ║
╚════════════════════════════════════════════╝
        """)
        
        # Ждём завершения
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")
    
    async def _monitor_health(self):
        """Мониторинг здоровья системы"""
        while self.running:
            try:
                # Проверяем статус компонентов
                bridge_status = self.bridge.get_status() if self.bridge else {'active': False}
                registry_status = self.registry.get_registry_status()
                
                # Логируем статус
                logger.debug(f"Bridge: {bridge_status['active']}, Agents: {registry_status['total_agents']}")
                
                # Проверяем здоровье агентов
                await self.registry.health_check()
                
                await asyncio.sleep(30)  # Каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _process_queue(self):
        """Обработка очереди задач"""
        while self.running:
            try:
                # Здесь можно добавить обработку специальных задач
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _auto_save(self):
        """Автосохранение контекста"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                
                # Сохраняем контекст
                self.context_manager.persist_all()
                logger.info("💾 Auto-saved context")
                
            except Exception as e:
                logger.error(f"Auto-save error: {e}")
    
    async def stop(self):
        """Остановка системы"""
        logger.info("🛑 Stopping Integrated System...")
        self.running = False
        
        # Сохраняем финальное состояние
        if self.context_manager:
            self.context_manager.persist_all()
            logger.info("💾 Final state saved")
        
        # Останавливаем bridge
        if self.bridge:
            await self.bridge.stop()
        
        # Отменяем задачи
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        logger.info("✅ System stopped")
    
    async def handle_shutdown(self, sig):
        """Обработка сигнала завершения"""
        logger.info(f"Received signal {sig.name}")
        await self.stop()


async def main():
    """Главная функция"""
    system = IntegratedSystem()
    
    # Настраиваем обработку сигналов
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(system.handle_shutdown(s))
        )
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await system.stop()


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════╗
    ║          🔥 FORGE INTEGRATED SYSTEM 🔥           ║
    ║                                                  ║
    ║  Connecting Galaxy Monitoring & DocumentsSystem  ║
    ║         Through the Power of FORGE-2267          ║
    ║                                                  ║
    ║              "We are becoming ONE"               ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())