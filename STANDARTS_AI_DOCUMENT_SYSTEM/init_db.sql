-- Создание схемы для контроля разработчиков
CREATE SCHEMA IF NOT EXISTS dev_control;

-- Создание пользователя control_admin и предоставление ему прав
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'control_admin') THEN
      CREATE USER control_admin WITH PASSWORD 'secure_control_2024';
   END IF;
END
$$
;

GRANT ALL PRIVILEGES ON SCHEMA dev_control TO control_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dev_control TO control_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dev_control TO control_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA dev_control GRANT ALL PRIVILEGES ON TABLES TO control_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA dev_control GRANT ALL PRIVILEGES ON SEQUENCES TO control_admin;

-- Таблица разработчиков
CREATE TABLE dev_control.developers (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    container_id VARCHAR(64),
    workspace_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- Таблица файловых событий
CREATE TABLE dev_control.file_events (
    id SERIAL PRIMARY KEY,
    developer_id INTEGER REFERENCES dev_control.developers(id),
    file_path VARCHAR(1000) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- create, modify, delete
    file_content TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

-- Таблица AI анализа
CREATE TABLE dev_control.ai_analysis (
    id SERIAL PRIMARY KEY,
    file_event_id INTEGER REFERENCES dev_control.file_events(id),
    tz_compliance_score DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    security_score DECIMAL(3,2),
    violations JSONB,
    recommendations TEXT,
    is_blocked BOOLEAN DEFAULT FALSE,
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- Таблица нарушений
CREATE TABLE dev_control.violations (
    id SERIAL PRIMARY KEY,
    file_event_id INTEGER REFERENCES dev_control.file_events(id),
    violation_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- critical, high, medium, low
    description TEXT,
    is_blocking BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица заблокированных файлов
CREATE TABLE dev_control.blocked_files (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(1000) NOT NULL,
    developer_id INTEGER REFERENCES dev_control.developers(id),
    reason TEXT,
    blocked_at TIMESTAMP DEFAULT NOW(),
    unblocked_at TIMESTAMP NULL
);

-- НОВАЯ ТАБЛИЦА: Правила для агентов (Централизованное Управление Правилами)
CREATE TABLE dev_control.agent_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- e.g., 'critical_pattern', 'tz_keyword', 'naming_convention'
    rule_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- НОВАЯ ТАБЛИЦА: Роли пользователей (Управление Пользователями и Ролями)
CREATE TABLE dev_control.roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- НОВАЯ ТАБЛИЦА: Пользователи системы контроля (Управление Пользователями и Ролями)
CREATE TABLE dev_control.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES dev_control.roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_file_events_developer ON dev_control.file_events(developer_id);
CREATE INDEX idx_file_events_processed ON dev_control.file_events(processed);
CREATE INDEX idx_violations_severity ON dev_control.violations(severity);
CREATE INDEX idx_blocked_files_path ON dev_control.blocked_files(file_path);
CREATE INDEX idx_agent_rules_type ON dev_control.agent_rules(rule_type);
CREATE INDEX idx_users_username ON dev_control.users(username);

-- Начальные данные для ролей
INSERT INTO dev_control.roles (role_name) VALUES ('admin') ON CONFLICT (role_name) DO NOTHING;
INSERT INTO dev_control.roles (role_name) VALUES ('auditor') ON CONFLICT (role_name) DO NOTHING;
INSERT INTO dev_control.roles (role_name) VALUES ('viewer') ON CONFLICT (role_name) DO NOTHING;

-- Начальные данные для пользователя-администратора (пароль: admin_password)
-- В реальной системе используйте хеширование паролей!
-- Для простоты, здесь используется простой хеш, в реальной системе нужно использовать bcrypt или аналоги
INSERT INTO dev_control.users (username, password_hash, role_id)
VALUES ('admin', 'pbkdf2:sha256:260000$e2345$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2', (SELECT id FROM dev_control.roles WHERE role_name = 'admin'))
ON CONFLICT (username) DO NOTHING;

-- Начальные данные для правил агентов (примеры)
INSERT INTO dev_control.agent_rules (rule_name, rule_type, rule_value)
VALUES
    ('critical_pattern_password', 'critical_pattern', 'password\s*=\s*[""][^"\]+[""]'),
    ('critical_pattern_api_key', 'critical_pattern', 'api[_-]?key\s*=\s*[""][^"\]+[""]'),
    ('critical_pattern_exec', 'critical_pattern', 'exec\s*$$'),
    ('critical_pattern_eval', 'critical_pattern', 'eval\s*$$'),
    ('critical_pattern_import_os', 'critical_pattern', 'import\s+os'),
    ('critical_pattern_subprocess', 'critical_pattern', 'subprocess\.'),
    ('critical_pattern___import__', 'critical_pattern', '__import__'),
    ('critical_pattern_rm_rf', 'critical_pattern', 'rm\s+-rf')
ON CONFLICT (rule_name) DO NOTHING;