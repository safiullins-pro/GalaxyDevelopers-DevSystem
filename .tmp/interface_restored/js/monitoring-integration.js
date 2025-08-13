/**
 * СИСТЕМА МОНИТОРИНГА И ПРОВЕРКИ
 * Интеграция с файловым наблюдателем и pipeline
 */

class MonitoringSystem {
    constructor() {
        this.websocket = null;
        this.fsWatcher = null;
        this.pipelineStatus = {};
        this.agents = {};
        this.checks = [];
        this.isRunning = false;
        
        this.init();
    }

    init() {
        console.log('🚀 Инициализация системы мониторинга...');
        
        // Подключение к WebSocket для real-time обновлений
        this.connectWebSocket();
        
        // Запуск файлового мониторинга
        this.startFileWatcher();
        
        // Инициализация pipeline проверок
        this.initPipelineChecks();
        
        // Запуск системы проверок
        this.startMonitoring();
    }

    connectWebSocket() {
        try {
            this.websocket = new WebSocket('ws://localhost:8765/monitoring');
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket подключен');
                this.updateStatus('connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMonitoringEvent(data);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket ошибка:', error);
                this.updateStatus('error');
                // Переподключение через 5 секунд
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket отключен');
                this.updateStatus('disconnected');
                // Автоматическое переподключение
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        } catch (error) {
            console.error('Не удалось создать WebSocket:', error);
            // Fallback на polling
            this.startPolling();
        }
    }

