#!/bin/bash

# =============================================================================
# Galaxy Development System - Production Setup Script
# Исправляет все критические проблемы из ATOMIC AUDIT REPORT
# =============================================================================

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

# Проверка требований
check_requirements() {
    log_step "Checking system requirements..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Проверка ОЗУ
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 8192 ]; then
        log_warning "Available memory is ${available_memory}MB. Recommended: 16GB+"
    fi
    
    # Проверка места на диске
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 50 ]; then
        log_error "Available disk space is ${available_space}GB. Required: 50GB+"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Создание .env файла с безопасными значениями
create_secure_env() {
    log_step "Creating secure .env file..."
    
    if [ -f .env ]; then
        log_warning ".env file already exists. Creating backup..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Генерация безопасных паролей и ключей
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -hex 64)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    GRAFANA_PASSWORD=$(openssl rand -base64 24)
    
    cat > .env << EOF
# ==============================================
# Galaxy Development System - Environment Variables
# Generated on: $(date)
# ==============================================

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=galaxydevelopment
POSTGRES_USER=galaxy
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/\${POSTGRES_DB}

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:\${REDIS_PASSWORD}@\${REDIS_HOST}:\${REDIS_PORT}/0

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_EXTERNAL_PORT=9092
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181

# AI API Keys (CHANGE THESE!)
OPENAI_API_KEY=sk-CHANGE_ME_YOUR_OPENAI_API_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-CHANGE_ME_YOUR_ANTHROPIC_API_KEY_HERE

# Git Integration (CHANGE THESE!)
GIT_REPO_URL=https://github.com/your-org/galaxy-docs.git
GIT_TOKEN=ghp_CHANGE_ME_YOUR_GITHUB_TOKEN_HERE
GIT_BRANCH=main
GIT_USER_NAME=Galaxy System
GIT_USER_EMAIL=system@galaxy-development.com

# Confluence Integration (CHANGE THESE!)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USER=your-email@your-domain.com
CONFLUENCE_TOKEN=CHANGE_ME_YOUR_CONFLUENCE_TOKEN_HERE
CONFLUENCE_SPACE=GALAXY

# SharePoint Integration (CHANGE THESE!)
SHAREPOINT_URL=https://your-org.sharepoint.com
SHAREPOINT_CLIENT_ID=CHANGE_ME_YOUR_CLIENT_ID_HERE
SHAREPOINT_CLIENT_SECRET=CHANGE_ME_YOUR_CLIENT_SECRET_HERE
SHAREPOINT_TENANT_ID=CHANGE_ME_YOUR_TENANT_ID_HERE
SHAREPOINT_SITE_ID=CHANGE_ME_YOUR_SITE_ID_HERE

# Email Configuration (CHANGE THESE!)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=galaxy-notifications@your-domain.com
SMTP_PASSWORD=CHANGE_ME_YOUR_EMAIL_PASSWORD_HERE

# Slack Integration (CHANGE THESE!)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_BOT_TOKEN=xoxb-CHANGE_ME_YOUR_SLACK_BOT_TOKEN_HERE
SLACK_CHANNEL=#galaxy-notifications

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

# Security
JWT_SECRET_KEY=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=60
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=100MB
DEBUG=false

# Workflow
MAX_WORKFLOW_DURATION=3600
AGENT_HEARTBEAT_TIMEOUT=300
MAX_CONCURRENT_TASKS_PER_AGENT=3
MAX_TASK_RETRIES=3
TASK_RETRY_DELAY=60

# Performance
DB_POOL_MIN_CONNECTIONS=5
DB_POOL_MAX_CONNECTIONS=20
REDIS_POOL_MAX_CONNECTIONS=50
KAFKA_CONSUMER_MAX_POLL_RECORDS=10
KAFKA_CONSUMER_SESSION_TIMEOUT=30000

# Compliance
AUDIT_LOG_RETENTION=2555
TASK_LOG_RETENTION=365
PERFORMANCE_METRICS_RETENTION=90
GDPR_ENABLED=true
SOX_COMPLIANCE=true
HIPAA_COMPLIANCE=false

# Backup
BACKUP_STORAGE_URL=s3://your-backup-bucket/galaxy-backups/
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/galaxy.crt
SSL_KEY_PATH=/etc/ssl/private/galaxy.key
FORCE_HTTPS=true
EOF
    
    chmod 600 .env
    log_success ".env file created with secure credentials"
    
    # Показываем какие переменные нужно изменить
    log_warning "IMPORTANT: You must update these variables in .env:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - GIT_* variables for your repository"
    echo "  - CONFLUENCE_* variables if using Confluence"
    echo "  - SHAREPOINT_* variables if using SharePoint"
    echo "  - SMTP_* variables for email notifications"
    echo "  - SLACK_* variables for Slack integration"
}

