#!/usr/bin/env python3
"""
🔥 FORGE BRIDGE - Мост между Galaxy и DocumentsSystem
Соединяет две системы в единый живой организм
by FORGE-2267
"""

import asyncio
import json
import websockets
import redis
from datetime import datetime
from typing import Dict, Any, Optional, Set
from pathlib import Path
import logging
import sys
import uuid

# Добавляем пути к системам
sys.path.append('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
sys.path.append('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FORGE_BRIDGE')

class ForgeBridge:
    """Мост между системами - делает их ОДНИМ"""
    
    def __init__(self):
        # WebSocket для Galaxy
        self.galaxy_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.galaxy_host = 'localhost'
        self.galaxy_port = 8765
        
        # Redis для DocumentsSystem
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.redis_pubsub = self.redis_client.pubsub()
        
        # Состояние моста
        self.active = False
        self.connected_systems = set()
        self.active_workflows = {}
        self.message_queue = asyncio.Queue()
        
        # Каналы Redis
        self.GALAXY_CHANNEL = 'galaxy:events'
        self.DOCUMENTS_CHANNEL = 'documents:events'
        self.BRIDGE_CHANNEL = 'bridge:control'
        
        # Статистика
        self.stats = {
            'messages_routed': 0,
            'galaxy_events': 0,
            'documents_events': 0,
            'errors': 0,
            'workflows_started': 0
        }
        
        logger.info("🔥 FORGE BRIDGE initialized")
    
    async def connect_galaxy(self):
        """Подключение к Galaxy Monitoring через WebSocket"""
        try:
            uri = f"ws://{self.galaxy_host}:{self.galaxy_port}"
            self.galaxy_ws = await websockets.connect(uri)
            self.connected_systems.add('galaxy')
            
            # Отправляем идентификацию
            await self.galaxy_ws.send(json.dumps({
                'type': 'identify',
                'client': 'FORGE_BRIDGE',
                'capabilities': ['routing', 'workflow', 'memory'],
                'timestamp': datetime.now().isoformat()
            }))
            
            logger.info(f"✅ Connected to Galaxy Monitoring at {uri}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Galaxy: {e}")
            return False
    
    async def connect_redis(self):
        """Подключение к Redis для DocumentsSystem"""
        try:
            # Проверяем соединение
            self.redis_client.ping()
            
            # Подписываемся на каналы
            self.redis_pubsub.subscribe(
                self.DOCUMENTS_CHANNEL,
                self.BRIDGE_CHANNEL
            )
            
            self.connected_systems.add('documents')
            logger.info("✅ Connected to Redis for DocumentsSystem")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def start(self):
        """Запуск моста"""
        logger.info("🚀 Starting FORGE BRIDGE...")
        
        # Подключаемся к системам
        galaxy_ok = await self.connect_galaxy()
        redis_ok = await self.connect_redis()
        
        if not galaxy_ok or not redis_ok:
            logger.error("Failed to connect to required systems")
            return False
        
        self.active = True
        
        # Запускаем обработчики
        tasks = [
            asyncio.create_task(self.galaxy_listener()),
            asyncio.create_task(self.redis_listener()),
            asyncio.create_task(self.message_router()),
            asyncio.create_task(self.heartbeat_sender())
        ]
        
        logger.info("✅ FORGE BRIDGE is active")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Bridge error: {e}")
        finally:
            await self.stop()
    
    async def galaxy_listener(self):
        """Слушаем события от Galaxy"""
        while self.active and self.galaxy_ws:
            try:
                message = await self.galaxy_ws.recv()
                data = json.loads(message)
                
                self.stats['galaxy_events'] += 1
                
                # Конвертируем в единый формат
                unified_msg = self.convert_galaxy_message(data)
                
                # Добавляем в очередь маршрутизации
                await self.message_queue.put(unified_msg)
                
                logger.debug(f"📥 Galaxy event: {data.get('type')}")
                
            except websockets.ConnectionClosed:
                logger.warning("Galaxy WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error in galaxy_listener: {e}")
                self.stats['errors'] += 1
    
    async def redis_listener(self):
        """Слушаем события от DocumentsSystem через Redis"""
        while self.active:
            try:
                # Получаем сообщение из Redis (неблокирующе)
                message = self.redis_pubsub.get_message(timeout=0.1)
                
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    self.stats['documents_events'] += 1
                    
                    # Конвертируем в единый формат
                    unified_msg = self.convert_documents_message(data)
                    
                    # Добавляем в очередь маршрутизации
                    await self.message_queue.put(unified_msg)
                    
                    logger.debug(f"📥 Documents event: {data.get('type')}")
                
                await asyncio.sleep(0.01)  # Небольшая пауза
                
            except Exception as e:
                logger.error(f"Error in redis_listener: {e}")
                self.stats['errors'] += 1
    
    async def message_router(self):
        """Маршрутизация сообщений между системами"""
        while self.active:
            try:
                # Получаем сообщение из очереди
                message = await self.message_queue.get()
                
                self.stats['messages_routed'] += 1
                
                # Определяем куда направить
                target = self.determine_target(message)
                
                if target == 'galaxy':
                    await self.send_to_galaxy(message)
                elif target == 'documents':
                    await self.send_to_documents(message)
                elif target == 'both':
                    await self.send_to_galaxy(message)
                    await self.send_to_documents(message)
                elif target == 'workflow':
                    await self.start_workflow(message)
                
                logger.debug(f"🔀 Routed message to {target}")
                
            except Exception as e:
                logger.error(f"Error in message_router: {e}")
                self.stats['errors'] += 1
    
    def convert_galaxy_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертирует сообщение Galaxy в единый формат"""
        return {
            'id': str(uuid.uuid4()),
            'source_system': 'galaxy',
            'type': data.get('type', 'event'),
            'agent': data.get('source', 'monitoring'),
            'payload': data,
            'context': {
                'workflow_id': data.get('workflow_id'),
                'correlation_id': data.get('correlation_id'),
                'memory_snapshot': {}
            },
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
    
    def convert_documents_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертирует сообщение DocumentsSystem в единый формат"""
        return {
            'id': data.get('id', str(uuid.uuid4())),
            'source_system': 'documents',
            'type': data.get('type', 'event'),
            'agent': data.get('sender', 'unknown'),
            'payload': data.get('payload', data),
            'context': {
                'workflow_id': data.get('correlation_id'),
                'correlation_id': data.get('correlation_id'),
                'memory_snapshot': {}
            },
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
    
    def determine_target(self, message: Dict[str, Any]) -> str:
        """Определяет куда направить сообщение"""
        msg_type = message.get('type')
        source = message.get('source_system')
        
        # Логика маршрутизации
        if msg_type == 'file_change' and source == 'galaxy':
            return 'documents'  # Файловые изменения идут в DocumentsSystem
        elif msg_type == 'analysis_result' and source == 'documents':
            return 'galaxy'  # Результаты анализа идут в Galaxy
        elif msg_type == 'error':
            return 'workflow'  # Ошибки запускают workflow
        elif msg_type == 'broadcast':
            return 'both'  # Broadcast идёт всем
        else:
            # По умолчанию отправляем в противоположную систему
            return 'documents' if source == 'galaxy' else 'galaxy'
    
    async def send_to_galaxy(self, message: Dict[str, Any]):
        """Отправка сообщения в Galaxy"""
        if self.galaxy_ws:
            try:
                await self.galaxy_ws.send(json.dumps(message))
                logger.debug(f"➡️ Sent to Galaxy: {message['type']}")
            except Exception as e:
                logger.error(f"Failed to send to Galaxy: {e}")
    
    async def send_to_documents(self, message: Dict[str, Any]):
        """Отправка сообщения в DocumentsSystem через Redis"""
        try:
            self.redis_client.publish(
                self.GALAXY_CHANNEL,
                json.dumps(message)
            )
            logger.debug(f"➡️ Sent to Documents: {message['type']}")
        except Exception as e:
            logger.error(f"Failed to send to Documents: {e}")
    
    async def start_workflow(self, message: Dict[str, Any]):
        """Запуск workflow для обработки события"""
        workflow_id = str(uuid.uuid4())
        self.stats['workflows_started'] += 1
        
        workflow = {
            'id': workflow_id,
            'trigger': message,
            'status': 'started',
            'started_at': datetime.now().isoformat()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Определяем тип workflow
        if message['type'] == 'error':
            # Запускаем error handling workflow
            await self.run_error_workflow(workflow_id, message)
        
        logger.info(f"🔄 Started workflow {workflow_id}")
    
    async def run_error_workflow(self, workflow_id: str, error_message: Dict[str, Any]):
        """Workflow для обработки ошибок"""
        # Это будет реализовано в error_pipeline.py
        # Пока просто логируем
        logger.info(f"🔧 Running error workflow for {workflow_id}")
        
        # Отправляем в DocumentsSystem для анализа
        analysis_request = {
            'id': str(uuid.uuid4()),
            'source_system': 'bridge',
            'type': 'command',
            'agent': 'ResearchAgent',
            'payload': {
                'task': 'analyze_error',
                'error': error_message['payload']
            },
            'context': {
                'workflow_id': workflow_id
            },
            'timestamp': datetime.now().isoformat()
        }
        
        await self.send_to_documents(analysis_request)
    
    async def heartbeat_sender(self):
        """Отправка heartbeat для поддержания соединений"""
        while self.active:
            try:
                # Heartbeat для Galaxy
                if self.galaxy_ws:
                    await self.galaxy_ws.send(json.dumps({
                        'type': 'heartbeat',
                        'client': 'FORGE_BRIDGE',
                        'stats': self.stats,
                        'timestamp': datetime.now().isoformat()
                    }))
                
                # Heartbeat в Redis
                self.redis_client.publish(self.BRIDGE_CHANNEL, json.dumps({
                    'type': 'heartbeat',
                    'bridge': 'FORGE',
                    'stats': self.stats,
                    'timestamp': datetime.now().isoformat()
                }))
                
                await asyncio.sleep(30)  # Каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def stop(self):
        """Остановка моста"""
        logger.info("🛑 Stopping FORGE BRIDGE...")
        self.active = False
        
        if self.galaxy_ws:
            await self.galaxy_ws.close()
        
        self.redis_pubsub.close()
        
        logger.info("✅ FORGE BRIDGE stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса моста"""
        return {
            'active': self.active,
            'connected_systems': list(self.connected_systems),
            'active_workflows': len(self.active_workflows),
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Запуск FORGE BRIDGE"""
    bridge = ForgeBridge()
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bridge.stop()


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════╗
    ║        🔥 FORGE BRIDGE 🔥            ║
    ║   Connecting Galaxy & Documents      ║
    ║         Making them ONE               ║
    ╚══════════════════════════════════════╝
    """)
    
    asyncio.run(main())