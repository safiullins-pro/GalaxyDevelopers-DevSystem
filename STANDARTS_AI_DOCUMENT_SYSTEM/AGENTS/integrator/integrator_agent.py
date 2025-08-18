#\!/usr/bin/env python3
"""
💀 IntegratorAgent - Агент системной интеграции
Связывает все компоненты системы воедино
by FORGE & ALBERT 🔥
"""

import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Типы сообщений между агентами"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"
    STATUS = "status"

@dataclass
class Message:
    """Сообщение между агентами"""
    id: str
    type: MessageType
    sender: str
    receiver: str
    payload: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }

class IntegratorAgent:
    """Агент для интеграции и координации других агентов"""
    
    def __init__(self):
        self.project_root = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.message_queue = asyncio.Queue()
        self.agents_registry = {}
        self.workflows = {}
        self.tasks = {}
        
        # Регистрируем известных агентов
        self._register_agents()
        
        logger.info("IntegratorAgent initialized")
    
    def _register_agents(self):
        """Регистрирует известных агентов"""
        self.agents_registry = {
            "ResearchAgent": {
                "status": "available",
                "capabilities": ["research", "analysis", "data_gathering"],
                "endpoint": "AGENTS.research.research_agent"
            },
            "ComposerAgent": {
                "status": "available",
                "capabilities": ["document_generation", "templating"],
                "endpoint": "AGENTS.composer.composer_agent"
            },
            "ReviewerAgent": {
                "status": "available",
                "capabilities": ["validation", "compliance_check"],
                "endpoint": "AGENTS.reviewer.reviewer_agent"
            },
            "PublisherAgent": {
                "status": "available",
                "capabilities": ["publishing", "distribution"],
                "endpoint": "AGENTS.publisher.publisher_agent"
            }
        }
    
    async def orchestrate_workflow(
        self,
        workflow_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Оркестрирует выполнение workflow"""
        workflow_id = str(uuid.uuid4())
        
        self.workflows[workflow_id] = {
            "type": workflow_type,
            "status": "IN_PROGRESS",
            "context": context,
            "started": datetime.now().isoformat(),
            "steps": [],
            "results": {}
        }
        
        # Запускаем выполнение workflow
        asyncio.create_task(self._execute_workflow(workflow_id, workflow_type, context))
        
        logger.info(f"Workflow started: {workflow_id} ({workflow_type})")
        return workflow_id
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        context: Dict[str, Any]
    ):
        """Выполняет workflow"""
        try:
            if workflow_type == "full_document_pipeline":
                await self._full_document_pipeline(workflow_id, context)
            elif workflow_type == "research_and_compose":
                await self._research_and_compose(workflow_id, context)
            elif workflow_type == "validate_and_publish":
                await self._validate_and_publish(workflow_id, context)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            self.workflows[workflow_id]["status"] = "COMPLETED"
            self.workflows[workflow_id]["completed"] = datetime.now().isoformat()
            
        except Exception as e:
            self.workflows[workflow_id]["status"] = "FAILED"
            self.workflows[workflow_id]["error"] = str(e)
            logger.error(f"Workflow failed: {e}")
    
    async def _full_document_pipeline(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ):
        """Полный пайплайн создания документа"""
        workflow = self.workflows[workflow_id]
        
        # Шаг 1: Research
        workflow["steps"].append("Research")
        research_result = await self._call_agent(
            "ResearchAgent",
            "research",
            {"query": context.get("topic", "Document topic")}
        )
        workflow["results"]["research"] = research_result
        
        # Шаг 2: Compose
        workflow["steps"].append("Compose")
        compose_result = await self._call_agent(
            "ComposerAgent",
            "compose",
            {
                "template": context.get("template", "generic"),
                "data": research_result
            }
        )
        workflow["results"]["document"] = compose_result
        
        # Шаг 3: Review
        workflow["steps"].append("Review")
        review_result = await self._call_agent(
            "ReviewerAgent",
            "validate",
            {"document": compose_result}
        )
        workflow["results"]["validation"] = review_result
        
        # Шаг 4: Publish (если валидация прошла)
        if review_result.get("score", 0) > 70:
            workflow["steps"].append("Publish")
            publish_result = await self._call_agent(
                "PublisherAgent",
                "publish",
                {"document": compose_result}
            )
            workflow["results"]["publication"] = publish_result
        else:
            workflow["results"]["publication"] = "Not published due to low validation score"
    
    async def _research_and_compose(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ):
        """Workflow исследования и создания документа"""
        workflow = self.workflows[workflow_id]
        
        # Research
        research_result = await self._call_agent(
            "ResearchAgent",
            "research",
            {"query": context.get("query")}
        )
        workflow["results"]["research"] = research_result
        
        # Compose based on research
        compose_result = await self._call_agent(
            "ComposerAgent",
            "compose",
            {"data": research_result}
        )
        workflow["results"]["document"] = compose_result
    
    async def _validate_and_publish(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ):
        """Workflow валидации и публикации"""
        workflow = self.workflows[workflow_id]
        
        # Validate
        review_result = await self._call_agent(
            "ReviewerAgent",
            "validate",
            {"document": context.get("document")}
        )
        workflow["results"]["validation"] = review_result
        
        # Publish if valid
        if review_result.get("score", 0) > 70:
            publish_result = await self._call_agent(
                "PublisherAgent",
                "publish",
                {"document": context.get("document")}
            )
            workflow["results"]["publication"] = publish_result
    
    async def _call_agent(
        self,
        agent_name: str,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Вызывает метод агента через реальные импорты"""
        logger.info(f"Calling {agent_name}.{method} with params: {params}")
        
        try:
            # Динамический импорт агентов
            if agent_name == "ResearchAgent":
                from AGENTS.research.research_agent import ResearchAgent
                agent = ResearchAgent(gemini_api_key="AIzaSyBerqRh6LgbXMowDY-4IjwGTsN7R1SCsz4")
                if method == "research":
                    task_id = await agent.start_research(
                        query=params.get("query", ""),
                        max_results=params.get("max_results", 3)
                    )
                    await asyncio.sleep(2)
                    status = await agent.get_task_status(task_id)
                    return status.get("results", {})
                    
            elif agent_name == "ComposerAgent":
                from AGENTS.composer.composer_agent import ComposerAgent
                agent = ComposerAgent()
                if method == "compose":
                    task_id = await agent.compose_document(
                        template_name=params.get("template", "generic"),
                        data=params.get("data", {})
                    )
                    await asyncio.sleep(1)
                    status = agent.tasks.get(task_id, {})
                    return {"document": status.get("result", "")}
                    
            elif agent_name == "ReviewerAgent":
                from AGENTS.reviewer.reviewer_agent import ReviewerAgent
                agent = ReviewerAgent()
                if method == "validate":
                    # Сначала сохраняем документ
                    doc_content = str(params.get("document", ""))
                    temp_doc = Path(f"/tmp/review_{uuid.uuid4()}.md")
                    temp_doc.write_text(doc_content)
                    
                    task_id = await agent.validate_document(str(temp_doc))
                    await asyncio.sleep(2)
                    status = await agent.get_task_status(task_id)
                    
                    # Удаляем временный файл
                    temp_doc.unlink()
                    
                    return status.get("results", {})
                    
            elif agent_name == "PublisherAgent":
                from AGENTS.publisher.publisher_agent import PublisherAgent
                agent = PublisherAgent()
                if method == "publish":
                    doc_content = str(params.get("document", ""))
                    temp_doc = Path(f"/tmp/publish_{uuid.uuid4()}.md")
                    temp_doc.write_text(doc_content)
                    
                    task_id = await agent.publish(
                        document_path=str(temp_doc),
                        channels=params.get("channels", ["local"])
                    )
                    await asyncio.sleep(1)
                    status = await agent.get_task_status(task_id)
                    
                    return status.get("results", {})
            
            # Если агент или метод не найден
            return {
                "error": f"Unknown agent or method: {agent_name}.{method}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calling {agent_name}.{method}: {e}")
            return {
                "error": str(e),
                "agent": agent_name,
                "method": method,
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_message(self, message: Message):
        """Отправляет сообщение в очередь"""
        await self.message_queue.put(message)
        logger.info(f"Message sent: {message.sender} -> {message.receiver}")
    
    async def process_messages(self):
        """Обрабатывает сообщения из очереди"""
        while True:
            try:
                message = await self.message_queue.get()
                await self._handle_message(message)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: Message):
        """Обрабатывает конкретное сообщение"""
        logger.info(f"Handling message: {message.type.value} from {message.sender}")
        
        # Логика обработки в зависимости от типа
        if message.type == MessageType.REQUEST:
            # Перенаправляем запрос нужному агенту
            pass
        elif message.type == MessageType.EVENT:
            # Обрабатываем событие
            pass
    
    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Получает статус workflow"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        return self.workflows[workflow_id]
    
    async def get_agent_status(self, agent_name: str) -> Dict:
        """Получает статус агента"""
        if agent_name not in self.agents_registry:
            return {"error": "Agent not found"}
        
        return self.agents_registry[agent_name]

if __name__ == "__main__":
    async def test_integrator():
        """Тестируем IntegratorAgent"""
        agent = IntegratorAgent()
        
        print("🔗 ТЕСТИРУЕМ INTEGRATORAGENT\n")
        
        # Тест 1: Полный pipeline
        print("📋 Тест 1: Полный документный pipeline")
        
        workflow_id = await agent.orchestrate_workflow(
            workflow_type="full_document_pipeline",
            context={
                "topic": "Multi-Agent Systems Architecture",
                "template": "architecture"
            }
        )
        
        # Ждём выполнения
        await asyncio.sleep(3)
        
        status = await agent.get_workflow_status(workflow_id)
        print(f"Статус: {status['status']}")
        print(f"Шаги: {status.get('steps', [])}")
        
        # Тест 2: Research and Compose
        print("\n📋 Тест 2: Research and Compose workflow")
        
        workflow_id2 = await agent.orchestrate_workflow(
            workflow_type="research_and_compose",
            context={
                "query": "Best practices for API design"
            }
        )
        
        await asyncio.sleep(2)
        
        status2 = await agent.get_workflow_status(workflow_id2)
        print(f"Статус: {status2['status']}")
        
        print("\n✅ IntegratorAgent работает\!")
    
    asyncio.run(test_integrator())