#!/usr/bin/env python3
"""
MessageBus - Центральная шина сообщений для всех агентов
ОБЕСПЕЧИВАЕТ: асинхронную коммуникацию, очереди, персистентность
Автор: GALAXYDEVELOPMENT
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import redis
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    """Типы сообщений в системе"""
    COMMAND = "command"          # Команда агенту
    EVENT = "event"              # Событие системы
    RESULT = "result"            # Результат выполнения
    ERROR = "error"              # Ошибка
    HEARTBEAT = "heartbeat"      # Проверка активности
    NOTIFICATION = "notification" # Уведомление
    METRICS = "metrics"          # Метрики
    AUDIT = "audit"              # Аудит действий

class MessagePriority(Enum):
    """Приоритеты сообщений"""
    CRITICAL = 1  # Критический
    HIGH = 2      # Высокий
    NORMAL = 3    # Обычный
    LOW = 4       # Низкий

@dataclass
class Message:
    """Структура сообщения"""
    id: str
    type: MessageType
    sender: str
    recipient: str  # или "broadcast" для всех
    payload: Dict[str, Any]
    timestamp: str
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None  # Для связывания запрос-ответ
    ttl: Optional[int] = None  # Time to live в секундах
    
    def to_json(self) -> str:
        """Сериализация в JSON"""
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        return json.dumps(data, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Десериализация из JSON"""
        data = json.loads(json_str)
        data['type'] = MessageType(data['type'])
        data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

