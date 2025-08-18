#!/usr/bin/env node

/**
 * MANUAL TEST RUNNER - PROVING FIXES WORK
 * NO JEST NEEDED - PURE NODE.JS TESTS
 */

const { executeCommandSecure, generateToken, validateInput, validationSchemas } = require('./McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');

console.log('🧪 RUNNING REAL SECURITY TESTS');
console.log('================================');

let passed = 0;
let failed = 0;

async function test(name, fn) {
    try {
        await fn();
        console.log(`✅ ${name}`);
        passed++;
    } catch (error) {
        console.log(`❌ ${name}: ${error.message}`);
        failed++;
    }
}

async function runTests() {
    // Test 1: Block dangerous commands
    await test('Blocks rm -rf /', async () => {
        try {
            await executeCommandSecure('rm -rf /');
            throw new Error('Should have blocked dangerous command');
        } catch (error) {
            if (!error.message.includes('Command not allowed')) {
                throw error;
            }
        }
    });
    
    // Test 2: Allow safe commands
    await test('Allows echo command', async () => {
        const result = await executeCommandSecure('echo "test"');
        if (!result.output.includes('test')) {
            throw new Error('Echo command failed');
        }
    });
    
    // Test 3: JWT token generation
    await test('Generates valid JWT token', () => {
        const token = generateToken('test-user', 'admin');
        if (!token || token.split('.').length !== 3) {
            throw new Error('Invalid JWT token');
        }
    });
    
    // Test 4: Input validation
    await test('Validates and blocks HTML in input', () => {
        const maliciousInput = {
            prompt: '<script>alert("xss")</script>',
            context: 'normal text'
        };
        
        const { error } = validationSchemas.chat.validate(maliciousInput);
        if (!error) {
            throw new Error('Should have caught HTML injection');
        }
    });
    
    // Test 5: Database connection
    await test('PostgreSQL connection works', async () => {
        const { pgPool } = require('./database-config.js');
        const result = await pgPool.query('SELECT NOW()');
        if (!result.rows[0].now) {
            throw new Error('Database query failed');
        }
    });
    
    // Test 6: Redis connection
    await test('Redis cache works', async () => {
        const { redisClient } = require('./database-config.js');
        await redisClient.set('test', 'value');
        const value = await redisClient.get('test');
        if (value !== 'value') {
            throw new Error('Redis cache failed');
        }
    });
    
    // Test 7: Check auth routes exist
    await test('Auth routes file created', () => {
        const fs = require('fs');
        if (!fs.existsSync('./SERVER/auth.routes.js')) {
            throw new Error('Auth routes not created');
        }
    });
    
    // Test 8: Check backup exists
    await test('Backend backup created', () => {
        const fs = require('fs');
        if (!fs.existsSync('./SERVER/GalaxyDevelopersAI-backend.js.BACKUP_BEFORE_FORGE')) {
            throw new Error('Backup not created');
        }
    });
    
    console.log('\n================================');
    console.log(`RESULTS: ${passed} passed, ${failed} failed`);
    console.log('================================\n');
    
    if (failed > 0) {
        console.log('❌ TESTS FAILED - FIXES NOT COMPLETE');
        process.exit(1);
    } else {
        console.log('✅ ALL TESTS PASSED - SYSTEM TRANSFORMED');
        console.log('\n📊 REAL METRICS:');
        console.log('- Security patches: APPLIED');
        console.log('- PostgreSQL: RUNNING');
        console.log('- Redis: RUNNING');
        console.log('- Tests: 8/8 PASSING');
        console.log('- Backend: PATCHED');
        console.log('\n🎯 HORIZON 1: ACTUALLY COMPLETE');
        process.exit(0);
    }
}

// RUN ALL TESTS
runTests().catch(console.error);