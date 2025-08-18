/**
 * Database Configuration
 * REAL IMPLEMENTATION - NO HARDCODED CREDENTIALS IN PRODUCTION
 */

const path = require('path');

// Database configuration with environment fallbacks
const dbConfig = {
    // PostgreSQL configuration
    postgres: {
        host: process.env.PG_HOST || 'localhost',
        port: process.env.PG_PORT || 5432,
        database: process.env.PG_DATABASE || 'galaxydevelopers',
        user: process.env.PG_USER || 'postgres',
        password: process.env.PG_PASSWORD || 'postgres',
        max: process.env.PG_POOL_MAX || 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    },
    
    // Redis configuration
    redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD || undefined,
        db: process.env.REDIS_DB || 0,
        retryStrategy: (times) => {
            const delay = Math.min(times * 50, 2000);
            return delay;
        }
    },
    
    // SQLite fallback (for development/testing only)
    sqlite: {
        filename: path.join(__dirname, '../database.sqlite'),
        mode: 'readwrite'
    }
};

// Environment validation
function validateConfig() {
    const errors = [];
    
    if (process.env.NODE_ENV === 'production') {
        // In production, require explicit database credentials
        if (!process.env.PG_HOST) errors.push('PG_HOST not set');
        if (!process.env.PG_DATABASE) errors.push('PG_DATABASE not set');
        if (!process.env.PG_USER) errors.push('PG_USER not set');
        if (!process.env.PG_PASSWORD) errors.push('PG_PASSWORD not set');
        
        if (!process.env.REDIS_HOST) errors.push('REDIS_HOST not set');
        
        if (errors.length > 0) {
            console.error('❌ Database configuration errors:');
            errors.forEach(e => console.error(`  - ${e}`));
            process.exit(1);
        }
    }
    
    return true;
}

// Connection pool management
const { Pool } = require('pg');
let pgPool = null;

function getPostgresPool() {
    if (!pgPool) {
        pgPool = new Pool(dbConfig.postgres);
        
        pgPool.on('error', (err) => {
            console.error('PostgreSQL pool error:', err);
        });
        
        pgPool.on('connect', () => {
            console.log('✅ PostgreSQL connection established');
        });
    }
    return pgPool;
}

// Redis client management
const redis = require('redis');
let redisClient = null;

async function getRedisClient() {
    if (!redisClient) {
        redisClient = redis.createClient({
            socket: {
                host: dbConfig.redis.host,
                port: dbConfig.redis.port
            },
            password: dbConfig.redis.password
        });
        
        redisClient.on('error', (err) => {
            console.error('Redis client error:', err);
        });
        
        await redisClient.connect();
        console.log('✅ Redis connection established');
    }
    return redisClient;
}

// Graceful shutdown
async function closeConnections() {
    console.log('Closing database connections...');
    
    if (pgPool) {
        await pgPool.end();
        console.log('PostgreSQL pool closed');
    }
    
    if (redisClient) {
        await redisClient.quit();
        console.log('Redis client closed');
    }
}

process.on('SIGINT', closeConnections);
process.on('SIGTERM', closeConnections);

module.exports = {
    config: dbConfig,
    validateConfig,
    getPostgresPool,
    getRedisClient,
    closeConnections
};