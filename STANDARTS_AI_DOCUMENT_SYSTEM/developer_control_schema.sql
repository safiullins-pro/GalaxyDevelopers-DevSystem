-- Таблица для контейнеров разработчиков
CREATE SCHEMA IF NOT EXISTS developer_control;

CREATE TABLE IF NOT EXISTS developer_control.containers (
    id SERIAL PRIMARY KEY,
    container_id VARCHAR(64) UNIQUE NOT NULL,
    developer_name VARCHAR(100) NOT NULL,
    workspace_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active',
    security_config JSONB,
    resource_limits JSONB
);

-- Таблица для событий файловой системы
CREATE TABLE IF NOT EXISTS developer_control.file_events (
    id SERIAL PRIMARY KEY,
    container_id VARCHAR(64) REFERENCES developer_control.containers(container_id),
    file_path VARCHAR(1000) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- create, modify, delete
    file_hash VARCHAR(64),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ai_analysis_result JSONB,
    blocked BOOLEAN DEFAULT FALSE,
    compliance_status VARCHAR(20)
);

-- Таблица для AI анализа кода
CREATE TABLE IF NOT EXISTS developer_control.code_analysis (
    id SERIAL PRIMARY KEY,
    file_event_id INTEGER REFERENCES developer_control.file_events(id),
    analysis_agent VARCHAR(100) NOT NULL,
    tz_compliance_score DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    security_score DECIMAL(3,2),
    violations JSONB,
    recommendations JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица для регистрации агентов (если еще не существует)
CREATE SCHEMA IF NOT EXISTS agents;
CREATE TABLE IF NOT EXISTS agents.registry (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Добавляем комментарии к таблицам и колонкам для ясности
COMMENT ON TABLE developer_control.containers IS 'Реестр изолированных контейнеров для разработчиков';
COMMENT ON COLUMN developer_control.containers.security_config IS 'Настройки безопасности, например, security-opt, apparmor profile';
COMMENT ON TABLE developer_control.file_events IS 'События файловой системы, отслеживаемые внутри контейнеров';
COMMENT ON COLUMN developer_control.file_events.file_hash IS 'Хеш файла для отслеживания изменений';
COMMENT ON TABLE developer_control.code_analysis IS 'Результаты анализа кода, проведенного AI аудитором';
