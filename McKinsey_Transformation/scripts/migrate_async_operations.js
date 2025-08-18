#!/usr/bin/env node

/**
 * McKinsey HORIZON 1 - Week 3: Async Operations Migration
 * Converts all blocking sync operations to async
 */

const fs = require('fs').promises;
const path = require('path');

const FILES_TO_MIGRATE = [
    '../../../SERVER/GalaxyDevelopersAI-backend.js',
    '../../../INTERFACE/js/monitoring-module.js',
    '../../../SERVER/gemini-functions.js'
];

async function migrateAsyncOperations() {
    console.log('🔄 Migrating to async operations...');
    
    for (const filePath of FILES_TO_MIGRATE) {
        const fullPath = path.join(__dirname, filePath);
        
        try {
            let code = await fs.readFile(fullPath, 'utf8');
            const originalCode = code;
            
            console.log(`  📝 Processing ${path.basename(filePath)}...`);
            
            // Convert fs.readFileSync to fs.promises.readFile
            code = code.replace(
                /fs\.readFileSync\((.*?)\)/g,
                'await fs.promises.readFile($1)'
            );
            
            // Convert fs.writeFileSync to fs.promises.writeFile
            code = code.replace(
                /fs\.writeFileSync\((.*?)\)/g,
                'await fs.promises.writeFile($1)'
            );
            
            // Convert fs.existsSync to fs.promises.access
            code = code.replace(
                /fs\.existsSync\((.*?)\)/g,
                'await fs.promises.access($1).then(() => true).catch(() => false)'
            );
            
            // Convert fs.mkdirSync to fs.promises.mkdir
            code = code.replace(
                /fs\.mkdirSync\((.*?)\)/g,
                'await fs.promises.mkdir($1)'
            );
            
            // Make functions async if they contain await
            code = code.replace(
                /function\s+(\w+)\s*\((.*?)\)\s*{([^}]*await[^}]*)/g,
                'async function $1($2) {$3'
            );
            
            // Make arrow functions async if they contain await
            code = code.replace(
                /(\w+)\s*=\s*\((.*?)\)\s*=>\s*{([^}]*await[^}]*)/g,
                '$1 = async ($2) => {$3'
            );
            
            // Make route handlers async
            code = code.replace(
                /app\.(get|post|put|delete)\((.*?),\s*\((req, res)\)\s*=>\s*{/g,
                'app.$1($2, async (req, res) => {'
            );
            
            if (code !== originalCode) {
                await fs.writeFile(fullPath, code);
                console.log(`    ✅ Migrated to async operations`);
            } else {
                console.log(`    ℹ️  No sync operations found`);
            }
            
        } catch (error) {
            console.error(`    ❌ Error processing ${filePath}:`, error.message);
        }
    }
    
    console.log('✅ Async migration completed!');
}

// Run migration
migrateAsyncOperations().catch(console.error);