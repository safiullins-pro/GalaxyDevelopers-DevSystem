/**
 * GALAXY MONITORING MODULE
 * Полная интеграция мониторинга в основную панель
 */

class GalaxyMonitoringModule {
    constructor() {
        this.config = null;
        this.ws = null;
        this.apiBase = 'http://localhost:8766';
        this.wsUrl = 'ws://localhost:8765';
        this.autoRefreshInterval = null;
        this.initialized = false;
        
        // Статусы компонентов
        this.componentStatus = {
            websocket: 'offline',
            fileObserver: 'offline',
            syntaxChecker: 'idle',
            securityScanner: 'idle',
            compliance: 'idle'
        };
        
        // Метрики
        this.metrics = {
            fileChanges: 0,
            syntaxErrors: 0,
            vulnerabilities: 0,
            complianceScore: {},
            activeConnections: 0
        };
    }

    // ========== ИНИЦИАЛИЗАЦИЯ ==========
    async init() {
        console.log('🚀 Инициализация Galaxy Monitoring Module...');
        
        try {
            // Загружаем конфиг
            await this.loadConfig();
            
            // Подключаем WebSocket
            this.connectWebSocket();
            
            // Запускаем автообновление
            this.startAutoRefresh();
            
            // Создаем UI элементы
            this.createMonitoringPanel();
            
            this.initialized = true;
            console.log('✅ Monitoring Module инициализирован');
            
            return true;
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            return false;
        }
    }

    // ========== КОНФИГУРАЦИЯ ==========
    async loadConfig() {
        try {
            const response = await fetch('/monitoring_config.json');
            this.config = await response.json();
            console.log('📄 Конфигурация загружена');
        } catch (error) {
            console.warn('⚠️ Используется конфигурация по умолчанию');
            this.config = this.getDefaultConfig();
        }
    }

    getDefaultConfig() {
        return {
            server: {
                websocket: { port: 8765 },
                api: { port: 8766 }
            },
            monitoring: {
                periodic_checks: { interval_seconds: 30 }
            }
        };
    }

    // ========== WEBSOCKET ==========
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
            console.log('📡 WebSocket подключен');
            this.componentStatus.websocket = 'online';
            this.updateStatusIndicators();
            this.showNotification('WebSocket подключен', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('❌ WebSocket ошибка:', error);
            this.componentStatus.websocket = 'error';
            this.updateStatusIndicators();
        };

