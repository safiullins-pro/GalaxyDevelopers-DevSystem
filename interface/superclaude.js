// SUPERCLAUDE Integration
class SuperClaude {
    constructor() {
        this.enabled = false;
        this.bridgeUrl = 'http://localhost:8889';
        this.memory = {};
        this.init();
    }
    
    init() {
        // Get elements
        this.toggle = document.getElementById('claude-bridge-enable');
        this.statusIcon = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.memoryIcon = document.getElementById('memory-indicator');
        this.clearBtn = document.getElementById('claude-clear-memory');
        this.container = document.querySelector('.claude-compact');
        this.info = document.querySelector('.claude-info');
        
        // Setup handlers
        this.toggle?.addEventListener('change', (e) => this.toggleBridge(e.target.checked));
        this.clearBtn?.addEventListener('click', () => this.clearMemory());
        this.memoryIcon?.addEventListener('click', () => this.showMemory());
        
        // Check status on load
        this.checkStatus();
    }
    
    async toggleBridge(enable) {
        this.enabled = enable;
        
        if (enable) {
            const status = await this.checkStatus();
            if (status) {
                this.setStatus('connected');
                this.loadMemory();
                
                // Override main chat endpoint
                window.CLAUDE_ENABLED = true;
                window.CLAUDE_ENDPOINT = this.bridgeUrl + '/chat';
            } else {
                alert('SUPERCLAUDE bridge not running!\nStart with: python3 ~/claude-bridge-memory.py');
                this.toggle.checked = false;
                this.enabled = false;
            }
        } else {
            this.setStatus('disconnected');
            window.CLAUDE_ENABLED = false;
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch(`${this.bridgeUrl}/memory`);
            if (response.ok) {
                this.memory = await response.json();
                return true;
            }
        } catch (e) {
            console.error('Bridge offline:', e);
        }
        return false;
    }
    
    async loadMemory() {
        try {
            const response = await fetch(`${this.bridgeUrl}/memory`);
            this.memory = await response.json();
            
            // Update memory indicator
            if (Object.keys(this.memory).length > 0) {
                this.memoryIcon.classList.add('active');
                this.memoryIcon.title = `Memory: ${JSON.stringify(this.memory)}`;
            } else {
                this.memoryIcon.classList.remove('active');
            }
        } catch (e) {
            console.error('Failed to load memory:', e);
        }
    }
    
    async clearMemory() {
        if (!confirm('Clear SUPERCLAUDE memory?')) return;
        
        try {
            await fetch(`${this.bridgeUrl}/memory/clear`, { method: 'POST' });
            this.memory = {};
            this.memoryIcon.classList.remove('active');
            this.statusText.textContent = 'MEMORY CLEARED';
            setTimeout(() => {
                this.statusText.textContent = 'CONNECTED';
            }, 2000);
        } catch (e) {
            console.error('Failed to clear memory:', e);
        }
    }
    
    showMemory() {
        if (Object.keys(this.memory).length > 0) {
            alert('SUPERCLAUDE Memory:\n' + JSON.stringify(this.memory, null, 2));
        } else {
            alert('Memory is empty');
        }
    }
    
    setStatus(status) {
        if (status === 'connected') {
            this.statusIcon.textContent = '🟢';
            this.statusIcon.className = 'claude-status connected';
            this.statusText.textContent = 'CONNECTED';
            this.container.classList.add('active');
            this.info.classList.add('active');
            document.body.classList.add('claude-active');
        } else {
            this.statusIcon.textContent = '⚫';
            this.statusIcon.className = 'claude-status';
            this.statusText.textContent = 'OFF';
            this.container.classList.remove('active');
            this.info.classList.remove('active');
            document.body.classList.remove('claude-active');
        }
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.superClaude = new SuperClaude();
    
    // Override sendMessage in app.js
    const originalSend = window.sendMessage;
    window.sendMessage = async function() {
        if (window.CLAUDE_ENABLED) {
            // Redirect to SUPERCLAUDE
            const promptInput = document.getElementById('prompt-input');
            const prompt = promptInput.value.trim();
            if (!prompt) return;
            
            // Add user message
            const chatArea = document.getElementById('chat-area');
            const userMsg = document.createElement('div');
            userMsg.className = 'message user-message';
            userMsg.textContent = prompt;
            chatArea.appendChild(userMsg);
            promptInput.value = '';
            
            // Send to SUPERCLAUDE
            try {
                const response = await fetch(window.CLAUDE_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                
                const data = await response.json();
                
                // Add AI response
                const aiMsg = document.createElement('div');
                aiMsg.className = 'message ai-message';
                aiMsg.textContent = data.response;
                chatArea.appendChild(aiMsg);
                
                // Update memory indicator if needed
                if (data.memory) {
                    window.superClaude.memory = data.memory;
                    window.superClaude.loadMemory();
                }
                
                chatArea.scrollTop = chatArea.scrollHeight;
            } catch (e) {
                console.error('SUPERCLAUDE error:', e);
            }
        } else {
            // Use original function
            return originalSend.apply(this, arguments);
        }
    };
});