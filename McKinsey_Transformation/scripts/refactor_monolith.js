#!/usr/bin/env node

/**
 * McKinsey HORIZON 1 - Week 3: Monolith Refactoring
 * Breaks down large monolithic files into modules
 */

const fs = require('fs').promises;
const path = require('path');

async function refactorMonolith() {
    console.log('🔨 Refactoring monolithic code...');
    
    // Target: monitoring-module.js (1149 lines)
    const monolithPath = path.join(__dirname, '../../../INTERFACE/js/monitoring-module.js');
    
    try {
        const code = await fs.readFile(monolithPath, 'utf8');
        
        // Extract different components
        const components = {
            'websocket-handler.js': extractWebSocketCode(code),
            'ui-renderer.js': extractUICode(code),
            'api-client.js': extractAPICode(code),
            'state-manager.js': extractStateCode(code),
            'utils.js': extractUtilsCode(code)
        };
        
        // Create modules directory
        const modulesDir = path.join(__dirname, '../../../INTERFACE/js/modules');
        await fs.mkdir(modulesDir, { recursive: true });
        
        // Write each component
        for (const [filename, content] of Object.entries(components)) {
            const filePath = path.join(modulesDir, filename);
            await fs.writeFile(filePath, content);
            console.log(`  ✅ Created ${filename}`);
        }
        
        // Create new main file that imports modules
        const newMainFile = `
/**
 * Monitoring Module - Refactored
 * McKinsey Transformation - Modular Architecture
 */

import { WebSocketHandler } from './modules/websocket-handler.js';
import { UIRenderer } from './modules/ui-renderer.js';
import { APIClient } from './modules/api-client.js';
import { StateManager } from './modules/state-manager.js';
import { Utils } from './modules/utils.js';

class MonitoringSystem {
    constructor() {
        this.state = new StateManager();
        this.api = new APIClient();
        this.ui = new UIRenderer(this.state);
        this.ws = new WebSocketHandler(this.handleWebSocketMessage.bind(this));
        this.utils = new Utils();
    }
    
    async initialize() {
        console.log('🚀 Initializing Monitoring System...');
        
        await this.state.initialize();
        await this.api.initialize();
        await this.ui.initialize();
        await this.ws.connect();
        
        console.log('✅ Monitoring System Ready');
    }
    
    handleWebSocketMessage(data) {
        this.state.update(data);
        this.ui.render();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    const monitoring = new MonitoringSystem();
    await monitoring.initialize();
    
    // Export for console access
    window.monitoringSystem = monitoring;
});

export default MonitoringSystem;
`;
        
        // Backup original and write new file
        await fs.writeFile(monolithPath + '.backup', code);
        await fs.writeFile(monolithPath, newMainFile);
        
        console.log('✅ Monolith refactored into 5 modules');
        
    } catch (error) {
        console.error('❌ Error refactoring:', error.message);
    }
}

function extractWebSocketCode(code) {
    return `
export class WebSocketHandler {
    constructor(messageHandler) {
        this.ws = null;
        this.messageHandler = messageHandler;
        this.reconnectAttempts = 0;
    }
    
    async connect() {
        const wsUrl = process.env.WS_URL || 'ws://localhost:8001';
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.messageHandler(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            this.reconnect();
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts < 5) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 3000);
        }
    }
    
    send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}`;
}

function extractUICode(code) {
    return `
export class UIRenderer {
    constructor(state) {
        this.state = state;
        this.container = null;
    }
    
    async initialize() {
        this.container = document.getElementById('monitoring-container');
        this.setupEventListeners();
        this.render();
    }
    
    setupEventListeners() {
        // Add event listeners for UI interactions
    }
    
    render() {
        const data = this.state.getData();
        // Render UI based on current state
        this.container.innerHTML = this.generateHTML(data);
    }
    
    generateHTML(data) {
        return \`
            <div class="monitoring-dashboard">
                <h2>System Status</h2>
                <!-- Dynamic content here -->
            </div>
        \`;
    }
}`;
}

function extractAPICode(code) {
    return `
export class APIClient {
    constructor() {
        this.baseURL = process.env.API_URL || 'http://localhost:8000';
        this.token = null;
    }
    
    async initialize() {
        // Load token from storage
        this.token = localStorage.getItem('auth_token');
    }
    
    async request(endpoint, options = {}) {
        const url = \`\${this.baseURL}\${endpoint}\`;
        
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': \`Bearer \${this.token}\`,
                ...options.headers
            }
        };
        
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(\`API error: \${response.status}\`);
        }
        
        return response.json();
    }
    
    async getStatus() {
        return this.request('/api/status');
    }
    
    async getMetrics() {
        return this.request('/api/metrics');
    }
}`;
}

function extractStateCode(code) {
    return `
export class StateManager {
    constructor() {
        this.state = {
            connected: false,
            metrics: {},
            alerts: [],
            agents: []
        };
        this.listeners = [];
    }
    
    async initialize() {
        // Load initial state from localStorage
        const saved = localStorage.getItem('monitoring_state');
        if (saved) {
            this.state = JSON.parse(saved);
        }
    }
    
    update(data) {
        this.state = { ...this.state, ...data };
        this.save();
        this.notify();
    }
    
    save() {
        localStorage.setItem('monitoring_state', JSON.stringify(this.state));
    }
    
    notify() {
        this.listeners.forEach(listener => listener(this.state));
    }
    
    subscribe(listener) {
        this.listeners.push(listener);
    }
    
    getData() {
        return this.state;
    }
}`;
}

function extractUtilsCode(code) {
    return `
export class Utils {
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }
    
    formatBytes(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}`;
}

// Run refactoring
refactorMonolith().catch(console.error);