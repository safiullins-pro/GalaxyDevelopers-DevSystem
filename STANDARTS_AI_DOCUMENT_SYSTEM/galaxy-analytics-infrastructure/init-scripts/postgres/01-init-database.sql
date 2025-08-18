-- =====================================================
-- GALAXY ANALYTICS DATABASE INITIALIZATION
-- =====================================================

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Создаем схемы
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS tasks;
CREATE SCHEMA IF NOT EXISTS compliance;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS metrics;

-- =====================================================
-- ТАБЛИЦЫ ДЛЯ АГЕНТОВ
-- =====================================================

-- Агенты
CREATE TABLE agents.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    capabilities JSONB NOT NULL DEFAULT '{}',
    configuration JSONB NOT NULL DEFAULT '{}',
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE
);

-- Память агентов
CREATE TABLE agents.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents.agents(id) ON DELETE CASCADE,
    tenant_id VARCHAR(255) NOT NULL,
    memory_type VARCHAR(100) NOT NULL, -- 'working', 'persistent', 'procedural'
    content JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255), -- ID в векторной БД
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    archived BOOLEAN DEFAULT FALSE
);

-- Сессии агентов
CREATE TABLE agents.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents.agents(id) ON DELETE CASCADE,
    tenant_id VARCHAR(255) NOT NULL,
    session_data JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- ТАБЛИЦЫ ДЛЯ ЗАДАЧ
-- =====================================================

-- Задачи
CREATE TABLE tasks.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to UUID REFERENCES agents.agents(id),
    assigned_by VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    progress DECIMAL(5,2) DEFAULT 0.00,
    deadline TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE
);

-- Зависимости задач
CREATE TABLE tasks.dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks', -- 'blocks', 'requires', 'related'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- Подзадачи
CREATE TABLE tasks.subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_task_id UUID NOT NULL REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    subtask_id UUID NOT NULL REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_task_id, subtask_id)
);

-- =====================================================
-- COMPLIANCE И AUDIT
-- =====================================================

-- Стандарты соответствия
CREATE TABLE compliance.standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'security', 'quality', 'process', 'data_protection'
    requirements JSONB NOT NULL DEFAULT '[]',
    automation_level VARCHAR(50) DEFAULT 'manual',
    criticality VARCHAR(50) DEFAULT 'medium',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Проверки соответствия
