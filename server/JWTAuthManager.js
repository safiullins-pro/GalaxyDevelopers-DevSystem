/**
 * JWT AUTHENTICATION MANAGER - Based on Perplexity Research
 * Implements complete JWT security with access/refresh tokens
 * Includes Redis blacklist and secure cookie storage
 */

const jwt = require('jsonwebtoken');
const crypto = require('crypto');

class JWTAuthManager {
    constructor(pgPool, redisClient) {
        this.pgPool = pgPool;
        this.redisClient = redisClient;
        
        // Load secrets from environment or generate secure ones
        this.ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || this.generateSecret();
        this.REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || this.generateSecret();
        
        // Token expiration times (based on Perplexity recommendations)
        this.ACCESS_TOKEN_EXPIRY = '15m';  // 15 minutes
        this.REFRESH_TOKEN_EXPIRY = '30d'; // 30 days
        
        // Maximum session lifetime (90 days)
        this.MAX_SESSION_LIFETIME = 90 * 24 * 60 * 60 * 1000;
        
        // Allowed algorithms (prevent algorithm confusion attack)
        this.ALLOWED_ALGORITHMS = ['HS256'];
    }
    
    /**
     * Generate cryptographically secure secret
     * Minimum 256 bits as recommended by Perplexity
     */
    generateSecret() {
        const secret = crypto.randomBytes(32).toString('hex');
        console.warn('⚠️  Generated JWT secret. For production, set JWT_ACCESS_SECRET and JWT_REFRESH_SECRET');
        return secret;
    }
    
    /**
     * Generate access token (short-lived)
     */
    generateAccessToken(userId, role = 'user') {
        const payload = {
            userId,
            role,
            type: 'access',
            jti: crypto.randomBytes(16).toString('hex'), // Unique token ID
            iat: Math.floor(Date.now() / 1000)
        };
        
        return jwt.sign(payload, this.ACCESS_SECRET, {
            expiresIn: this.ACCESS_TOKEN_EXPIRY,
            algorithm: 'HS256'
        });
    }
    
    /**
     * Generate refresh token (long-lived)
     */
    generateRefreshToken(userId) {
        const payload = {
            userId,
            type: 'refresh',
            jti: crypto.randomBytes(16).toString('hex'), // Unique token ID
            iat: Math.floor(Date.now() / 1000)
        };
        
        return jwt.sign(payload, this.REFRESH_SECRET, {
            expiresIn: this.REFRESH_TOKEN_EXPIRY,
            algorithm: 'HS256'
        });
    }
    
