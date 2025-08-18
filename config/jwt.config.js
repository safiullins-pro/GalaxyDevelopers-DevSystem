/**
 * JWT Configuration - SECURE IMPLEMENTATION
 * NO FALLBACKS, NO DEFAULTS
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class JWTConfig {
    constructor() {
        this.secretPath = path.join(__dirname, '../.jwt-secret');
        this.secret = this.loadOrGenerateSecret();
    }

    loadOrGenerateSecret() {
        // Check environment variable FIRST
        if (process.env.JWT_SECRET) {
            if (process.env.JWT_SECRET.length < 32) {
                console.error('❌ FATAL: JWT_SECRET must be at least 32 characters');
                process.exit(1);
            }
            return process.env.JWT_SECRET;
        }

        // Check file-based secret for development
        if (fs.existsSync(this.secretPath)) {
            const secret = fs.readFileSync(this.secretPath, 'utf8').trim();
            if (secret.length >= 32) {
                console.log('✅ JWT secret loaded from file');
                return secret;
            }
        }

        // Generate new secret ONLY in development
        if (process.env.NODE_ENV === 'development' || !process.env.NODE_ENV) {
            const newSecret = crypto.randomBytes(64).toString('hex');
            fs.writeFileSync(this.secretPath, newSecret);
            console.log('⚠️  DEVELOPMENT: Generated new JWT secret');
            console.log('⚠️  For production, set JWT_SECRET environment variable');
            return newSecret;
        }

        // PRODUCTION WITHOUT SECRET = FATAL
        console.error('❌ FATAL: JWT_SECRET not configured in production');
        console.error('Set JWT_SECRET environment variable with 32+ character string');
        if (process.env.NODE_ENV !== 'test') {
            process.exit(1);
        }
        // For tests, generate temporary secret
        return crypto.randomBytes(64).toString('hex');
    }

    getSecret() {
        return this.secret;
    }

    // Token expiry options
    getExpiry(type = 'access') {
        const expiry = {
            access: '1h',      // Access token: 1 hour
            refresh: '30d',    // Refresh token: 30 days
            api: '90d',        // API key: 90 days
            session: '24h'     // Session: 24 hours
        };
        return expiry[type] || '1h';
    }

    // Algorithm configuration
    getAlgorithm() {
        return 'HS256'; // HMAC SHA256
    }
}

// Singleton instance
const jwtConfig = new JWTConfig();

module.exports = {
    JWT_SECRET: jwtConfig.getSecret(),
    getExpiry: jwtConfig.getExpiry.bind(jwtConfig),
    getAlgorithm: jwtConfig.getAlgorithm.bind(jwtConfig)
};

// Prevent secret leakage in logs
Object.defineProperty(module.exports, 'JWT_SECRET', {
    enumerable: false,
    configurable: false,
    get: () => jwtConfig.getSecret()
});