    startFileWatcher() {
        // Отслеживаемые директории
        const watchPaths = [
            '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/',
            '/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/',
            '/Users/safiullins_pro/Documents/Александр Толстых/'
        ];
        
        // Запуск fswatch через fetch API
        fetch('/api/monitoring/start-watcher', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paths: watchPaths,
                excludePatterns: [
                    '.DS_Store',
                    '*.tmp',
                    '*.swp',
                    '.git/',
                    'node_modules/'
                ]
            })
        }).then(response => response.json())
          .then(data => {
              console.log('📂 Файловый мониторинг запущен:', data);
              this.fsWatcher = data.watcherId;
          })
          .catch(error => {
              console.error('Ошибка запуска файлового мониторинга:', error);
          });
    }

    initPipelineChecks() {
        // Определение этапов проверки
        this.checks = [
            {
                id: 'file-change',
                name: 'Обнаружение изменений',
                status: 'idle',
                handler: this.checkFileChanges.bind(this)
            },
            {
                id: 'syntax-check',
                name: 'Проверка синтаксиса',
                status: 'idle',
                handler: this.checkSyntax.bind(this)
            },
            {
                id: 'security-scan',
                name: 'Сканирование безопасности',
                status: 'idle',
                handler: this.checkSecurity.bind(this)
            },
            {
                id: 'compliance-check',
                name: 'Проверка соответствия',
                status: 'idle',
                handler: this.checkCompliance.bind(this)
            },
            {
                id: 'ai-validation',
                name: 'AI валидация',
                status: 'idle',
                handler: this.checkWithAI.bind(this)
            },
            {
                id: 'integration-test',
                name: 'Интеграционный тест',
                status: 'idle',
                handler: this.runIntegrationTest.bind(this)
            }
        ];
    }

    startMonitoring() {
        if (this.isRunning) {
            console.log('⚠️ Мониторинг уже запущен');
            return;
        }
        
        this.isRunning = true;
        console.log('🎯 Система проверок запущена');
        
        // Запуск периодических проверок
        this.monitoringInterval = setInterval(() => {
            this.runChecks();
        }, 5000); // каждые 5 секунд
        
        // Немедленный запуск первой проверки
        this.runChecks();
    }

    async runChecks() {
        console.log('🔍 Запуск цикла проверок...');
        
        for (const check of this.checks) {
            try {
                this.updateCheckStatus(check.id, 'running');
                const result = await check.handler();
                
                if (result.success) {
                    this.updateCheckStatus(check.id, 'passed');
                } else {
                    this.updateCheckStatus(check.id, 'failed', result.error);
                }
            } catch (error) {
                console.error(`Ошибка в проверке ${check.name}:`, error);
                this.updateCheckStatus(check.id, 'error', error.message);
            }
        }
        
        this.updatePipelineUI();
    }

    async checkFileChanges() {
        // Проверка изменений файлов
        const response = await fetch('/api/monitoring/file-changes');
        const changes = await response.json();
        
        if (changes.length > 0) {
            console.log(`📝 Обнаружено ${changes.length} изменений`);
            this.processFileChanges(changes);
        }
        
        return { success: true, changes: changes.length };
    }

    async checkSyntax() {
        // Проверка синтаксиса кода
        const response = await fetch('/api/monitoring/syntax-check');
        const result = await response.json();
        
        if (result.errors && result.errors.length > 0) {
            console.error('❌ Найдены синтаксические ошибки:', result.errors);
            return { success: false, error: `${result.errors.length} ошибок` };
        }
        
        return { success: true };
    }

    async checkSecurity() {
        // Проверка безопасности
        const response = await fetch('/api/monitoring/security-scan');
        const result = await response.json();
        
        if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            console.warn('⚠️ Найдены уязвимости:', result.vulnerabilities);
            return { success: false, error: `${result.vulnerabilities.length} уязвимостей` };
        }
        
        return { success: true };
    }

    async checkCompliance() {
        // Проверка соответствия стандартам
        const standards = ['ISO27001', 'ITIL4', 'COBIT'];
        const results = [];
        
        for (const standard of standards) {
            const response = await fetch(`/api/monitoring/compliance/${standard}`);
            const result = await response.json();
            results.push(result);
        }
        
        const failed = results.filter(r => !r.compliant);
        if (failed.length > 0) {
            return { success: false, error: `Не соответствует ${failed.length} стандартам` };
        }
        
        return { success: true };
    }

    async checkWithAI() {
        // AI валидация через агентов
        const response = await fetch('/api/agents/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agents: ['ResearchAgent', 'ReviewerAgent'],
                context: this.getCurrentContext()
            })
        });
        
        const result = await response.json();
        
        if (result.score < 95) {
            return { success: false, error: `Score: ${result.score}%` };
        }
        
        return { success: true, score: result.score };
    }

    async runIntegrationTest() {
        // Запуск интеграционных тестов
        const response = await fetch('/api/monitoring/integration-test');
        const result = await response.json();
        
        if (result.failed > 0) {
            return { success: false, error: `${result.failed} тестов провалено` };
        }
        
        return { success: true, passed: result.passed };
    }

    processFileChanges(changes) {
        changes.forEach(change => {
            // Обновление UI для каждого изменения
            this.addFileChangeToUI(change);
            
            // Запуск агента для обработки
            if (change.type === 'modified' || change.type === 'created') {
                this.triggerAgentProcessing(change);
            }
        });
    }

    triggerAgentProcessing(change) {
        // Определение какой агент должен обработать изменение
        const agentMap = {
            '.md': 'ComposerAgent',
            '.py': 'ReviewerAgent',
            '.js': 'ReviewerAgent',
            '.json': 'IntegratorAgent',
            '.yaml': 'IntegratorAgent'
        };
        
        const ext = change.path.substring(change.path.lastIndexOf('.'));
        const agent = agentMap[ext] || 'ResearchAgent';
        
        // Отправка задачи агенту
        fetch('/api/agents/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent: agent,
                file: change.path,
                action: change.type
            })
        });
    }

    handleMonitoringEvent(data) {
        console.log('📡 Событие мониторинга:', data);
        
        switch (data.type) {
            case 'file_change':
                this.processFileChanges([data.change]);
                break;
            case 'agent_status':
                this.updateAgentStatus(data.agent, data.status);
                break;
            case 'pipeline_update':
                this.updatePipelineStatus(data.stage, data.status);
                break;
            case 'alert':
                this.showAlert(data.message, data.severity);
                break;
        }
    }

    updateCheckStatus(checkId, status, error = null) {
        const check = this.checks.find(c => c.id === checkId);
        if (check) {
            check.status = status;
            check.error = error;
            check.lastRun = new Date().toISOString();
        }
    }

    updatePipelineUI() {
        // Обновление UI pipeline в sidebar
        const pipelineStages = document.querySelectorAll('.stage');
        
        this.checks.forEach((check, index) => {
            if (pipelineStages[index]) {
                const stage = pipelineStages[index];
                const statusIcon = stage.querySelector('.stage-status');
                
                // Удаление старых классов
                stage.classList.remove('active', 'error', 'warning');
                
                switch (check.status) {
                    case 'running':
                        stage.classList.add('active');
                        statusIcon.textContent = '⚙';
                        break;
                    case 'passed':
                        statusIcon.textContent = '✓';
                        break;
                    case 'failed':
                        stage.classList.add('error');
                        statusIcon.textContent = '❌';
                        break;
                    case 'error':
                        stage.classList.add('warning');
                        statusIcon.textContent = '⚠️';
                        break;
                    default:
                        statusIcon.textContent = '⏸';
                }
            }
        });
    }

    updateAgentStatus(agentName, status) {
        const agentElements = document.querySelectorAll('.agent-item');
        
        agentElements.forEach(element => {
            if (element.textContent.includes(agentName)) {
                element.classList.remove('active', 'error');
                
                if (status === 'active') {
                    element.classList.add('active');
                } else if (status === 'error') {
                    element.classList.add('error');
                }
                
                const taskSpan = element.querySelector('.agent-task');
                if (taskSpan) {
                    taskSpan.textContent = status;
                }
            }
        });
    }

    updatePipelineStatus(stage, status) {
        const stageElement = document.querySelector(`[data-stage="${stage}"]`);
        if (stageElement) {
            stageElement.classList.remove('active', 'error');
            
            if (status === 'active') {
                stageElement.classList.add('active');
            } else if (status === 'error') {
                stageElement.classList.add('error');
            }
        }
    }

    addFileChangeToUI(change) {
        const chatArea = document.getElementById('chat-area');
        
        const notification = document.createElement('div');
        notification.className = 'file-change-notification';
        notification.innerHTML = `
            <div class="change-icon">📄</div>
            <div class="change-details">
                <div class="change-file">${change.path.split('/').pop()}</div>
                <div class="change-type">${change.type}</div>
                <div class="change-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        chatArea.appendChild(notification);
        
        // Автоматическая прокрутка вниз
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    showAlert(message, severity = 'info') {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${severity}`;
        alertContainer.innerHTML = `
            <span class="alert-icon">${severity === 'error' ? '❌' : severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
            <span class="alert-message">${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            alertContainer.remove();
        }, 5000);
    }

    getCurrentContext() {
        return {
            memory: window.GalaxyMemory ? window.GalaxyMemory.getContext() : {},
            pipeline: this.pipelineStatus,
            agents: this.agents,
            checks: this.checks
        };
    }

    startPolling() {
        // Fallback на polling если WebSocket недоступен
        console.log('📊 Запуск polling режима');
        
        setInterval(async () => {
            try {
                const response = await fetch('/api/monitoring/status');
                const data = await response.json();
                this.handleMonitoringEvent(data);
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 3000);
    }

    updateStatus(status) {
        const statusStrip = document.getElementById('status-strip');
        if (statusStrip) {
            statusStrip.className = `status-strip ${status}`;
        }
    }

    stop() {
        this.isRunning = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        if (this.websocket) {
            this.websocket.close();
        }
        
        console.log('🛑 Система мониторинга остановлена');
    }
}

// Инициализация системы мониторинга
const monitoring = new MonitoringSystem();

// Экспорт для глобального доступа
window.GalaxyMonitoring = monitoring;

console.log('🔥 Система проверки АКТИВИРОВАНА');