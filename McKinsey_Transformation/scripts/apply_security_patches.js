#!/usr/bin/env node

/**
 * McKinsey HORIZON 1 - Security Patches Automation
 * Automatically applies critical security fixes to existing codebase
 */

const fs = require('fs').promises;
const path = require('path');

const BACKEND_PATH = path.join(__dirname, '../../SERVER/GalaxyDevelopersAI-backend.js');
const SECURITY_MODULE = path.join(__dirname, '../Horizon_1_Simplify/Week1_Security_Fixes.js');

async function applySecurityPatches() {
    console.log('🔧 Applying security patches...');
    
    try {
        // Read the original backend file
        let backendCode = await fs.readFile(BACKEND_PATH, 'utf8');
        
        // Patch 1: Replace execSync with secure spawn
        if (backendCode.includes('execSync')) {
            console.log('  ✅ Patching execSync vulnerability...');
            
            // Add security module import
            const securityImport = `const { executeCommandSecure, authenticateToken, validateInput, validationSchemas, rateLimiters } = require('./McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');\n`;
            
            if (!backendCode.includes('Week1_Security_Fixes')) {
                backendCode = securityImport + backendCode;
            }
            
            // Replace execSync calls
            backendCode = backendCode.replace(
                /const\s*{\s*execSync\s*}\s*=\s*require\(['"]child_process['"]\);?/g,
                '// execSync removed for security - using executeCommandSecure instead'
            );
            
            backendCode = backendCode.replace(
                /execSync\((.*?)\)/g,
                'await executeCommandSecure($1)'
            );
            
            // Make functions async if they contain executeCommandSecure
            backendCode = backendCode.replace(
                /function\s+(\w+)\s*\((.*?)\)\s*{([^}]*executeCommandSecure[^}]*)/g,
                'async function $1($2) {$3'
            );
        }
        
        // Patch 2: Add authentication to routes
        if (!backendCode.includes('authenticateToken')) {
            console.log('  ✅ Adding authentication middleware...');
            
            // Add auth to chat endpoint
            backendCode = backendCode.replace(
                /app\.post\(['"]\/chat['"]/g,
                "app.post('/chat', authenticateToken, validateInput(validationSchemas.chat)"
            );
            
            // Add auth to other endpoints
            backendCode = backendCode.replace(
                /app\.(get|post|put|delete)\(['"]\/api\//g,
                "app.$1('/api/, authenticateToken, "
            );
        }
        
        // Patch 3: Add rate limiting
        if (!backendCode.includes('rateLimiters')) {
            console.log('  ✅ Adding rate limiting...');
            
            // Add rate limiting to auth routes
            backendCode = backendCode.replace(
                /app\.post\(['"]\/auth\//g,
                "app.post('/auth/, rateLimiters.auth, "
            );
            
            // Add general rate limiting
            const rateLimitSetup = `
// Apply rate limiting to all routes
app.use('/api/', rateLimiters.api);
app.use('/auth/', rateLimiters.auth);
`;
            
            // Insert after express app creation
            backendCode = backendCode.replace(
                /const app = express\(\);/g,
                `const app = express();\n${rateLimitSetup}`
            );
        }
        
        // Patch 4: Add input validation
        if (!backendCode.includes('helmet')) {
            console.log('  ✅ Adding security headers...');
            
            const securityHeaders = `
const helmet = require('helmet');
const cors = require('cors');

// Security headers
app.use(helmet());
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
}));
`;
            
            backendCode = backendCode.replace(
                /const app = express\(\);/g,
                `const app = express();\n${securityHeaders}`
            );
        }
        
        // Patch 5: Add health check endpoint
        if (!backendCode.includes('/health')) {
            console.log('  ✅ Adding health check endpoint...');
            
            const healthCheck = `
// Health check endpoint (no auth required)
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});
`;
            
            // Add before server start
            backendCode = backendCode.replace(
                /app\.listen\(/g,
                `${healthCheck}\n\napp.listen(`
            );
        }
        
        // Save patched file
        await fs.writeFile(BACKEND_PATH, backendCode);
        console.log('✅ Security patches applied successfully!');
        
        // Create auth routes file
        await createAuthRoutes();
        
    } catch (error) {
        console.error('❌ Error applying patches:', error.message);
        process.exit(1);
    }
}

async function createAuthRoutes() {
    console.log('  📝 Creating authentication routes...');
    
    const authRoutes = `
const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const { generateToken, validateInput, validationSchemas } = require('../McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');

// User registration
router.post('/register', validateInput(validationSchemas.register), async (req, res) => {
    try {
        const { email, password, name } = req.validatedBody;
        
        // Hash password
        const passwordHash = await bcrypt.hash(password, 10);
        
        // TODO: Save to database
        // const user = await db.createUser({ email, passwordHash, name });
        
        // Generate token
        const token = generateToken('temp-user-id', 'user');
        
        res.json({
            success: true,
            token,
            user: { email, name }
        });
    } catch (error) {
        res.status(500).json({ error: 'Registration failed' });
    }
});

// User login
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        // TODO: Get user from database
        // const user = await db.getUserByEmail(email);
        
        // Temporary hardcoded check
        if (email === 'admin@galaxydevelopers.com' && password === 'SecurePass123!') {
            const token = generateToken('admin-id', 'admin');
            
            res.json({
                success: true,
                token,
                user: { email, name: 'Admin' }
            });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    } catch (error) {
        res.status(500).json({ error: 'Login failed' });
    }
});

module.exports = router;
`;
    
    await fs.writeFile(
        path.join(__dirname, '../../SERVER/auth.routes.js'),
        authRoutes
    );
    
    console.log('  ✅ Authentication routes created');
}

// Run patches
applySecurityPatches().catch(console.error);