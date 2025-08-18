#!/usr/bin/env python3
"""
Document Integration System
Интеграция извлеченного опыта с системой документооборота
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import shutil

class DocumentIntegrator:
    def __init__(self):
        self.base_path = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem")
        self.docs_path = self.base_path / "DOCUMENTS"
        self.memory_path = self.base_path / "memory"
        self.experience_path = self.docs_path / "EXPERIENCE"
        self.patterns_path = self.docs_path / "PATTERNS"
        
        # Создаем необходимые директории
        self.experience_path.mkdir(parents=True, exist_ok=True)
        self.patterns_path.mkdir(parents=True, exist_ok=True)
        
    def integrate_experience(self, experience_file: str) -> Dict[str, Any]:
        """
        Интегрирует извлеченный опыт в систему документооборота
        """
        with open(experience_file, 'r', encoding='utf-8') as f:
            experience = json.load(f)
        
        results = {
            'errors_documented': 0,
            'discoveries_documented': 0,
            'patterns_created': 0,
            'memory_updated': False
        }
        
        # 1. Документируем ошибки
        if experience.get('errors'):
            error_doc = self.create_error_documentation(experience['errors'])
            error_file = self.experience_path / f"errors_{datetime.now().strftime('%Y%m%d')}.md"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(error_doc)
            results['errors_documented'] = len(experience['errors'])
            
        # 2. Документируем открытия
        if experience.get('discoveries'):
            discovery_doc = self.create_discovery_documentation(experience['discoveries'])
            discovery_file = self.experience_path / f"discoveries_{datetime.now().strftime('%Y%m%d')}.md"
            with open(discovery_file, 'w', encoding='utf-8') as f:
                f.write(discovery_doc)
            results['discoveries_documented'] = len(experience['discoveries'])
            
        # 3. Создаем паттерны из опыта
        patterns = self.extract_patterns(experience)
        if patterns:
            for pattern_name, pattern_content in patterns.items():
                pattern_file = self.patterns_path / f"{pattern_name}.md"
                with open(pattern_file, 'w', encoding='utf-8') as f:
                    f.write(pattern_content)
                results['patterns_created'] += 1
                
        # 4. Обновляем memory систему
        self.update_memory_system(experience)
        results['memory_updated'] = True
        
        return results
    
    def create_error_documentation(self, errors: List[str]) -> str:
        """
        Создает документацию по ошибкам
        """
        doc = ["# 🔴 ДОКУМЕНТАЦИЯ ОШИБОК"]
        doc.append(f"\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.append("\n## Обнаруженные проблемы\n")
        
        for i, error in enumerate(errors, 1):
            # Извлекаем timestamp и описание
            parts = error.split(": ", 1)
            if len(parts) == 2:
                timestamp, description = parts
                doc.append(f"### {i}. Ошибка в {timestamp}")
                doc.append(f"\n{description}\n")
                
                # Добавляем рекомендации на основе паттернов
                if "RuntimeError: no running event loop" in description:
                    doc.append("**Решение**: Использовать `loop.call_soon_threadsafe()` для thread-safe async вызовов\n")
                elif "modal" in description.lower():
                    doc.append("**Решение**: Проверять существование модального окна перед созданием нового\n")
                elif "timezone" in description.lower():
                    doc.append("**Решение**: Использовать `tzinfo=timezone.utc` для datetime объектов\n")
        
        doc.append("\n## Извлеченные уроки\n")
        doc.append("- Всегда проверять существующий код перед созданием нового")
        doc.append("- Использовать thread-safe методы для async операций")
        doc.append("- Правильно управлять жизненным циклом UI компонентов")
        
        return "\n".join(doc)
    
    def create_discovery_documentation(self, discoveries: List[str]) -> str:
        """
        Создает документацию по открытиям
        """
        doc = ["# 🟢 ДОКУМЕНТАЦИЯ ОТКРЫТИЙ"]
        doc.append(f"\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.append("\n## Успешные решения\n")
        
        for i, discovery in enumerate(discoveries, 1):
            parts = discovery.split(": ", 1)
            if len(parts) == 2:
                timestamp, description = parts
                doc.append(f"### {i}. Открытие в {timestamp}")
                doc.append(f"\n{description}\n")
        
        doc.append("\n## Ключевые инсайты\n")
        doc.append("- Градиентный дизайн создает визуально привлекательный интерфейс")
        doc.append("- Proximity detection улучшает UX взаимодействие")
        doc.append("- Pipeline статусы помогают отслеживать прогресс")
        
        return "\n".join(doc)
    
    def extract_patterns(self, experience: Dict) -> Dict[str, str]:
        """
        Извлекает паттерны из опыта
        """
        patterns = {}
        
        # Паттерн для File Observer
        if any("File Observer" in str(e) for e in experience.get('errors', [])):
            patterns['file_observer_pattern'] = self.create_file_observer_pattern()
            
        # Паттерн для UI компонентов
        if any("modal" in str(e).lower() for e in experience.get('errors', [])):
            patterns['modal_management_pattern'] = self.create_modal_pattern()
            
        # Паттерн для Pipeline дизайна
        if experience.get('file_changes'):
            pipeline_files = [f for f in experience['file_changes'] 
                            if 'pipeline' in f.get('file', '').lower()]
            if pipeline_files:
                patterns['pipeline_design_pattern'] = self.create_pipeline_pattern()
        
        return patterns
    
    def create_file_observer_pattern(self) -> str:
        """
        Создает паттерн для File Observer
        """
        return """# 📋 ПАТТЕРН: Thread-Safe File Observer

