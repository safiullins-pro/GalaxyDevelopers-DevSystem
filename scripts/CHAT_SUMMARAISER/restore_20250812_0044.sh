#!/bin/bash
# Auto-generated restoration script
# Generated at: 2025-08-13 11:05:26.065679

# Restore /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/css/main.css
cat > '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/css/main.css.restored' << 'EOF'
:root {
    --bg-primary: #0a0a0a;
    --bg-secondary: #141414;
    --bg-tertiary: #1a1a1a;
    --bg-card: rgba(255, 255, 255, 0.03);
    --border-color: rgba(255, 255, 255, 0.12);
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --text-muted: #666666;
    --accent-primary: #6366f1;
    --accent-secondary: #8b5cf6;
    --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
    --tab-height: 35px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    flex-direction: column;
    position: relative;
}

body::before {
    content: '';
    position: fixed;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
    pointer-events: none;
    animation: float 20s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    33% { transform: translate(-30px, -30px) rotate(120deg); }
    66% { transform: translate(30px, -30px) rotate(240deg); }
}

.header {
    padding: 10px 30px;
    border-bottom: 1px solid var(--border-color);
    background: rgba(20, 20, 20, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    position: relative;
    z-index: 100;
}

.header h1 {
    font-size: 20px;
    font-weight: 600;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}

.wrapper {
    flex: 1;
    display: flex;
    overflow: hidden;
    position: relative;
}

.sidebar {
    width: 320px;
    background: rgba(20, 20, 20, 0.5);
    border-right: 1px solid var(--border-color);
    padding: 24px;
    overflow-y: auto;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.sidebar::-webkit-scrollbar {
    width: 6px;
}

.sidebar::-webkit-scrollbar-track {
    background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* Неоновая полоса статуса */
.status-strip {
    height: 3px;
    width: 100%;
    position: relative;
    overflow: hidden;
    background: transparent;
    border-bottom: 1px solid var(--border-color);
}

.status-strip::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
        transparent 0%,
        transparent 10%,
        var(--accent-primary) 50%,
        transparent 90%,
        transparent 100%);
    box-shadow: 0 0 8px rgba(99, 102, 241, 0.5), 
               0 0 16px rgba(99, 102, 241, 0.3);
    transition: all 0.3s ease;
}

.status-strip.error::before {
    background: linear-gradient(90deg, 
        transparent 0%,
        transparent 10%,
        var(--error) 50%,
        transparent 90%,
        transparent 100%);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5), 
               0 0 16px rgba(239, 68, 68, 0.3);
}

.status-strip.warning::before {
    background: linear-gradient(90deg, 
        transparent 0%,
        transparent 10%,
        var(--warning) 50%,
        transparent 90%,
        transparent 100%);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.5), 
               0 0 16px rgba(245, 158, 11, 0.3);
}

.status-strip.loading::before {
    background: linear-gradient(90deg, 
        transparent 0%, 
        var(--accent-primary) 50%, 
        transparent 100%);
    animation: statusFlow 2s ease-in-out infinite;
}

@keyframes statusFlow {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* Proximity язычок - ПОЛНОСТЬЮ СКРЫТ изначально */
.proximity-instruction {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%) translateY(-100%);
    z-index: 60;
    overflow: visible;
    width: fit-content;
    min-width: 200px;
}

/* Язычок */
.instruction-tab {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 0 0 12px 12px;
    padding: 8px 24px;
    cursor: pointer;
    font-size: 12px;
    color: white;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    text-align: center;
    height: var(--tab-height);
    display: flex;
    align-items: center;
    justify-content: center;
    user-select: none;
    white-space: nowrap;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    position: relative;
    overflow: hidden;
}

.instruction-tab::before {
    content: '📝';
    margin-right: 6px;
    font-size: 14px;
}

.instruction-tab::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s ease;
}

.instruction-tab:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.instruction-tab:hover::after {
    left: 100%;
}

