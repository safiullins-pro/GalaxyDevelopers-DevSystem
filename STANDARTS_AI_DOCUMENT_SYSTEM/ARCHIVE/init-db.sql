-- База данных для системы GalaxyDevelopment

-- Таблица процессов
CREATE TABLE IF NOT EXISTS processes (
    id SERIAL PRIMARY KEY,
    process_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    owner VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    itil_category VARCHAR(100),
    iso_compliance BOOLEAN DEFAULT false,
    cobit_alignment VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица агентов
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    last_ping TIMESTAMP,
    processed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    performance_score DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заданий для агентов
CREATE TABLE IF NOT EXISTS agent_tasks (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    process_id VARCHAR(20),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    priority INTEGER DEFAULT 5,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(agent_name),
    FOREIGN KEY (process_id) REFERENCES processes(process_id)
);

-- Таблица документации
CREATE TABLE IF NOT EXISTS documentation (
    id SERIAL PRIMARY KEY,
    process_id VARCHAR(20) NOT NULL,
    doc_type VARCHAR(50) NOT NULL, -- 'research', 'composed', 'reviewed', 'published'
    content TEXT,
    metadata JSONB,
    version VARCHAR(20) DEFAULT '1.0',
    quality_score DECIMAL(5,2),
    compliance_score DECIMAL(5,2),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes(process_id)
);

-- Таблица метрик производительности
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100),
    process_id VARCHAR(20),
    metric_value DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ролей команды (35 специалистов)
CREATE TABLE IF NOT EXISTS team_roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'AI/ML', 'Backend', 'Frontend', 'Process', 'Support'
    responsibilities TEXT[],
    processes_assigned TEXT[],
    performance_kpis JSONB,
    status VARCHAR(50) DEFAULT 'active'
);

