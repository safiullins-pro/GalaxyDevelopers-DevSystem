// Claude Connector for GalaxyDevelopers
class ClaudeConnector {
    constructor() {
        this.baseURL = 'http://localhost:8888';
        this.isConnected = false;
    }
    
    async connect() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            const data = await response.json();
            this.isConnected = data.status === 'ok';
            console.log('🔗 Claude connected:', this.isConnected);
            return this.isConnected;
        } catch (e) {
            console.error('❌ Claude connection failed:', e);
            return false;
        }
    }
    
    async sendMessage(prompt, settings = {}) {
        if (!this.isConnected) await this.connect();
        
        const response = await fetch(`${this.baseURL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                instruction: settings.instruction || '',
                context: settings.context || '',
                temperature: settings.temperature || 0,
                maxTokens: settings.maxTokens || 8192
            })
        });
        
        return await response.json();
    }
}

// Auto-inject Claude option
document.addEventListener('DOMContentLoaded', () => {
    const modelSelect = document.getElementById('model');
    if (modelSelect) {
        const claudeOption = document.createElement('option');
        claudeOption.value = 'claude-3-opus';
        claudeOption.textContent = '🤖 Claude 3 Opus';
        modelSelect.appendChild(claudeOption);
        
        console.log('✅ Claude option added to model selector');
    }
    
    // Initialize connector
    window.claudeConnector = new ClaudeConnector();
    window.claudeConnector.connect();
});

// Claude Bridge Control Panel Integration
document.addEventListener('DOMContentLoaded', () => {
    const bridgeToggle = document.getElementById('claude-bridge-enable');
    const rotatorToggle = document.getElementById('rotator-disable');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const testBtn = document.getElementById('test-claude-btn');
    
    let claudeEnabled = false;
    const CLAUDE_BRIDGE_URL = 'http://localhost:8889';
    
    // Check Claude bridge status
    async function checkClaudeStatus() {
        try {
            const response = await fetch(`${CLAUDE_BRIDGE_URL}/health`);
            if (response.ok) {
                statusIndicator.className = 'status-indicator connected';
                statusIndicator.textContent = '🟢';
                statusText.textContent = 'Claude Ready';
                return true;
            }
        } catch (e) {
            statusIndicator.className = 'status-indicator disconnected';
            statusIndicator.textContent = '⚫';
            statusText.textContent = 'Bridge Offline';
        }
        return false;
    }
    
    // Toggle Claude bridge
    bridgeToggle?.addEventListener('change', async (e) => {
        claudeEnabled = e.target.checked;
        if (claudeEnabled) {
            const status = await checkClaudeStatus();
            if (!status) {
                alert('Claude bridge not running! Start with: python3 ~/claude-bridge.py');
                bridgeToggle.checked = false;
                claudeEnabled = false;
            }
        } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusIndicator.textContent = '⚫';
            statusText.textContent = 'Disconnected';
        }
    });
    
    // Disable rotator when checked
    rotatorToggle?.addEventListener('change', (e) => {
        if (e.target.checked) {
            console.log('🔄 Rotator disabled');
            // Здесь можно добавить логику отключения ротатора
        }
    });
    
    // Test Claude button
    testBtn?.addEventListener('click', async () => {
        if (!claudeEnabled) {
            alert('Enable Claude bridge first!');
            return;
        }
        
        testBtn.disabled = true;
        testBtn.innerHTML = '<span class="forge-btn-text">⏳ Testing...</span>';
        
        try {
            const response = await fetch(`${CLAUDE_BRIDGE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: 'Say "Claude is connected!" if you can hear me.' })
            });
            
            const data = await response.json();
            if (data.response) {
                alert('✅ Claude says: ' + data.response);
            }
        } catch (e) {
            alert('❌ Test failed: ' + e.message);
        }
        
        testBtn.disabled = false;
        testBtn.innerHTML = '<span class="forge-btn-text">🧪 Test Claude</span>';
    });
    
    // Auto-check status every 5 seconds when enabled
    setInterval(() => {
        if (claudeEnabled) {
            checkClaudeStatus();
        }
    }, 5000);
});
