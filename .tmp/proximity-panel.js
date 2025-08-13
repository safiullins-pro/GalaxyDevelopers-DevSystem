// JavaScript для proximity-instruction панели
// Добавить в app.js или создать отдельный файл

// Proximity Instruction Panel Logic
function initProximityPanel() {
    const panel = document.getElementById('proximity-instruction');
    const tab = document.getElementById('instruction-tab');
    const instructionPanel = document.getElementById('instruction-panel');
    const textarea = document.getElementById('instruction-textarea');
    
    if (!panel || !tab) return;
    
    let isExpanded = false;
    let animationFrame = null;
    let currentY = -100;
    let targetY = -100;
    let mouseY = 0;
    let isMouseOverPanel = false;
    
    // Плавная анимация
    function animate() {
        const diff = targetY - currentY;
        
        // Более плавное сглаживание
        if (Math.abs(diff) > 0.1) {
            currentY += diff * 0.15; // Увеличил коэффициент для более плавного движения
            panel.style.transform = `translateX(-50%) translateY(${currentY}%)`;
            animationFrame = requestAnimationFrame(animate);
        } else {
            currentY = targetY;
            panel.style.transform = `translateX(-50%) translateY(${currentY}%)`;
            animationFrame = null;
        }
    }
    
    // Отслеживание позиции мыши
    document.addEventListener('mousemove', (e) => {
        mouseY = e.clientY;
        
        // Если мышь в верхней части экрана (0-100px)
        if (mouseY < 100 && !isExpanded) {
            // Чем ближе к верху, тем больше выдвигается
            const proximity = 1 - (mouseY / 100);
            targetY = -100 + (proximity * 70); // Выдвигается максимум на 70%
            
            if (!animationFrame) {
                animationFrame = requestAnimationFrame(animate);
            }
        } else if (!isMouseOverPanel && !isExpanded && mouseY >= 100) {
            // Плавно прячем обратно
            targetY = -100;
            if (!animationFrame) {
                animationFrame = requestAnimationFrame(animate);
            }
        }
    });
    
    // При наведении на саму панель
    panel.addEventListener('mouseenter', () => {
        isMouseOverPanel = true;
        if (!isExpanded) {
            targetY = 0; // Полностью показываем
            panel.classList.add('showing-panel'); // Показываем textarea
            if (!animationFrame) {
                animationFrame = requestAnimationFrame(animate);
            }
        }
    });
    
    panel.addEventListener('mouseleave', () => {
        isMouseOverPanel = false;
        if (!isExpanded) {
            targetY = -100;
            panel.classList.remove('showing-panel'); // Скрываем textarea
            if (!animationFrame) {
                animationFrame = requestAnimationFrame(animate);
            }
        }
    });
    
    // Клик по язычку для фиксации панели
    tab.addEventListener('click', (e) => {
        e.stopPropagation();
        isExpanded = !isExpanded;
        
        if (isExpanded) {
            targetY = 0;
            panel.classList.add('showing-panel');
            panel.classList.add('expanded');
            // Фокус на textarea при раскрытии
            setTimeout(() => textarea.focus(), 300);
        } else {
            targetY = -100;
            panel.classList.remove('showing-panel');
            panel.classList.remove('expanded');
        }
        
        if (!animationFrame) {
            animationFrame = requestAnimationFrame(animate);
        }
    });
    
    // Сохранение инструкции при изменении
    if (textarea) {
        textarea.addEventListener('input', () => {
            localStorage.setItem('systemInstruction', textarea.value);
        });
        
        // Загрузка сохраненной инструкции
        const savedInstruction = localStorage.getItem('systemInstruction');
        if (savedInstruction) {
            textarea.value = savedInstruction;
        }
    }
    
    // Закрытие при клике вне панели
    document.addEventListener('click', (e) => {
        if (isExpanded && !panel.contains(e.target)) {
            isExpanded = false;
            targetY = -100;
            panel.classList.remove('showing-panel');
            panel.classList.remove('expanded');
            
            if (!animationFrame) {
                animationFrame = requestAnimationFrame(animate);
            }
        }
    });
}

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProximityPanel);
} else {
    initProximityPanel();
}