        this.ws.onclose = () => {
            console.log('🔌 WebSocket отключен');
            this.componentStatus.websocket = 'offline';
            this.updateStatusIndicators();
            
            // Переподключение через 5 сек
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }

    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'file_change':
                this.handleFileChange(data.change);
                break;
            case 'system_status':
                this.updateSystemStatus(data);
                break;
            case 'agent_status':
                this.updateAgentStatus(data);
                break;
            default:
                console.log('📨 WebSocket:', data);
        }
    }

    // ========== API МЕТОДЫ ==========
    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, options);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    async getSystemStatus() {
        return await this.fetchAPI('/api/monitoring/status');
    }

    async getFileChanges() {
        return await this.fetchAPI('/api/monitoring/file-changes');
    }

    async runSyntaxCheck() {
        this.componentStatus.syntaxChecker = 'running';
        this.updateStatusIndicators();
        
        const result = await this.fetchAPI('/api/monitoring/syntax-check');
        
        this.metrics.syntaxErrors = result.total;
        this.componentStatus.syntaxChecker = 'idle';
        this.updateStatusIndicators();
        
        return result;
    }

    async runSecurityScan() {
        this.componentStatus.securityScanner = 'running';
        this.updateStatusIndicators();
        
        const result = await this.fetchAPI('/api/monitoring/security-scan');
        
        this.metrics.vulnerabilities = result.total;
        this.componentStatus.securityScanner = 'idle';
        this.updateStatusIndicators();
        
        return result;
    }

    async checkCompliance(standard) {
        const result = await this.fetchAPI(`/api/monitoring/compliance/${standard}`);
        this.metrics.complianceScore[standard] = result.score;
        return result;
    }

    async runIntegrationTests() {
        return await this.fetchAPI('/api/monitoring/integration-test');
    }

    // ========== УПРАВЛЕНИЕ СЕРВЕРОМ ==========
    async startServer() {
        try {
            // Запускаем через системный скрипт
            const response = await fetch('/api/system/start-monitoring', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Сервер мониторинга запущен', 'success');
                setTimeout(() => this.init(), 2000);
                return true;
            }
        } catch (error) {
            this.showNotification('Ошибка запуска сервера', 'error');
            return false;
        }
    }

    async stopServer() {
        try {
            const response = await fetch('/api/system/stop-monitoring', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Сервер мониторинга остановлен', 'info');
                this.componentStatus.websocket = 'offline';
                this.componentStatus.fileObserver = 'offline';
                this.updateStatusIndicators();
                return true;
            }
        } catch (error) {
            this.showNotification('Ошибка остановки сервера', 'error');
            return false;
        }
    }

    async restartServer() {
        await this.stopServer();
        setTimeout(() => this.startServer(), 1000);
    }

    // ========== UI ПАНЕЛЬ ==========
    createMonitoringPanel() {
        // Проверяем, не создана ли уже панель
        if (document.getElementById('galaxy-monitoring-panel')) {
            return;
        }

        const panel = document.createElement('div');
        panel.id = 'galaxy-monitoring-panel';
        panel.className = 'monitoring-panel';
        panel.innerHTML = `
            <div class="monitoring-header">
                <h3>🌌 Galaxy Monitoring</h3>
                <div class="monitoring-controls">
                    <button id="mon-refresh" class="mon-btn mon-btn-sm">🔄</button>
                    <button id="mon-settings" class="mon-btn mon-btn-sm">⚙️</button>
                    <button id="mon-toggle" class="mon-btn mon-btn-sm">📊</button>
                </div>
            </div>
            
            <div class="monitoring-content" id="monitoring-content">
                <!-- Статусы компонентов -->
                <div class="mon-section">
                    <h4>Статус системы</h4>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-indicator" id="ws-status"></span>
                            <span>WebSocket</span>
                        </div>
                        <div class="status-item">
                            <span class="status-indicator" id="file-status"></span>
                            <span>File Observer</span>
                        </div>
                        <div class="status-item">
                            <span class="status-indicator" id="syntax-status"></span>
                            <span>Syntax Check</span>
                        </div>
                        <div class="status-item">
                            <span class="status-indicator" id="security-status"></span>
                            <span>Security Scan</span>
                        </div>
                    </div>
                </div>
                
                <!-- Метрики -->
                <div class="mon-section">
                    <h4>Метрики</h4>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value" id="metric-files">0</div>
                            <div class="metric-label">Изменений файлов</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="metric-errors">0</div>
                            <div class="metric-label">Синт. ошибок</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="metric-vulns">0</div>
                            <div class="metric-label">Уязвимостей</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="metric-connections">0</div>
                            <div class="metric-label">Подключений</div>
                        </div>
                    </div>
                </div>
                
                <!-- Compliance -->
                <div class="mon-section">
                    <h4>Compliance</h4>
                    <div class="compliance-bars">
                        <div class="compliance-item">
                            <label>ISO 27001</label>
                            <div class="progress-bar">
                                <div class="progress-fill" id="iso-progress" style="width: 0%"></div>
                            </div>
                            <span id="iso-score">0%</span>
                        </div>
                        <div class="compliance-item">
                            <label>ITIL 4</label>
                            <div class="progress-bar">
                                <div class="progress-fill" id="itil-progress" style="width: 0%"></div>
                            </div>
                            <span id="itil-score">0%</span>
                        </div>
                        <div class="compliance-item">
                            <label>COBIT</label>
                            <div class="progress-bar">
                                <div class="progress-fill" id="cobit-progress" style="width: 0%"></div>
                            </div>
                            <span id="cobit-score">0%</span>
                        </div>
                    </div>
                </div>
                
                <!-- Действия -->
                <div class="mon-section">
                    <h4>Управление</h4>
                    <div class="action-buttons">
                        <button class="mon-btn mon-btn-primary" onclick="galaxyMonitoring.runFullScan()">
                            🔍 Полное сканирование
                        </button>
                        <button class="mon-btn" onclick="galaxyMonitoring.runSyntaxCheck()">
                            ✓ Проверка синтаксиса
                        </button>
                        <button class="mon-btn" onclick="galaxyMonitoring.runSecurityScan()">
                            🔒 Сканирование безопасности
                        </button>
                        <button class="mon-btn" onclick="galaxyMonitoring.checkAllCompliance()">
                            📋 Проверка Compliance
                        </button>
                        <button class="mon-btn mon-btn-danger" onclick="galaxyMonitoring.restartServer()">
                            🔄 Перезапуск сервера
                        </button>
                    </div>
                </div>
                
                <!-- Лог изменений -->
                <div class="mon-section">
                    <h4>Последние изменения</h4>
                    <div class="change-log" id="change-log">
                        <div class="log-item">Ожидание изменений...</div>
                    </div>
                </div>
            </div>
        `;

        // Добавляем стили
        this.injectStyles();
        
        // Добавляем панель в body
        document.body.appendChild(panel);
        
        // Привязываем события
        this.bindEvents();
        
        // Обновляем статусы
        this.updateStatusIndicators();
    }

    injectStyles() {
        if (document.getElementById('monitoring-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'monitoring-styles';
        styles.textContent = `
            .monitoring-panel {
                position: fixed;
                right: 20px;
                top: 20px;
                width: 400px;
                max-height: 90vh;
                background: rgba(20, 20, 20, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                overflow: hidden;
                z-index: 10000;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            }
            
            .monitoring-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: rgba(99, 102, 241, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .monitoring-header h3 {
                margin: 0;
                color: #fff;
                font-size: 18px;
            }
            
            .monitoring-controls {
                display: flex;
                gap: 8px;
            }
            
            .monitoring-content {
                padding: 20px;
                overflow-y: auto;
                max-height: calc(90vh - 60px);
            }
            
            .mon-section {
                margin-bottom: 25px;
            }
            
            .mon-section h4 {
                color: #a0a0a0;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 12px;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 6px;
                font-size: 13px;
            }
            
            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #666;
            }
            
            .status-indicator.online { background: #10b981; }
            .status-indicator.running { background: #3b82f6; animation: pulse 1s infinite; }
            .status-indicator.error { background: #ef4444; }
            .status-indicator.warning { background: #f59e0b; }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            
            .metric-card {
                background: rgba(255, 255, 255, 0.03);
                padding: 12px;
                border-radius: 6px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #6366f1;
            }
            
            .metric-label {
                font-size: 11px;
                color: #666;
                margin-top: 4px;
            }
            
            .compliance-item {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
            }
            
            .compliance-item label {
                width: 80px;
                font-size: 12px;
                color: #a0a0a0;
            }
            
            .progress-bar {
                flex: 1;
                height: 20px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #10b981, #3b82f6);
                transition: width 0.5s;
            }
            
            .compliance-item span {
                width: 40px;
                text-align: right;
                font-size: 12px;
                color: #fff;
            }
            
            .action-buttons {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .mon-btn {
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #fff;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            
            .mon-btn:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: translateY(-1px);
            }
            
            .mon-btn-primary {
                background: rgba(99, 102, 241, 0.2);
                border-color: rgba(99, 102, 241, 0.3);
                grid-column: span 2;
            }
            
            .mon-btn-danger {
                background: rgba(239, 68, 68, 0.2);
                border-color: rgba(239, 68, 68, 0.3);
            }
            
            .mon-btn-sm {
                padding: 4px 8px;
                font-size: 14px;
            }
            
            .change-log {
                max-height: 150px;
                overflow-y: auto;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                padding: 10px;
            }
            
            .log-item {
                padding: 6px;
                margin-bottom: 4px;
                font-size: 11px;
                color: #a0a0a0;
                border-left: 2px solid #6366f1;
                padding-left: 10px;
            }
            
            .notification {
                position: fixed;
                top: 80px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 6px;
                color: #fff;
                font-size: 14px;
                z-index: 10001;
                animation: slideIn 0.3s;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            .notification.success { background: #10b981; }
            .notification.error { background: #ef4444; }
            .notification.info { background: #3b82f6; }
            .notification.warning { background: #f59e0b; }
            
            /* Settings Modal */
            .settings-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 100000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .settings-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(5px);
            }
            
            .settings-content {
                position: relative;
                background: rgba(20, 20, 20, 0.98);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 0;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow: hidden;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
            }
            
            .settings-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                background: rgba(99, 102, 241, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .settings-header h3 {
                margin: 0;
                color: #fff;
                font-size: 18px;
            }
            
            .settings-close {
                background: none;
                border: none;
                color: #666;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.3s;
            }
            
            .settings-close:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
            }
            
            .settings-body {
                padding: 20px;
                overflow-y: auto;
                max-height: calc(80vh - 140px);
            }
            
            .settings-group {
                margin-bottom: 20px;
            }
            
            .settings-group label {
                display: block;
                color: #a0a0a0;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            .settings-input {
                width: 100%;
                padding: 10px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #fff;
                font-size: 14px;
            }
            
            .settings-input:focus {
                outline: none;
                border-color: #6366f1;
                background: rgba(255, 255, 255, 0.08);
            }
            
            .settings-actions {
                display: flex;
                gap: 10px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.3);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .settings-btn {
                flex: 1;
                padding: 10px 20px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #fff;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }
            
            .settings-btn:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            .settings-btn-primary {
                background: rgba(99, 102, 241, 0.2);
                border-color: rgba(99, 102, 241, 0.3);
            }
            
            .settings-btn-primary:hover {
                background: rgba(99, 102, 241, 0.3);
            }
        `;
        
        document.head.appendChild(styles);
    }

    bindEvents() {
        // Кнопка обновления
        document.getElementById('mon-refresh')?.addEventListener('click', () => {
            this.refreshAll();
        });
        
        // Кнопка настроек
        document.getElementById('mon-settings')?.addEventListener('click', () => {
            this.showSettings();
        });
        
        // Кнопка сворачивания
        document.getElementById('mon-toggle')?.addEventListener('click', () => {
            this.togglePanel();
        });
    }

    // ========== ОБНОВЛЕНИЕ UI ==========
    updateStatusIndicators() {
        const wsStatus = document.getElementById('ws-status');
        const fileStatus = document.getElementById('file-status');
        const syntaxStatus = document.getElementById('syntax-status');
        const securityStatus = document.getElementById('security-status');
        
        if (wsStatus) {
            wsStatus.className = `status-indicator ${this.componentStatus.websocket}`;
        }
        
        if (fileStatus) {
            fileStatus.className = `status-indicator ${this.componentStatus.fileObserver}`;
        }
        
        if (syntaxStatus) {
            syntaxStatus.className = `status-indicator ${this.componentStatus.syntaxChecker === 'running' ? 'running' : 'online'}`;
        }
        
        if (securityStatus) {
            securityStatus.className = `status-indicator ${this.componentStatus.securityScanner === 'running' ? 'running' : 'online'}`;
        }
    }

    updateMetrics() {
        document.getElementById('metric-files').textContent = this.metrics.fileChanges;
        document.getElementById('metric-errors').textContent = this.metrics.syntaxErrors;
        document.getElementById('metric-vulns').textContent = this.metrics.vulnerabilities;
        document.getElementById('metric-connections').textContent = this.metrics.activeConnections;
    }

    updateComplianceScores() {
        for (const [standard, score] of Object.entries(this.metrics.complianceScore)) {
            const key = standard.toLowerCase().replace(/[0-9]/g, '');
            const progressBar = document.getElementById(`${key}-progress`);
            const scoreText = document.getElementById(`${key}-score`);
            
            if (progressBar) {
                progressBar.style.width = `${score}%`;
            }
            if (scoreText) {
                scoreText.textContent = `${Math.round(score)}%`;
            }
        }
    }

    updateSystemStatus(data) {
        this.componentStatus.fileObserver = data.file_observer_active ? 'online' : 'offline';
        this.metrics.activeConnections = data.websocket_clients || 0;
        this.metrics.fileChanges = data.recent_changes || 0;
        
        this.updateStatusIndicators();
        this.updateMetrics();
    }

    handleFileChange(change) {
        this.metrics.fileChanges++;
        this.updateMetrics();
        
        // Добавляем в лог
        const log = document.getElementById('change-log');
        if (log) {
            const item = document.createElement('div');
            item.className = 'log-item';
            const time = new Date().toLocaleTimeString();
            const fileName = change.path.split('/').pop();
            item.textContent = `[${time}] ${change.type}: ${fileName}`;
            
            log.insertBefore(item, log.firstChild);
            
            // Ограничиваем количество записей
            while (log.children.length > 20) {
                log.removeChild(log.lastChild);
            }
        }
    }

    updateAgentStatus(data) {
        console.log('Agent status:', data);
    }

    // ========== ДЕЙСТВИЯ ==========
    async runFullScan() {
        this.showNotification('Запуск полного сканирования...', 'info');
        
        try {
            await Promise.all([
                this.runSyntaxCheck(),
                this.runSecurityScan(),
                this.checkAllCompliance()
            ]);
            
            this.showNotification('Полное сканирование завершено', 'success');
        } catch (error) {
            this.showNotification('Ошибка при сканировании', 'error');
        }
    }

    async checkAllCompliance() {
        const standards = ['ISO27001', 'ITIL4', 'COBIT'];
        
        for (const standard of standards) {
            await this.checkCompliance(standard);
        }
        
        this.updateComplianceScores();
    }

    async refreshAll() {
        try {
            const status = await this.getSystemStatus();
            this.updateSystemStatus(status);
            
            await this.checkAllCompliance();
            
            this.showNotification('Данные обновлены', 'success');
        } catch (error) {
            this.showNotification('Ошибка обновления', 'error');
        }
    }

    // ========== АВТООБНОВЛЕНИЕ ==========
    startAutoRefresh() {
        // Обновляем каждые 30 секунд
        this.autoRefreshInterval = setInterval(() => {
            this.refreshAll();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    // ========== НАСТРОЙКИ ==========
    showSettings() {
        // Удаляем существующую модалку если есть
        this.closeSettings();
        
        // Создаем модальное окно с настройками
        const modal = document.createElement('div');
        modal.id = 'monitoring-settings-modal';
        modal.className = 'settings-modal';
        modal.innerHTML = `
            <div class="settings-overlay" onclick="galaxyMonitoring.closeSettings()"></div>
            <div class="settings-content">
                <div class="settings-header">
                    <h3>Настройки мониторинга</h3>
                    <button class="settings-close" onclick="galaxyMonitoring.closeSettings()">✕</button>
                </div>
                <div class="settings-body">
                    <div class="settings-group">
                        <label>
                            <input type="checkbox" id="auto-refresh" checked>
                            Автообновление (каждые 30 сек)
                        </label>
                    </div>
                    <div class="settings-group">
                        <label>
                            <input type="checkbox" id="notifications" checked>
                            Уведомления
                        </label>
                    </div>
                    <div class="settings-group">
                        <label>WebSocket URL:</label>
                        <input type="text" id="ws-url" value="${this.wsUrl}" class="settings-input">
                    </div>
                    <div class="settings-group">
                        <label>API URL:</label>
                        <input type="text" id="api-url" value="${this.apiBase}" class="settings-input">
                    </div>
                </div>
                <div class="settings-actions">
                    <button class="settings-btn settings-btn-primary" onclick="galaxyMonitoring.saveSettings()">Сохранить</button>
                    <button class="settings-btn" onclick="galaxyMonitoring.closeSettings()">Отмена</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    saveSettings() {
        // Сохраняем настройки
        const autoRefresh = document.getElementById('auto-refresh').checked;
        const notifications = document.getElementById('notifications').checked;
        const wsUrl = document.getElementById('ws-url').value;
        const apiUrl = document.getElementById('api-url').value;
        
        this.wsUrl = wsUrl;
        this.apiBase = apiUrl;
        
        if (autoRefresh) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }
        
        localStorage.setItem('galaxy-monitoring-settings', JSON.stringify({
            autoRefresh,
            notifications,
            wsUrl,
            apiUrl
        }));
        
        this.closeSettings();
        this.showNotification('Настройки сохранены', 'success');
    }

    closeSettings() {
        const modal = document.getElementById('monitoring-settings-modal');
        if (modal) {
            modal.remove();
        }
    }

    togglePanel() {
        const content = document.getElementById('monitoring-content');
        if (content) {
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }
    }

    // ========== УВЕДОМЛЕНИЯ ==========
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // ========== ДЕСТРУКТОР ==========
    destroy() {
        this.stopAutoRefresh();
        
        if (this.ws) {
            this.ws.close();
        }
        
        document.getElementById('galaxy-monitoring-panel')?.remove();
        document.getElementById('monitoring-styles')?.remove();
        
        this.initialized = false;
    }
}

// Создаем глобальный экземпляр
window.galaxyMonitoring = new GalaxyMonitoringModule();

// Автозапуск при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Ждем 2 секунды и инициализируем
    setTimeout(() => {
        galaxyMonitoring.init();
    }, 2000);
});