#!/usr/bin/env node
"use strict";
/**
 * 🤖 GALAXY ANALYTICS BASE AGENT
 *
 * Базовый агент с подключением к Redis Message Bus и PostgreSQL
 * - Получает команды из Redis
 * - Выполняет базовые операции
 * - Сохраняет результаты в PostgreSQL
 * - Отправляет heartbeat каждые 30 секунд
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const redis_1 = require("redis");
const pg_1 = require("pg");
const process = __importStar(require("process"));
class GalaxyBaseAgent {
    constructor(config) {
        this.isRunning = false;
        this.config = config;
        this.redis = (0, redis_1.createClient)({
            socket: {
                host: config.redis.host,
                port: config.redis.port
            },
            password: config.redis.password
        });
        this.postgres = new pg_1.Client({
            host: config.postgres.host,
            port: config.postgres.port,
            database: config.postgres.database,
            user: config.postgres.user,
            password: config.postgres.password
        });
    }
    async start() {
        try {
            console.log(`🚀 Запуск агента ${this.config.agent.name} (${this.config.agent.id})`);
            await this.connectRedis();
            await this.connectPostgres();
            await this.registerAgent();
            await this.startHeartbeat();
            await this.listenForCommands();
            this.isRunning = true;
            console.log('✅ Агент успешно запущен и готов к работе');
        }
        catch (error) {
            console.error('❌ Ошибка запуска агента:', error);
            await this.shutdown();
            process.exit(1);
        }
    }
    async connectRedis() {
        try {
            await this.redis.connect();
            console.log('✅ Подключение к Redis установлено');
        }
        catch (error) {
            throw new Error(`Ошибка подключения к Redis: ${error}`);
        }
    }
    async connectPostgres() {
        try {
            await this.postgres.connect();
            console.log('✅ Подключение к PostgreSQL установлено');
        }
        catch (error) {
            throw new Error(`Ошибка подключения к PostgreSQL: ${error}`);
        }
    }
    async registerAgent() {
        try {
            const query = `
        INSERT INTO agents.registry (agent_id, agent_name, agent_type, status, registered_at, last_heartbeat)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (agent_id) DO UPDATE SET
          agent_name = $2,
          status = $4,
          last_heartbeat = $6
      `;
            await this.postgres.query(query, [
                this.config.agent.id,
                this.config.agent.name,
                'base',
                'active',
                new Date(),
                new Date()
            ]);
            console.log('✅ Агент зарегистрирован в PostgreSQL');
        }
        catch (error) {
            throw new Error(`Ошибка регистрации агента: ${error}`);
        }
    }
    async startHeartbeat() {
        this.heartbeatTimer = setInterval(async () => {
            try {
                await this.sendHeartbeat();
            }
            catch (error) {
                console.error('❌ Ошибка отправки heartbeat:', error);
            }
        }, this.config.agent.heartbeatInterval);
        console.log(`✅ Heartbeat запущен (интервал: ${this.config.agent.heartbeatInterval}ms)`);
    }
    async sendHeartbeat() {
        const heartbeat = {
            agentId: this.config.agent.id,
            timestamp: new Date().toISOString(),
            status: 'alive',
            memoryUsage: process.memoryUsage(),
            uptime: process.uptime()
        };
        await this.redis.publish('agent:heartbeat', JSON.stringify(heartbeat));
        await this.postgres.query('UPDATE agents.registry SET last_heartbeat = $1 WHERE agent_id = $2', [new Date(), this.config.agent.id]);
    }
    async listenForCommands() {
        const subscriber = this.redis.duplicate();
        await subscriber.connect();
        const channelName = `agent:${this.config.agent.id}:commands`;
        await subscriber.subscribe(channelName, async (message) => {
            try {
                const command = JSON.parse(message);
                console.log(`📨 Получена команда: ${command.type} (ID: ${command.id})`);
                await this.executeCommand(command);
            }
            catch (error) {
                console.error('❌ Ошибка обработки команды:', error);
            }
        });
        console.log(`👂 Слушаю команды на канале: ${channelName}`);
    }
    async executeCommand(command) {
        const startTime = Date.now();
        let result;
        try {
            let commandResult;
            switch (command.type) {
                case 'ping':
                    commandResult = { message: 'pong', timestamp: new Date().toISOString() };
                    break;
                case 'analyze':
                    commandResult = await this.analyzeData(command.payload);
                    break;
                case 'status':
                    commandResult = {
                        agentId: this.config.agent.id,
                        status: 'running',
                        uptime: process.uptime(),
                        memory: process.memoryUsage()
                    };
                    break;
                default:
                    throw new Error(`Неизвестный тип команды: ${command.type}`);
            }
            result = {
                commandId: command.id,
                status: 'success',
                result: commandResult,
                executedAt: new Date().toISOString(),
                duration: Date.now() - startTime
            };
        }
        catch (error) {
            result = {
                commandId: command.id,
                status: 'error',
                error: error instanceof Error ? error.message : String(error),
                executedAt: new Date().toISOString(),
                duration: Date.now() - startTime
            };
        }
        await this.saveCommandResult(result);
        await this.sendCommandResult(result);
    }
    async analyzeData(payload) {
        console.log('🔍 Анализируем данные...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        return {
            analysis: 'completed',
            dataPoints: payload?.data?.length || 0,
            timestamp: new Date().toISOString(),
            summary: 'Базовый анализ выполнен успешно'
        };
    }
    async saveCommandResult(result) {
        const query = `
      INSERT INTO tasks.command_results (command_id, agent_id, status, result, error, executed_at, duration)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
    `;
        await this.postgres.query(query, [
            result.commandId,
            this.config.agent.id,
            result.status,
            JSON.stringify(result.result),
            result.error,
            result.executedAt,
            result.duration
        ]);
    }
    async sendCommandResult(result) {
        await this.redis.publish('agent:results', JSON.stringify(result));
        console.log(`📤 Результат команды ${result.commandId} отправлен (${result.status})`);
    }
    async shutdown() {
        console.log('🛑 Завершение работы агента...');
        this.isRunning = false;
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        try {
            await this.postgres.query('UPDATE agents.registry SET status = $1 WHERE agent_id = $2', ['inactive', this.config.agent.id]);
        }
        catch (error) {
            console.error('❌ Ошибка обновления статуса агента:', error);
        }
        await this.redis.quit();
        await this.postgres.end();
        console.log('✅ Агент успешно завершен');
    }
}
// Конфигурация по умолчанию
const defaultConfig = {
    redis: {
        host: 'localhost',
        port: 6379,
        password: 'galaxy_redis_secure_2024'
    },
    postgres: {
        host: 'localhost',
        port: 5432,
        database: 'galaxy_analytics',
        user: 'galaxy_admin',
        password: 'galaxy_secure_pass_2024'
    },
    agent: {
        id: `agent-${Date.now()}`,
        name: 'Galaxy Base Agent',
        heartbeatInterval: 30000
    }
};
// Запуск агента
if (require.main === module) {
    const agent = new GalaxyBaseAgent(defaultConfig);
    // Обработка сигналов завершения
    process.on('SIGINT', async () => {
        console.log('\n🛑 Получен сигнал SIGINT');
        await agent.shutdown();
        process.exit(0);
    });
    process.on('SIGTERM', async () => {
        console.log('\n🛑 Получен сигнал SIGTERM');
        await agent.shutdown();
        process.exit(0);
    });
    agent.start().catch(console.error);
}
exports.default = GalaxyBaseAgent;
//# sourceMappingURL=agent.js.map