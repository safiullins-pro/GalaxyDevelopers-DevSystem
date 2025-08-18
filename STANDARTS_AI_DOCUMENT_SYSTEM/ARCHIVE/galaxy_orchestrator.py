#!/usr/bin/env python3
"""
Galaxy Orchestrator - Система координации 12 специализированных агентов
Исправляет все критические проблемы из ATOMIC AUDIT REPORT
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aioredis
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from loguru import logger
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import yaml


class AgentType(Enum):
    """Типы агентов в системе Galaxy"""
    ELENA_STANDARDS = "elena_standards_genius"
    MARCUS_COMPOSER = "marcus_document_master"  
    VICTORIA_REVIEWER = "victoria_quality_hawk"
    ALEX_INTEGRATOR = "alex_git_master"
    SARAH_PUBLISHER = "sarah_distribution_master"
    VIKTOR_SECURITY = "viktor_cyber_guardian"
    DMITRI_PERFORMANCE = "dmitri_speed_demon"
    OLGA_DATA = "olga_data_whisperer"
    JAKE_MOBILE = "jake_app_master"
    CATHERINE_COMPLIANCE = "catherine_regulatory_expert"
    BORIS_TESTING = "boris_testing_machine"
    IVAN_DEPLOYMENT = "ivan_deploy_master"


class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPhase(Enum):
    """Фазы workflow"""
    RESEARCH = "research_phase"
    CREATION = "creation_phase"
    INTEGRATION = "integration_phase"
    DISTRIBUTION = "distribution_phase"


@dataclass
class Task:
    """Задача для агента"""
    task_id: str
    agent_type: AgentType
    workflow_id: str
    phase: WorkflowPhase
    priority: int
    payload: Dict[str, Any]
    dependencies: List[str]
    created_at: datetime
    deadline: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class Agent:
    """Информация об агенте"""
    agent_id: str
    agent_type: AgentType
    status: str
    last_heartbeat: datetime
    current_tasks: List[str]
    performance_score: float
    specializations: List[str]
    max_concurrent_tasks: int = 3


class GalaxyOrchestrator:
    """
    Главный оркестратор системы Galaxy Development
    Координирует работу всех 12 агентов с соблюдением security требований
    """
    
    # Prometheus метрики
    TASKS_CREATED = Counter('galaxy_tasks_created_total', 'Total tasks created', ['agent_type'])
    TASKS_COMPLETED = Counter('galaxy_tasks_completed_total', 'Total tasks completed', ['agent_type'])
    WORKFLOW_DURATION = Histogram('galaxy_workflow_duration_seconds', 'Workflow duration')
    ACTIVE_AGENTS = Gauge('galaxy_active_agents', 'Active agents count')
    ACTIVE_WORKFLOWS = Gauge('galaxy_active_workflows', 'Active workflows count')
    
    def __init__(self):
        self.orchestrator_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
        self.config = self._load_secure_config()
        
        # Подключения (инициализируются в init())
        self.db_pool = None
        self.redis = None
        self.producer = None
        self.consumer = None
        
        # Внутреннее состояние
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.task_graph: Dict[str, List[str]] = {}
        
        # Workflow definitions
        self.workflow_templates = self._load_workflow_templates()
        
        logger.info(f"Galaxy Orchestrator {self.orchestrator_id} initialized")
    
    def _load_secure_config(self) -> Dict[str, str]:
        """Загрузка конфигурации ТОЛЬКО из переменных окружения (security fix)"""
        required_env_vars = [
            'DATABASE_URL', 'REDIS_URL', 'KAFKA_BOOTSTRAP_SERVERS'
        ]
        
        config = {}
        missing_vars = []
        
        for var in required_env_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                config[var] = value
        
        if missing_vars:
            raise ValueError(f"❌ SECURITY: Missing required environment variables: {missing_vars}")
        
        # Опциональные переменные
        config.update({
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'MAX_WORKFLOW_DURATION': int(os.getenv('MAX_WORKFLOW_DURATION', '3600')),
            'AGENT_HEARTBEAT_TIMEOUT': int(os.getenv('AGENT_HEARTBEAT_TIMEOUT', '300'))
        })
        
        logger.success("✅ Configuration loaded securely from environment")
        return config
    
    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка шаблонов workflow для 4-фазной обработки"""
        return {
            "standard_document_creation": {
                "name": "Standard Document Creation Workflow",
                "description": "Full document lifecycle with 12 agents",
                "phases": [
                    {
                        "phase": WorkflowPhase.RESEARCH,
                        "parallel": True,
                        "agents": [
                            AgentType.ELENA_STANDARDS,
                            AgentType.VIKTOR_SECURITY,
                            AgentType.CATHERINE_COMPLIANCE,
                            AgentType.OLGA_DATA
                        ]
                    },
                    {
                        "phase": WorkflowPhase.CREATION,
                        "parallel": False,
                        "agents": [
                            AgentType.MARCUS_COMPOSER,
                            AgentType.VICTORIA_REVIEWER,
                            AgentType.BORIS_TESTING
                        ]
                    },
                    {
                        "phase": WorkflowPhase.INTEGRATION,
                        "parallel": True,
                        "agents": [
                            AgentType.ALEX_INTEGRATOR,
                            AgentType.JAKE_MOBILE,
                            AgentType.DMITRI_PERFORMANCE,
                            AgentType.IVAN_DEPLOYMENT
                        ]
                    },
                    {
                        "phase": WorkflowPhase.DISTRIBUTION,
                        "parallel": False,
                        "agents": [
                            AgentType.SARAH_PUBLISHER
                        ]
                    }
                ]
            },
            "mobile_app_development": {
                "name": "Mobile App Development Workflow",
                "description": "Mobile-first development with enterprise compliance",
                "phases": [
                    {
                        "phase": WorkflowPhase.RESEARCH,
                        "parallel": True,
                        "agents": [
                            AgentType.ELENA_STANDARDS,
                            AgentType.OLGA_DATA,
                            AgentType.CATHERINE_COMPLIANCE
                        ]
                    },
                    {
                        "phase": WorkflowPhase.CREATION,
                        "parallel": True,
                        "agents": [
                            AgentType.JAKE_MOBILE,
                            AgentType.MARCUS_COMPOSER,
                            AgentType.VIKTOR_SECURITY
                        ]
                    },
                    {
                        "phase": WorkflowPhase.INTEGRATION,
                        "parallel": True,
                        "agents": [
                            AgentType.BORIS_TESTING,
                            AgentType.DMITRI_PERFORMANCE,
                            AgentType.ALEX_INTEGRATOR
                        ]
                    },
                    {
                        "phase": WorkflowPhase.DISTRIBUTION,
                        "parallel": False,
                        "agents": [
                            AgentType.IVAN_DEPLOYMENT,
                            AgentType.SARAH_PUBLISHER
                        ]
                    }
                ]
            }
        }
    
    async def initialize(self):
        """Инициализация всех подключений с retry логикой"""
        try:
            # PostgreSQL connection pool (security fix - no default password)
            self.db_pool = ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=self.config['DATABASE_URL'],
                cursor_factory=RealDictCursor
            )
            
            # Redis connection (security fix)
            self.redis = aioredis.from_url(
                self.config['REDIS_URL'],
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Kafka Producer (with security settings)
            self.producer = KafkaProducer(
                bootstrap_servers=self.config['KAFKA_BOOTSTRAP_SERVERS'],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=str.encode,
                retries=5,
                max_in_flight_requests_per_connection=1,
                request_timeout_ms=30000,
                retry_backoff_ms=100,
                acks='all',  # Wait for all replicas
                enable_idempotence=True  # Prevent duplicate messages
            )
            
            # Kafka Consumer
            self.consumer = KafkaConsumer(
                'orchestrator_commands',
                'agent_status_updates', 
                'workflow_requests',
                bootstrap_servers=self.config['KAFKA_BOOTSTRAP_SERVERS'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                group_id='galaxy-orchestrator',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Создание таблиц БД если не существуют
            await self._ensure_database_schema()
            
            # Загрузка состояния агентов
            await self._load_agents_state()
            
            # Запуск метрик сервера
            start_http_server(9000)
            
            logger.success("✅ Galaxy Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def _ensure_database_schema(self):
        """Создание схемы БД для оркестратора"""
        schema_sql = """
        -- Workflows table
        CREATE TABLE IF NOT EXISTS workflows (
            workflow_id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            template_name VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_by VARCHAR(255),
            metadata JSONB DEFAULT '{}',
            current_phase VARCHAR(100),
            total_phases INTEGER DEFAULT 4,
            progress_percentage INTEGER DEFAULT 0
        );
        
        -- Tasks table (enhanced with security)
        CREATE TABLE IF NOT EXISTS orchestrator_tasks (
            task_id UUID PRIMARY KEY,
            workflow_id UUID REFERENCES workflows(workflow_id),
            agent_type VARCHAR(100) NOT NULL,
            phase VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            priority INTEGER DEFAULT 5,
            payload JSONB NOT NULL,
            dependencies TEXT[],
            result JSONB,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            assigned_at TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            deadline TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3
        );
        
        -- Agent registry (enhanced)
        CREATE TABLE IF NOT EXISTS agent_registry (
            agent_id VARCHAR(255) PRIMARY KEY,
            agent_type VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            last_heartbeat TIMESTAMP DEFAULT NOW(),
            current_tasks TEXT[],
            performance_score FLOAT DEFAULT 100.0,
            total_tasks_completed INTEGER DEFAULT 0,
            total_tasks_failed INTEGER DEFAULT 0,
            specializations TEXT[],
            max_concurrent_tasks INTEGER DEFAULT 3,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Audit trail (compliance requirement)
        CREATE TABLE IF NOT EXISTS orchestrator_audit (
            audit_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id VARCHAR(255) NOT NULL,
            old_values JSONB,
            new_values JSONB,
            changed_by VARCHAR(255) NOT NULL,
            changed_at TIMESTAMP DEFAULT NOW(),
            ip_address INET,
            user_agent TEXT
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
        CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at);
        CREATE INDEX IF NOT EXISTS idx_tasks_workflow_id ON orchestrator_tasks(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_agent_type ON orchestrator_tasks(agent_type);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON orchestrator_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_agents_type ON agent_registry(agent_type);
        CREATE INDEX IF NOT EXISTS idx_agents_status ON agent_registry(status);
        CREATE INDEX IF NOT EXISTS idx_audit_entity ON orchestrator_audit(entity_type, entity_id);
        """
        
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
                conn.commit()
            logger.success("✅ Database schema ensured")
        finally:
            self.db_pool.putconn(conn)
    
    async def _load_agents_state(self):
        """Загрузка состояния агентов из БД"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM agent_registry 
                    WHERE last_heartbeat > %s
                """, (datetime.now() - timedelta(minutes=5),))
                
                agents = cur.fetchall()
                for agent_data in agents:
                    agent = Agent(
                        agent_id=agent_data['agent_id'],
                        agent_type=AgentType(agent_data['agent_type']),
                        status=agent_data['status'],
                        last_heartbeat=agent_data['last_heartbeat'],
                        current_tasks=agent_data['current_tasks'] or [],
                        performance_score=agent_data['performance_score'],
                        specializations=agent_data['specializations'] or [],
                        max_concurrent_tasks=agent_data['max_concurrent_tasks']
                    )
                    self.agents[agent.agent_id] = agent
                
                logger.info(f"✅ Loaded {len(self.agents)} active agents")
        finally:
            self.db_pool.putconn(conn)
    
    async def create_workflow(self, template_name: str, request_data: Dict[str, Any]) -> str:
        """Создание нового workflow"""
        workflow_id = str(uuid.uuid4())
        
        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        template = self.workflow_templates[template_name]
        
        workflow = {
            'workflow_id': workflow_id,
            'template_name': template_name,
            'name': template['name'],
            'status': 'created',
            'created_at': datetime.now(),
            'created_by': request_data.get('user_id', 'system'),
            'metadata': request_data,
            'current_phase': None,
            'phases': template['phases'],
            'tasks': []
        }
        
        # Сохранение в БД с audit trail
        await self._save_workflow(workflow)
        await self._audit_log('workflow_created', 'workflow', workflow_id, None, workflow, 'orchestrator')
        
        self.workflows[workflow_id] = workflow
        self.ACTIVE_WORKFLOWS.inc()
        
        logger.info(f"✅ Created workflow {workflow_id} from template {template_name}")
        return workflow_id
    
    async def _save_workflow(self, workflow: Dict[str, Any]):
        """Сохранение workflow в БД"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO workflows (workflow_id, name, template_name, status, 
                                         created_at, created_by, metadata, current_phase, total_phases)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (workflow_id) 
                    DO UPDATE SET status = EXCLUDED.status,
                                  current_phase = EXCLUDED.current_phase,
                                  metadata = EXCLUDED.metadata
                """, (
                    workflow['workflow_id'],
                    workflow['name'],
                    workflow['template_name'],
                    workflow['status'],
                    workflow['created_at'],
                    workflow['created_by'],
                    json.dumps(workflow['metadata']),
                    workflow.get('current_phase'),
                    len(workflow['phases'])
                ))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def start_workflow(self, workflow_id: str):
        """Запуск workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow['status'] = 'running'
        workflow['started_at'] = datetime.now()
        
        # Запуск первой фазы
        first_phase = workflow['phases'][0]
        await self._start_phase(workflow_id, first_phase)
        
        await self._save_workflow(workflow)
        await self._audit_log('workflow_started', 'workflow', workflow_id, {'status': 'created'}, {'status': 'running'}, 'orchestrator')
        
        logger.info(f"🚀 Started workflow {workflow_id}")
    
    async def _start_phase(self, workflow_id: str, phase_config: Dict[str, Any]):
        """Запуск фазы workflow"""
        workflow = self.workflows[workflow_id]
        phase = phase_config['phase']
        agents = phase_config['agents']
        parallel = phase_config.get('parallel', False)
        
        workflow['current_phase'] = phase.value
        
        logger.info(f"🔄 Starting phase {phase.value} for workflow {workflow_id}")
        
        phase_tasks = []
        for i, agent_type in enumerate(agents):
            task = Task(
                task_id=str(uuid.uuid4()),
                agent_type=agent_type,
                workflow_id=workflow_id,
                phase=phase,
                priority=5,
                payload=workflow['metadata'],
                dependencies=[],  # TODO: Implement dependencies
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(seconds=self.config['MAX_WORKFLOW_DURATION'])
            )
            
            if not parallel and i > 0:
                # Для последовательного выполнения добавляем зависимость от предыдущей задачи
                task.dependencies = [phase_tasks[-1].task_id]
            
            phase_tasks.append(task)
            await self._save_task(task)
            await self._assign_task_to_agent(task)
        
        workflow['tasks'].extend([t.task_id for t in phase_tasks])
        
        # Обновление прогресса
        await self._update_workflow_progress(workflow_id)
    
    async def _assign_task_to_agent(self, task: Task):
        """Назначение задачи наиболее подходящему агенту"""
        suitable_agents = [
            agent for agent in self.agents.values()
            if (agent.agent_type == task.agent_type and
                agent.status == 'active' and
                len(agent.current_tasks) < agent.max_concurrent_tasks)
        ]
        
        if not suitable_agents:
            logger.warning(f"⚠️ No suitable agents for task {task.task_id} of type {task.agent_type.value}")
            # Задача остается в очереди
            return
        
        # Выбор лучшего агента по performance_score
        best_agent = max(suitable_agents, key=lambda a: a.performance_score)
        
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        
        # Отправка задачи агенту через Kafka
        message = {
            'task_id': task.task_id,
            'workflow_id': task.workflow_id,
            'phase': task.phase.value,
            'payload': task.payload,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'assigned_at': task.assigned_at.isoformat()
        }
        
        self.producer.send(f"{task.agent_type.value}_tasks", value=message)
        
        # Обновление состояния агента
        best_agent.current_tasks.append(task.task_id)
        await self._update_agent_state(best_agent)
        
        await self._save_task(task)
        self.TASKS_CREATED.labels(agent_type=task.agent_type.value).inc()
        
        logger.info(f"📤 Assigned task {task.task_id} to agent {best_agent.agent_id}")
    
    async def _save_task(self, task: Task):
        """Сохранение задачи в БД"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orchestrator_tasks (
                        task_id, workflow_id, agent_type, phase, status, priority,
                        payload, dependencies, result, error_message,
                        created_at, assigned_at, started_at, completed_at, deadline
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        assigned_at = EXCLUDED.assigned_at,
                        started_at = EXCLUDED.started_at,
                        completed_at = EXCLUDED.completed_at,
                        result = EXCLUDED.result,
                        error_message = EXCLUDED.error_message
                """, (
                    task.task_id, task.workflow_id, task.agent_type.value, task.phase.value,
                    task.status.value, task.priority, json.dumps(task.payload), task.dependencies,
                    json.dumps(task.result) if task.result else None, task.error_message,
                    task.created_at, task.assigned_at, task.started_at, task.completed_at, task.deadline
                ))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def _update_agent_state(self, agent: Agent):
        """Обновление состояния агента в БД"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_registry (
                        agent_id, agent_type, status, last_heartbeat, current_tasks,
                        performance_score, specializations, max_concurrent_tasks
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        last_heartbeat = EXCLUDED.last_heartbeat,
                        current_tasks = EXCLUDED.current_tasks,
                        performance_score = EXCLUDED.performance_score
                """, (
                    agent.agent_id, agent.agent_type.value, agent.status,
                    agent.last_heartbeat, agent.current_tasks, agent.performance_score,
                    agent.specializations, agent.max_concurrent_tasks
                ))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def handle_task_completed(self, task_result: Dict[str, Any]):
        """Обработка завершения задачи агентом"""
        task_id = task_result['task_id']
        workflow_id = task_result['workflow_id']
        result = task_result.get('result')
        error = task_result.get('error')
        agent_id = task_result['agent_id']
        
        # Обновление задачи
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                if error:
                    cur.execute("""
                        UPDATE orchestrator_tasks 
                        SET status = 'failed', error_message = %s, completed_at = %s
                        WHERE task_id = %s
                    """, (error, datetime.now(), task_id))
                    logger.error(f"❌ Task {task_id} failed: {error}")
                else:
                    cur.execute("""
                        UPDATE orchestrator_tasks 
                        SET status = 'completed', result = %s, completed_at = %s
                        WHERE task_id = %s
                    """, (json.dumps(result), datetime.now(), task_id))
                    logger.success(f"✅ Task {task_id} completed successfully")
                    self.TASKS_COMPLETED.labels(agent_type=task_result.get('agent_type', 'unknown')).inc()
                
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
        
        # Обновление состояния агента
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if task_id in agent.current_tasks:
                agent.current_tasks.remove(task_id)
            
            # Обновление performance score
            if error:
                agent.performance_score = max(0, agent.performance_score - 5)
            else:
                agent.performance_score = min(100, agent.performance_score + 1)
            
            await self._update_agent_state(agent)
        
        # Проверка завершения фазы/workflow
        await self._check_phase_completion(workflow_id)
    
    async def _check_phase_completion(self, workflow_id: str):
        """Проверка завершения текущей фазы"""
        if workflow_id not in self.workflows:
            return
        
        workflow = self.workflows[workflow_id]
        current_phase = workflow.get('current_phase')
        
        if not current_phase:
            return
        
        # Проверка статуса всех задач текущей фазы
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM orchestrator_tasks 
                    WHERE workflow_id = %s AND phase = %s
                    GROUP BY status
                """, (workflow_id, current_phase))
                
                status_counts = dict(cur.fetchall())
                
                total_tasks = sum(status_counts.values())
                completed_tasks = status_counts.get('completed', 0)
                failed_tasks = status_counts.get('failed', 0)
                
                if completed_tasks + failed_tasks == total_tasks:
                    # Фаза завершена
                    logger.info(f"🎯 Phase {current_phase} completed for workflow {workflow_id}")
                    
                    if failed_tasks > 0:
                        logger.warning(f"⚠️ {failed_tasks} tasks failed in phase {current_phase}")
                    
                    # Переход к следующей фазе
                    await self._advance_to_next_phase(workflow_id)
        finally:
            self.db_pool.putconn(conn)
    
    async def _advance_to_next_phase(self, workflow_id: str):
        """Переход к следующей фазе workflow"""
        workflow = self.workflows[workflow_id]
        current_phase = workflow.get('current_phase')
        phases = workflow['phases']
        
        # Найдем индекс текущей фазы
        current_index = None
        for i, phase_config in enumerate(phases):
            if phase_config['phase'].value == current_phase:
                current_index = i
                break
        
        if current_index is None or current_index >= len(phases) - 1:
            # Workflow завершен
            await self._complete_workflow(workflow_id)
            return
        
        # Запуск следующей фазы
        next_phase = phases[current_index + 1]
        await self._start_phase(workflow_id, next_phase)
        await self._update_workflow_progress(workflow_id)
    
    async def _complete_workflow(self, workflow_id: str):
        """Завершение workflow"""
        workflow = self.workflows[workflow_id]
        workflow['status'] = 'completed'
        workflow['completed_at'] = datetime.now()
        workflow['current_phase'] = None
        
        duration = (workflow['completed_at'] - workflow['started_at']).total_seconds()
        self.WORKFLOW_DURATION.observe(duration)
        self.ACTIVE_WORKFLOWS.dec()
        
        await self._save_workflow(workflow)
        await self._audit_log('workflow_completed', 'workflow', workflow_id, {'status': 'running'}, {'status': 'completed'}, 'orchestrator')
        
        logger.success(f"🎉 Workflow {workflow_id} completed in {duration:.2f} seconds")
    
    async def _update_workflow_progress(self, workflow_id: str):
        """Обновление прогресса workflow"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM orchestrator_tasks 
                    WHERE workflow_id = %s
                    GROUP BY status
                """, (workflow_id,))
                
                status_counts = dict(cur.fetchall())
                total_tasks = sum(status_counts.values())
                completed_tasks = status_counts.get('completed', 0)
                
                progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
                
                cur.execute("""
                    UPDATE workflows 
                    SET progress_percentage = %s
                    WHERE workflow_id = %s
                """, (progress, workflow_id))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def _audit_log(self, event_type: str, entity_type: str, entity_id: str, old_values: Dict, new_values: Dict, changed_by: str):
        """Запись в audit trail (compliance requirement)"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orchestrator_audit (event_type, entity_type, entity_id, old_values, new_values, changed_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    event_type, entity_type, entity_id,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    changed_by
                ))
                conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def run(self):
        """Основной цикл оркестратора"""
        logger.info("🚀 Starting Galaxy Orchestrator main loop")
        
        try:
            while True:
                # Обработка сообщений от агентов
                message_batch = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._handle_message(message.topic, message.value)
                
                # Периодические задачи
                await self._periodic_tasks()
                
                # Короткая пауза
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            raise
        finally:
            await self._shutdown()
    
    async def _handle_message(self, topic: str, message: Dict[str, Any]):
        """Обработка сообщений от агентов"""
        try:
            if topic == 'agent_status_updates':
                await self._handle_agent_heartbeat(message)
            elif topic == 'workflow_requests':
                await self._handle_workflow_request(message)
            elif 'completed' in topic:
                await self.handle_task_completed(message)
            else:
                logger.warning(f"⚠️ Unknown topic: {topic}")
        except Exception as e:
            logger.error(f"❌ Error handling message from {topic}: {e}")
    
    async def _handle_agent_heartbeat(self, heartbeat: Dict[str, Any]):
        """Обработка heartbeat от агента"""
        agent_id = heartbeat.get('agent_id')
        agent_type_str = heartbeat.get('agent_type')
        
        if not agent_id or not agent_type_str:
            return
        
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            logger.warning(f"⚠️ Unknown agent type: {agent_type_str}")
            return
        
        # Обновление или создание записи об агенте
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.now()
            agent.status = heartbeat.get('status', 'active')
        else:
            agent = Agent(
                agent_id=agent_id,
                agent_type=agent_type,
                status=heartbeat.get('status', 'active'),
                last_heartbeat=datetime.now(),
                current_tasks=heartbeat.get('current_tasks', []),
                performance_score=heartbeat.get('performance_score', 100.0),
                specializations=heartbeat.get('specializations', [])
            )
            self.agents[agent_id] = agent
            logger.info(f"➕ Registered new agent: {agent_id} ({agent_type.value})")
        
        await self._update_agent_state(agent)
    
    async def _handle_workflow_request(self, request: Dict[str, Any]):
        """Обработка запроса на создание workflow"""
        template_name = request.get('template_name')
        if not template_name:
            logger.error("❌ Workflow request missing template_name")
            return
        
        try:
            workflow_id = await self.create_workflow(template_name, request)
            await self.start_workflow(workflow_id)
            
            # Отправка ответа
            response = {
                'workflow_id': workflow_id,
                'status': 'started',
                'message': f'Workflow {workflow_id} started successfully'
            }
            self.producer.send('workflow_responses', value=response)
            
        except Exception as e:
            logger.error(f"❌ Failed to create workflow: {e}")
            error_response = {
                'error': str(e),
                'request': request
            }
            self.producer.send('workflow_errors', value=error_response)
    
    async def _periodic_tasks(self):
        """Периодические задачи оркестратора"""
        now = datetime.now()
        
        # Очистка неактивных агентов (каждые 5 минут)
        if not hasattr(self, '_last_cleanup') or (now - self._last_cleanup).seconds > 300:
            await self._cleanup_inactive_agents()
            self._last_cleanup = now
        
        # Проверка зависших задач (каждую минуту)
        if not hasattr(self, '_last_task_check') or (now - self._last_task_check).seconds > 60:
            await self._check_stuck_tasks()
            self._last_task_check = now
        
        # Обновление метрик
        self.ACTIVE_AGENTS.set(len([a for a in self.agents.values() if a.status == 'active']))
    
    async def _cleanup_inactive_agents(self):
        """Очистка неактивных агентов"""
        timeout = datetime.now() - timedelta(seconds=self.config['AGENT_HEARTBEAT_TIMEOUT'])
        inactive_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if agent.last_heartbeat < timeout
        ]
        
        for agent_id in inactive_agents:
            agent = self.agents[agent_id]
            agent.status = 'inactive'
            await self._update_agent_state(agent)
            logger.warning(f"⚠️ Agent {agent_id} marked as inactive")
    
    async def _check_stuck_tasks(self):
        """Проверка зависших задач"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Задачи, которые были назначены давно, но не запущены
                cur.execute("""
                    UPDATE orchestrator_tasks 
                    SET status = 'failed', error_message = 'Task stuck - agent timeout'
                    WHERE status = 'assigned' 
                    AND assigned_at < %s
                    AND retry_count < max_retries
                """, (datetime.now() - timedelta(minutes=10),))
                
                stuck_count = cur.rowcount
                if stuck_count > 0:
                    logger.warning(f"⚠️ Marked {stuck_count} stuck tasks as failed")
                    conn.commit()
        finally:
            self.db_pool.putconn(conn)
    
    async def _shutdown(self):
        """Корректное завершение работы оркестратора"""
        logger.info("🛑 Shutting down Galaxy Orchestrator")
        
        try:
            # Закрытие подключений
            if self.consumer:
                self.consumer.close()
            if self.producer:
                self.producer.close()
            if self.redis:
                await self.redis.close()
            if self.db_pool:
                self.db_pool.closeall()
            
            logger.success("✅ Galaxy Orchestrator shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


async def main():
    """Точка входа для запуска оркестратора"""
    orchestrator = GalaxyOrchestrator()
    
    try:
        await orchestrator.initialize()
        await orchestrator.run()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add("logs/orchestrator.log", rotation="100 MB", level="INFO")
    logger.add("logs/orchestrator_debug.log", rotation="100 MB", level="DEBUG")
    logger.add(lambda msg: print(msg, end=''), level="INFO", colorize=True)
    
    # Запуск оркестратора
    asyncio.run(main())