class MessageBus:
    """Центральная шина сообщений"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        """Инициализация шины сообщений"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.listener_task = None
        
        # Директории для персистентности
        self.base_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.events_dir = self.base_dir / "08_EVENTS"
        self.audit_dir = self.base_dir / "09_AUDIT"
        self.events_dir.mkdir(exist_ok=True)
        self.audit_dir.mkdir(exist_ok=True)
        
        print("🚌 MessageBus initialized with Redis")
    
    async def start(self):
        """Запуск шины сообщений"""
        if not self.running:
            self.running = True
            self.listener_task = asyncio.create_task(self._listen_messages())
            print("✅ MessageBus started")
    
    async def stop(self):
        """Остановка шины сообщений"""
        if self.running:
            self.running = False
            if self.listener_task:
                self.listener_task.cancel()
            print("🛑 MessageBus stopped")
    
    async def publish(self, message: Message):
        """Публикация сообщения"""
        try:
            # Генерируем ID если нет
            if not message.id:
                message.id = str(uuid.uuid4())
            
            # Добавляем timestamp
            if not message.timestamp:
                message.timestamp = datetime.now().isoformat()
            
            # Сохраняем в Redis
            channel = f"agent:{message.recipient}" if message.recipient != "broadcast" else "broadcast"
            
            # Публикуем в канал
            self.redis_client.publish(channel, message.to_json())
            
            # Сохраняем в очередь по приоритету
            queue_key = f"queue:{message.recipient}:{message.priority.value}"
            self.redis_client.lpush(queue_key, message.to_json())
            
            # TTL если указан
            if message.ttl:
                self.redis_client.expire(queue_key, message.ttl)
            
            # Логируем событие
            await self._log_event(message)
            
            # Аудит для критических сообщений
            if message.type == MessageType.AUDIT or message.priority == MessagePriority.CRITICAL:
                await self._audit_message(message)
            
            print(f"📤 Published: {message.type.value} from {message.sender} to {message.recipient}")
            
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            raise
    
    async def subscribe(self, agent_id: str, handler: Callable):
        """Подписка агента на сообщения"""
        channel = f"agent:{agent_id}"
        
        if channel not in self.subscribers:
            self.subscribers[channel] = []
            self.pubsub.subscribe(channel, "broadcast")
        
        self.subscribers[channel].append(handler)
        print(f"📥 {agent_id} subscribed to messages")
    
    async def unsubscribe(self, agent_id: str, handler: Callable):
        """Отписка агента от сообщений"""
        channel = f"agent:{agent_id}"
        
        if channel in self.subscribers:
            if handler in self.subscribers[channel]:
                self.subscribers[channel].remove(handler)
            
            if not self.subscribers[channel]:
                del self.subscribers[channel]
                self.pubsub.unsubscribe(channel)
        
        print(f"📤 {agent_id} unsubscribed from messages")
    
    async def get_pending_messages(self, agent_id: str, priority: Optional[MessagePriority] = None) -> List[Message]:
        """Получение ожидающих сообщений для агента"""
        messages = []
        
        if priority:
            # Конкретный приоритет
            queue_key = f"queue:{agent_id}:{priority.value}"
            raw_messages = self.redis_client.lrange(queue_key, 0, -1)
        else:
            # Все приоритеты (от высокого к низкому)
            for p in MessagePriority:
                queue_key = f"queue:{agent_id}:{p.value}"
                raw_messages = self.redis_client.lrange(queue_key, 0, -1)
                
                for raw_msg in raw_messages:
                    messages.append(Message.from_json(raw_msg))
                
                # Очищаем очередь после чтения
                self.redis_client.delete(queue_key)
        
        return messages
    
    async def _listen_messages(self):
        """Прослушивание входящих сообщений"""
        try:
            while self.running:
                message = self.pubsub.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # Парсим сообщение
                    msg = Message.from_json(data)
                    
                    # Вызываем обработчики
                    if channel in self.subscribers:
                        for handler in self.subscribers[channel]:
                            try:
                                await handler(msg)
                            except Exception as e:
                                print(f"❌ Handler error: {e}")
                
                await asyncio.sleep(0.01)  # Небольшая пауза
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Listener error: {e}")
    
    async def _log_event(self, message: Message):
        """Логирование событий"""
        event_file = self.events_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        event = {
            "timestamp": message.timestamp,
            "message_id": message.id,
            "type": message.type.value,
            "sender": message.sender,
            "recipient": message.recipient,
            "priority": message.priority.value,
            "correlation_id": message.correlation_id
        }
        
        with open(event_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    async def _audit_message(self, message: Message):
        """Аудит критических сообщений"""
        audit_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        audit_record = {
            "timestamp": message.timestamp,
            "message_id": message.id,
            "type": message.type.value,
            "sender": message.sender,
            "recipient": message.recipient,
            "priority": message.priority.value,
            "payload": message.payload,
            "correlation_id": message.correlation_id
        }
        
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_record, ensure_ascii=False) + '\n')
    
    async def broadcast(self, sender: str, message_type: MessageType, payload: Dict[str, Any]):
        """Широковещательное сообщение всем агентам"""
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=sender,
            recipient="broadcast",
            payload=payload,
            timestamp=datetime.now().isoformat(),
            priority=MessagePriority.NORMAL
        )
        
        await self.publish(message)
    
    async def send_command(self, sender: str, recipient: str, command: str, params: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Отправка команды агенту"""
        correlation_id = str(uuid.uuid4())
        
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.COMMAND,
            sender=sender,
            recipient=recipient,
            payload={
                "command": command,
                "params": params
            },
            timestamp=datetime.now().isoformat(),
            priority=priority,
            correlation_id=correlation_id
        )
        
        await self.publish(message)
        return correlation_id
    
    async def send_result(self, sender: str, recipient: str, correlation_id: str, result: Any, success: bool = True):
        """Отправка результата выполнения"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESULT if success else MessageType.ERROR,
            sender=sender,
            recipient=recipient,
            payload={
                "result": result,
                "success": success
            },
            timestamp=datetime.now().isoformat(),
            priority=MessagePriority.NORMAL,
            correlation_id=correlation_id
        )
        
        await self.publish(message)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик шины сообщений"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "subscribers": len(self.subscribers),
            "channels": list(self.subscribers.keys()),
            "redis_info": self.redis_client.info()
        }
        
        # Размеры очередей
        queue_sizes = {}
        for key in self.redis_client.keys("queue:*"):
            queue_sizes[key] = self.redis_client.llen(key)
        
        metrics["queue_sizes"] = queue_sizes
        
        return metrics


# Пример использования
async def test_message_bus():
    """Тестирование шины сообщений"""
    
    # Создаем шину
    bus = MessageBus()
    await bus.start()
    
    # Обработчик сообщений для агента
    async def agent_handler(message: Message):
        print(f"📨 Agent received: {message.type.value} - {message.payload}")
    
    # Подписываемся
    await bus.subscribe("TestAgent", agent_handler)
    
    # Отправляем команду
    correlation_id = await bus.send_command(
        sender="Orchestrator",
        recipient="TestAgent",
        command="process_document",
        params={"document_id": "DOC_001"},
        priority=MessagePriority.HIGH
    )
    
    # Broadcast сообщение
    await bus.broadcast(
        sender="System",
        message_type=MessageType.NOTIFICATION,
        payload={"message": "System maintenance in 5 minutes"}
    )
    
    # Ждем немного
    await asyncio.sleep(2)
    
    # Получаем метрики
    metrics = bus.get_metrics()
    print(f"📊 Metrics: {metrics}")
    
    # Останавливаем
    await bus.stop()


if __name__ == "__main__":
    # Запуск теста
    asyncio.run(test_message_bus())