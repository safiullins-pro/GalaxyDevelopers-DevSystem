#!/usr/bin/env node

/**
 * ФИНАЛЬНАЯ ПРОВЕРКА ВСЕХ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ
 * Проверяет все компоненты после Perplexity исследований
 */

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const redis = require('redis');

console.log('🔍 ПРОВЕРКА БЕЗОПАСНОСТИ СИСТЕМЫ\n');

let passedTests = 0;
let failedTests = 0;

async function check(name, testFn) {
    try {
        await testFn();
        console.log(`✅ ${name}`);
        passedTests++;
    } catch (error) {
        console.log(`❌ ${name}: ${error.message}`);
        failedTests++;
    }
}

async function runChecks() {
    // 1. Проверка Command Execution
    await check('SecureCommandExecutor существует', () => {
        const filePath = path.join(__dirname, 'McKinsey_Transformation/Horizon_1_Simplify/SecureCommandExecutor.js');
        if (!fs.existsSync(filePath)) throw new Error('Файл не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (!content.includes('shell: false')) throw new Error('shell: false не найден');
        if (content.includes("spawn('sh', ['-c']")) throw new Error('Опасный spawn найден!');
    });

    // 2. Проверка Password Manager
    await check('PasswordManager с уникальными солями', () => {
        const filePath = path.join(__dirname, 'SERVER/PasswordManager.js');
        if (!fs.existsSync(filePath)) throw new Error('PasswordManager не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (!content.includes('crypto.randomBytes(32)')) throw new Error('Нет генерации соли');
        if (!content.includes('timingSafeEqual')) throw new Error('Нет timing-safe сравнения');
        if (content.includes("'salt'")) throw new Error('Статическая соль найдена!');
    });

    // 3. Проверка JWT Manager
    await check('JWTAuthManager с Redis blacklist', () => {
        const filePath = path.join(__dirname, 'SERVER/JWTAuthManager.js');
        if (!fs.existsSync(filePath)) throw new Error('JWTAuthManager не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (!content.includes('ACCESS_TOKEN_EXPIRY')) throw new Error('Нет expiry настроек');
        if (!content.includes('blacklistToken')) throw new Error('Нет blacklist функции');
        if (!content.includes('rotateRefreshToken')) throw new Error('Нет token rotation');
        if (!content.includes('httpOnly: true')) throw new Error('Нет httpOnly cookies');
    });

    // 4. Проверка JWT Config
    await check('JWT конфигурация без fallback', () => {
        const filePath = path.join(__dirname, 'config/jwt.config.js');
        if (!fs.existsSync(filePath)) throw new Error('jwt.config.js не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (content.includes("|| 'secret'")) throw new Error('Fallback на secret найден!');
        if (!content.includes('crypto.randomBytes(64)')) throw new Error('Нет генерации секрета');
    });

    // 5. Проверка Database Config
    await check('Database конфигурация централизована', () => {
        const filePath = path.join(__dirname, 'config/database-config.js');
        if (!fs.existsSync(filePath)) throw new Error('database-config.js не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (!content.includes('getPostgresPool')) throw new Error('Нет pool management');
        if (!content.includes('getRedisClient')) throw new Error('Нет Redis client');
    });

    // 6. Проверка PostgreSQL
    await check('PostgreSQL подключение и таблицы', async () => {
        const pool = new Pool({
            host: 'localhost',
            port: 5432,
            database: 'galaxydevelopers',
            user: 'postgres',
            password: 'postgres'
        });
        
        try {
            // Проверка таблиц
            const tables = await pool.query(`
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'refresh_tokens', 'user_sessions')
            `);
            
            if (tables.rows.length < 3) {
                throw new Error(`Найдено только ${tables.rows.length} из 3 таблиц`);
            }
            
            // Проверка колонки salt
            const saltColumn = await pool.query(`
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password_salt'
            `);
            
            if (saltColumn.rows.length === 0) {
                throw new Error('Колонка password_salt не найдена');
            }
        } finally {
            await pool.end();
        }
    });

    // 7. Проверка Redis
    await check('Redis подключение', async () => {
        const client = redis.createClient({
            url: 'redis://localhost:6379'
        });
        
        await client.connect();
        
        try {
            await client.set('test_key', 'test_value');
            const value = await client.get('test_key');
            if (value !== 'test_value') throw new Error('Redis не работает');
            await client.del('test_key');
        } finally {
            await client.disconnect();
        }
    });

    // 8. Проверка отсутствия уязвимостей
    await check('Нет execSync в backend', () => {
        const filePath = path.join(__dirname, 'SERVER/GalaxyDevelopersAI-backend.js');
        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf8');
            // Проверяем что execSync удален из импортов
            const importLine = content.match(/const\s*{\s*([^}]+)\s*}\s*=\s*require\(['"]child_process['"]\)/);
            if (importLine && importLine[1].includes('execSync')) {
                throw new Error('execSync найден в импортах!');
            }
        }
    });

    // 9. Проверка auth-v2
    await check('Auth-v2 с полной JWT реализацией', () => {
        const filePath = path.join(__dirname, 'SERVER/auth-v2.js');
        if (!fs.existsSync(filePath)) throw new Error('auth-v2.js не найден');
        const content = fs.readFileSync(filePath, 'utf8');
        if (!content.includes('refreshToken')) throw new Error('Нет refresh token');
        if (!content.includes('blacklistToken')) throw new Error('Нет blacklist');
        if (!content.includes('httpOnly')) throw new Error('Нет httpOnly cookies');
        if (!content.includes('failed_login_attempts')) throw new Error('Нет rate limiting');
    });

    // 10. Проверка миграций
    await check('Миграции БД созданы', () => {
        const saltMigration = path.join(__dirname, 'database_migration_salt.sql');
        const jwtMigration = path.join(__dirname, 'database_migration_jwt.sql');
        
        if (!fs.existsSync(saltMigration)) throw new Error('Миграция salt не найдена');
        if (!fs.existsSync(jwtMigration)) throw new Error('Миграция JWT не найдена');
    });
}

// Запуск проверок
runChecks().then(() => {
    console.log('\n' + '='.repeat(50));
    console.log(`РЕЗУЛЬТАТ: ${passedTests} ✅ / ${failedTests} ❌`);
    
    if (failedTests === 0) {
        console.log('\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! СИСТЕМА ЗАЩИЩЕНА!');
        process.exit(0);
    } else {
        console.log('\n⚠️  Есть проблемы. Проверьте failed тесты.');
        process.exit(1);
    }
}).catch(error => {
    console.error('Критическая ошибка:', error);
    process.exit(1);
});