-- Таблица чек-листов
CREATE TABLE IF NOT EXISTS checklists (
    id SERIAL PRIMARY KEY,
    checklist_id VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    items JSONB NOT NULL, -- массив чек-листа
    compliance_standards TEXT[], -- ITIL, ISO, COBIT, NIST
    applicable_roles TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка базовых агентов
INSERT INTO agents (agent_name, agent_type) VALUES
('ResearchAgent', 'research'),
('ComposerAgent', 'composer'),
('ReviewerAgent', 'reviewer'),
('IntegratorAgent', 'integrator'),
('PublisherAgent', 'publisher');

-- Вставка ролей команды (35 специалистов)
INSERT INTO team_roles (role_name, category, responsibilities) VALUES
-- AI/ML КОМАНДА (7 экспертов)
('AI/ML Engineer', 'AI/ML', ARRAY['Нейросетевое моделирование', 'TensorFlow/PyTorch', 'Production ML системы']),
('LLM Integration Specialist', 'AI/ML', ARRAY['Промпт-инжиниринг', 'GPT-4/Gemini интеграция', 'Few-shot learning']),
('Automation Engineer', 'AI/ML', ARRAY['CLI автоматизация', 'Bash/Python скрипты', 'Infrastructure as Code']),
('Data Scientist', 'AI/ML', ARRAY['Аналитика данных', 'A/B тестирование', 'Business insights']),
('Prompt Engineer', 'AI/ML', ARRAY['Оптимизация промптов', 'Токен-эффективность', 'HPSS методология']),
('AI QA Engineer', 'AI/ML', ARRAY['Тестирование AI', 'Adversarial testing', 'Bias detection']),
('MLOps Engineer', 'AI/ML', ARRAY['ML в продакшн', 'MLflow/Kubeflow', 'Model monitoring']),

-- BACKEND & INFRASTRUCTURE (8 экспертов)
('System Architect', 'Backend', ARRAY['Архитектура системы', 'Микросервисы', 'Domain-driven design']),
('Backend Lead Developer', 'Backend', ARRAY['API разработка', 'FastAPI/Express', 'GraphQL/gRPC']),
('DevOps Engineer', 'Backend', ARRAY['Kubernetes', 'CI/CD', 'Infrastructure automation']),
('Database Engineer', 'Backend', ARRAY['PostgreSQL/SQLite', 'Query optimization', 'Database design']),
('Kafka/Message Queue Specialist', 'Backend', ARRAY['Apache Kafka', 'RabbitMQ', 'Event streaming']),
('GCP Cloud Engineer', 'Backend', ARRAY['Google Cloud', 'Serverless', 'Cloud Functions']),
('Security Engineer', 'Backend', ARRAY['ITIL/ISO compliance', 'Security by design', 'Zero-trust']),
('API Developer', 'Backend', ARRAY['REST/GraphQL API', 'OpenAPI', 'API testing']),

-- FRONTEND & UX (5 экспертов)
('Frontend Lead', 'Frontend', ARRAY['React/TypeScript', 'Component architecture', 'Modern patterns']),
('macOS Developer', 'Frontend', ARRAY['Swift/SwiftUI', 'AppKit', 'Native macOS apps']),
('UI/UX Designer', 'Frontend', ARRAY['User research', 'Figma', 'Interface design']),
('Technical Writer', 'Frontend', ARRAY['Техническая документация', 'Markdown', 'GitBook']),
('Web Developer', 'Frontend', ARRAY['MkDocs/VitePress', 'Static sites', 'Jamstack']),

-- PROCESS & QUALITY (8 экспертов)
('Technical Lead', 'Process', ARRAY['Команда координация', 'Техническое видение', 'Agile leadership']),
('QA Lead', 'Process', ARRAY['Testing strategy', 'Quality assurance', 'Test automation']),
('Business Analyst', 'Process', ARRAY['Требования анализ', 'Use cases', 'Business metrics']),
('Compliance Officer', 'Process', ARRAY['ITIL/ISO/SOX compliance', 'Audit trails', 'Standards']),
('Process Owner', 'Process', ARRAY['ITIL v4', 'Process management', 'KPI monitoring']),
('Service Owner', 'Process', ARRAY['IT услуги', 'SLA/OLA', 'Customer satisfaction']),
('Scrum Master', 'Process', ARRAY['Agile coaching', 'Scrum ceremonies', 'Team facilitation']),
('Release Manager', 'Process', ARRAY['Release planning', 'Deployment', 'Rollback strategies']),

-- SUPPORT & OPERATIONS (7 экспертов)
('Site Reliability Engineer', 'Support', ARRAY['99.99% uptime', 'Monitoring', 'Chaos engineering']),
('Integration Specialist', 'Support', ARRAY['API integrations', 'Data transformation', 'System connectivity']),
('Data Engineer', 'Support', ARRAY['ETL/ELT pipelines', 'Big Data', 'Apache Spark']),
('Mobile Developer', 'Support', ARRAY['iOS/Android native', 'Performance optimization', 'App store']),
('Performance Engineer', 'Support', ARRAY['Performance tuning', 'Load testing', 'Optimization']),
('Support Engineer', 'Support', ARRAY['Troubleshooting', 'Customer support', 'Issue resolution']),
('Training Specialist', 'Support', ARRAY['Team training', 'Knowledge transfer', 'Mentorship']);

-- Вставка примеров процессов
INSERT INTO processes (process_id, name, domain, owner, itil_category, iso_compliance, cobit_alignment) VALUES
('001', 'Incident Management', 'ITSM', 'Service Desk Manager', 'Service Operation', true, 'APO'),
('002', 'Change Management', 'ITSM', 'Change Manager', 'Service Transition', true, 'BAI'),
('003', 'Code Review Process', 'Development', 'Tech Lead', NULL, false, 'BAI'),
('004', 'Security Assessment', 'Security', 'CISO', NULL, true, 'APO'),
('005', 'Performance Testing', 'QA', 'QA Manager', NULL, false, 'BAI');

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_processes_status ON processes(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent ON agent_tasks(agent_name);
CREATE INDEX IF NOT EXISTS idx_documentation_process ON documentation(process_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Функция обновления timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_processes_updated_at 
    BEFORE UPDATE ON processes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();