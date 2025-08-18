# =====================================================
# WB ANALYTICS INFRASTRUCTURE MAKEFILE
# =====================================================

.PHONY: help start stop restart status health clean logs backup restore

# Default target
help: ## Show this help message
	@echo "🚀 WB Analytics Infrastructure Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Infrastructure management
start: ## Start all services
	@echo "🚀 Starting WB Analytics Infrastructure..."
	@./start.sh

stop: ## Stop all services
	@echo "🛑 Stopping WB Analytics Infrastructure..."
	@./stop.sh

restart: ## Restart all services
	@echo "🔄 Restarting WB Analytics Infrastructure..."
	@./stop.sh
	@./start.sh

clean: ## Stop and remove all data (DESTRUCTIVE!)
	@echo "🧹 Cleaning WB Analytics Infrastructure..."
	@read -p "Are you sure? This will delete ALL data! (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@./stop.sh --clean

# Status and monitoring  
status: ## Show container status
	@echo "📊 WB Analytics Infrastructure Status"
	@echo "===================================="
	@docker-compose ps

health: ## Run health checks
	@./health-check.sh

logs: ## Show logs for all services
	@docker-compose logs -f

logs-%: ## Show logs for specific service (e.g., make logs-postgres)
	@docker-compose logs -f $*

# Database operations
db-shell: ## Connect to PostgreSQL database
	@docker-compose exec postgres psql -U wb_admin -d wb_analytics

db-backup: ## Backup database
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U wb_admin wb_analytics > backups/wb_analytics_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

db-restore: ## Restore database from backup (Usage: make db-restore FILE=backup.sql)
ifndef FILE
	@echo "❌ Please specify backup file: make db-restore FILE=backup.sql"
	@exit 1
endif
	@echo "🔄 Restoring database from $(FILE)..."
	@docker-compose exec -T postgres psql -U wb_admin -d wb_analytics < $(FILE)
	@echo "✅ Database restored"

# Redis operations
redis-shell: ## Connect to Redis
	@docker-compose exec redis redis-cli

redis-flush: ## Flush all Redis data
	@echo "⚠️  This will delete ALL Redis data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose exec redis redis-cli FLUSHALL
	@echo "✅ Redis data cleared"

# Development helpers
dev-setup: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@cp -n .env.example .env || true
	@echo "📄 Environment file ready: .env"
	@echo "✏️  Edit .env file if needed, then run: make start"

dev-reset: ## Reset development environment (keeps data)
	@echo "🔄 Resetting development environment..."
	@docker-compose down
	@docker-compose up -d
	@echo "✅ Development environment reset"

# Monitoring shortcuts
grafana: ## Open Grafana in browser
	@echo "📊 Opening Grafana..."
	@open http://localhost:3000 || xdg-open http://localhost:3000 2>/dev/null || echo "Open http://localhost:3000 in your browser"

adminer: ## Open Adminer (Database GUI) in browser  
	@echo "🗄️  Opening Adminer..."
	@open http://localhost:8080 || xdg-open http://localhost:8080 2>/dev/null || echo "Open http://localhost:8080 in your browser"

redis-gui: ## Open Redis Insight in browser
	@echo "📈 Opening Redis Insight..."
	@open http://localhost:8001 || xdg-open http://localhost:8001 2>/dev/null || echo "Open http://localhost:8001 in your browser"

minio: ## Open MinIO console in browser
	@echo "💾 Opening MinIO Console..."
	@open http://localhost:9001 || xdg-open http://localhost:9001 2>/dev/null || echo "Open http://localhost:9001 in your browser"

# Testing
test-connections: ## Test all service connections
	@echo "🔍 Testing service connections..."
	@./health-check.sh

# Maintenance
update: ## Update all Docker images
	@echo "📦 Updating Docker images..."
	@docker-compose pull
	@echo "✅ Images updated. Run 'make restart' to use new versions"

prune: ## Clean up unused Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	@docker system prune -f
	@echo "✅ Cleanup completed"

# Documentation
docs: ## Show service URLs and credentials
	@echo "🔗 WB Analytics Infrastructure URLs & Credentials"
	@echo "================================================="
	@echo ""
	@echo "📊 Grafana:         http://localhost:3000"
	@echo "   Username:        admin"
	@echo "   Password:        wb_grafana_2024"
	@echo ""
	@echo "🗄️  Adminer:         http://localhost:8080"  
	@echo "   System:          PostgreSQL"
	@echo "   Server:          postgres"
	@echo "   Username:        wb_admin"
	@echo "   Password:        wb_secure_pass_2024"
	@echo "   Database:        wb_analytics"
	@echo ""
	@echo "📈 Redis Insight:   http://localhost:8001"
	@echo "   Host:            redis"
	@echo "   Port:            6379"
	@echo "   Password:        wb_redis_secure_2024"
	@echo ""
	@echo "💾 MinIO Console:   http://localhost:9001"
	@echo "   Username:        wb_minio_admin"
	@echo "   Password:        wb_minio_secure_2024"
	@echo ""
	@echo "🔌 Direct Connections:"
	@echo "   PostgreSQL:      localhost:5432"
	@echo "   Redis:           localhost:6379"
	@echo "   ChromaDB:        localhost:8000"
	@echo "   MinIO API:       localhost:9000"
	@echo "   Prometheus:      localhost:9090"
	@echo ""