## Проблема
RuntimeError: no running event loop при обработке файловых изменений

## Решение
```python
try:
    loop = asyncio.get_event_loop()
    if loop and loop.is_running():
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(
                self.broadcast_to_websockets(change_data)
            )
        )
except RuntimeError:
    pass
```

## Когда использовать
- При интеграции синхронных callback'ов с async кодом
- При работе с watchdog и asyncio
- При необходимости thread-safe операций

## Преимущества
✅ Избегает RuntimeError
✅ Thread-safe
✅ Не блокирует основной поток
"""
    
    def create_modal_pattern(self) -> str:
        """
        Создает паттерн для модальных окон
        """
        return """# 📋 ПАТТЕРН: Управление модальными окнами

## Проблема
Множественные экземпляры модальных окон при повторном открытии

## Решение
```javascript
// Проверяем и удаляем существующий модальный
const existingModal = document.getElementById('settings-modal');
if (existingModal) {
    existingModal.remove();
}

// Создаем новый с уникальным ID
const modal = document.createElement('div');
modal.id = 'settings-modal';
modal.className = 'modal';
```

## Принципы
1. Всегда проверять существование перед созданием
2. Использовать уникальные ID
3. Правильно очищать при закрытии
4. Избегать утечек памяти
"""
    
    def create_pipeline_pattern(self) -> str:
        """
        Создает паттерн для Pipeline дизайна
        """
        return """# 📋 ПАТТЕРН: Pipeline Status Design

## Визуальная структура
```
INBOX → RESEARCH → DESIGN → CONTENT → DEVELOPMENT → REVIEW → DEPLOY
```

## Ключевые элементы
1. **Градиентный фон**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
2. **Статусы этапов**: ✓ (готово), ⚙ (в процессе), ⏸ (ожидание)
3. **Анимации**: pulse для активных элементов
4. **Proximity detection**: реакция на приближение курсора

## CSS стили
```css
.pipeline-status {
    background: linear-gradient(135deg, 
        rgba(102, 126, 234, 0.1) 0%, 
        rgba(118, 75, 162, 0.1) 100%);
    border-radius: 12px;
    padding: 16px;
}

.stage.active {
    background: linear-gradient(135deg, 
        rgba(102, 126, 234, 0.2) 0%, 
        rgba(118, 75, 162, 0.2) 100%);
    border: 1px solid rgba(102, 126, 234, 0.4);
}
```