    /**
     * Verify access token with blacklist check
     */
    async verifyAccessToken(token) {
        try {
            // Check Redis blacklist first
            const isBlacklisted = await this.isTokenBlacklisted(token);
            if (isBlacklisted) {
                throw new Error('Token has been revoked');
            }
            
            // Verify token with explicit algorithm check
            const decoded = jwt.verify(token, this.ACCESS_SECRET, {
                algorithms: this.ALLOWED_ALGORITHMS
            });
            
            // Ensure it's an access token
            if (decoded.type !== 'access') {
                throw new Error('Invalid token type');
            }
            
            return decoded;
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Verify refresh token
     */
    async verifyRefreshToken(token) {
        try {
            // Check if refresh token exists in database
            const result = await this.pgPool.query(
                'SELECT * FROM refresh_tokens WHERE token = $1 AND revoked = false',
                [token]
            );
            
            if (result.rows.length === 0) {
                throw new Error('Refresh token not found or revoked');
            }
            
            // Verify token signature
            const decoded = jwt.verify(token, this.REFRESH_SECRET, {
                algorithms: this.ALLOWED_ALGORITHMS
            });
            
            // Ensure it's a refresh token
            if (decoded.type !== 'refresh') {
                throw new Error('Invalid token type');
            }
            
            // Check maximum session lifetime
            const tokenAge = Date.now() - (decoded.iat * 1000);
            if (tokenAge > this.MAX_SESSION_LIFETIME) {
                throw new Error('Maximum session lifetime exceeded');
            }
            
            return decoded;
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Store refresh token in database
     */
    async storeRefreshToken(userId, token) {
        try {
            // Calculate expiry time
            const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
            
            await this.pgPool.query(
                `INSERT INTO refresh_tokens (user_id, token, expires_at, created_at) 
                 VALUES ($1, $2, $3, NOW())`,
                [userId, token, expiresAt]
            );
        } catch (error) {
            console.error('Failed to store refresh token:', error);
            throw error;
        }
    }
    
    /**
     * Rotate refresh token (issue new, revoke old)
     */
    async rotateRefreshToken(oldToken, userId) {
        const client = await this.pgPool.connect();
        
        try {
            await client.query('BEGIN');
            
            // Revoke old token
            await client.query(
                'UPDATE refresh_tokens SET revoked = true WHERE token = $1',
                [oldToken]
            );
            
            // Generate new tokens
            const newAccessToken = this.generateAccessToken(userId);
            const newRefreshToken = this.generateRefreshToken(userId);
            
            // Store new refresh token
            const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
            await client.query(
                `INSERT INTO refresh_tokens (user_id, token, expires_at, created_at) 
                 VALUES ($1, $2, $3, NOW())`,
                [userId, newRefreshToken, expiresAt]
            );
            
            await client.query('COMMIT');
            
            return {
                accessToken: newAccessToken,
                refreshToken: newRefreshToken
            };
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }
    
    /**
     * Add token to Redis blacklist
     */
    async blacklistToken(token, type = 'access') {
        try {
            const decoded = jwt.decode(token);
            if (!decoded || !decoded.exp) return;
            
            // Calculate TTL (time until token expires)
            const ttl = decoded.exp - Math.floor(Date.now() / 1000);
            
            if (ttl > 0) {
                // Add to Redis with expiry matching token TTL
                await this.redisClient.setEx(
                    `blacklist:${token}`,
                    ttl,
                    JSON.stringify({ type, userId: decoded.userId })
                );
            }
        } catch (error) {
            console.error('Failed to blacklist token:', error);
        }
    }
    
    /**
     * Check if token is blacklisted
     */
    async isTokenBlacklisted(token) {
        try {
            const result = await this.redisClient.get(`blacklist:${token}`);
            return result !== null;
        } catch (error) {
            console.error('Failed to check blacklist:', error);
            return false; // Fail open to avoid blocking legitimate requests
        }
    }
    
    /**
     * Revoke all refresh tokens for a user (e.g., on password change)
     */
    async revokeAllUserTokens(userId) {
        try {
            await this.pgPool.query(
                'UPDATE refresh_tokens SET revoked = true WHERE user_id = $1',
                [userId]
            );
        } catch (error) {
            console.error('Failed to revoke user tokens:', error);
            throw error;
        }
    }
    
    /**
     * Clean up expired tokens from database
     */
    async cleanupExpiredTokens() {
        try {
            const result = await this.pgPool.query(
                'DELETE FROM refresh_tokens WHERE expires_at < NOW() OR revoked = true'
            );
            return result.rowCount;
        } catch (error) {
            console.error('Failed to cleanup tokens:', error);
            return 0;
        }
    }
    
    /**
     * Generate secure cookie options
     */
    getSecureCookieOptions() {
        return {
            httpOnly: true,        // Prevent JS access (XSS protection)
            secure: process.env.NODE_ENV === 'production', // HTTPS only in production
            sameSite: 'strict',    // CSRF protection
            maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
            path: '/'
        };
    }
}

module.exports = JWTAuthManager;

/**
 * USAGE EXAMPLE:
 * 
 * const JWTAuthManager = require('./JWTAuthManager');
 * const authManager = new JWTAuthManager(pgPool, redisClient);
 * 
 * // Login - issue tokens
 * const accessToken = authManager.generateAccessToken(userId, role);
 * const refreshToken = authManager.generateRefreshToken(userId);
 * await authManager.storeRefreshToken(userId, refreshToken);
 * 
 * // Set refresh token in httpOnly cookie
 * res.cookie('refreshToken', refreshToken, authManager.getSecureCookieOptions());
 * res.json({ accessToken });
 * 
 * // Verify access token
 * const decoded = await authManager.verifyAccessToken(token);
 * 
 * // Refresh tokens
 * const { accessToken, refreshToken } = await authManager.rotateRefreshToken(oldToken, userId);
 * 
 * // Logout - blacklist and revoke
 * await authManager.blacklistToken(accessToken);
 * await authManager.revokeAllUserTokens(userId);
 * 
 * SECURITY FEATURES:
 * ✅ Separate access/refresh tokens
 * ✅ Redis blacklist for revocation
 * ✅ Token rotation on refresh
 * ✅ HttpOnly cookies for refresh tokens
 * ✅ Algorithm confusion prevention
 * ✅ Strong secret generation
 * ✅ Maximum session lifetime
 * ✅ Database persistence for refresh tokens
 */