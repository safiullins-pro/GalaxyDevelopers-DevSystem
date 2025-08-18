/**
 * AUTHENTICATION V2 - Complete JWT Implementation
 * Based on Perplexity research with access/refresh tokens
 * Includes Redis blacklist and httpOnly cookies
 */

const express = require('express');
const router = express.Router();
const { validateInput, validationSchemas } = require('../McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');
const { getPostgresPool, getRedisClient } = require('../config/database-config.js');
const PasswordManager = require('./PasswordManager.js');
const JWTAuthManager = require('./JWTAuthManager.js');

// Initialize connections and managers
const pgPool = getPostgresPool();
let authManager;

// Initialize auth manager with Redis
(async () => {
    try {
        const redisClient = await getRedisClient();
        authManager = new JWTAuthManager(pgPool, redisClient);
        console.log('✅ JWT Auth Manager initialized with Redis');
    } catch (error) {
        console.error('Failed to initialize auth manager:', error);
        process.exit(1);
    }
})();

/**
 * REGISTER - Create new user with secure password
 */
router.post('/register', validateInput(validationSchemas.register), async (req, res) => {
    try {
        const { email, password, name } = req.validatedBody;
        
        // Check password strength
        const strength = PasswordManager.checkPasswordStrength(password);
        if (strength.strength === 'weak') {
            return res.status(400).json({ 
                error: 'Password is too weak',
                details: strength.checks
            });
        }
        
        // Check if user exists
        const existing = await pgPool.query(
            'SELECT id FROM users WHERE email = $1',
            [email]
        );
        
        if (existing.rows.length > 0) {
            return res.status(409).json({ error: 'Email already registered' });
        }
        
        // Hash password with unique salt
        const { salt, hash } = PasswordManager.hashPassword(password);
        
        // Create user
        const result = await pgPool.query(
            `INSERT INTO users (email, password_hash, password_salt, name, created_at) 
             VALUES ($1, $2, $3, $4, NOW()) 
             RETURNING id, email, name`,
            [email, hash, salt, name]
        );
        
        const user = result.rows[0];
        
        // Generate tokens
        const accessToken = authManager.generateAccessToken(user.id, 'user');
        const refreshToken = authManager.generateRefreshToken(user.id);
        
        // Store refresh token
        await authManager.storeRefreshToken(user.id, refreshToken);
        
        // Create session record
        const sessionId = require('crypto').randomBytes(32).toString('hex');
        await pgPool.query(
            `INSERT INTO user_sessions (user_id, session_id, ip_address, user_agent)
             VALUES ($1, $2, $3, $4)`,
            [user.id, sessionId, req.ip, req.headers['user-agent']]
        );
        
        // Set refresh token in httpOnly cookie
        res.cookie('refreshToken', refreshToken, authManager.getSecureCookieOptions());
        
        res.status(201).json({
            success: true,
            accessToken,
            user: { id: user.id, email: user.email, name: user.name }
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ error: 'Registration failed' });
    }
});

/**
 * LOGIN - Authenticate user and issue tokens
 */
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password required' });
        }
        
        // Get user with rate limit check
        const result = await pgPool.query(
            `SELECT id, email, name, password_hash, password_salt, role,
                    failed_login_attempts, last_failed_login
             FROM users WHERE email = $1`,
            [email]
        );
        
        if (result.rows.length === 0) {
            // Don't reveal if email exists
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        
        // Check if account is locked (5 failed attempts in last 15 minutes)
        if (user.failed_login_attempts >= 5) {
            const timeSinceLastFail = Date.now() - new Date(user.last_failed_login).getTime();
            if (timeSinceLastFail < 15 * 60 * 1000) {
                return res.status(429).json({ 
                    error: 'Account temporarily locked. Try again later.' 
                });
            }
        }
        
        // Verify password
        if (!PasswordManager.verifyPassword(password, user.password_hash, user.password_salt)) {
            // Update failed attempts
            await pgPool.query(
                `UPDATE users 
                 SET failed_login_attempts = failed_login_attempts + 1,
                     last_failed_login = NOW()
                 WHERE id = $1`,
                [user.id]
            );
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        // Reset failed attempts on successful login
        await pgPool.query(
            `UPDATE users 
             SET failed_login_attempts = 0,
                 last_login = NOW()
             WHERE id = $1`,
            [user.id]
        );
        
        // Generate tokens
        const accessToken = authManager.generateAccessToken(user.id, user.role || 'user');
        const refreshToken = authManager.generateRefreshToken(user.id);
        
        // Store refresh token
        await authManager.storeRefreshToken(user.id, refreshToken);
        
        // Create session record
        const sessionId = require('crypto').randomBytes(32).toString('hex');
        await pgPool.query(
            `INSERT INTO user_sessions (user_id, session_id, ip_address, user_agent)
             VALUES ($1, $2, $3, $4)`,
            [user.id, sessionId, req.ip, req.headers['user-agent']]
        );
        
        // Set refresh token in httpOnly cookie
        res.cookie('refreshToken', refreshToken, authManager.getSecureCookieOptions());
        
        res.json({
            success: true,
            accessToken,
            user: { 
                id: user.id, 
                email: user.email, 
                name: user.name,
                role: user.role || 'user'
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Login failed' });
    }
});

/**
 * REFRESH - Exchange refresh token for new access token
 */
router.post('/refresh', async (req, res) => {
    try {
        const refreshToken = req.cookies.refreshToken;
        
        if (!refreshToken) {
            return res.status(401).json({ error: 'No refresh token provided' });
        }
        
        // Verify refresh token
        const decoded = await authManager.verifyRefreshToken(refreshToken);
        
        // Get user info
        const result = await pgPool.query(
            'SELECT id, role FROM users WHERE id = $1',
            [decoded.userId]
        );
        
        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'User not found' });
        }
        
        const user = result.rows[0];
        
        // Rotate tokens
        const { accessToken, refreshToken: newRefreshToken } = 
            await authManager.rotateRefreshToken(refreshToken, user.id);
        
        // Update session
        await pgPool.query(
            'UPDATE user_sessions SET last_activity = NOW() WHERE user_id = $1 AND ended_at IS NULL',
            [user.id]
        );
        
        // Set new refresh token in cookie
        res.cookie('refreshToken', newRefreshToken, authManager.getSecureCookieOptions());
        
        res.json({
            success: true,
            accessToken
        });
    } catch (error) {
        console.error('Token refresh error:', error);
        res.status(401).json({ error: 'Invalid or expired refresh token' });
    }
});