/* Состояние когда панель раскрыта по клику */
.proximity-instruction.expanded {
    width: 70%;
}

.proximity-instruction.expanded .instruction-tab {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
}

.proximity-instruction.expanded .instruction-panel {
    display: block;
}


/* Панель с textarea - скрыта по умолчанию */
.instruction-panel {
    padding: 10px;
    display: none;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0 0 8px 8px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.instruction-panel textarea {
    width: calc(100% - 20px);
    height: 100px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 10px;
    color: var(--text-primary);
    resize: vertical;
    font-family: inherit;
    font-size: 13px;
    outline: none;
}

.instruction-panel textarea:focus {
    outline: none;
    border-color: var(--accent-primary);
}

.instruction-panel textarea::placeholder {
    color: var(--text-secondary);
}

.content {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
}

/* Pipeline Status Panel */
.pipeline-status {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
    border: 1px solid rgba(102, 126, 234, 0.2);
}

.pipeline-status h3 {
    color: var(--text-primary);
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.pipeline-stages {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.stage {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    transition: all 0.3s ease;
    border: 1px solid transparent;
    cursor: pointer;
}

.stage:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(102, 126, 234, 0.3);
    transform: translateX(4px);
}

.stage.active {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    border-color: rgba(102, 126, 234, 0.4);
}

.stage-icon {
    font-size: 16px;
    margin-right: 10px;
}

.stage-name {
    flex: 1;
    font-size: 11px;
    font-weight: 500;
    color: var(--text-secondary);
}

.stage.active .stage-name {
    color: var(--text-primary);
}

.stage-status {
    font-size: 14px;
}

/* Agent Status Panel */
.agent-status {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
    border: 1px solid rgba(16, 185, 129, 0.2);
}

.agent-status h3 {
    color: var(--text-primary);
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.agent-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.agent-item {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 6px;
    font-size: 11px;
    transition: all 0.2s ease;
}

.agent-item:hover {
    background: rgba(255, 255, 255, 0.05);
}

.agent-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
    margin-right: 10px;
    position: relative;
}

.agent-item.active .agent-indicator {
    background: #10b981;
    animation: pulse 2s ease-in-out infinite;
}

.agent-item.active .agent-indicator::after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.3);
    animation: ripple 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

@keyframes ripple {
    0% { transform: scale(1); opacity: 1; }
    100% { transform: scale(1.5); opacity: 0; }
}

.agent-item > span:nth-child(2) {
    flex: 1;
    color: var(--text-secondary);
    font-weight: 500;
}

.agent-item.active > span:nth-child(2) {
    color: var(--text-primary);
}

.agent-task {
    font-size: 10px;
    color: var(--text-muted);
    font-style: italic;
}

.body {
    flex: 1;
    padding: 30px 0;
    overflow-y: auto;
    background: var(--bg-primary);
    position: relative;
}

.body::-webkit-scrollbar {
    width: 6px;
}

.body::-webkit-scrollbar-track {
    background: transparent;
}

.body::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

.footer {
    border-top: 1px solid var(--border-color);
    padding: 15px;
    background: rgba(20, 20, 20, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

.message {
    margin: 0 30px 24px 30px;
    padding: 16px 20px;
    border-radius: 16px;
    white-space: pre-wrap;
    word-wrap: break-word;
    position: relative;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.user-message {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    margin-left: auto;
    max-width: 70%;
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}

.ai-message {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    max-width: 70%;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.input-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

#prompt-input {
    flex: 1;
    padding: 12px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: 12px;
    font-size: 14px;
    font-family: inherit;
    resize: none;
    min-height: 44px;
    max-height: 300px;
    height: 44px;
    overflow-y: hidden;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    line-height: 20px;
}

#prompt-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

#prompt-input::placeholder {
    color: var(--text-muted);
}

#send-btn {
    padding: 14px 20px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    height: 44px;
    min-width: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
}

#send-btn:hover {
    background: var(--bg-card);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 0 8px rgba(99, 102, 241, 0.15),
               inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transform: translateY(-1px);
}

#send-btn:active {
    transform: translateY(0);
    box-shadow: 0 0 4px rgba(99, 102, 241, 0.1);
}

