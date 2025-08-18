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

import { createClient, RedisClientType } from 'redis';
import { Client as PgClient } from 'pg';
import * as process from 'process';

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

interface Command {
  id: string;
  type: string;
  payload: any;
  timestamp: string;
  sender?: string;
}

interface CommandResult {
  commandId: string;
  status: 'success' | 'error';
  result?: any;
  error?: string;
  executedAt: string;
  duration: number;
}

class GalaxyBaseAgent {
  private redis: RedisClientType;
  private postgres: PgClient;
  private config: AgentConfig;
  private isRunning: boolean = false;
  private heartbeatTimer?: NodeJS.Timeout;

  constructor(config: AgentConfig) {
    this.config = config;
    
    this.redis = createClient({
      socket: {
        host: config.redis.host,
        port: config.redis.port
      },
      password: config.redis.password
    });

    this.postgres = new PgClient({
      host: config.postgres.host,
      port: config.postgres.port,
      database: config.postgres.database,
      user: config.postgres.user,
      password: config.postgres.password
    });
  }

  async start(): Promise<void> {
    try {
      console.log(`🚀 Запуск агента ${this.config.agent.name} (${this.config.agent.id})`);

      await this.connectRedis();
      await this.connectPostgres();
      await this.registerAgent();
      await this.startHeartbeat();
      await this.listenForCommands();

      this.isRunning = true;
      console.log('✅ Агент успешно запущен и готов к работе');

    } catch (error) {
      console.error('❌ Ошибка запуска агента:', error);
      await this.shutdown();
      process.exit(1);
    }
  }

  private async connectRedis(): Promise<void> {
    try {
      await this.redis.connect();
      console.log('✅ Подключение к Redis установлено');
    } catch (error) {
      throw new Error(`Ошибка подключения к Redis: ${error}`);
    }
  }

  private async connectPostgres(): Promise<void> {
    try {
      await this.postgres.connect();
      console.log('✅ Подключение к PostgreSQL установлено');
    } catch (error) {
      throw new Error(`Ошибка подключения к PostgreSQL: ${error}`);
    }
  }

  private async registerAgent(): Promise<void> {
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
    } catch (error) {
      throw new Error(`Ошибка регистрации агента: ${error}`);
    }
  }

  private async startHeartbeat(): Promise<void> {
    this.heartbeatTimer = setInterval(async () => {
      try {
        await this.sendHeartbeat();
      } catch (error) {
        console.error('❌ Ошибка отправки heartbeat:', error);
      }
    }, this.config.agent.heartbeatInterval);

    console.log(`✅ Heartbeat запущен (интервал: ${this.config.agent.heartbeatInterval}ms)`);
  }

  private async sendHeartbeat(): Promise<void> {
    const heartbeat = {
      agentId: this.config.agent.id,
      timestamp: new Date().toISOString(),
      status: 'alive',
      memoryUsage: process.memoryUsage(),
      uptime: process.uptime()
    };

    await this.redis.publish('agent:heartbeat', JSON.stringify(heartbeat));

    await this.postgres.query(
      'UPDATE agents.registry SET last_heartbeat = $1 WHERE agent_id = $2',
      [new Date(), this.config.agent.id]
    );
  }

  private async listenForCommands(): Promise<void> {
    const subscriber = this.redis.duplicate();
    await subscriber.connect();

    const channelName = `agent:${this.config.agent.id}:commands`;
    
    await subscriber.subscribe(channelName, async (message) => {
      try {
        const command: Command = JSON.parse(message);
        console.log(`📨 Получена команда: ${command.type} (ID: ${command.id})`);
        
        await this.executeCommand(command);
      } catch (error) {
        console.error('❌ Ошибка обработки команды:', error);
      }
    });

    console.log(`👂 Слушаю команды на канале: ${channelName}`);
  }

  private async executeCommand(command: Command): Promise<void> {
    const startTime = Date.now();
    let result: CommandResult;

    try {
      let commandResult: any;

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

    } catch (error) {
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

  private async analyzeData(payload: any): Promise<any> {
    console.log('🔍 Анализируем данные...');
    
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      analysis: 'completed',
      dataPoints: payload?.data?.length || 0,
      timestamp: new Date().toISOString(),
      summary: 'Базовый анализ выполнен успешно'
    };
  }

  private async saveCommandResult(result: CommandResult): Promise<void> {
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

  private async sendCommandResult(result: CommandResult): Promise<void> {
    await this.redis.publish('agent:results', JSON.stringify(result));
    console.log(`📤 Результат команды ${result.commandId} отправлен (${result.status})`);
  }

  async shutdown(): Promise<void> {
    console.log('🛑 Завершение работы агента...');
    
    this.isRunning = false;
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    try {
      await this.postgres.query(
        'UPDATE agents.registry SET status = $1 WHERE agent_id = $2',
        ['inactive', this.config.agent.id]
      );
    } catch (error) {
      console.error('❌ Ошибка обновления статуса агента:', error);
    }

    await this.redis.quit();
    await this.postgres.end();
    
    console.log('✅ Агент успешно завершен');
  }
}

// Конфигурация по умолчанию
const defaultConfig: AgentConfig = {
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

export default GalaxyBaseAgent;