/**
 * LOGOUT - Blacklist tokens and end session
 */
router.post('/logout', async (req, res) => {
    try {
        const accessToken = req.headers.authorization?.split(' ')[1];
        const refreshToken = req.cookies.refreshToken;
        
        if (accessToken) {
            // Blacklist access token
            await authManager.blacklistToken(accessToken, 'access');
            
            // Get user ID from token
            const decoded = require('jsonwebtoken').decode(accessToken);
            if (decoded && decoded.userId) {
                // End session
                await pgPool.query(
                    `UPDATE user_sessions 
                     SET ended_at = NOW(), end_reason = 'logout'
                     WHERE user_id = $1 AND ended_at IS NULL`,
                    [decoded.userId]
                );
            }
        }
        
        if (refreshToken) {
            // Revoke refresh token
            await pgPool.query(
                'UPDATE refresh_tokens SET revoked = true, revoked_at = NOW() WHERE token = $1',
                [refreshToken]
            );
        }
        
        // Clear cookie
        res.clearCookie('refreshToken');
        
        res.json({ success: true, message: 'Logged out successfully' });
    } catch (error) {
        console.error('Logout error:', error);
        res.status(500).json({ error: 'Logout failed' });
    }
});

/**
 * VERIFY - Check if access token is valid
 */
router.get('/verify', async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({ valid: false, error: 'No token provided' });
        }
        
        const decoded = await authManager.verifyAccessToken(token);
        
        res.json({ 
            valid: true, 
            userId: decoded.userId,
            role: decoded.role 
        });
    } catch (error) {
        res.status(401).json({ valid: false, error: error.message });
    }
});

/**
 * REVOKE ALL - Revoke all user tokens (for password change)
 */
router.post('/revoke-all', async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }
        
        const decoded = await authManager.verifyAccessToken(token);
        
        // Revoke all user tokens
        await authManager.revokeAllUserTokens(decoded.userId);
        
        // Blacklist current access token
        await authManager.blacklistToken(token, 'access');
        
        // Clear cookie
        res.clearCookie('refreshToken');
        
        res.json({ 
            success: true, 
            message: 'All tokens revoked. Please login again.' 
        });
    } catch (error) {
        console.error('Revoke all error:', error);
        res.status(500).json({ error: 'Failed to revoke tokens' });
    }
});

/**
 * Middleware to verify JWT token
 */
const authenticateToken = async (req, res, next) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({ error: 'Access denied. No token provided.' });
        }
        
        const decoded = await authManager.verifyAccessToken(token);
        req.user = decoded;
        
        // Update session activity
        if (decoded.userId) {
            pgPool.query(
                'UPDATE user_sessions SET last_activity = NOW() WHERE user_id = $1 AND ended_at IS NULL',
                [decoded.userId]
            ).catch(console.error);
        }
        
        next();
    } catch (error) {
        if (error.message === 'Token has been revoked') {
            return res.status(403).json({ error: 'Token has been revoked' });
        }
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({ error: 'Token expired', code: 'TOKEN_EXPIRED' });
        }
        return res.status(403).json({ error: 'Invalid token' });
    }
};

// Export router and middleware
module.exports = {
    router,
    authenticateToken
};

console.log('✅ AUTHENTICATION V2 INITIALIZED - Complete JWT implementation with Redis blacklist');