#send-btn:disabled {
    background: var(--bg-tertiary);
    cursor: not-allowed;
    opacity: 0.5;
}

.settings-section {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 0;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.2s ease;
}

.settings-section:hover {
    border-color: rgba(99, 102, 241, 0.2);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.sidebar h3 {
    font-size: 12px;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 8px;
    margin-top: 16px;
    letter-spacing: 1px;
    font-weight: 600;
}

.sidebar h3:first-child {
    margin-top: 0;
}

textarea.settings, input.settings, select.settings {
    width: 100%;
    padding: 12px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: 8px;
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 13px;
    resize: none;
    min-height: 100px;
    transition: all 0.2s ease;
}

textarea.settings:focus, input.settings:focus, select.settings:focus {
    outline: none;
    border-color: var(--accent-primary);
    background: rgba(99, 102, 241, 0.05);
}

select.settings {
    min-height: 44px;
    cursor: pointer;
}

input.settings {
    min-height: 44px;
}

.status {
    padding: 12px 30px;
    background: rgba(20, 20, 20, 0.8);
    border-top: 1px solid var(--border-color);
    font-size: 12px;
    color: var(--text-muted);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    display: flex;
    align-items: center;
    gap: 8px;
}

.status::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--success);
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.error {
    color: var(--error);
}

.error::before {
    background: var(--error);
}

.loading {
    color: var(--accent-primary);
}

.loading::before {
    background: var(--accent-primary);
    animation: pulse 1s ease-in-out infinite;
}

#screenshot-btn {
    position: absolute;
    right: 30px;
    top: 50%;
    transform: translateY(-50%);
    padding: 10px 20px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: 10px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

#screenshot-btn:hover {
    background: rgba(99, 102, 241, 0.1);
    border-color: var(--accent-primary);
    transform: translateY(-50%) scale(1.05);
}

/* Tools panel */
.tools-panel {
    position: absolute;
    right: 30px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    gap: 10px;
    align-items: center;
}

.tool-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.tool-btn:hover {
    background: rgba(99, 102, 241, 0.1);
    border-color: var(--accent-primary);
    transform: scale(1.1);
}

.tool-btn.active {
    background: var(--accent-gradient);
    border-color: transparent;
}

.sub-tools {
    display: none;
    gap: 8px;
}

.sub-tools.show {
    display: flex;
}

/* Element selector mode */
body.selector-mode * {
    cursor: crosshair !important;
}

body.selector-mode *:hover {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 2px;
}

/* Streaming text */
@keyframes thinking {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}

.thinking-indicator {
    color: var(--accent-primary);
    font-style: italic;
    animation: thinking 1.5s ease-in-out infinite;
}

