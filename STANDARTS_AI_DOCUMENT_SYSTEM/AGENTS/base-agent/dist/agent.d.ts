#!/usr/bin/env node
/**
 * 🤖 GALAXY ANALYTICS BASE AGENT
 *
 * Базовый агент с подключением к Redis Message Bus и PostgreSQL
 * - Получает команды из Redis
 * - Выполняет базовые операции
 * - Сохраняет результаты в PostgreSQL
 * - Отправляет heartbeat каждые 30 секунд
 */
interface AgentConfig {
    redis: {
        host: string;
        port: number;
        password: string;
    };
    postgres: {
        host: string;
        port: number;
        database: string;
        user: string;
        password: string;
    };
    agent: {
        id: string;
        name: string;
        heartbeatInterval: number;
    };
}
declare class GalaxyBaseAgent {
    private redis;
    private postgres;
    private config;
    private isRunning;
    private heartbeatTimer?;
    constructor(config: AgentConfig);
    start(): Promise<void>;
    private connectRedis;
    private connectPostgres;
    private registerAgent;
    private startHeartbeat;
    private sendHeartbeat;
    private listenForCommands;
    private executeCommand;
    private analyzeData;
    private saveCommandResult;
    private sendCommandResult;
    shutdown(): Promise<void>;
}
export default GalaxyBaseAgent;
//# sourceMappingURL=agent.d.ts.map