CREATE TABLE compliance.checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    standard_id UUID NOT NULL REFERENCES compliance.standards(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents.agents(id) ON DELETE CASCADE,
    check_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'warning'
    details JSONB NOT NULL DEFAULT '{}',
    auto_fixed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Аудит событий
CREATE TABLE audit.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL, -- 'agent', 'task', 'compliance', etc.
    entity_id UUID NOT NULL,
    actor_id VARCHAR(255) NOT NULL, -- user or agent ID
    tenant_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- МЕТРИКИ И ПРОИЗВОДИТЕЛЬНОСТЬ
-- =====================================================

-- Метрики агентов
CREATE TABLE metrics.agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents.agents(id) ON DELETE CASCADE,
    tenant_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Метрики задач
CREATE TABLE metrics.task_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks.tasks(id) ON DELETE CASCADE,
    tenant_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Системные метрики
CREATE TABLE metrics.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    component VARCHAR(100), -- 'database', 'redis', 'message_bus', etc.
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================================

-- Агенты
CREATE INDEX idx_agents_tenant_id ON agents.agents(tenant_id);
CREATE INDEX idx_agents_status ON agents.agents(status);
CREATE INDEX idx_agents_type ON agents.agents(type);
CREATE INDEX idx_agents_last_heartbeat ON agents.agents(last_heartbeat);

-- Память агентов
CREATE INDEX idx_memories_agent_id ON agents.memories(agent_id);
CREATE INDEX idx_memories_tenant_id ON agents.memories(tenant_id);
CREATE INDEX idx_memories_type ON agents.memories(memory_type);
CREATE INDEX idx_memories_created_at ON agents.memories(created_at);
CREATE INDEX idx_memories_expires_at ON agents.memories(expires_at) WHERE expires_at IS NOT NULL;

-- Задачи
CREATE INDEX idx_tasks_tenant_id ON tasks.tasks(tenant_id);
CREATE INDEX idx_tasks_assigned_to ON tasks.tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks.tasks(status);
CREATE INDEX idx_tasks_priority ON tasks.tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks.tasks(created_at);
CREATE INDEX idx_tasks_deadline ON tasks.tasks(deadline) WHERE deadline IS NOT NULL;

-- Compliance
CREATE INDEX idx_checks_standard_id ON compliance.checks(standard_id);
CREATE INDEX idx_checks_task_id ON compliance.checks(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_checks_agent_id ON compliance.checks(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX idx_checks_status ON compliance.checks(status);

-- Аудит
CREATE INDEX idx_audit_events_entity_type_id ON audit.events(entity_type, entity_id);
CREATE INDEX idx_audit_events_tenant_id ON audit.events(tenant_id);
CREATE INDEX idx_audit_events_created_at ON audit.events(created_at);
CREATE INDEX idx_audit_events_actor_id ON audit.events(actor_id);

-- Метрики
CREATE INDEX idx_agent_metrics_agent_id ON metrics.agent_metrics(agent_id);
CREATE INDEX idx_agent_metrics_recorded_at ON metrics.agent_metrics(recorded_at);
CREATE INDEX idx_task_metrics_task_id ON metrics.task_metrics(task_id);
CREATE INDEX idx_task_metrics_recorded_at ON metrics.task_metrics(recorded_at);
CREATE INDEX idx_system_metrics_component ON metrics.system_metrics(component);
CREATE INDEX idx_system_metrics_recorded_at ON metrics.system_metrics(recorded_at);

-- =====================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКИХ ОБНОВЛЕНИЙ
-- =====================================================

-- Обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agents_updated_at 
    BEFORE UPDATE ON agents.agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_standards_updated_at 
    BEFORE UPDATE ON compliance.standards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ПАРТИЦИОНИРОВАНИЕ ДЛЯ БОЛЬШИХ ТАБЛИЦ
-- =====================================================

-- Партиционирование метрик по месяцам
CREATE TABLE metrics.agent_metrics_template (LIKE metrics.agent_metrics INCLUDING ALL);
ALTER TABLE metrics.agent_metrics_template ADD CONSTRAINT agent_metrics_partition_check 
    CHECK (recorded_at >= DATE '2024-01-01' AND recorded_at < DATE '2024-02-01');

-- =====================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =====================================================

-- Стандартные стандарты соответствия
INSERT INTO compliance.standards (name, version, type, criticality, requirements) VALUES
('ISO 27001', '2022', 'security', 'critical', '[
    {"id": "A.8.25", "title": "Secure Development Life Cycle", "description": "Information security in project management"},
    {"id": "A.8.31", "title": "Separation of environments", "description": "Development, testing and operational environments shall be separated"},
    {"id": "A.14.2.1", "title": "Secure development policy", "description": "Rules for the development of software and systems shall be established and applied"}
]'),
('GDPR', '2018', 'data_protection', 'critical', '[
    {"id": "Art.25", "title": "Data protection by design", "description": "Data protection by design and by default"},
    {"id": "Art.32", "title": "Security of processing", "description": "Appropriate technical and organisational measures"},
    {"id": "Art.35", "title": "Data protection impact assessment", "description": "DPIA when processing likely to result in high risk"}
]'),
('NIST SSDF', '1.1', 'security', 'high', '[
    {"id": "PO.1.1", "title": "Security policies", "description": "Establish security policies and requirements"},
    {"id": "PS.1.1", "title": "Access control", "description": "Protect all forms of code from unauthorized access"},
    {"id": "PW.1.1", "title": "Security requirements", "description": "Identify and document security requirements"}
]'),
('CMMI Level 3', '2.0', 'process', 'medium', '[
    {"id": "REQM", "title": "Requirements Management", "description": "Manage requirements and identify inconsistencies"},
    {"id": "CM", "title": "Configuration Management", "description": "Establish and maintain configuration management"},
    {"id": "PPQA", "title": "Process Quality Assurance", "description": "Provide staff and management with objective insight"}
]');

-- Создаем пользователей с ограниченными правами
CREATE USER galaxy_agent_user WITH PASSWORD 'galaxy_agent_secure_2024';
CREATE USER galaxy_readonly_user WITH PASSWORD 'galaxy_readonly_secure_2024';

-- Права для агента
GRANT USAGE ON SCHEMA agents, tasks, compliance, audit, metrics TO galaxy_agent_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA agents, tasks, compliance, audit, metrics TO galaxy_agent_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agents, tasks, compliance, audit, metrics TO galaxy_agent_user;

-- Права только для чтения
GRANT USAGE ON SCHEMA agents, tasks, compliance, audit, metrics TO galaxy_readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA agents, tasks, compliance, audit, metrics TO galaxy_readonly_user;

COMMIT;