/* Попап для комментария к элементу */
.comment-popup {
    position: fixed;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    z-index: 10000;
    min-width: 300px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

.comment-popup textarea {
    width: 100%;
    min-height: 80px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: 8px;
    padding: 8px;
    margin: 8px 0;
    resize: none;
    font-family: inherit;
}

.comment-popup-buttons {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.comment-popup button {
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
}

.comment-popup button:hover {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
}

.comment-popup-title {
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 8px;
}
EOF

# Restore /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/js/app.js
cat > '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/js/app.js.restored' << 'EOF'
const chatArea = document.getElementById('chat-area');
const promptInput = document.getElementById('prompt-input');
const sendBtn = document.getElementById('send-btn');
const contextEl = document.getElementById('context');
const modelEl = document.getElementById('model');
const structureBtn = document.getElementById('structure-btn');
const toolsBtn = document.getElementById('tools-btn');
const subTools = document.getElementById('sub-tools');
const selectorBtn = document.getElementById('selector-btn');
const statusStrip = document.getElementById('status-strip');
const instructionTextarea = document.getElementById('instruction-textarea');

let isProcessing = false;
let selectorMode = false;

function addMessage(text, isUser = false, streaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'} ${streaming ? 'streaming' : ''}`;
    messageDiv.textContent = text;
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    return messageDiv;
}

function setStatus(text, isError = false, isWarning = false) {
    // Обновляем неоновую полосу
    statusStrip.className = 'status-strip';
    if (isError) {
        statusStrip.classList.add('error');
    } else if (isWarning) {
        statusStrip.classList.add('warning');
    }
    
    // Статусная строка обновлена через statusStrip
}

async function sendMessage() {
    if (isProcessing || !promptInput.value.trim()) return;
    
    const prompt = promptInput.value.trim();
    const instruction = instructionTextarea.value.trim();
    const context = contextEl.value.trim();
    const endpoint = '/chat';
    const model = modelEl.value;
    
    isProcessing = true;
    sendBtn.disabled = true;
    
    addMessage(prompt, true);
    promptInput.value = '';
    
    setStatus('Processing...', false, false);
    statusStrip.classList.add('loading');
    
    // Создаем пустое сообщение для streaming
    const aiMessageDiv = addMessage('', false, true);
    
    // Показываем индикатор размышления
    aiMessageDiv.innerHTML = '<span class="thinking-indicator">Thinking...</span>';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt,
                instruction,
                context,
                model
                // stream: true  // ВРЕМЕННО ОТКЛЮЧЕНО
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Обрабатываем streaming ответ
        if (response.headers.get('content-type')?.includes('text/event-stream')) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            
            aiMessageDiv.textContent = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') continue;
                        
                        try {
                            const json = JSON.parse(data);
                            if (json.chunk) {
                                fullText += json.chunk;
                                aiMessageDiv.textContent = fullText;
                                chatArea.scrollTop = chatArea.scrollHeight;
                            }
                        } catch (e) {
                            // Игнорируем ошибки парсинга
                        }
                    }
                }
            }
            
            aiMessageDiv.classList.remove('streaming');
        } else {
            // Fallback к обычному режиму
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            aiMessageDiv.textContent = data.response;
            aiMessageDiv.classList.remove('streaming');
        }
        
        setStatus('Ready', false, false);
        
    } catch (error) {
        addMessage(`Error: ${error.message}`, false);
        setStatus(`Error: ${error.message}`, true, false);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        promptInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);

promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey || e.shiftKey)) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea
promptInput.addEventListener('input', () => {
    promptInput.style.height = '44px';
    promptInput.style.height = Math.min(promptInput.scrollHeight, 300) + 'px';
});

// Tools panel
toolsBtn.addEventListener('click', () => {
    subTools.classList.toggle('show');
    toolsBtn.classList.toggle('active');
});

// Send page structure (HTML without scripts)
structureBtn.addEventListener('click', async () => {
    // Закрываем панель
    subTools.classList.remove('show');
    toolsBtn.classList.remove('active');
    
    // Клонируем документ и удаляем скрипты
    const docClone = document.documentElement.cloneNode(true);
    const scripts = docClone.querySelectorAll('script');
    scripts.forEach(script => script.remove());
    
    // Убираем inline JS обработчики
    const allElements = docClone.querySelectorAll('*');
    allElements.forEach(el => {
        Array.from(el.attributes).forEach(attr => {
            if (attr.name.startsWith('on')) {
                el.removeAttribute(attr.name);
            }
        });
    });
    
    const htmlStructure = docClone.outerHTML;
    
    try {
        await fetch('http://127.0.0.1:37777/element-selected', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                element: 'FULL_PAGE_STRUCTURE',
                html: htmlStructure,
                info: 'Full page HTML structure without scripts'
            })
        });
        
        // Меняем иконку на галочку
        const originalIcon = structureBtn.textContent;
        structureBtn.textContent = '✅';
        setTimeout(() => {
            structureBtn.textContent = originalIcon;
        }, 2000);
    } catch (error) {
        console.error('Structure send error:', error);
    }
});

