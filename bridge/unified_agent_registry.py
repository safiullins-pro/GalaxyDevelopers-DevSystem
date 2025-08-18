#!/usr/bin/env python3
"""
🤖 UNIFIED AGENT REGISTRY - Единый реестр всех агентов
Объединяет агентов из Galaxy и DocumentsSystem
by FORGE-2267
"""

import asyncio
import json
import importlib
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import logging
import sys
from enum import Enum
from dataclasses import dataclass

# Добавляем пути к системам
sys.path.append('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
sys.path.append('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AGENT_REGISTRY')


class AgentStatus(Enum):
    """Статусы агентов"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class AgentCapability(Enum):
    """Возможности агентов"""
    RESEARCH = "research"
    COMPOSE = "compose"
    REVIEW = "review"
    INTEGRATE = "integrate"
    PUBLISH = "publish"
    ANALYZE = "analyze"
    MONITOR = "monitor"
    PROTECT = "protect"
    MEMORY = "memory"


@dataclass
class Agent:
    """Описание агента"""
    id: str
    name: str
    system: str  # 'galaxy' или 'documents'
    status: AgentStatus
    capabilities: List[AgentCapability]
    module_path: str
    class_name: str
    instance: Optional[Any] = None
    last_active: Optional[datetime] = None
    task_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = None


class UnifiedAgentRegistry:
    """Единый реестр всех агентов системы"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.capability_map: Dict[AgentCapability, List[str]] = {}
        self.load_balancer_state: Dict[str, int] = {}
        
        # Определение агентов
        self.agent_definitions = [
            # DocumentsSystem агенты
            {
                'id': 'research_agent_docs',
                'name': 'ResearchAgent',
                'system': 'documents',
                'capabilities': [AgentCapability.RESEARCH, AgentCapability.ANALYZE],
                'module_path': 'AGENTS.research.research_agent',
                'class_name': 'ResearchAgent'
            },
            {
                'id': 'composer_agent_docs',
                'name': 'ComposerAgent',
                'system': 'documents',
                'capabilities': [AgentCapability.COMPOSE],
                'module_path': 'AGENTS.composer.composer_agent',
                'class_name': 'ComposerAgent'
            },
            {
                'id': 'reviewer_agent_docs',
                'name': 'ReviewerAgent',
                'system': 'documents',
                'capabilities': [AgentCapability.REVIEW],
                'module_path': 'AGENTS.reviewer.reviewer_agent',
                'class_name': 'ReviewerAgent'
            },
            {
                'id': 'integrator_agent_docs',
                'name': 'IntegratorAgent',
                'system': 'documents',
                'capabilities': [AgentCapability.INTEGRATE],
                'module_path': 'AGENTS.integrator.integrator_agent',
                'class_name': 'IntegratorAgent'
            },
            {
                'id': 'publisher_agent_docs',
                'name': 'PublisherAgent',
                'system': 'documents',
                'capabilities': [AgentCapability.PUBLISH],
                'module_path': 'AGENTS.publisher.publisher_agent',
                'class_name': 'PublisherAgent'
            },
            
            # Galaxy агенты
            {
                'id': 'research_agent_galaxy',
                'name': 'ResearchAgent',
                'system': 'galaxy',
                'capabilities': [AgentCapability.RESEARCH, AgentCapability.ANALYZE],
                'module_path': 'DEV_MONITORING.agents.research_agent',
                'class_name': 'ResearchAgent'
            },
            {
                'id': 'reviewer_agent_galaxy',
                'name': 'ReviewerAgent',
                'system': 'galaxy',
                'capabilities': [AgentCapability.REVIEW, AgentCapability.ANALYZE],
                'module_path': 'DEV_MONITORING.agents.reviewer_agent',
                'class_name': 'ReviewerAgent'
            },
            {
                'id': 'composer_agent_galaxy',
                'name': 'ComposerAgent',
                'system': 'galaxy',
                'capabilities': [AgentCapability.COMPOSE],
                'module_path': 'DEV_MONITORING.agents.composer_agent',
                'class_name': 'ComposerAgent'
            },
            
            # Специальные агенты
            {
                'id': 'memory_agent',
                'name': 'MemoryAgent',
                'system': 'galaxy',
                'capabilities': [AgentCapability.MEMORY],
                'module_path': 'MEMORY.real_memory.REAL_MEMORY_SYSTEM',
                'class_name': 'RealMemorySystem'
            }
        ]
        
        logger.info("🤖 Unified Agent Registry initialized")
    
    async def initialize_all_agents(self):
        """Инициализация всех агентов"""
        logger.info("Initializing all agents...")
        
        for agent_def in self.agent_definitions:
            agent = Agent(
                id=agent_def['id'],
                name=agent_def['name'],
                system=agent_def['system'],
                status=AgentStatus.INITIALIZING,
                capabilities=agent_def['capabilities'],
                module_path=agent_def['module_path'],
                class_name=agent_def['class_name'],
                metadata={}
            )
            
            # Пытаемся загрузить агента
            success = await self.load_agent(agent)
            
            if success:
                agent.status = AgentStatus.AVAILABLE
                agent.last_active = datetime.now()
            else:
                agent.status = AgentStatus.OFFLINE
            
            # Регистрируем агента
            self.register_agent(agent)
        
        logger.info(f"✅ Initialized {len(self.agents)} agents")
        self.print_registry_status()
    
    async def load_agent(self, agent: Agent) -> bool:
        """Загрузка и инициализация агента"""
        try:
            # Импортируем модуль
            module = importlib.import_module(agent.module_path)
            
            # Получаем класс агента
            agent_class = getattr(module, agent.class_name)
            
            # Создаём экземпляр
            agent.instance = agent_class()
            
            logger.info(f"✅ Loaded {agent.name} from {agent.system}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {agent.name}: {e}")
            return False
    
    def register_agent(self, agent: Agent):
        """Регистрация агента в реестре"""
        self.agents[agent.id] = agent
        
        # Обновляем capability map
        for capability in agent.capabilities:
            if capability not in self.capability_map:
                self.capability_map[capability] = []
            self.capability_map[capability].append(agent.id)
        
        # Инициализируем load balancer state
        self.load_balancer_state[agent.id] = 0
        
        logger.debug(f"Registered {agent.id}")
    
    def get_agents_by_capability(
        self,
        capability: AgentCapability,
        system: Optional[str] = None
    ) -> List[Agent]:
        """Получить агентов по возможности"""
        agent_ids = self.capability_map.get(capability, [])
        agents = []
        
        for agent_id in agent_ids:
            agent = self.agents[agent_id]
            if system is None or agent.system == system:
                if agent.status == AgentStatus.AVAILABLE:
                    agents.append(agent)
        
        return agents
    
    def select_agent_for_task(
        self,
        capability: AgentCapability,
        prefer_system: Optional[str] = None
    ) -> Optional[Agent]:
        """Выбрать агента для задачи с load balancing"""
        # Получаем доступных агентов
        agents = self.get_agents_by_capability(capability, prefer_system)
        
        if not agents:
            # Пробуем без предпочтения системы
            agents = self.get_agents_by_capability(capability)
        
        if not agents:
            logger.warning(f"No available agents for {capability}")
            return None
        
        # Load balancing: выбираем агента с наименьшей нагрузкой
        selected = min(agents, key=lambda a: self.load_balancer_state[a.id])
        
        # Увеличиваем счётчик нагрузки
        self.load_balancer_state[selected.id] += 1
        selected.task_count += 1
        selected.last_active = datetime.now()
        
        logger.info(f"Selected {selected.id} for {capability}")
        return selected
    
    async def execute_task(
        self,
        capability: AgentCapability,
        task: Dict[str, Any],
        prefer_system: Optional[str] = None
    ) -> Dict[str, Any]:
        """Выполнить задачу через подходящего агента"""
        agent = self.select_agent_for_task(capability, prefer_system)
        
        if not agent:
            return {
                'success': False,
                'error': f'No agent available for {capability}'
            }
        
        if not agent.instance:
            return {
                'success': False,
                'error': f'Agent {agent.id} not loaded'
            }
        
        try:
            # Обновляем статус
            agent.status = AgentStatus.BUSY
            
            # Выполняем задачу
            result = await self.call_agent_method(agent, task)
            
            # Обновляем статус обратно
            agent.status = AgentStatus.AVAILABLE
            
            # Уменьшаем счётчик нагрузки
            self.load_balancer_state[agent.id] = max(0, self.load_balancer_state[agent.id] - 1)
            
            return {
                'success': True,
                'agent': agent.id,
                'result': result
            }
            
        except Exception as e:
            agent.error_count += 1
            agent.status = AgentStatus.ERROR
            logger.error(f"Error executing task on {agent.id}: {e}")
            
            return {
                'success': False,
                'agent': agent.id,
                'error': str(e)
            }
    
    async def call_agent_method(self, agent: Agent, task: Dict[str, Any]) -> Any:
        """Вызов метода агента"""
        # Определяем метод на основе типа задачи
        task_type = task.get('type', 'process')
        
        # Мапинг типов задач на методы
        method_map = {
            'research': 'research',
            'compose': 'compose',
            'review': 'review',
            'publish': 'publish',
            'analyze': 'analyze',
            'process': 'process_task',
            'execute': 'execute'
        }
        
        method_name = method_map.get(task_type, 'process_task')
        
        # Пытаемся получить метод
        if hasattr(agent.instance, method_name):
            method = getattr(agent.instance, method_name)
            
            # Вызываем метод
            if asyncio.iscoroutinefunction(method):
                return await method(task)
            else:
                return method(task)
        else:
            # Fallback на общий метод
            if hasattr(agent.instance, 'execute'):
                return agent.instance.execute(task)
            else:
                raise AttributeError(f"Agent {agent.id} has no suitable method for task")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Получить статус реестра"""
        return {
            'total_agents': len(self.agents),
            'systems': {
                'galaxy': len([a for a in self.agents.values() if a.system == 'galaxy']),
                'documents': len([a for a in self.agents.values() if a.system == 'documents'])
            },
            'by_status': {
                status.value: len([a for a in self.agents.values() if a.status == status])
                for status in AgentStatus
            },
            'capabilities': {
                cap.value: len(agents)
                for cap, agents in self.capability_map.items()
            },
            'agents': [
                {
                    'id': agent.id,
                    'name': agent.name,
                    'system': agent.system,
                    'status': agent.status.value,
                    'capabilities': [c.value for c in agent.capabilities],
                    'task_count': agent.task_count,
                    'error_count': agent.error_count
                }
                for agent in self.agents.values()
            ]
        }
    
    def print_registry_status(self):
        """Печать статуса реестра"""
        status = self.get_registry_status()
        
        print("\n" + "="*50)
        print("     🤖 AGENT REGISTRY STATUS")
        print("="*50)
        print(f"Total Agents: {status['total_agents']}")
        print(f"  Galaxy: {status['systems']['galaxy']}")
        print(f"  Documents: {status['systems']['documents']}")
        print("\nBy Status:")
        for s, count in status['by_status'].items():
            if count > 0:
                print(f"  {s}: {count}")
        print("\nCapabilities:")
        for cap, count in status['capabilities'].items():
            print(f"  {cap}: {count} agents")
        print("="*50 + "\n")
    
    async def health_check(self):
        """Проверка здоровья всех агентов"""
        for agent in self.agents.values():
            if agent.instance and hasattr(agent.instance, 'health_check'):
                try:
                    is_healthy = await agent.instance.health_check()
                    agent.status = AgentStatus.AVAILABLE if is_healthy else AgentStatus.ERROR
                except:
                    agent.status = AgentStatus.ERROR
            elif agent.status == AgentStatus.AVAILABLE:
                # Простая проверка что объект существует
                if agent.instance is None:
                    agent.status = AgentStatus.OFFLINE


# Глобальный реестр
registry = None


async def get_registry() -> UnifiedAgentRegistry:
    """Получить глобальный реестр"""
    global registry
    if registry is None:
        registry = UnifiedAgentRegistry()
        await registry.initialize_all_agents()
    return registry


if __name__ == '__main__':
    async def test():
        """Тестирование реестра"""
        reg = await get_registry()
        
        # Тест выбора агента
        agent = reg.select_agent_for_task(AgentCapability.RESEARCH)
        if agent:
            print(f"Selected agent: {agent.id}")
        
        # Тест выполнения задачи
        result = await reg.execute_task(
            AgentCapability.RESEARCH,
            {'type': 'research', 'query': 'test'},
            prefer_system='documents'
        )
        print(f"Task result: {result}")
    
    asyncio.run(test())