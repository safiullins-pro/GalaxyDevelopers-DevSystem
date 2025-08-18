#!/usr/bin/env python3
"""
🎭 WORKFLOW ORCHESTRATOR - Дирижёр сложных процессов
Управляет многошаговыми workflow между системами
by FORGE-2267
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

from unified_agent_registry import get_registry, AgentCapability

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WORKFLOW_ORCHESTRATOR')


class WorkflowStatus(Enum):
    """Статусы workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"


class StepStatus(Enum):
    """Статусы шагов"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@dataclass
class WorkflowStep:
    """Шаг workflow"""
    id: str
    name: str
    capability: AgentCapability
    task: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    rollback_task: Optional[Dict[str, Any]] = None


@dataclass
class Workflow:
    """Описание workflow"""
    id: str
    name: str
    type: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    context: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator:
    """Оркестратор workflow"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.workflow_templates = self._init_templates()
        self.registry = None
        
        logger.info("🎭 Workflow Orchestrator initialized")
    
    def _init_templates(self) -> Dict[str, Callable]:
        """Инициализация шаблонов workflow"""
        return {
            'full_document_pipeline': self._create_full_document_pipeline,
            'error_analysis_and_fix': self._create_error_analysis_workflow,
            'code_review_and_improve': self._create_code_review_workflow,
            'monitoring_to_docs': self._create_monitoring_to_docs_workflow,
            'emergency_fix': self._create_emergency_fix_workflow
        }
    
    async def initialize(self):
        """Инициализация оркестратора"""
        self.registry = await get_registry()
        logger.info("✅ Orchestrator initialized with agent registry")
    
    async def create_workflow(
        self,
        workflow_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Создание нового workflow"""
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Создаём workflow из шаблона
        workflow = self.workflow_templates[workflow_type](context)
        
        # Сохраняем workflow
        self.workflows[workflow.id] = workflow
        
        logger.info(f"📋 Created workflow {workflow.id} ({workflow_type})")
        return workflow.id
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """Запуск workflow"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PENDING:
            logger.warning(f"Workflow {workflow_id} already started")
            return False
        
        # Запускаем выполнение в отдельной задаче
        task = asyncio.create_task(self._execute_workflow(workflow))
        self.running_workflows[workflow_id] = task
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        logger.info(f"🚀 Started workflow {workflow_id}")
        return True
    
    async def _execute_workflow(self, workflow: Workflow):
        """Выполнение workflow"""
        try:
            # Выполняем шаги последовательно или параллельно
            for step in workflow.steps:
                if step.status != StepStatus.PENDING:
                    continue
                
                # Проверяем зависимости
                if not self._check_dependencies(workflow, step):
                    step.status = StepStatus.SKIPPED
                    continue
                
                # Выполняем шаг
                await self._execute_step(workflow, step)
                
                # Если шаг провалился и нет rollback - останавливаем
                if step.status == StepStatus.FAILED:
                    if not await self._handle_step_failure(workflow, step):
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = f"Step {step.name} failed: {step.error}"
                        break
            
            # Проверяем финальный статус
            if workflow.status == WorkflowStatus.RUNNING:
                if all(s.status in [StepStatus.SUCCESS, StepStatus.SKIPPED] for s in workflow.steps):
                    workflow.status = WorkflowStatus.COMPLETED
                else:
                    workflow.status = WorkflowStatus.FAILED
            
            workflow.completed_at = datetime.now()
            
            logger.info(f"✅ Workflow {workflow.id} completed with status {workflow.status}")
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            logger.error(f"❌ Workflow {workflow.id} failed: {e}")
        
        finally:
            # Удаляем из running
            if workflow.id in self.running_workflows:
                del self.running_workflows[workflow.id]
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep):
        """Выполнение шага workflow"""
        logger.info(f"▶️ Executing step {step.name}")
        
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # Добавляем контекст workflow в задачу
            task = {
                **step.task,
                'workflow_id': workflow.id,
                'step_id': step.id,
                'context': workflow.context
            }
            
            # Выполняем через реестр агентов
            result = await self.registry.execute_task(
                step.capability,
                task
            )
            
            if result['success']:
                step.status = StepStatus.SUCCESS
                step.result = result
                workflow.results[step.id] = result['result']
                
                # Обновляем контекст для следующих шагов
                if 'context_update' in result.get('result', {}):
                    workflow.context.update(result['result']['context_update'])
                
                logger.info(f"✅ Step {step.name} completed successfully")
            else:
                step.status = StepStatus.FAILED
                step.error = result.get('error', 'Unknown error')
                logger.error(f"❌ Step {step.name} failed: {step.error}")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"❌ Step {step.name} error: {e}")
        
        finally:
            step.completed_at = datetime.now()
    
    def _check_dependencies(self, workflow: Workflow, step: WorkflowStep) -> bool:
        """Проверка зависимостей шага"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in workflow.steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != StepStatus.SUCCESS:
                return False
        return True
    
    async def _handle_step_failure(self, workflow: Workflow, step: WorkflowStep) -> bool:
        """Обработка провала шага"""
        if step.rollback_task:
            logger.info(f"🔄 Rolling back step {step.name}")
            
            try:
                # Выполняем rollback
                result = await self.registry.execute_task(
                    step.capability,
                    step.rollback_task
                )
                
                if result['success']:
                    step.status = StepStatus.ROLLED_BACK
                    logger.info(f"✅ Rollback successful for {step.name}")
                    return True
                else:
                    logger.error(f"❌ Rollback failed for {step.name}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Rollback error for {step.name}: {e}")
                return False
        
        return False
    
    # Шаблоны workflow
    
    def _create_full_document_pipeline(self, context: Dict[str, Any]) -> Workflow:
        """Полный pipeline создания документа"""
        workflow_id = str(uuid.uuid4())
        
        steps = [
            WorkflowStep(
                id="research",
                name="Research Topic",
                capability=AgentCapability.RESEARCH,
                task={
                    'type': 'research',
                    'query': context.get('topic', 'Documentation topic')
                }
            ),
            WorkflowStep(
                id="compose",
                name="Compose Document",
                capability=AgentCapability.COMPOSE,
                task={
                    'type': 'compose',
                    'template': context.get('template', 'default')
                },
                dependencies=["research"]
            ),
            WorkflowStep(
                id="review",
                name="Review Document",
                capability=AgentCapability.REVIEW,
                task={
                    'type': 'review',
                    'standards': context.get('standards', ['ISO27001'])
                },
                dependencies=["compose"]
            ),
            WorkflowStep(
                id="publish",
                name="Publish Document",
                capability=AgentCapability.PUBLISH,
                task={
                    'type': 'publish',
                    'channels': context.get('channels', ['local'])
                },
                dependencies=["review"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name="Full Document Pipeline",
            type="full_document_pipeline",
            status=WorkflowStatus.PENDING,
            steps=steps,
            context=context,
            created_at=datetime.now()
        )
    
    def _create_error_analysis_workflow(self, context: Dict[str, Any]) -> Workflow:
        """Workflow анализа и исправления ошибок"""
        workflow_id = str(uuid.uuid4())
        
        steps = [
            WorkflowStep(
                id="analyze_error",
                name="Analyze Error",
                capability=AgentCapability.ANALYZE,
                task={
                    'type': 'analyze',
                    'error': context.get('error'),
                    'file_path': context.get('file_path')
                }
            ),
            WorkflowStep(
                id="research_fix",
                name="Research Fix",
                capability=AgentCapability.RESEARCH,
                task={
                    'type': 'research',
                    'query': 'fix for error'
                },
                dependencies=["analyze_error"]
            ),
            WorkflowStep(
                id="compose_fix",
                name="Compose Fix",
                capability=AgentCapability.COMPOSE,
                task={
                    'type': 'compose',
                    'template': 'code_fix'
                },
                dependencies=["research_fix"]
            ),
            WorkflowStep(
                id="review_fix",
                name="Review Fix",
                capability=AgentCapability.REVIEW,
                task={
                    'type': 'review',
                    'check_type': 'code_quality'
                },
                dependencies=["compose_fix"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name="Error Analysis and Fix",
            type="error_analysis_and_fix",
            status=WorkflowStatus.PENDING,
            steps=steps,
            context=context,
            created_at=datetime.now()
        )
    
    def _create_code_review_workflow(self, context: Dict[str, Any]) -> Workflow:
        """Workflow review и улучшения кода"""
        workflow_id = str(uuid.uuid4())
        
        steps = [
            WorkflowStep(
                id="analyze_code",
                name="Analyze Code",
                capability=AgentCapability.ANALYZE,
                task={
                    'type': 'analyze',
                    'file_path': context.get('file_path'),
                    'analysis_type': 'quality'
                }
            ),
            WorkflowStep(
                id="review_security",
                name="Security Review",
                capability=AgentCapability.REVIEW,
                task={
                    'type': 'review',
                    'check_type': 'security'
                },
                dependencies=["analyze_code"]
            ),
            WorkflowStep(
                id="compose_improvements",
                name="Compose Improvements",
                capability=AgentCapability.COMPOSE,
                task={
                    'type': 'compose',
                    'template': 'code_improvements'
                },
                dependencies=["review_security"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name="Code Review and Improve",
            type="code_review_and_improve",
            status=WorkflowStatus.PENDING,
            steps=steps,
            context=context,
            created_at=datetime.now()
        )
    
    def _create_monitoring_to_docs_workflow(self, context: Dict[str, Any]) -> Workflow:
        """Workflow от мониторинга к документации"""
        workflow_id = str(uuid.uuid4())
        
        steps = [
            WorkflowStep(
                id="analyze_metrics",
                name="Analyze Metrics",
                capability=AgentCapability.ANALYZE,
                task={
                    'type': 'analyze',
                    'metrics': context.get('metrics'),
                    'analysis_type': 'performance'
                }
            ),
            WorkflowStep(
                id="compose_report",
                name="Compose Report",
                capability=AgentCapability.COMPOSE,
                task={
                    'type': 'compose',
                    'template': 'monitoring_report'
                },
                dependencies=["analyze_metrics"]
            ),
            WorkflowStep(
                id="publish_report",
                name="Publish Report",
                capability=AgentCapability.PUBLISH,
                task={
                    'type': 'publish',
                    'channels': ['git', 'slack']
                },
                dependencies=["compose_report"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name="Monitoring to Documentation",
            type="monitoring_to_docs",
            status=WorkflowStatus.PENDING,
            steps=steps,
            context=context,
            created_at=datetime.now()
        )
    
    def _create_emergency_fix_workflow(self, context: Dict[str, Any]) -> Workflow:
        """Экстренный workflow исправления"""
        workflow_id = str(uuid.uuid4())
        
        steps = [
            WorkflowStep(
                id="emergency_analysis",
                name="Emergency Analysis",
                capability=AgentCapability.ANALYZE,
                task={
                    'type': 'analyze',
                    'priority': 'critical',
                    'issue': context.get('issue')
                }
            ),
            WorkflowStep(
                id="quick_fix",
                name="Apply Quick Fix",
                capability=AgentCapability.COMPOSE,
                task={
                    'type': 'compose',
                    'template': 'emergency_fix'
                },
                dependencies=["emergency_analysis"],
                rollback_task={
                    'type': 'rollback',
                    'restore_point': context.get('backup_id')
                }
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name="Emergency Fix",
            type="emergency_fix",
            status=WorkflowStatus.PENDING,
            steps=steps,
            context=context,
            created_at=datetime.now()
        )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Получить статус workflow"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        return {
            'id': workflow.id,
            'name': workflow.name,
            'type': workflow.type,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'steps': [
                {
                    'id': step.id,
                    'name': step.name,
                    'status': step.status.value,
                    'error': step.error
                }
                for step in workflow.steps
            ],
            'results': workflow.results,
            'error': workflow.error
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Отмена workflow"""
        if workflow_id in self.running_workflows:
            task = self.running_workflows[workflow_id]
            task.cancel()
            
            workflow = self.workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            
            logger.info(f"🛑 Cancelled workflow {workflow_id}")
            return True
        
        return False


# Глобальный оркестратор
orchestrator = None


async def get_orchestrator() -> WorkflowOrchestrator:
    """Получить глобальный оркестратор"""
    global orchestrator
    if orchestrator is None:
        orchestrator = WorkflowOrchestrator()
        await orchestrator.initialize()
    return orchestrator


if __name__ == '__main__':
    async def test():
        """Тестирование оркестратора"""
        orch = await get_orchestrator()
        
        # Создаём workflow
        workflow_id = await orch.create_workflow(
            'full_document_pipeline',
            {'topic': 'Test Documentation'}
        )
        
        print(f"Created workflow: {workflow_id}")
        
        # Запускаем workflow
        await orch.start_workflow(workflow_id)
        
        # Ждём завершения
        await asyncio.sleep(5)
        
        # Получаем статус
        status = orch.get_workflow_status(workflow_id)
        print(f"Workflow status: {json.dumps(status, indent=2)}")
    
    asyncio.run(test())