// Element selector mode
selectorBtn.addEventListener('click', () => {
    selectorMode = !selectorMode;
    document.body.classList.toggle('selector-mode');
    selectorBtn.classList.toggle('active');
    
    if (selectorMode) {
        // Закрываем панель
        subTools.classList.remove('show');
        toolsBtn.classList.remove('active');
        
        // Обработчик клика по элементу
        document.addEventListener('click', handleElementClick);
    } else {
        document.removeEventListener('click', handleElementClick);
    }
});

async function handleElementClick(e) {
    // Не реагируем на клики по кнопкам инструментов и попапу
    if (e.target.closest('.tools-panel') || e.target.closest('.comment-popup')) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    const element = e.target;
    const selector = getElementSelector(element);
    const html = element.outerHTML;
    
    // Получаем путь к элементу и его контекст
    const elementPath = getElementPath(element);
    const parentHTML = element.parentElement ? element.parentElement.outerHTML : null;
    
    // Получаем вычисленные стили
    const computedStyles = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    
    // Собираем важные стили
    const styles = {
        width: computedStyles.width,
        height: computedStyles.height,
        padding: computedStyles.padding,
        margin: computedStyles.margin,
        display: computedStyles.display,
        position: computedStyles.position,
        top: computedStyles.top,
        left: computedStyles.left,
        right: computedStyles.right,
        bottom: computedStyles.bottom,
        backgroundColor: computedStyles.backgroundColor,
        color: computedStyles.color,
        fontSize: computedStyles.fontSize,
        fontFamily: computedStyles.fontFamily,
        border: computedStyles.border,
        borderRadius: computedStyles.borderRadius,
        overflow: computedStyles.overflow,
        flex: computedStyles.flex,
        flexDirection: computedStyles.flexDirection,
        zIndex: computedStyles.zIndex
    };
    
    // Размеры и позиция
    const dimensions = {
        boundingRect: {
            width: rect.width,
            height: rect.height,
            top: rect.top,
            left: rect.left,
            right: rect.right,
            bottom: rect.bottom
        },
        offsetWidth: element.offsetWidth,
        offsetHeight: element.offsetHeight,
        scrollWidth: element.scrollWidth,
        scrollHeight: element.scrollHeight,
        clientWidth: element.clientWidth,
        clientHeight: element.clientHeight
    };
    
    // Создаем попап для комментария
    const popup = document.createElement('div');
    popup.className = 'comment-popup';
    popup.style.left = e.clientX + 10 + 'px';
    popup.style.top = e.clientY + 10 + 'px';
    
    // Корректируем позицию если выходит за экран
    if (e.clientX + 310 > window.innerWidth) {
        popup.style.left = (e.clientX - 310) + 'px';
    }
    if (e.clientY + 200 > window.innerHeight) {
        popup.style.top = (e.clientY - 200) + 'px';
    }
    
    popup.innerHTML = `
        <div class="comment-popup-title">Comment for: ${elementPath}</div>
        <textarea placeholder="What needs to be fixed here?" autofocus></textarea>
        <div class="comment-popup-buttons">
            <button class="cancel-btn">Cancel</button>
            <button class="send-btn">Send</button>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    const textarea = popup.querySelector('textarea');
    const sendBtn = popup.querySelector('.send-btn');
    const cancelBtn = popup.querySelector('.cancel-btn');
    
    textarea.focus();
    
    // Обработчик отправки
    const sendElement = async () => {
        const comment = textarea.value.trim();
        
        try {
            const response = await fetch('http://127.0.0.1:37777/element-selected', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    element: `ELEMENT: ${elementPath}`,
                    comment: comment || 'No comment',
                    selector,
                    html,
                    parentHTML,
                    tagName: element.tagName,
                    className: element.className,
                    id: element.id,
                    text: element.textContent?.substring(0, 200),
                    attributes: Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value})),
                    computedStyles: styles,
                    dimensions: dimensions
                })
            });
            
            if (response.ok) {
                // Показываем что элемент отправлен
                element.style.outline = '3px solid var(--success)';
                setTimeout(() => {
                    element.style.outline = '';
                }, 1000);
                
                // Обновляем статус
                setStatus('Element sent to backend successfully', false, false);
                setTimeout(() => setStatus('Ready', false, false), 3000);
            } else {
                throw new Error('Failed to send element');
            }
        } catch (error) {
            console.error('Failed to send element:', error);
            setStatus('Error: Failed to send element', true, false);
        }
        
        // Удаляем попап
        popup.remove();
        
        // Выключаем режим селектора
        selectorMode = false;
        document.body.classList.remove('selector-mode');
        selectorBtn.classList.remove('active');
        document.removeEventListener('click', handleElementClick);
    };
    
    // Обработчик отмены
    const cancel = () => {
        popup.remove();
        // Остаемся в режиме селектора
    };
    
    sendBtn.addEventListener('click', sendElement);
    cancelBtn.addEventListener('click', cancel);
    
    // Enter отправляет, Escape отменяет
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            sendElement();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            cancel();
        }
    });
}

function getElementSelector(element) {
    if (element.id) return `#${element.id}`;
    if (element.className) return `.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
}

function getElementPath(element) {
    const path = [];
    while (element && element.nodeType === Node.ELEMENT_NODE) {
        let selector = element.tagName.toLowerCase();
        if (element.id) {
            selector += '#' + element.id;
            path.unshift(selector);
            break;
        } else if (element.className) {
            selector += '.' + element.className.split(' ').join('.');
        }
        path.unshift(selector);
        element = element.parentElement;
    }
    return path.join(' > ');
}

// Save settings to localStorage
contextEl.addEventListener('change', () => {
    localStorage.setItem('galaxydevelopers-ai-context', contextEl.value);
});

modelEl.addEventListener('change', () => {
    localStorage.setItem('galaxydevelopers-ai-model', modelEl.value);
});

// --- НАЧАЛО НОВОГО КОДА ДЛЯ PROXIMITY-ПАНЕЛИ ---

const proximityInstruction = document.getElementById('proximity-instruction');
const instructionTab = document.getElementById('instruction-tab');
const instructionPanel = document.getElementById('instruction-panel');

// Зона активации в пикселях от верхнего края окна
const activationZone = 100;

// Переменные для плавной анимации (используем пиксели)
let tabHeightPx = 35; // Высота язычка в пикселях
let currentY = -35; // Текущая позиция в пикселях (изначально скрыт)
let targetY = -35;  // Целевая позиция в пикселях
const smoothing = 0.08; // Коэффициент сглаживания (меньше = плавнее)

let isPanelExpanded = false; // Флаг раскрытия панели по клику
let isMouseOverPanel = false; // Флаг, находится ли мышь над самой панелью

// Инициализация: получаем реальную высоту язычка
function initPanel() {
    tabHeightPx = instructionTab.offsetHeight || 35;
    currentY = -tabHeightPx;
    targetY = -tabHeightPx;
    proximityInstruction.style.transform = `translateX(-50%) translateY(${currentY}px)`;
}

// 1. Отслеживаем, когда мышь заходит на панель и уходит с нее
proximityInstruction.addEventListener('mouseenter', () => {
    isMouseOverPanel = true;
    if (!isPanelExpanded) {
        targetY = 0; // Показываем язычок полностью
    }
});

proximityInstruction.addEventListener('mouseleave', () => {
    isMouseOverPanel = false;
    if (!isPanelExpanded) {
        targetY = -tabHeightPx; // Скрываем язычок
    }
});

// 2. КЛИК НА ЯЗЫЧОК - полное раскрытие панели
instructionTab.addEventListener('click', (e) => {
    e.stopPropagation();
    isPanelExpanded = !isPanelExpanded;
    proximityInstruction.classList.toggle('expanded');
    
    if (isPanelExpanded) {
        // При раскрытии - полностью выдвигаем
        targetY = 0;
        currentY = 0; // Сразу устанавливаем позицию
        proximityInstruction.style.transform = `translateX(-50%) translateY(0px)`;
    } else {
        // При закрытии - скрываем язычок
        targetY = -tabHeightPx;
    }
});

// 3. Закрытие при клике вне панели
document.addEventListener('click', (event) => {
    if (isPanelExpanded && !proximityInstruction.contains(event.target)) {
        isPanelExpanded = false;
        proximityInstruction.classList.remove('expanded');
        targetY = -tabHeightPx; // Скрываем язычок при закрытии
    }
});

// 4. Отслеживаем движение мыши ПО ВСЕМУ ОКНУ
window.addEventListener('mousemove', (e) => {
    // Если панель раскрыта по клику - не меняем ее позицию
    if (isPanelExpanded) return;
    
    // Если мышь наведена на саму панель
    if (isMouseOverPanel) {
        targetY = 0; // Полностью видимая панель при наведении
        return;
    }

    const mouseY = e.clientY;

    if (mouseY < activationZone) {
        // Мышь в зоне активации. Плавно показываем язычок
        // При mouseY = 0 -> targetY = 0 (полностью видим)
        // При mouseY = activationZone -> targetY = -tabHeightPx (полностью скрыт)
        const progress = mouseY / activationZone;
        targetY = -tabHeightPx * progress;
    } else {
        // Мышь вне зоны активации - скрываем язычок
        targetY = -tabHeightPx;
    }
});

// 5. Главный цикл анимации. Он работает постоянно.
function animatePanel() {
    // Анимируем только если панель не раскрыта кликом
    if (!isPanelExpanded) {
        const diff = targetY - currentY;
        // Если разница больше порога, продолжаем анимацию
        if (Math.abs(diff) > 0.01) {
            // Используем easing для более плавного движения
            currentY += diff * smoothing;
            
            // Округляем до 2 знаков после запятой для точности
            const roundedY = Math.round(currentY * 100) / 100;
            proximityInstruction.style.transform = `translateX(-50%) translateY(${roundedY}px)`;
        } else {
            // Если достаточно близко к цели, устанавливаем точное значение
            currentY = targetY;
            proximityInstruction.style.transform = `translateX(-50%) translateY(${targetY}px)`;
        }
    }
    requestAnimationFrame(animatePanel);
}

// --- КОНЕЦ НОВОГО КОДА ДЛЯ PROXIMITY-ПАНЕЛИ ---

// Сохранение в localStorage  
if (instructionTextarea) {
    instructionTextarea.addEventListener('input', () => {
        localStorage.setItem('galaxydevelopers-ai-instruction', instructionTextarea.value);
    });
}

// Load settings from localStorage
window.addEventListener('load', () => {
    const savedInstruction = localStorage.getItem('galaxydevelopers-ai-instruction');
    const savedContext = localStorage.getItem('galaxydevelopers-ai-context');
    const savedModel = localStorage.getItem('galaxydevelopers-ai-model');
    
    if (savedInstruction && instructionTextarea) instructionTextarea.value = savedInstruction;
    if (savedContext && contextEl) contextEl.value = savedContext;
    if (savedModel && modelEl) modelEl.value = savedModel;
    
    // ИНИЦИАЛИЗАЦИЯ PROXIMITY ПАНЕЛИ
    initPanel();
    animatePanel();
    
    promptInput.focus();
});
EOF

# Restore /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/index.html
cat > '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/index.html.restored' << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GalaxyDevelopers AI Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <div class="header">
        <h1>GalaxyDevelopers AI Chat</h1>
        <div class="tools-panel">
            <button id="tools-btn" class="tool-btn" title="Tools">🛠️</button>
            <div id="sub-tools" class="sub-tools">
                <button id="selector-btn" class="tool-btn" title="Element Selector">🎯</button>
                <button id="structure-btn" class="tool-btn" title="Send Page Structure">📄</button>
            </div>
        </div>
    </div>
    
    <div class="wrapper">
        <div class="sidebar">
            <!-- Pipeline Status -->
            <div class="pipeline-status">
                <h3>📊 PIPELINE STATUS</h3>
                <div class="pipeline-stages">
                    <div class="stage active" data-stage="inbox">
                        <span class="stage-icon">📥</span>
                        <span class="stage-name">INBOX</span>
                        <span class="stage-status">✓</span>
                    </div>
                    <div class="stage" data-stage="research">
                        <span class="stage-icon">🔍</span>
                        <span class="stage-name">RESEARCH</span>
                        <span class="stage-status">⚙</span>
                    </div>
                    <div class="stage" data-stage="design">
                        <span class="stage-icon">🎨</span>
                        <span class="stage-name">DESIGN</span>
                        <span class="stage-status">⏸</span>
                    </div>
                    <div class="stage" data-stage="content">
                        <span class="stage-icon">📝</span>
                        <span class="stage-name">CONTENT</span>
                        <span class="stage-status">⏸</span>
                    </div>
                    <div class="stage" data-stage="development">
                        <span class="stage-icon">💻</span>
                        <span class="stage-name">DEVELOPMENT</span>
                        <span class="stage-status">⏸</span>
                    </div>
                    <div class="stage" data-stage="review">
                        <span class="stage-icon">✅</span>
                        <span class="stage-name">REVIEW</span>
                        <span class="stage-status">⏸</span>
                    </div>
                    <div class="stage" data-stage="deployment">
                        <span class="stage-icon">🚀</span>
                        <span class="stage-name">DEPLOY</span>
                        <span class="stage-status">⏸</span>
                    </div>
                </div>
            </div>

            <!-- Agent Status -->
            <div class="agent-status">
                <h3>🤖 AGENT STATUS</h3>
                <div class="agent-list">
                    <div class="agent-item active">
                        <span class="agent-indicator"></span>
                        <span>ResearchAgent</span>
                        <span class="agent-task">Analyzing...</span>
                    </div>
                    <div class="agent-item">
                        <span class="agent-indicator"></span>
                        <span>ComposerAgent</span>
                        <span class="agent-task">Idle</span>
                    </div>
                    <div class="agent-item">
                        <span class="agent-indicator"></span>
                        <span>ReviewerAgent</span>
                        <span class="agent-task">Idle</span>
                    </div>
                    <div class="agent-item">
                        <span class="agent-indicator"></span>
                        <span>IntegratorAgent</span>
                        <span class="agent-task">Idle</span>
                    </div>
                    <div class="agent-item">
                        <span class="agent-indicator"></span>
                        <span>PublisherAgent</span>
                        <span class="agent-task">Idle</span>
                    </div>
                </div>
            </div>
            
            <h3>CONTEXT</h3>
            <textarea id="context" class="settings" placeholder="Additional context..."></textarea>
            
            <h3>MODEL</h3>
            <select id="model" class="settings">
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Fast)</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                    <option value="gemini-2.0-flash-thinking-exp">Gemini 2.0 Thinking</option>
                </select>
            
        </div>
        
        <div class="content">
            <div class="status-strip" id="status-strip"></div>
            <div class="body" id="chat-area">
                <div class="proximity-instruction" id="proximity-instruction">
                    <div class="instruction-tab" id="instruction-tab">SYSTEM INSTRUCTION</div>
                    <div class="instruction-panel" id="instruction-panel">
                        <textarea id="instruction-textarea" placeholder="System instruction..."></textarea>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <div class="input-container">
                    <textarea id="prompt-input" placeholder="Type your message..."></textarea>
                    <button id="send-btn">▶</button>
                </div>
            </div>
            
        </div>
    </div>

    <script src="js/app.js"></script>
    <script src="memory-system.js"></script>
    <script src="pipeline-monitor.js"></script>
    <script src="js/monitoring-integration.js"></script>
</body>
</html>
EOF

