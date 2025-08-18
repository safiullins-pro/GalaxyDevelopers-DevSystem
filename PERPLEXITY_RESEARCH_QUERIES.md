# ЗАПРОСЫ ДЛЯ PERPLEXITY - КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ БЕЗОПАСНОСТИ

## P0-1: БЕЗОПАСНОЕ ВЫПОЛНЕНИЕ КОМАНД (spawn vs execSync)

**Запрос на английском для Perplexity:**
```
Node.js secure command execution without shell injection vulnerability

Current VULNERABLE code:
const { spawn } = require('child_process');
const child = spawn('sh', ['-c', command]); // THIS IS A BACKDOOR

Problems:
1. spawn('sh', ['-c', command]) is WORSE than execSync - it allows full shell access
2. User input can inject arbitrary commands
3. No input validation or sanitization

Show me:
1. Why spawn('sh', ['-c']) is dangerous (with examples of exploitation)
2. How to use spawn SAFELY without shell (spawn command with arguments array)
3. When execFile is better than spawn
4. Input validation techniques for command arguments
5. Complete example of safe command execution in Node.js
6. How to whitelist allowed commands
7. Alternative: using dedicated libraries like execa

Need production-ready code that passes security audit.
```

## P0-2: ПРАВИЛЬНОЕ ХЕШИРОВАНИЕ ПАРОЛЕЙ

**Запрос для паролей пользователей:**
```
Password hashing best practices in Node.js with crypto module (not bcrypt)

Current VULNERABLE implementation uses STATIC salt:
crypto.pbkdf2Sync(password, 'salt', 100000, 64, 'sha512')

Critical problems with static salt:
- Same salt for all passwords
- Vulnerable to rainbow table attacks
- One breach compromises all passwords

Show me:
1. How to generate unique salt per user using crypto.randomBytes()
2. How to store salt with password hash in database (format: salt:hash or JSON)
3. Complete password hashing function with unique salt
4. Complete password verification function
5. Why static salt is catastrophically dangerous (attack scenarios)
6. Example PostgreSQL schema for storing salt and hash
7. Migration strategy from static to unique salts

Requirements:
- Use only Node.js built-in crypto module
- Must pass security audit
- Production-ready code
```

## P0-3: JWT КОНФИГУРАЦИЯ

**Запрос для JWT безопасности:**
```
JWT security best practices Node.js production

Current issues:
1. JWT secret might be hardcoded
2. No token refresh mechanism
3. No blacklist for revoked tokens

Show me:
1. Secure JWT secret management (environment variables, key rotation)
2. Access token + Refresh token pattern implementation
3. Token blacklist/revocation with Redis
4. Proper token expiration times
5. How to store tokens securely (httpOnly cookies vs localStorage)
6. Complete authentication flow with JWT
7. How to prevent JWT attacks (algorithm confusion, weak secrets)

Using jsonwebtoken library, Node.js, PostgreSQL, Redis
```

## ДОПОЛНИТЕЛЬНЫЙ ЗАПРОС ПРО AI (если это про детерминированную генерацию)

**Запрос про AI генерацию:**
```
Deterministic AI text generation with seeds/salts for reproducible outputs

Context: Building AI system that needs consistent responses for same inputs
Platform: Google Gemini API / OpenAI API

Questions:
1. How do deterministic seeds work in LLM generation?
2. Difference between temperature, top-k, top-p, and seed parameters
3. How to implement reproducible generation with:
   - Google Gemini API (generationConfig.seed)
   - OpenAI API (seed parameter)
4. Best practices for deterministic AI outputs
5. When to use fixed vs random seeds
6. How to ensure same input → same output
7. Trade-offs of deterministic generation

Show code examples for both APIs with seed implementation
```

## РЕЗЮМЕ НА РУССКОМ

### Что нужно исправить КРИТИЧЕСКИ:

1. **spawn('sh', ['-c'])** - это ХУЖЕ чем execSync, это полноценный бэкдор
   - Нужно: spawn БЕЗ shell, только с массивом аргументов
   - Или использовать execFile с whitelist команд

2. **Статическая соль 'salt'** - катастрофическая уязвимость
   - Нужно: уникальная соль для каждого пользователя через crypto.randomBytes
   - Хранить как salt:hash или в отдельных колонках БД

3. **JWT без ротации** - токены живут вечно
   - Нужно: access + refresh токены
   - Blacklist в Redis для отозванных токенов

### Что я НЕ ПОНИМАЮ и нужно изучить:
- Разница между spawn, exec, execFile, execSync
- Почему spawn с shell хуже execSync
- Как правильно генерировать и хранить соль
- Паттерн access/refresh токенов
- Детерминированная генерация в AI (если это про это)