const chatArea = document.getElementById('chat-area');
const promptInput = document.getElementById('prompt-input');
const sendBtn = document.getElementById('send-btn');
const statusBar = document.getElementById('status');
const instructionEl = document.getElementById('instruction');
const contextEl = document.getElementById('context');
const endpointEl = document.getElementById('endpoint');
const modelEl = document.getElementById('model');
const structureBtn = document.getElementById('structure-btn');
const toolsBtn = document.getElementById('tools-btn');
const subTools = document.getElementById('sub-tools');
const selectorBtn = document.getElementById('selector-btn');

// FORGE elements
const temperatureSlider = document.getElementById('temperature');
const tempValue = document.getElementById('temp-value');
const topKInput = document.getElementById('topK');
const topPSlider = document.getElementById('topP');
const topPValue = document.getElementById('topP-value');
const maxTokensInput = document.getElementById('maxTokens');

let isProcessing = false;
let selectorMode = false;
let currentModel = 'gemini-2.0-flash-thinking-exp';

// Temperature slider update
if (temperatureSlider && tempValue) {
    temperatureSlider.addEventListener('input', () => {
        tempValue.textContent = parseFloat(temperatureSlider.value).toFixed(1);
    });
}

// TopP slider update
if (topPSlider && topPValue) {
    topPSlider.addEventListener('input', () => {
        topPValue.textContent = parseFloat(topPSlider.value).toFixed(1);
    });
}

// Mode buttons
document.addEventListener('DOMContentLoaded', function() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (btn.id === 'forge-mode-btn') {
                setForgeMode();
            } else if (btn.id === 'creative-mode-btn') {
                setCreativeMode();
            } else if (btn.id === 'balanced-mode-btn') {
                setBalancedMode();
            }
        });
    });
});

function setForgeMode() {
    if (temperatureSlider) temperatureSlider.value = 0;
    if (tempValue) tempValue.textContent = '0.0';
    if (topKInput) topKInput.value = 1;
    if (topPSlider) topPSlider.value = 1;
    if (topPValue) topPValue.textContent = '1.0';
}

function setCreativeMode() {
    if (temperatureSlider) temperatureSlider.value = 1.2;
    if (tempValue) tempValue.textContent = '1.2';
    if (topKInput) topKInput.value = 40;
    if (topPSlider) topPSlider.value = 0.9;
    if (topPValue) topPValue.textContent = '0.9';
}

function setBalancedMode() {
    if (temperatureSlider) temperatureSlider.value = 0.7;
    if (tempValue) tempValue.textContent = '0.7';
    if (topKInput) topKInput.value = 20;
    if (topPSlider) topPSlider.value = 0.95;
    if (topPValue) topPValue.textContent = '0.95';
}

function addMessage(text, isUser = false, streaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'} ${streaming ? 'streaming' : ''}`;
    messageDiv.textContent = text;
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    return messageDiv;
}

function setStatus(text, isError = false, isLoading = false) {
    const statusStrip = document.querySelector('.status-strip');
    if (statusStrip) {
        statusStrip.className = 'status-strip';
        if (isLoading) statusStrip.classList.add('loading');
        if (isError) statusStrip.classList.add('error');
    }
}

