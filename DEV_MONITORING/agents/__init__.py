#!/usr/bin/env python3
"""
🤖 GALAXY AI AGENTS
Система интеллектуальных агентов для мониторинга
"""

from .research_agent import ResearchAgent
from .reviewer_agent import ReviewerAgent
from .composer_agent import ComposerAgent

__all__ = ['ResearchAgent', 'ReviewerAgent', 'ComposerAgent', 'AgentManager']

class AgentManager:
    """Менеджер управления AI агентами"""
    
    def __init__(self):
        # Инициализация агентов
        self.agents = {
            'ResearchAgent': ResearchAgent(),
            'ReviewerAgent': ReviewerAgent(),
            'ComposerAgent': ComposerAgent()
        }
        
        self.task_queue = []
        self.active_tasks = {}
        self.completed_tasks = []
    
    def get_agent(self, agent_name: str):
        """Получение агента по имени"""
        return self.agents.get(agent_name)
    
    def list_agents(self):
        """Список всех агентов"""
        return [agent.get_status() for agent in self.agents.values()]
    
    def submit_task(self, agent_name: str, task: dict):
        """Отправка задачи агенту"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        
        # Выполнение задачи
        result = agent.execute_task(task)
        
        # Сохранение результата
        self.completed_tasks.append({
            "agent": agent_name,
            "task": task,
            "result": result,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        return result
    
    def get_all_status(self):
        """Получение статуса всех агентов"""
        return {
            name: agent.get_status() 
            for name, agent in self.agents.items()
        }
    
    def get_statistics(self):
        """Общая статистика работы агентов"""
        stats = {
            "total_tasks": len(self.completed_tasks),
            "agents": {}
        }
        
        for name, agent in self.agents.items():
            stats["agents"][name] = agent.stats
        
        return stats