// PROXIMITY TAB HANDLER - ЯЗЫЧОК ПО КООРДИНАТАМ
class ProximityTab {
    constructor() {
        this.init();
    }
    
    init() {
        this.tab = document.querySelector('.proximity-instruction');
        this.isExpanded = false;
        
        if (!this.tab) return;
        
        // Mouse tracking для верхней области экрана
        document.addEventListener('mousemove', (e) => {
            if (!this.isExpanded && e.clientY <= 50) {
                // Мышь в верхней части - показываем язычок
                let progress = (50 - e.clientY) / 50; // 0 to 1
                let translateY = -90 + (progress * 100); // от -90% до 10px
                this.tab.style.transform = `translateX(-50%) translateY(${translateY}%)`;
            } else if (!this.isExpanded && e.clientY > 100) {
                // Мышь далеко - прячем
                this.tab.style.transform = 'translateX(-50%) translateY(-90%)';
            }
        });
        
        // Click handler for tab
        const tabBtn = document.querySelector('.instruction-tab');
        if (tabBtn) {
            tabBtn.addEventListener('click', () => {
                this.toggle();
            });
        }
    }
    
    toggle() {
        this.isExpanded = !this.isExpanded;
        if (this.isExpanded) {
            this.tab.style.transform = 'translateX(-50%) translateY(0px)';
        } else {
            // Возвращаем к mouse tracking
            const mouseY = event.clientY || 0;
            this.handleMouseMove(mouseY);
        }
    }
}

// Memory Panel - ПАНЕЛЬ ПАМЯТИ
class MemoryPanel {
    constructor() {
        this.visible = false;
        this.createPanel();
        this.setupHandlers();
    }
    
    createPanel() {
        const panel = document.createElement('div');
        panel.className = 'memory-panel';
        panel.innerHTML = `
            <div class="memory-tab">MEM</div>
            <div class="memory-content">
                <h3>MEMORY</h3>
                <div class="memory-stats">
                    <div class="stat-item">
                        <span class="stat-label">Conversations:</span>
                        <span class="stat-value" id="conv-count">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Context Size:</span>
                        <span class="stat-value" id="ctx-size">0</span>
                    </div>
                </div>
                <div class="memory-actions">
                    <button id="mem-clear">Clear</button>
                    <button id="mem-export">Export</button>
                    <button id="mem-import">Import</button>
                </div>
                <div class="memory-preview" id="memory-preview">
                    No memory data
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        this.panel = panel;
    }
    
    setupHandlers() {
        const tab = this.panel.querySelector('.memory-tab');
        tab.addEventListener('click', () => this.toggle());
        
        // Memory actions
        document.getElementById('mem-clear')?.addEventListener('click', () => this.clearMemory());
        document.getElementById('mem-export')?.addEventListener('click', () => this.exportMemory());
        document.getElementById('mem-import')?.addEventListener('click', () => this.importMemory());
    }
    
    toggle() {
        this.visible = !this.visible;
        this.panel.classList.toggle('visible', this.visible);
        this.updateMemoryData();
    }
    
    updateMemoryData() {
        if (!this.visible) return;
        
        // Update from SUPERCLAUDE if available
        if (window.superClaude && window.superClaude.memory) {
            const memory = window.superClaude.memory;
            document.getElementById('conv-count').textContent = Object.keys(memory).length;
            document.getElementById('ctx-size').textContent = JSON.stringify(memory).length + ' chars';
            document.getElementById('memory-preview').innerHTML = 
                `<pre>${JSON.stringify(memory, null, 2)}</pre>`;
        }
    }
    
    clearMemory() {
        if (window.superClaude) {
            window.superClaude.clearMemory();
        }
        this.updateMemoryData();
    }
    
    exportMemory() {
        if (window.superClaude && window.superClaude.memory) {
            const data = JSON.stringify(window.superClaude.memory, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'superclaude-memory.json';
            a.click();
            URL.revokeObjectURL(url);
        }
    }
    
    importMemory() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const data = JSON.parse(e.target.result);
                        if (window.superClaude) {
                            window.superClaude.memory = data;
                            // TODO: отправить на сервер
                        }
                        this.updateMemoryData();
                    } catch (err) {
                        alert('Invalid JSON file');
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    new ProximityTab();
    new MemoryPanel();
});