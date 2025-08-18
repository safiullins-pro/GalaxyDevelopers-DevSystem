import { createClient } from 'redis';
import { exec } from 'child_process';

const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = parseInt(process.env.REDIS_PORT || '6379', 10);
const AGENT_ID = 'ai_code_auditor';

// --- Основные каналы Redis ---
const CHANNELS = {
    FILE_CHANGES: 'file_changes',
    AGENT_PING: 'agent_ping',
    AGENT_PONG: 'agent_pong',
    ANALYSIS_RESULTS: 'analysis_results',
    BLOCKING_REQUESTS: 'blocking_requests'
};

class AiCodeAuditorAgent {
    private redisClient: any;
    private subscriber: any;
    private lastHeartbeat: number = 0;
    private heartbeatInterval: number = 30 * 1000; // 30 секунд

    constructor() {
        this.redisClient = createClient({
            socket: {
                host: REDIS_HOST,
                port: REDIS_PORT,
            }
        });

        this.subscriber = this.redisClient.duplicate();

        this.redisClient.on('error', (err: Error) => console.error('Redis Client Error', err));
        this.subscriber.on('error', (err: Error) => console.error('Redis Subscriber Error', err));
    }

    public async start(): Promise<void> {
        console.log(`🤖 ${AGENT_ID} запускается...`);
        await this.connect();
        await this.subscribeToChannels();
        this.setupHeartbeat();
        console.log(`✅ ${AGENT_ID} запущен и слушает каналы.`);
    }

    private async connect(): Promise<void> {
        try {
            await this.redisClient.connect();
            await this.subscriber.connect();
            console.log('Успешное подключение к Redis.');
        } catch (err) {
            console.error('Не удалось подключиться к Redis:', err);
            process.exit(1);
        }
    }

    private async subscribeToChannels(): Promise<void> {
        console.log(`Подписка на каналы: ${CHANNELS.FILE_CHANGES}, ${CHANNELS.AGENT_PING}`);
        await this.subscriber.subscribe(CHANNELS.FILE_CHANGES, (message: string) => this.handleFileChange(message));
        await this.subscriber.subscribe(CHANNELS.AGENT_PING, (message: string) => this.handlePing(message));
    }

    private async handleFileChange(message: string): Promise<void> {
        try {
            const event = JSON.parse(message);
            console.log(`
📄 Получено событие изменения файла: ${event.file_path}`);
            
            // 1. Получение ТЗ и контекста из ChromaDB (эмуляция)
            const requirements = await this.getRequirementsFromChromaDB(event.file_path);
            console.log('   - Получены требования из ChromaDB.');

            // 2. Анализ кода с помощью AI
            console.log('   - Запуск AI анализа кода...');
            const analysisResult = await this.analyzeCode(event.file_content, requirements);
            console.log(`   - Анализ завершен. Соответствие ТЗ: ${analysisResult.tzComplianceScore * 100}%, Качество: ${analysisResult.qualityScore * 100}%`);

            // 3. Сохранение результата в PostgreSQL (эмуляция)
            await this.saveResultToPostgres(event.id, analysisResult);
            console.log('   - Результаты анализа сохранены в PostgreSQL.');

            // 4. Публикация результата
            await this.redisClient.publish(CHANNELS.ANALYSIS_RESULTS, JSON.stringify(analysisResult));

            // 5. Блокировка коммита при нарушениях
            if (analysisResult.tzComplianceScore < 0.8 || analysisResult.qualityScore < 0.7) {
                console.error(`   - 🚫 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ НАРУШЕНИЯ!`);
                await this.requestCommitBlock(event.commit_id);
            }

        } catch (err) {
            console.error('Ошибка при обработке изменения файла:', err);
        }
    }

    private async handlePing(message: string): Promise<void> {
        try {
            const pingData = JSON.parse(message);
            if (pingData.agent_id === AGENT_ID) {
                console.log('❤️ Получен ping, отвечаю pong...');
                const pongMessage = JSON.stringify({ agent_id: AGENT_ID, status: 'alive', timestamp: new Date().toISOString() });
                await this.redisClient.lPush(CHANNELS.AGENT_PONG, pongMessage);
            }
        } catch (err) {
            console.error('Ошибка при обработке ping:', err);
        }
    }

    private async getRequirementsFromChromaDB(filePath: string): Promise<any> {
        // Эмуляция запроса к ChromaDB
        return new Promise(resolve => setTimeout(() => resolve({
            related_ticket: 'JIRA-123',
            acceptance_criteria: ['Function must return a number', 'Must handle null input'],
        }), 200));
    }

    private async analyzeCode(code: string, requirements: any): Promise<any> {
        // Эмуляция вызова AI (OpenAI/Anthropic/Llama)
        // В реальном приложении здесь будет HTTP-запрос к модели
        return new Promise(resolve => setTimeout(() => {
            const violations = [];
            if (code.length < 50) violations.push('Code is too short');
            
            resolve({
                tzComplianceScore: code.includes('return') ? 0.9 : 0.5,
                qualityScore: 0.85,
                securityScore: 0.95,
                violations: violations,
                recommendations: ['Add more comments'],
                analyzedAt: new Date().toISOString()
            });
        }, 1000));
    }

    private async saveResultToPostgres(eventId: number, result: any): Promise<void> {
        // Эмуляция записи в PostgreSQL
        console.log(`   - (Эмуляция) Сохранение результата для file_event_id: ${eventId}`);
        return Promise.resolve();
    }

    private async requestCommitBlock(commitId: string): Promise<void> {
        const blockMessage = JSON.stringify({ commit_id: commitId, reason: 'AI Auditor found critical issues.' });
        await this.redisClient.publish(CHANNELS.BLOCKING_REQUESTS, blockMessage);
        console.log(`   - Отправлен запрос на блокировку коммита ${commitId}`);
    }

    private setupHeartbeat(): void {
        setInterval(async () => {
            const now = Date.now();
            if (now - this.lastHeartbeat > this.heartbeatInterval) {
                const heartbeatMessage = JSON.stringify({ agent_id: AGENT_ID, timestamp: new Date().toISOString() });
                await this.redisClient.hSet('agents:health', AGENT_ID, heartbeatMessage);
                this.lastHeartbeat = now;
                console.log('❤️ Отправлен heartbeat');
            }
        }, this.heartbeatInterval);
    }
}

const agent = new AiCodeAuditorAgent();
agent.start();