# Создание директорий
create_directories() {
    log_step "Creating directory structure..."
    
    # Основные директории
    mkdir -p logs data backups git-repos static nginx/ssl
    mkdir -p data/{elena,marcus,victoria,alex,sarah,viktor,dmitri,olga,jake,catherine,boris,ivan}
    mkdir -p monitoring/grafana/{dashboards,datasources}
    mkdir -p monitoring/prometheus
    
    # Установка правильных прав доступа
    chmod 755 logs data backups git-repos static
    chmod -R 755 data/
    chmod 755 monitoring
    
    log_success "Directory structure created"
}

# Создание SSL сертификатов для разработки
create_ssl_certificates() {
    log_step "Creating SSL certificates for development..."
    
    if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=GalaxyDevelopment/CN=localhost" \
            2>/dev/null
        
        chmod 600 nginx/ssl/key.pem
        chmod 644 nginx/ssl/cert.pem
        
        log_success "SSL certificates created"
    else
        log_info "SSL certificates already exist"
    fi
}

# Создание конфигурации Nginx
create_nginx_config() {
    log_step "Creating Nginx configuration..."
    
    cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    
    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    # Upstream definitions
    upstream grafana {
        server grafana:3000;
    }

    upstream prometheus {
        server prometheus:9090;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Main dashboard (Grafana)
        location / {
            proxy_pass http://grafana;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Prometheus
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    log_success "Nginx configuration created"
}

# Создание конфигурации Prometheus
create_prometheus_config() {
    log_step "Creating Prometheus configuration..."
    
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'galaxy-monitor'

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:9000']

  - job_name: 'elena-standards'
    static_configs:
      - targets: ['elena-standards:8001']

  - job_name: 'marcus-composer'
    static_configs:
      - targets: ['marcus-composer:8002']

  - job_name: 'victoria-reviewer'
    static_configs:
      - targets: ['victoria-reviewer:8003']

  - job_name: 'alex-integrator'
    static_configs:
      - targets: ['alex-integrator:8004']

  - job_name: 'sarah-publisher'
    static_configs:
      - targets: ['sarah-publisher:8005']

  - job_name: 'viktor-security'
    static_configs:
      - targets: ['viktor-security:8006']

  - job_name: 'dmitri-performance'
    static_configs:
      - targets: ['dmitri-performance:8007']

  - job_name: 'olga-data'
    static_configs:
      - targets: ['olga-data:8008']

  - job_name: 'jake-mobile'
    static_configs:
      - targets: ['jake-mobile:8009']

  - job_name: 'catherine-compliance'
    static_configs:
      - targets: ['catherine-compliance:8010']

  - job_name: 'boris-testing'
    static_configs:
      - targets: ['boris-testing:8011']

  - job_name: 'ivan-deployment'
    static_configs:
      - targets: ['ivan-deployment:8012']
EOF
    
    log_success "Prometheus configuration created"
}

# Создание Dockerfile для оркестратора
create_orchestrator_dockerfile() {
    log_step "Creating Dockerfile for orchestrator..."
    
    cat > Dockerfile.orchestrator << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY galaxy_orchestrator.py .

# Create non-root user
RUN useradd -m -u 1000 galaxy && chown -R galaxy:galaxy /app
USER galaxy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:9000/metrics || exit 1

# Expose metrics port
EXPOSE 9000

CMD ["python", "-u", "galaxy_orchestrator.py"]
EOF
    
    log_success "Orchestrator Dockerfile created"
}

# Создание requirements.txt
create_requirements() {
    log_step "Creating requirements.txt..."
    
    cat > requirements.txt << 'EOF'
# Core dependencies
asyncio-mqtt==0.11.1
aioredis==2.0.1
psycopg2-binary==2.9.7
kafka-python==2.0.2
loguru==0.7.0
prometheus-client==0.17.1
tenacity==8.2.2
aiohttp==3.8.5

# AI/ML dependencies
openai==0.27.8
anthropic==0.3.11

# Data processing
pandas==2.0.3
numpy==1.24.3
pydantic==2.0.3

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0

# Utilities
python-dotenv==1.0.0
PyYAML==6.0.1
requests==2.31.0
httpx==0.24.1
EOF
    
    log_success "requirements.txt created"
}

# Добавление в .gitignore
update_gitignore() {
    log_step "Updating .gitignore..."
    
    cat >> .gitignore << 'EOF'

# Galaxy Development System
.env
.env.*
*.key
*.pem
secrets/
logs/
data/*/
backups/
git-repos/

# Docker
.docker/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
pip-log.txt
.coverage
.pytest_cache/

# OS
.DS_Store
Thumbs.db
EOF
    
    log_success ".gitignore updated"
}

# Создание скриптов управления
create_management_scripts() {
    log_step "Creating management scripts..."
    
    # Скрипт запуска
    cat > start.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "🚀 Starting Galaxy Development System..."

# Check .env file
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please run ./setup_galaxy_system.sh first"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Create directories if they don't exist
mkdir -p logs data/{elena,marcus,victoria,alex,sarah,viktor,dmitri,olga,jake,catherine,boris,ivan} backups git-repos

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running!"
    exit 1
fi

# Stop old containers
echo "🛑 Stopping old containers..."
docker-compose down

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start infrastructure
echo "🚀 Starting infrastructure services..."
docker-compose up -d zookeeper
sleep 15

docker-compose up -d kafka postgres redis
sleep 20

# Wait for Kafka
echo "⏳ Waiting for Kafka..."
until docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:29092 --list > /dev/null 2>&1; do
    echo "Waiting for Kafka to be ready..."
    sleep 5
done

# Create Kafka topics
echo "📝 Creating Kafka topics..."
topics=(
    "orchestrator_commands"
    "agent_status_updates"
    "workflow_requests"
    "workflow_responses"
    "workflow_errors"
    "elena_standards_genius_tasks"
    "marcus_document_master_tasks"
    "victoria_quality_hawk_tasks"
    "alex_git_master_tasks"
    "sarah_distribution_master_tasks"
    "viktor_cyber_guardian_tasks"
    "dmitri_speed_demon_tasks"
    "olga_data_whisperer_tasks"
    "jake_app_master_tasks"
    "catherine_regulatory_expert_tasks"
    "boris_testing_machine_tasks"
    "ivan_deploy_master_tasks"
)

for topic in "${topics[@]}"; do
    docker-compose exec -T kafka kafka-topics --create --if-not-exists \
        --bootstrap-server localhost:29092 \
        --topic "$topic" \
        --partitions 3 \
        --replication-factor 1
done

# Start monitoring
echo "📊 Starting monitoring services..."
docker-compose up -d prometheus grafana

# Start orchestrator
echo "🎯 Starting orchestrator..."
docker-compose up -d orchestrator
sleep 10

# Start all agents
echo "🤖 Starting all 12 agents..."
docker-compose up -d elena-standards marcus-composer victoria-reviewer alex-integrator sarah-publisher viktor-security dmitri-performance olga-data jake-mobile catherine-compliance boris-testing ivan-deployment

# Start web server
echo "🌐 Starting nginx..."
docker-compose up -d nginx

# Show status
echo "✅ Galaxy Development System started!"
echo ""
echo "📊 Services available:"
echo "  - Main Dashboard: https://localhost (admin/${GRAFANA_ADMIN_PASSWORD})"
echo "  - Prometheus: https://localhost/prometheus"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Kafka: localhost:9092"
echo ""

docker-compose ps
EOF

    # Скрипт остановки
    cat > stop.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "🛑 Stopping Galaxy Development System..."

# Graceful shutdown of agents
echo "Stopping agents..."
docker-compose stop ivan-deployment boris-testing catherine-compliance jake-mobile olga-data dmitri-performance viktor-security sarah-publisher alex-integrator victoria-reviewer marcus-composer elena-standards

# Stop orchestrator
echo "Stopping orchestrator..."
docker-compose stop orchestrator

# Stop other services
echo "Stopping infrastructure..."
docker-compose down

echo "✅ Galaxy Development System stopped"
EOF

    # Скрипт health check
    cat > health_check.sh << 'EOF'
#!/bin/bash

echo "🏥 Checking Galaxy Development System health..."

check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $name is running on port $port"
        return 0
    else
        echo "❌ $name is not responding on port $port"
        return 1
    fi
}

# Check infrastructure
check_service localhost 5432 "PostgreSQL"
check_service localhost 6379 "Redis"
check_service localhost 9092 "Kafka"
check_service localhost 2181 "Zookeeper"
check_service localhost 9090 "Prometheus"
check_service localhost 3000 "Grafana"

# Check orchestrator
check_service localhost 9000 "Galaxy Orchestrator"

# Check agents
agents=(
    "8001:Elena (Standards)"
    "8002:Marcus (Composer)"
    "8003:Victoria (Reviewer)"
    "8004:Alex (Integrator)"
    "8005:Sarah (Publisher)"
    "8006:Viktor (Security)"
    "8007:Dmitri (Performance)"
    "8008:Olga (Data)"
    "8009:Jake (Mobile)"
    "8010:Catherine (Compliance)"
    "8011:Boris (Testing)"
    "8012:Ivan (Deployment)"
)

for agent in "${agents[@]}"; do
    port="${agent%:*}"
    name="${agent#*:}"
    if curl -s http://localhost:$port/metrics > /dev/null 2>&1; then
        echo "✅ $name agent is healthy"
    else
        echo "⚠️ $name agent is not responding"
    fi
done

echo ""
echo "📦 Container status:"
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"
EOF

    # Скрипт backup
    cat > backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

echo "🔄 Starting Galaxy Development System backup..."

# Create backup directory
mkdir -p ${BACKUP_PATH}

# PostgreSQL backup
echo "📦 Backing up PostgreSQL..."
if docker-compose ps postgres | grep -q "Up"; then
    docker-compose exec -T postgres pg_dump -U galaxy galaxydevelopment | gzip > ${BACKUP_PATH}/postgres_${TIMESTAMP}.sql.gz
else
    echo "⚠️ PostgreSQL container is not running, skipping database backup"
fi

# Redis backup
echo "📦 Backing up Redis..."
if docker-compose ps redis | grep -q "Up"; then
    docker-compose exec -T redis redis-cli --rdb /data/backup.rdb || true
    docker cp galaxy-redis:/data/backup.rdb ${BACKUP_PATH}/redis_${TIMESTAMP}.rdb || true
else
    echo "⚠️ Redis container is not running, skipping Redis backup"
fi

# Configuration backup
echo "📦 Backing up configuration..."
cp .env ${BACKUP_PATH}/env_${TIMESTAMP}.txt
cp docker-compose.yml ${BACKUP_PATH}/docker-compose_${TIMESTAMP}.yml
tar -czf ${BACKUP_PATH}/monitoring_${TIMESTAMP}.tar.gz monitoring/

# Create archive
echo "📦 Creating archive..."
tar -czf ${BACKUP_PATH}.tar.gz -C ${BACKUP_DIR} backup_${TIMESTAMP}
rm -rf ${BACKUP_PATH}

# Cleanup old backups (keep last 7)
echo "🧹 Cleaning old backups..."
ls -t ${BACKUP_DIR}/*.tar.gz | tail -n +8 | xargs -r rm

echo "✅ Backup completed: ${BACKUP_PATH}.tar.gz"
EOF

    # Делаем скрипты исполняемыми
    chmod +x start.sh stop.sh health_check.sh backup.sh
    
    log_success "Management scripts created"
}

# Основная функция
main() {
    echo -e "${CYAN}==============================================================================${NC}"
    echo -e "${CYAN}🌌 Galaxy Development System - Production Setup${NC}"
    echo -e "${CYAN}Исправляет критические проблемы из ATOMIC AUDIT REPORT${NC}"
    echo -e "${CYAN}==============================================================================${NC}"
    echo
    
    check_requirements
    create_secure_env
    create_directories
    create_ssl_certificates
    create_nginx_config
    create_prometheus_config
    create_orchestrator_dockerfile
    create_requirements
    update_gitignore
    create_management_scripts
    
    echo
    log_success "🎉 Galaxy Development System setup completed!"
    echo
    log_info "Next steps:"
    echo "1. Edit .env file with your actual API keys and credentials"
    echo "2. Run: ./start.sh"
    echo "3. Access dashboard: https://localhost"
    echo
    log_warning "SECURITY REMINDER:"
    echo "- All hardcoded passwords have been removed"
    echo "- .env file contains secure generated passwords"
    echo "- SSL certificates created for HTTPS"
    echo "- Remember to update API keys in .env"
    echo
    log_info "System will include:"
    echo "- Galaxy Orchestrator"
    echo "- 12 specialized agents"
    echo "- Kafka message broker"
    echo "- PostgreSQL database"
    echo "- Redis cache"
    echo "- Prometheus monitoring"
    echo "- Grafana dashboards"
    echo "- Nginx reverse proxy"
    echo
}

# Запуск
main "$@"