## Применение
Используется для визуализации многоэтапных процессов с красивым градиентным дизайном
"""
    
    def update_memory_system(self, experience: Dict) -> None:
        """
        Обновляет memory систему проекта
        """
        memory_file = self.memory_path / "CLAUDE.md"
        
        # Читаем существующий файл если есть
        existing_content = ""
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Добавляем новую секцию с извлеченным опытом
        new_section = f"""

## 📚 ИЗВЛЕЧЕННЫЙ ОПЫТ ({datetime.now().strftime('%Y-%m-%d')})

### Ключевые ошибки и решения
- **File Observer crash**: Решено через `loop.call_soon_threadsafe()`
- **Modal multiplication**: Добавлена проверка существования перед созданием
- **Timezone issues**: Использование `tzinfo=timezone.utc`

### Успешные паттерны
- Pipeline Status с градиентами (#667eea → #764ba2)
- Proximity detection для улучшения UX
- Agent Status мониторинг с анимациями

### Изменения файлов
- Обновлено файлов: {len(experience.get('file_changes', []))}
- Основные изменения: interface/index.html, interface/css/main.css, interface/js/app.js

### Важные уроки
1. ВСЕГДА проверять существующий код перед созданием нового
2. Использовать thread-safe методы для async операций  
3. Следовать установленным паттернам проекта
4. НЕ создавать муляжи - только рабочий код
"""
        
        # Записываем обновленный файл
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(existing_content + new_section)
    
    def create_integration_report(self, results: Dict[str, Any]) -> str:
        """
        Создает отчет об интеграции
        """
        report = ["# 📊 ОТЧЕТ ОБ ИНТЕГРАЦИИ ОПЫТА"]
        report.append(f"\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("\n## Результаты интеграции\n")
        
        report.append(f"✅ Документировано ошибок: {results['errors_documented']}")
        report.append(f"✅ Документировано открытий: {results['discoveries_documented']}")
        report.append(f"✅ Создано паттернов: {results['patterns_created']}")
        report.append(f"✅ Memory система обновлена: {'Да' if results['memory_updated'] else 'Нет'}")
        
        report.append("\n## Расположение файлов\n")
        report.append(f"- Документация ошибок: `{self.experience_path}/errors_*.md`")
        report.append(f"- Документация открытий: `{self.experience_path}/discoveries_*.md`")
        report.append(f"- Паттерны: `{self.patterns_path}/*.md`")
        report.append(f"- Memory: `{self.memory_path}/CLAUDE.md`")
        
        report.append("\n## Следующие шаги\n")
        report.append("1. Проверить созданную документацию")
        report.append("2. Применить извлеченные паттерны в новых разработках")
        report.append("3. Использовать документацию для обучения команды")
        
        return "\n".join(report)


def main():
    """
    Основная функция интеграции
    """
    print("🚀 Запуск интеграции опыта с документооборотом...")
    
    # Путь к файлу с извлеченным опытом
    experience_file = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER/experience_20250812_0044.json"
    
    # Создаем интегратор
    integrator = DocumentIntegrator()
    
    # Выполняем интеграцию
    results = integrator.integrate_experience(experience_file)
    
    # Создаем отчет
    report = integrator.create_integration_report(results)
    
    # Сохраняем отчет
    report_file = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOCUMENTS/integration_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Интеграция завершена!")
    print(f"📄 Отчет сохранен: {report_file}")
    print(f"\nРезультаты:")
    print(f"  - Ошибок документировано: {results['errors_documented']}")
    print(f"  - Открытий документировано: {results['discoveries_documented']}")
    print(f"  - Паттернов создано: {results['patterns_created']}")
    print(f"  - Memory обновлен: {'✓' if results['memory_updated'] else '✗'}")


if __name__ == "__main__":
    main()