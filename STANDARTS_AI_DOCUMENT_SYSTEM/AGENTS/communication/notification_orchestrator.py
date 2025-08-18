#!/usr/bin/env python3
"""
NotificationOrchestrator - Оркестратор уведомлений для всех агентов
РЕШАЕТ: проблему спящих агентов, эскалацию, real-time updates
Автор: GALAXYDEVELOPMENT
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from enum import Enum
import websockets
import aiohttp
from dataclasses import dataclass, asdict

from message_bus import MessageBus, Message, MessageType, MessagePriority

class NotificationChannel(Enum):
    """Каналы уведомлений"""
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"
    INTERNAL = "internal"

class NotificationLevel(Enum):
    """Уровни уведомлений"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"

@dataclass
class Notification:
    """Структура уведомления"""
    id: str
    level: NotificationLevel
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    
class AgentStatus:
    """Статус агента"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_active = False
        self.last_heartbeat = None
        self.current_task = None
        self.task_started_at = None
        self.response_times = []  # История времени ответа
        self.error_count = 0
        self.success_count = 0

class NotificationOrchestrator:
    """Оркестратор уведомлений"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.agents: Dict[str, AgentStatus] = {}
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.webhook_endpoints: Dict[str, str] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.escalation_rules: Dict[str, Dict] = {}
        
        # Настройки
        self.heartbeat_interval = 30  # секунд
        self.agent_timeout = 120  # секунд до считания агента неактивным
        self.task_timeout = 600  # секунд на выполнение задачи
        
        # Директории
        self.base_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.notifications_dir = self.base_dir / "11_NOTIFICATIONS"
        self.notifications_dir.mkdir(exist_ok=True)
        
        self.running = False
        self.tasks = []
        
        print("📢 NotificationOrchestrator initialized")
    
    async def start(self):
        """Запуск оркестратора"""
        if not self.running:
            self.running = True
            
            # Запускаем фоновые задачи
            self.tasks = [
                asyncio.create_task(self._process_notifications()),
                asyncio.create_task(self._monitor_agents()),
                asyncio.create_task(self._check_timeouts()),
                asyncio.create_task(self._websocket_server())
            ]
            
            # Подписываемся на сообщения
            await self.message_bus.subscribe("NotificationOrchestrator", self._handle_message)
            
            print("✅ NotificationOrchestrator started")
    
    async def stop(self):
        """Остановка оркестратора"""
        if self.running:
            self.running = False
            
            # Отменяем задачи
            for task in self.tasks:
                task.cancel()
            
            # Закрываем WebSocket соединения
            for client in self.websocket_clients:
                await client.close()
            
            print("🛑 NotificationOrchestrator stopped")
    
    async def register_agent(self, agent_id: str):
        """Регистрация агента"""
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentStatus(agent_id)
            print(f"📝 Agent registered: {agent_id}")
    
    async def wake_agent(self, agent_id: str, task: Dict[str, Any]):
        """Пробуждение спящего агента"""
        await self.register_agent(agent_id)
        
        # Отправляем команду активации
        correlation_id = await self.message_bus.send_command(
            sender="NotificationOrchestrator",
            recipient=agent_id,
            command="wake_up",
            params={"task": task},
            priority=MessagePriority.HIGH
        )
        
        # Обновляем статус
        agent = self.agents[agent_id]
        agent.current_task = task
        agent.task_started_at = datetime.now()
        
        # Уведомляем о пробуждении
        await self.notify(
            level=NotificationLevel.INFO,
            channel=NotificationChannel.INTERNAL,
            recipient=agent_id,
            subject="Agent Activated",
            message=f"Agent {agent_id} activated for task: {task.get('name', 'Unknown')}"
        )
        
        print(f"⏰ Waking agent: {agent_id}")
        return correlation_id
    
    async def notify(self, level: NotificationLevel, channel: NotificationChannel, 
                    recipient: str, subject: str, message: str, 
                    metadata: Optional[Dict[str, Any]] = None):
        """Отправка уведомления"""
        
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            level=level,
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        # Добавляем в очередь
        await self.notification_queue.put(notification)
        
        # Логируем
        await self._log_notification(notification)
    
    async def escalate(self, agent_id: str, issue: str, context: Dict[str, Any]):
        """Эскалация проблемы"""
        
        # Определяем уровень эскалации
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        escalation_level = "manager"
        if agent.error_count > 5:
            escalation_level = "director"
        if agent.error_count > 10:
            escalation_level = "critical"
        
        # Отправляем уведомление об эскалации
        await self.notify(
            level=NotificationLevel.WARNING if escalation_level == "manager" else NotificationLevel.CRITICAL,
            channel=NotificationChannel.SLACK,
            recipient=escalation_level,
            subject=f"Escalation: {agent_id}",
            message=f"Issue: {issue}\nErrors: {agent.error_count}\nContext: {json.dumps(context)}",
            metadata={"agent_id": agent_id, "escalation_level": escalation_level}
        )
        
        print(f"⚠️ Escalated issue for {agent_id} to {escalation_level}")
    
    async def _process_notifications(self):
        """Обработка очереди уведомлений"""
        while self.running:
            try:
                # Получаем уведомление из очереди
                notification = await asyncio.wait_for(
                    self.notification_queue.get(), 
                    timeout=1.0
                )
                
                # Отправляем по соответствующему каналу
                success = await self._send_notification(notification)
                
                # Retry логика
                if not success and notification.retry_count < notification.max_retries:
                    notification.retry_count += 1
                    await asyncio.sleep(2 ** notification.retry_count)  # Exponential backoff
                    await self.notification_queue.put(notification)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Error processing notification: {e}")
    
    async def _send_notification(self, notification: Notification) -> bool:
        """Отправка уведомления по конкретному каналу"""
        
        try:
            if notification.channel == NotificationChannel.WEBSOCKET:
                return await self._send_websocket(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack(notification)
            elif notification.channel == NotificationChannel.INTERNAL:
                return await self._send_internal(notification)
            else:
                print(f"⚠️ Unsupported channel: {notification.channel}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            return False
    
    async def _send_websocket(self, notification: Notification) -> bool:
        """Отправка через WebSocket"""
        
        message = {
            "type": "notification",
            "level": notification.level.value,
            "subject": notification.subject,
            "message": notification.message,
            "timestamp": notification.timestamp,
            "metadata": notification.metadata
        }
        
        # Отправляем всем подключенным клиентам
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send(json.dumps(message))
            except:
                disconnected.add(client)
        
        # Удаляем отключенных
        self.websocket_clients -= disconnected
        
        return True
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Отправка через Webhook"""
        
        endpoint = self.webhook_endpoints.get(notification.recipient)
        if not endpoint:
            return False
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json=asdict(notification),
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
    
    async def _send_slack(self, notification: Notification) -> bool:
        """Отправка в Slack"""
        
        # Здесь должна быть интеграция с Slack API
        # Пока просто логируем
        print(f"📬 Slack notification: {notification.subject}")
        return True
    
    async def _send_internal(self, notification: Notification) -> bool:
        """Внутреннее уведомление через MessageBus"""
        
        await self.message_bus.publish(
            Message(
                id=notification.id,
                type=MessageType.NOTIFICATION,
                sender="NotificationOrchestrator",
                recipient=notification.recipient,
                payload={
                    "level": notification.level.value,
                    "subject": notification.subject,
                    "message": notification.message,
                    "metadata": notification.metadata
                },
                timestamp=notification.timestamp,
                priority=MessagePriority.NORMAL
            )
        )
        return True
    
    async def _monitor_agents(self):
        """Мониторинг состояния агентов"""
        
        while self.running:
            try:
                # Отправляем heartbeat всем агентам
                for agent_id in self.agents:
                    await self.message_bus.send_command(
                        sender="NotificationOrchestrator",
                        recipient=agent_id,
                        command="heartbeat",
                        params={},
                        priority=MessagePriority.LOW
                    )
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring agents: {e}")
    
    async def _check_timeouts(self):
        """Проверка таймаутов"""
        
        while self.running:
            try:
                now = datetime.now()
                
                for agent_id, agent in self.agents.items():
                    # Проверка heartbeat
                    if agent.last_heartbeat:
                        time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
                        
                        if time_since_heartbeat > self.agent_timeout and agent.is_active:
                            agent.is_active = False
                            await self.escalate(
                                agent_id,
                                "Agent not responding",
                                {"last_heartbeat": agent.last_heartbeat.isoformat()}
                            )
                    
                    # Проверка таймаута задачи
                    if agent.task_started_at and agent.current_task:
                        task_duration = (now - agent.task_started_at).total_seconds()
                        
                        if task_duration > self.task_timeout:
                            await self.escalate(
                                agent_id,
                                "Task timeout",
                                {
                                    "task": agent.current_task,
                                    "started_at": agent.task_started_at.isoformat(),
                                    "duration": task_duration
                                }
                            )
                            agent.current_task = None
                            agent.task_started_at = None
                
                await asyncio.sleep(10)  # Проверяем каждые 10 секунд
                
            except Exception as e:
                print(f"❌ Error checking timeouts: {e}")
    
    async def _websocket_server(self):
        """WebSocket сервер для real-time уведомлений"""
        
        async def handler(websocket, path):
            self.websocket_clients.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                self.websocket_clients.remove(websocket)
        
        try:
            async with websockets.serve(handler, "localhost", 8765):
                await asyncio.Future()  # Работаем вечно
        except Exception as e:
            print(f"❌ WebSocket server error: {e}")
    
    async def _handle_message(self, message: Message):
        """Обработка входящих сообщений"""
        
        if message.type == MessageType.HEARTBEAT:
            # Обновляем heartbeat агента
            agent = self.agents.get(message.sender)
            if agent:
                agent.last_heartbeat = datetime.now()
                agent.is_active = True
        
        elif message.type == MessageType.RESULT:
            # Обновляем статистику агента
            agent = self.agents.get(message.sender)
            if agent:
                if message.payload.get("success"):
                    agent.success_count += 1
                else:
                    agent.error_count += 1
                
                # Очищаем текущую задачу
                if agent.current_task:
                    duration = (datetime.now() - agent.task_started_at).total_seconds()
                    agent.response_times.append(duration)
                    agent.current_task = None
                    agent.task_started_at = None
    
    async def _log_notification(self, notification: Notification):
        """Логирование уведомлений"""
        
        log_file = self.notifications_dir / f"notifications_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(notification), ensure_ascii=False) + '\n')
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса агента"""
        
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        avg_response_time = (
            sum(agent.response_times) / len(agent.response_times)
            if agent.response_times else 0
        )
        
        return {
            "agent_id": agent.agent_id,
            "is_active": agent.is_active,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "current_task": agent.current_task,
            "task_started_at": agent.task_started_at.isoformat() if agent.task_started_at else None,
            "success_count": agent.success_count,
            "error_count": agent.error_count,
            "avg_response_time": avg_response_time
        }
    
    def get_all_agents_status(self) -> Dict[str, Any]:
        """Получение статуса всех агентов"""
        
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.agents
        }


# Тестирование
async def test_notification_orchestrator():
    """Тест оркестратора уведомлений"""
    
    # Создаем компоненты
    bus = MessageBus()
    orchestrator = NotificationOrchestrator(bus)
    
    await bus.start()
    await orchestrator.start()
    
    # Регистрируем агентов
    await orchestrator.register_agent("TestAgent1")
    await orchestrator.register_agent("TestAgent2")
    
    # Будим агента
    await orchestrator.wake_agent("TestAgent1", {"name": "Process Document", "doc_id": "DOC_001"})
    
    # Отправляем уведомления
    await orchestrator.notify(
        level=NotificationLevel.INFO,
        channel=NotificationChannel.INTERNAL,
        recipient="TestAgent1",
        subject="Task Started",
        message="Processing document DOC_001"
    )
    
    # Ждем немного
    await asyncio.sleep(2)
    
    # Получаем статусы
    status = orchestrator.get_all_agents_status()
    print(f"📊 Agents status: {json.dumps(status, indent=2)}")
    
    # Останавливаем
    await orchestrator.stop()
    await bus.stop()


if __name__ == "__main__":
    asyncio.run(test_notification_orchestrator())