async function sendMessage() {
    if (isProcessing || !promptInput.value.trim()) return;
    
    const prompt = promptInput.value.trim();
    const instruction = instructionEl.value.trim();
    const context = contextEl.value.trim();
    
    // Debug: проверяем состояние переключателей памяти
    const memoryConversations = document.getElementById('memory-conversations')?.checked || false;
    const memorySnapshots = document.getElementById('memory-snapshots')?.checked || false;
    const memoryPrompts = document.getElementById('memory-prompts')?.checked || false;
    const memoryVectors = document.getElementById('memory-vectors')?.checked || false;
    
    console.log('🧠 MEMORY DEBUG:', {
        conversations: memoryConversations,
        snapshots: memorySnapshots,
        prompts: memoryPrompts,
        vectors: memoryVectors
    });
    
    // Check if Claude Bridge is enabled
    const claudeBridgeEnabled = document.getElementById('claude-bridge-enable')?.checked;
    const endpoint = claudeBridgeEnabled ? 'http://localhost:8889/chat' : 'http://localhost:37777/chat';
    
    isProcessing = true;
    sendBtn.disabled = true;
    
    addMessage(prompt, true);
    promptInput.value = '';
    
    // Обновляем статус с информацией о памяти
    const memoryStatus = (memoryConversations || memorySnapshots || memoryPrompts || memoryVectors) 
        ? '🧠 Processing with memory...' 
        : 'Processing...';
    setStatus(memoryStatus, false, true);
    
    // Создаем пустое сообщение для streaming
    const aiMessageDiv = addMessage('', false, true);
    
    // Показываем индикатор размышления
    aiMessageDiv.innerHTML = '<span class="thinking-indicator">Thinking...</span>';
    
    try {
        const model = claudeBridgeEnabled ? 'claude-3-opus' : currentModel;
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt,
                instruction,
                context,
                model,
                temperature: parseFloat(temperatureSlider?.value || 0),
                topK: parseInt(topKInput?.value || 1),
                topP: parseFloat(topPSlider?.value || 1),
                maxTokens: parseInt(maxTokensInput?.value || 8192),
                useMemory: memoryConversations,
                memorySnapshots: memorySnapshots,
                memoryPrompts: memoryPrompts,
                memoryVectors: memoryVectors
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Fallback к обычному режиму
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        aiMessageDiv.textContent = data.response;
        aiMessageDiv.classList.remove('streaming');
        
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
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        sendMessage();
    }
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
            await fetch('http://127.0.0.1:37777/element-selected', {
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
                    attributes: Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))
                })
            });
            
            // Показываем что элемент отправлен
            element.style.outline = '3px solid var(--success)';
            setTimeout(() => {
                element.style.outline = '';
            }, 1000);
        } catch (error) {
            console.error('Failed to send element:', error);
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
            sendElement();
        } else if (e.key === 'Escape') {
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

// MEMORY CONTROL PANEL HANDLERS
document.addEventListener('DOMContentLoaded', function() {
    // Memory control buttons
    const memoryLoadBtn = document.getElementById('memory-load-btn');
    const memoryClearBtn = document.getElementById('memory-clear-btn');
    const memoryExportBtn = document.getElementById('memory-export-btn');
    const memoryPreviewContent = document.getElementById('memory-preview-content');
    
    // Load memory from API
    const loadMemoryPreview = async () => {
        try {
            console.log('🔄 Loading memory preview...');
            const response = await fetch('http://localhost:37777/memory/context?limit=5');
            console.log('📥 Memory response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📊 Memory data:', data);
            
            if (data.context && data.context.length > 0) {
                let memoryHtml = '';
                data.context.forEach(item => {
                    memoryHtml += `
                        <div class="memory-item">
                            <div class="memory-timestamp">[${item.timestamp}]</div>
                            <div class="memory-user">👤 ${item.user.substring(0, 80)}${item.user.length > 80 ? '...' : ''}</div>
                            <div class="memory-ai">🤖 ${item.assistant.substring(0, 80)}${item.assistant.length > 80 ? '...' : ''}</div>
                        </div>`;
                });
                memoryPreviewContent.innerHTML = memoryHtml;
            } else {
                memoryPreviewContent.textContent = 'No memory data available';
            }
        } catch (err) {
            memoryPreviewContent.textContent = 'Error loading memory: ' + err.message;
            console.error('Failed to load memory:', err);
        }
    };
    
    // Auto-load memory on page load
    loadMemoryPreview();
    
    // Load button handler
    if (memoryLoadBtn) {
        memoryLoadBtn.addEventListener('click', () => {
            loadMemoryPreview();
            memoryLoadBtn.textContent = '✅ Loaded';
            setTimeout(() => {
                memoryLoadBtn.textContent = '📥 Load';
            }, 1500);
        });
    }
    
    // Clear memory button handler
    if (memoryClearBtn) {
        memoryClearBtn.addEventListener('click', async () => {
            if (confirm('Вы уверены что хотите очистить всю память?')) {
                try {
                    // Clear memory API (пока заглушка)
                    console.log('🗑️ Clearing memory...');
                    memoryPreviewContent.textContent = 'Memory cleared';
                    
                    memoryClearBtn.textContent = '✅ Cleared';
                    setTimeout(() => {
                        memoryClearBtn.textContent = '🗑️ Clear';
                    }, 1500);
                } catch (err) {
                    console.error('Failed to clear memory:', err);
                }
            }
        });
    }
    
    // Export memory button handler
    if (memoryExportBtn) {
        memoryExportBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('http://localhost:37777/memory/context?limit=100');
                const data = await response.json();
                
                if (data.context) {
                    const exportData = JSON.stringify(data, null, 2);
                    const blob = new Blob([exportData], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `memory-export-${new Date().toISOString().substring(0, 19)}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    memoryExportBtn.textContent = '✅ Exported';
                    setTimeout(() => {
                        memoryExportBtn.textContent = '💾 Export';
                    }, 1500);
                }
            } catch (err) {
                console.error('Failed to export memory:', err);
            }
        });
    }
});

// Memory FORGE handlers
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик кнопки сохранения снапшота
    const saveSnapshotBtn = document.getElementById('memory-save-snapshot');
    if (saveSnapshotBtn) {
        saveSnapshotBtn.addEventListener('click', async () => {
            // Собираем весь контекст из чата
            const messages = Array.from(document.querySelectorAll('.message')).map(msg => ({
                type: msg.classList.contains('user-message') ? 'user' : 'ai',
                content: msg.textContent
            }));
            
            const snapshot = {
                context: JSON.stringify(messages),
                tags: ['manual', 'chat'],
                metadata: {
                    timestamp: new Date().toISOString(),
                    messageCount: messages.length
                }
            };
            
            try {
                const response = await fetch('http://localhost:37777/memory/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(snapshot)
                });
                
                if (response.ok) {
                    // Анимация успеха
                    saveSnapshotBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                    saveSnapshotBtn.querySelector('.forge-btn-text').textContent = '✅ Saved!';
                    
                    setTimeout(() => {
                        saveSnapshotBtn.style.background = '';
                        saveSnapshotBtn.querySelector('.forge-btn-text').textContent = '💾 Save Context Snapshot';
                    }, 2000);
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                console.error('Snapshot save error:', error);
                
                // Анимация ошибки
                saveSnapshotBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                saveSnapshotBtn.querySelector('.forge-btn-text').textContent = '❌ Error!';
                
                setTimeout(() => {
                    saveSnapshotBtn.style.background = '';
                    saveSnapshotBtn.querySelector('.forge-btn-text').textContent = '💾 Save Context Snapshot';
                }, 2000);
            }
        });
    }
});

// Save settings to localStorage
instructionEl.addEventListener('change', () => {
    localStorage.setItem('galaxydevelopers-ai-instruction', instructionEl.value);
});

contextEl.addEventListener('change', () => {
    localStorage.setItem('galaxydevelopers-ai-context', contextEl.value);
});

endpointEl.addEventListener('change', () => {
    localStorage.setItem('galaxydevelopers-ai-endpoint', endpointEl.value);
});

// Load settings from localStorage
window.addEventListener('load', () => {
    const savedInstruction = localStorage.getItem('galaxydevelopers-ai-instruction');
    const savedContext = localStorage.getItem('galaxydevelopers-ai-context');
    const savedEndpoint = localStorage.getItem('galaxydevelopers-ai-endpoint');
    const savedModel = localStorage.getItem('galaxydevelopers-ai-model');
    
    if (savedInstruction && instructionTextarea) instructionTextarea.value = savedInstruction;
    if (savedContext && contextEl) contextEl.value = savedContext;
    if (savedModel) {
        // Устанавливаем сохраненную модель
        currentModel = savedModel;
        // Обновляем отображение кнопки
        const modelNameSpan = document.querySelector(".current-model-name");
        if (modelNameSpan) {
            // Найдем display name через загрузку моделей
            loadModels().then(() => {
                // После загрузки моделей найдем нужную
                fetch('http://localhost:37777/models').then(r => r.json()).then(data => {
                    const model = data.models?.find(m => m.name === savedModel);
                    if (model && modelNameSpan) {
                        modelNameSpan.textContent = model.displayName;
                    }
                });
            });
        }
    }
    
    promptInput.focus();
});

async function loadModels() {
    try {
        const response = await fetch("http://localhost:37777/models");
        const data = await response.json();
        
        if (data.models) {
            renderModels(data.models, data.forge_recommended);
        }
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

function selectModel(modelName, displayName) {
    currentModel = modelName;
    
    // Update button text
    const modelNameSpan = document.querySelector(".current-model-name");
    if (modelNameSpan) {
        modelNameSpan.textContent = displayName;
    }
    
    // Сохраняем в localStorage
    localStorage.setItem('galaxydevelopers-ai-model', modelName);
    
    // Update selected card
    document.querySelectorAll(".model-card").forEach(card => {
        card.classList.remove("selected");
    });
    
    if (event && event.currentTarget) {
        event.currentTarget.classList.add("selected");
    }
    
    // Animate and close
    setTimeout(() => {
        hideModelPopup();
    }, 200);
}