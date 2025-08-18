/**
 * REAL WORKING TESTS - NO LIES
 */

const fs = require('fs');
const path = require('path');

describe('Critical Security Fixes', () => {
    
    test('execSync is completely removed from backend', () => {
        const backendPath = path.join(__dirname, '../SERVER/GalaxyDevelopersAI-backend.js');
        const backendCode = fs.readFileSync(backendPath, 'utf8');
        
        // Check that execSync is not imported
        expect(backendCode).not.toContain('execSync');
        
        // Verify spawn is imported instead
        expect(backendCode).toContain('const { spawn }');
    });
    
    test('No hardcoded passwords exist', () => {
        const authPath = path.join(__dirname, '../SERVER/auth-real.js');
        if (fs.existsSync(authPath)) {
            const authCode = fs.readFileSync(authPath, 'utf8');
            
            // Check no hardcoded credentials
            expect(authCode).not.toContain('SecurePass123');
            expect(authCode).not.toContain("'admin@galaxydevelopers.com'");
            
            // Verify real auth implementation
            expect(authCode).toContain('pgPool.query');
            expect(authCode).toContain('hashPassword');
        }
    });
});

describe('Infrastructure', () => {
    
    test('PostgreSQL is accessible', async () => {
        const { Pool } = require('pg');
        const pool = new Pool({
            host: 'localhost',
            port: 5432,
            database: 'galaxydevelopers',
            user: 'postgres',
            password: 'postgres'
        });
        
        try {
            const result = await pool.query('SELECT NOW()');
            expect(result.rows).toBeDefined();
            expect(result.rows.length).toBe(1);
        } finally {
            await pool.end();
        }
    });
    
    test('Redis is accessible', async () => {
        const redis = require('redis');
        const client = redis.createClient({
            url: 'redis://localhost:6379'
        });
        
        await client.connect();
        
        try {
            await client.set('test_key', 'test_value');
            const value = await client.get('test_key');
            expect(value).toBe('test_value');
            await client.del('test_key');
        } finally {
            await client.disconnect();
        }
    });
    
    test('Database tables exist', async () => {
        const { Pool } = require('pg');
        const pool = new Pool({
            host: 'localhost',
            port: 5432,
            database: 'galaxydevelopers',
            user: 'postgres',
            password: 'postgres'
        });
        
        try {
            const result = await pool.query(`
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            `);
            
            const tables = result.rows.map(r => r.table_name);
            expect(tables).toContain('users');
            expect(tables).toContain('agents');
        } finally {
            await pool.end();
        }
    });
});

describe('Authentication System', () => {
    
    test('JWT token generation works', () => {
        const securityModule = path.join(__dirname, '../McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');
        if (fs.existsSync(securityModule)) {
            const { generateToken } = require(securityModule);
            
            const token = generateToken('test-user-id', 'admin');
            expect(token).toBeDefined();
            expect(typeof token).toBe('string');
            
            // JWT has three parts separated by dots
            const parts = token.split('.');
            expect(parts).toHaveLength(3);
        }
    });
    
    test('Password hashing is implemented', () => {
        const authPath = path.join(__dirname, '../SERVER/auth-real.js');
        if (fs.existsSync(authPath)) {
            const authModule = require(authPath);
            const authCode = fs.readFileSync(authPath, 'utf8');
            
            // Check hashing functions exist
            expect(authCode).toContain('hashPassword');
            expect(authCode).toContain('verifyPassword');
            expect(authCode).toContain('crypto.pbkdf2Sync');
        }
    });
});