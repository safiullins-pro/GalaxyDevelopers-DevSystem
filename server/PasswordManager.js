/**
 * SECURE PASSWORD MANAGER - Based on Perplexity Research
 * Implements proper password hashing with unique salts per user
 * NO STATIC SALT - Each user gets unique 32-byte salt
 */

const crypto = require('crypto');

class PasswordManager {
    /**
     * Hash a password with a unique salt
     * @param {string} password - Plain text password
     * @returns {Object} Object with salt and hash
     */
    static hashPassword(password) {
        if (!password || typeof password !== 'string') {
            throw new Error('Password must be a non-empty string');
        }
        
        if (password.length < 8) {
            throw new Error('Password must be at least 8 characters');
        }
        
        // Generate unique 32-byte salt for this user
        const salt = crypto.randomBytes(32).toString('hex');
        
        // Hash with 100,000 iterations (OWASP recommendation)
        const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex');
        
        return { salt, hash };
    }
    
    /**
     * Verify a password against stored hash and salt
     * Uses timing-safe comparison to prevent timing attacks
     * @param {string} inputPassword - Password to verify
     * @param {string} storedHash - Stored password hash
     * @param {string} storedSalt - Stored salt
     * @returns {boolean} True if password matches
     */
    static verifyPassword(inputPassword, storedHash, storedSalt) {
        if (!inputPassword || !storedHash || !storedSalt) {
            return false;
        }
        
        try {
            // Hash input with stored salt
            const hash = crypto.pbkdf2Sync(inputPassword, storedSalt, 100000, 64, 'sha512').toString('hex');
            
            // Timing-safe comparison to prevent timing attacks
            return crypto.timingSafeEqual(
                Buffer.from(hash, 'hex'), 
                Buffer.from(storedHash, 'hex')
            );
        } catch (error) {
            // Return false for any error (invalid hex, etc)
            return false;
        }
    }
    
    /**
     * Hash password and return as single string "salt:hash"
     * Useful for single-column storage
     * @param {string} password - Plain text password
     * @returns {string} Combined "salt:hash" string
     */
    static hashPasswordCombined(password) {
        const { salt, hash } = this.hashPassword(password);
        return `${salt}:${hash}`;
    }
    
    /**
     * Verify password from combined "salt:hash" format
     * @param {string} inputPassword - Password to verify
     * @param {string} storedData - Combined "salt:hash" string
     * @returns {boolean} True if password matches
     */
    static verifyPasswordCombined(inputPassword, storedData) {
        if (!storedData || !storedData.includes(':')) {
            return false;
        }
        
        const [salt, hash] = storedData.split(':');
        
        if (!salt || !hash) {
            return false;
        }
        
        return this.verifyPassword(inputPassword, hash, salt);
    }
    
    /**
     * Generate a secure random password
     * @param {number} length - Password length (default 16)
     * @returns {string} Random password
     */
    static generateSecurePassword(length = 16) {
        const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
        let password = '';
        
        // Use crypto.randomBytes for secure randomness
        const randomBytes = crypto.randomBytes(length);
        
        for (let i = 0; i < length; i++) {
            password += charset[randomBytes[i] % charset.length];
        }
        
        return password;
    }
    
    /**
     * Check password strength
     * @param {string} password - Password to check
     * @returns {Object} Strength assessment
     */
    static checkPasswordStrength(password) {
        const checks = {
            minLength: password.length >= 8,
            hasUpperCase: /[A-Z]/.test(password),
            hasLowerCase: /[a-z]/.test(password),
            hasNumbers: /\d/.test(password),
            hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(password),
            notCommon: !this.isCommonPassword(password)
        };
        
        const score = Object.values(checks).filter(v => v).length;
        
        return {
            score: score,
            strength: score <= 2 ? 'weak' : score <= 4 ? 'medium' : 'strong',
            checks: checks
        };
    }
    
    /**
     * Check if password is in common passwords list
     * @param {string} password - Password to check
     * @returns {boolean} True if password is common
     */
    static isCommonPassword(password) {
        // Small subset of common passwords for demo
        // In production, use a comprehensive list
        const commonPasswords = [
            'password', '123456', '12345678', 'qwerty', 'abc123',
            'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
            'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
            'bailey', 'passw0rd', 'shadow', '123123', '654321'
        ];
        
        return commonPasswords.includes(password.toLowerCase());
    }
}

module.exports = PasswordManager;

/**
 * USAGE EXAMPLES:
 * 
 * const PasswordManager = require('./PasswordManager');
 * 
 * // Hash a new password
 * const { salt, hash } = PasswordManager.hashPassword('mySecurePassword123!');
 * 
 * // Store in database:
 * // INSERT INTO users (email, password_hash, password_salt) VALUES (?, ?, ?)
 * 
 * // Verify password during login
 * const isValid = PasswordManager.verifyPassword(inputPassword, storedHash, storedSalt);
 * 
 * // Combined format (salt:hash)
 * const combined = PasswordManager.hashPasswordCombined('myPassword');
 * const isValid = PasswordManager.verifyPasswordCombined(inputPassword, combined);
 * 
 * SECURITY FEATURES:
 * ✅ Unique 32-byte salt per user
 * ✅ 100,000 PBKDF2 iterations
 * ✅ SHA-512 hashing algorithm
 * ✅ Timing-safe comparison
 * ✅ Proper error handling
 * ✅ Password strength checking
 * 
 * ATTACKS PREVENTED:
 * 🚫 Rainbow table attacks (unique salts)
 * 🚫 Timing attacks (timingSafeEqual)
 * 🚫 Mass compromise (no shared salt)
 * 🚫 Identical password detection
 * 🚫 Brute force (100k iterations)
 */