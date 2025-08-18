#!/usr/bin/env node

/**
 * McKinsey HORIZON 1 - Week 3: Error Handling Setup
 * Standardizes error handling across the application
 */

const fs = require('fs').promises;
const path = require('path');

async function setupErrorHandling() {
    console.log('🛡️ Setting up standardized error handling...');
    
    // Create error handler module
    const errorHandlerCode = `
/**
 * Centralized Error Handling System
 * McKinsey Transformation - Enterprise Grade
 */

class AppError extends Error {
    constructor(message, statusCode = 500, isOperational = true) {
        super(message);
        this.statusCode = statusCode;
        this.isOperational = isOperational;
        this.timestamp = new Date().toISOString();
        
        Error.captureStackTrace(this, this.constructor);
    }
}

class ValidationError extends AppError {
    constructor(message, fields = []) {
        super(message, 400);
        this.fields = fields;
        this.type = 'VALIDATION_ERROR';
    }
}

class AuthenticationError extends AppError {
    constructor(message = 'Authentication failed') {
        super(message, 401);
        this.type = 'AUTH_ERROR';
    }
}

class AuthorizationError extends AppError {
    constructor(message = 'Access denied') {
        super(message, 403);
        this.type = 'AUTHZ_ERROR';
    }
}

class NotFoundError extends AppError {
    constructor(resource = 'Resource') {
        super(\`\${resource} not found\`, 404);
        this.type = 'NOT_FOUND';
    }
}

class RateLimitError extends AppError {
    constructor(retryAfter = 60) {
        super('Rate limit exceeded', 429);
        this.type = 'RATE_LIMIT';
        this.retryAfter = retryAfter;
    }
}

class DatabaseError extends AppError {
    constructor(message = 'Database operation failed') {
        super(message, 500);
        this.type = 'DATABASE_ERROR';
        this.isOperational = false;
    }
}

// Global error handler middleware
const errorHandler = (err, req, res, next) => {
    // Log error
    logError(err, req);
    
    // Handle known operational errors
    if (err instanceof AppError && err.isOperational) {
        return res.status(err.statusCode).json({
            error: err.message,
            type: err.type || 'ERROR',
            timestamp: err.timestamp,
            ...(err.fields && { fields: err.fields }),
            ...(err.retryAfter && { retryAfter: err.retryAfter })
        });
    }
    
    // Handle Joi validation errors
    if (err.name === 'ValidationError') {
        return res.status(400).json({
            error: 'Validation failed',
            type: 'VALIDATION_ERROR',
            details: err.details
        });
    }
    
    // Handle JWT errors
    if (err.name === 'JsonWebTokenError') {
        return res.status(401).json({
            error: 'Invalid token',
            type: 'AUTH_ERROR'
        });
    }
    
    if (err.name === 'TokenExpiredError') {
        return res.status(401).json({
            error: 'Token expired',
            type: 'AUTH_ERROR'
        });
    }
    
    // Handle unknown errors (don't leak internal details)
    console.error('Unhandled error:', err);
    
    // Send generic error response
    res.status(500).json({
        error: 'Internal server error',
        type: 'INTERNAL_ERROR',
        timestamp: new Date().toISOString()
    });
    
    // For critical errors, trigger alerts
    if (!err.isOperational) {
        alertOps(err, req);
    }
};

// Async error wrapper
const asyncHandler = (fn) => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

// Error logging
const logError = (err, req) => {
    const errorLog = {
        timestamp: new Date().toISOString(),
        error: {
            message: err.message,
            stack: err.stack,
            type: err.type || err.name,
            statusCode: err.statusCode
        },
        request: {
            method: req.method,
            url: req.url,
            ip: req.ip,
            userAgent: req.get('user-agent')
        },
        user: req.user ? { id: req.user.userId } : null
    };
    
    // Log to file (in production, use proper logging service)
    console.error('ERROR:', JSON.stringify(errorLog, null, 2));
    
    // TODO: Send to logging service (e.g., ELK stack)
};

// Alert operations team for critical errors
const alertOps = async (err, req) => {
    const alert = {
        severity: 'CRITICAL',
        error: err.message,
        stack: err.stack,
        timestamp: new Date().toISOString(),
        request: \`\${req.method} \${req.url}\`
    };
    
    console.error('🚨 CRITICAL ERROR - OPS ALERT:', alert);
    
    // TODO: Send to PagerDuty/Slack/Email
};

// Process-level error handlers
process.on('uncaughtException', (err) => {
    console.error('UNCAUGHT EXCEPTION:', err);
    // Log error
    // Alert ops team
    // Gracefully shutdown
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('UNHANDLED REJECTION at:', promise, 'reason:', reason);
    // Log error
    // Alert ops team
});

module.exports = {
    AppError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    DatabaseError,
    errorHandler,
    asyncHandler
};
`;
    
    // Save error handler module
    const errorHandlerPath = path.join(__dirname, '../../../SERVER/error-handler.js');
    await fs.writeFile(errorHandlerPath, errorHandlerCode);
    console.log('  ✅ Created error-handler.js');
    
    // Update backend to use error handler
    const backendPath = path.join(__dirname, '../../../SERVER/GalaxyDevelopersAI-backend.js');
    
    try {
        let backendCode = await fs.readFile(backendPath, 'utf8');
        
        // Add error handler import
        if (!backendCode.includes('error-handler')) {
            const errorImport = `const { errorHandler, asyncHandler, NotFoundError } = require('./error-handler.js');\n`;
            backendCode = errorImport + backendCode;
        }
        
        // Wrap route handlers with asyncHandler
        backendCode = backendCode.replace(
            /app\.(get|post|put|delete)\((.*?),\s*async\s*\((req, res)\)\s*=>/g,
            'app.$1($2, asyncHandler(async (req, res) =>'
        );
        
        // Add error handler middleware (must be last)
        if (!backendCode.includes('app.use(errorHandler)')) {
            backendCode = backendCode.replace(
                /app\.listen\(/g,
                `// Error handling middleware (must be last)\napp.use(errorHandler);\n\napp.listen(`
            );
        }
        
        // Add 404 handler
        if (!backendCode.includes('404 handler')) {
            const notFoundHandler = `
// 404 handler (before error handler)
app.use((req, res, next) => {
    next(new NotFoundError('Endpoint'));
});
`;
            backendCode = backendCode.replace(
                /app\.use\(errorHandler\)/g,
                `${notFoundHandler}\napp.use(errorHandler)`
            );
        }
        
        await fs.writeFile(backendPath, backendCode);
        console.log('  ✅ Updated backend with error handling');
        
    } catch (error) {
        console.error('  ❌ Error updating backend:', error.message);
    }
    
    console.log('✅ Error handling setup completed!');
}

// Run setup
setupErrorHandling().catch(console.error);