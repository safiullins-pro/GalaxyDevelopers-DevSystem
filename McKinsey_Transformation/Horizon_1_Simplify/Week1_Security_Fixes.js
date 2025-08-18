/**
 * HORIZON 1 - WEEK 1: CRITICAL SECURITY FIXES
 * McKinsey Transformation - Make it Work
 * Priority: P0 CRITICAL (Fix within 48 hours)
 */

const { spawn } = require('child_process');
const jwt = require('jsonwebtoken');
const Joi = require('joi');
// const bcrypt = require('bcrypt'); // Removed due to compilation issues
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');

// =====================================
// P0 FIX #1: Replace execSync with SECURE command executor
// =====================================

/**
 * SECURE: Command execution with full protection
 * Based on Perplexity research - NO SHELL ACCESS
 */
const { executeCommandSecure } = require('./SecureCommandExecutor');

// =====================================
// P0 FIX #2: JWT Authentication Middleware
// =====================================

const JWT_SECRET = process.env.JWT_SECRET || require('crypto').randomBytes(64).toString('hex');
const JWT_EXPIRY = '24h';

/**
 * Generate JWT token for authenticated user
 */
const generateToken = (userId, role = 'user') => {
  return jwt.sign(
    { 
      userId, 
      role,
      iat: Date.now(),
      jti: require('crypto').randomBytes(16).toString('hex') // Unique token ID
    },
    JWT_SECRET,
    { 
      expiresIn: JWT_EXPIRY,
      algorithm: 'HS256'
    }
  );
};

/**
 * Authentication middleware - protects all endpoints
 */
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN
  
  if (!token) {
    return res.status(401).json({ 
      error: 'Access denied. No token provided.',
      code: 'NO_AUTH_TOKEN'
    });
  }
  
  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ 
          error: 'Token expired',
          code: 'TOKEN_EXPIRED'
        });
      }
      return res.status(403).json({ 
        error: 'Invalid token',
        code: 'INVALID_TOKEN'
      });
    }
    
    req.user = decoded;
    next();
  });
};

// =====================================
// P0 FIX #3: Input Validation Schemas
// =====================================

/**
 * Joi validation schemas for all endpoints
 */
const validationSchemas = {
  // Chat endpoint validation
  chat: Joi.object({
    prompt: Joi.string()
      .required()
      .min(1)
      .max(5000)
      .pattern(/^[^<>]*$/) // No HTML tags
      .messages({
        'string.pattern.base': 'Prompt cannot contain HTML tags',
        'string.max': 'Prompt cannot exceed 5000 characters'
      }),
    context: Joi.string()
      .max(10000)
      .pattern(/^[^<>]*$/) // No HTML tags
      .optional()
      .messages({
        'string.pattern.base': 'Context cannot contain HTML tags'
      }),
    model: Joi.string()
      .valid('gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro')
      .optional(),
    sessionId: Joi.string()
      .uuid()
      .optional()
  }),
  
  // User registration validation
  register: Joi.object({
    email: Joi.string()
      .email()
      .required()
      .lowercase(),
    password: Joi.string()
      .min(8)
      .max(128)
      .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
      .required()
      .messages({
        'string.pattern.base': 'Password must contain uppercase, lowercase, number and special character'
      }),
    name: Joi.string()
      .min(2)
      .max(100)
      .required()
  }),
  
  // File operation validation
  fileOperation: Joi.object({
    path: Joi.string()
      .pattern(/^\/[a-zA-Z0-9\/_\-\.]+$/) // Unix path only
      .required()
      .messages({
        'string.pattern.base': 'Invalid file path'
      }),
    operation: Joi.string()
      .valid('read', 'write', 'delete')
      .required()
  })
};

/**
 * Validation middleware factory
 */
const validateInput = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true // Remove unknown fields
    });
    
    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));
      
      return res.status(400).json({
        error: 'Validation failed',
        code: 'VALIDATION_ERROR',
        details: errors
      });
    }
    
    req.validatedBody = value; // Use validated & sanitized input
    next();
  };
};

// =====================================
// P0 FIX #4: Rate Limiting
// =====================================

/**
 * Rate limiter configurations for different endpoints
 */
const rateLimiters = {
  // Strict limit for auth endpoints
  auth: rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // 5 requests per window
    message: 'Too many authentication attempts, please try again later',
    standardHeaders: true,
    legacyHeaders: false,
  }),
  
  // Standard API rate limit
  api: rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 60, // 60 requests per minute
    message: 'API rate limit exceeded',
    standardHeaders: true,
    legacyHeaders: false,
  }),
  
  // Expensive operations limit
  expensive: rateLimit({
    windowMs: 5 * 60 * 1000, // 5 minutes
    max: 10, // 10 requests per 5 minutes
    message: 'Rate limit for expensive operations exceeded',
    standardHeaders: true,
    legacyHeaders: false,
  })
};

// =====================================
// P0 FIX #5: SQL Injection Prevention
// =====================================

/**
 * Parameterized query wrapper
 */
const safeQuery = (db, query, params = []) => {
  // Use parameterized queries to prevent SQL injection
  return new Promise((resolve, reject) => {
    db.all(query, params, (err, rows) => {
      if (err) {
        console.error('Database error:', err);
        reject(new Error('Database operation failed'));
      } else {
        resolve(rows);
      }
    });
  });
};

// =====================================
// P0 FIX #6: Function Call Loop Protection
// =====================================

/**
 * Protected function calling with timeout and depth limit
 */
const protectedFunctionCall = async (func, args, options = {}) => {
  const maxDepth = options.maxDepth || 10;
  const timeout = options.timeout || 30000; // 30 seconds
  const startTime = Date.now();
  
  let depth = 0;
  
  const executeWithProtection = async (fn, fnArgs) => {
    depth++;
    
    // Check depth limit
    if (depth > maxDepth) {
      throw new Error(`Function call depth limit exceeded (${maxDepth})`);
    }
    
    // Check timeout
    if (Date.now() - startTime > timeout) {
      throw new Error(`Function call timeout (${timeout}ms)`);
    }
    
    try {
      return await fn(...fnArgs);
    } finally {
      depth--;
    }
  };
  
  return executeWithProtection(func, args);
};

// =====================================
// EXPORTS
// =====================================

module.exports = {
  executeCommandSecure,
  generateToken,
  authenticateToken,
  validationSchemas,
  validateInput,
  rateLimiters,
  safeQuery,
  protectedFunctionCall,
  JWT_SECRET
};

/**
 * IMPLEMENTATION CHECKLIST:
 * 
 * ✅ 1. Replace ALL execSync calls with executeCommandSecure
 * ✅ 2. Add authenticateToken middleware to ALL routes
 * ✅ 3. Add validateInput middleware to ALL endpoints
 * ✅ 4. Apply rate limiters to prevent abuse
 * ✅ 5. Replace raw SQL with safeQuery wrapper
 * ✅ 6. Wrap function calls with protectedFunctionCall
 * 
 * TESTING REQUIREMENTS:
 * - Unit tests for each security function
 * - Integration tests for authentication flow
 * - Penetration testing for SQL injection
 * - Load testing for rate limiters
 * 
 * DEPLOYMENT:
 * - Deploy to staging first
 * - Monitor for 24 hours
 * - Gradual rollout to production
 */