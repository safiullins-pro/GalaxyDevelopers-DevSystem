
// PostgreSQL configuration - REAL CONNECTION
const { Pool } = require('pg');
const pgPool = new Pool({
    host: process.env.PG_HOST || 'localhost',
    port: process.env.PG_PORT || 5432,
    database: process.env.PG_DATABASE || 'galaxydevelopers',
    user: process.env.PG_USER || 'postgres',
    password: process.env.PG_PASSWORD || 'postgres'
});

// Redis configuration - REAL CACHE
const redis = require('redis');
const redisClient = redis.createClient({
    url: process.env.REDIS_URL || 'redis://localhost:6379'
});

redisClient.connect().catch(console.error);

module.exports = { pgPool, redisClient };
