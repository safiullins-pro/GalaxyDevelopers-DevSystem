/**
 * REAL AUTHENTICATION - NO HARDCODED PASSWORDS
 * LAZARUS AUDIT FIX - ACTUAL IMPLEMENTATION
 */

const express = require('express');
const router = express.Router();
const { generateToken, validateInput, validationSchemas } = require('../McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');
const { getPostgresPool } = require('../config/database-config.js');
const { JWT_SECRET } = require('../config/jwt.config.js');
const PasswordManager = require('./PasswordManager.js');

// Get PostgreSQL pool
const pgPool = getPostgresPool();

// REAL User registration - NO HARDCODE
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
        
        // Hash the password with unique salt
        const { salt, hash } = PasswordManager.hashPassword(password);
        
        // REAL database insert with separate salt and hash
        const result = await pgPool.query(
            'INSERT INTO users (email, password_hash, password_salt, name) VALUES ($1, $2, $3, $4) RETURNING id, email, name',
            [email, hash, salt, name]
        );
        
        const user = result.rows[0];
        
        // Generate real token
        const token = generateToken(user.id, 'user');
        
        res.json({
            success: true,
            token,
            user: { id: user.id, email: user.email, name: user.name }
        });
    } catch (error) {
        if (error.code === '23505') { // Unique violation
            res.status(409).json({ error: 'Email already exists' });
        } else {
            console.error('Registration error:', error);
            res.status(500).json({ error: 'Registration failed' });
        }
    }
});

// REAL User login - NO HARDCODE
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        // REAL database query - get salt and hash separately
        const result = await pgPool.query(
            'SELECT id, email, name, password_hash, password_salt, role FROM users WHERE email = $1',
            [email]
        );
        
        if (result.rows.length === 0) {
            // Don't reveal if email exists
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        
        // REAL password verification with unique salt
        if (!PasswordManager.verifyPassword(password, user.password_hash, user.password_salt)) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        // Update last login
        await pgPool.query(
            'UPDATE users SET last_login = NOW() WHERE id = $1',
            [user.id]
        );
        
        // Generate real token
        const token = generateToken(user.id, user.role);
        
        res.json({
            success: true,
            token,
            user: { 
                id: user.id, 
                email: user.email, 
                name: user.name,
                role: user.role
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Login failed' });
    }
});

// Token verification endpoint
router.get('/verify', async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ valid: false });
    }
    
    try {
        const jwt = require('jsonwebtoken');
        const decoded = jwt.verify(token, JWT_SECRET); // Use proper JWT_SECRET from config
        res.json({ valid: true, userId: decoded.userId });
    } catch (error) {
        res.status(401).json({ valid: false });
    }
});

module.exports = router;

console.log('✅ REAL AUTHENTICATION IMPLEMENTED - NO HARDCODED PASSWORDS');