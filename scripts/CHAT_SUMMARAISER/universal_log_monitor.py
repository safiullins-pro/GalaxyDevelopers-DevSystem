#!/usr/bin/env python3
"""
Universal Log Monitor - следит за ВСЕМИ логами
Отслеживает Claude логи, системные логи, логи приложений
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    """Обработчик изменений лог файлов"""
    
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue
        self.file_positions = {}  # file_path -> last_position
        
    def on_modified(self, event):
        if not event.is_directory and (event.src_path.endswith('.log') or 
                                      event.src_path.endswith('.jsonl') or
                                      event.src_path.endswith('.txt')):
            self.process_log_file(event.src_path)
    
    def process_log_file(self, file_path: str):
        """Обрабатывает изменения в лог файле"""
        try:
            # Получаем последнюю позицию
            last_pos = self.file_positions.get(file_path, 0)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Переходим к последней позиции
                f.seek(last_pos)
                
                # Читаем новые строки
                new_lines = f.readlines()
                
                if new_lines:
                    # Сохраняем новую позицию
                    self.file_positions[file_path] = f.tell()
                    
                    # Добавляем в очередь
                    for line in new_lines:
                        self.log_queue.put({
                            'file': file_path,
                            'content': line.strip(),
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        })
                        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

class UniversalLogMonitor:
    def __init__(self):
        self.log_queue = queue.Queue()
        self.observers = []
        
        # Директории для мониторинга
        self.watch_dirs = [
            # Claude логи
            Path("/Users/safiullins_pro/.claude"),
            Path("/Users/safiullins_pro/.claude/projects"),
            
            # Системные логи GalaxyDevelopers
            Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/logs"),
            Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER/realtime_logs"),
            
            # Логи мониторинга
            Path("/tmp"),  # временные логи
            
            # Логи Gemini
            Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/GEMINI_SYSTEM/logs")
        ]
        
        # Паттерны для извлечения важной информации
        self.patterns = {
            'file_changes': ['filePath', 'modified', 'created', 'deleted'],
            'errors': ['error', 'exception', 'failed', 'crash', 'ошибка'],
            'api_calls': ['GET', 'POST', 'PUT', 'DELETE', 'api/', '/api'],
            'claude_tools': ['tool_use', 'tool_result', 'toolUseResult'],
            'system_events': ['started', 'stopped', 'connected', 'disconnected']
        }
        
        # Статистика
        self.stats = {
            'total_logs_processed': 0,
            'files_monitored': set(),
            'important_events': [],
            'start_time': datetime.now(timezone.utc)
        }
        
        # Выходной файл для важных событий
        self.output_dir = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER/aggregated_logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.output_dir / f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    def start_monitoring(self):
        """Запускает мониторинг всех директорий"""
        print("🔍 Starting Universal Log Monitor")
        print(f"📁 Monitoring {len(self.watch_dirs)} directories")
        
        # Создаем обработчик
        handler = LogFileHandler(self.log_queue)
        
        # Запускаем наблюдателей для каждой директории
        for watch_dir in self.watch_dirs:
            if watch_dir.exists():
                observer = Observer()
                observer.schedule(handler, str(watch_dir), recursive=True)
                observer.start()
                self.observers.append(observer)
                print(f"  ✅ Watching: {watch_dir}")
                
                # Сканируем существующие лог файлы
                self._scan_existing_logs(watch_dir, handler)
            else:
                print(f"  ⚠️ Directory not found: {watch_dir}")
        
        # Запускаем обработчик событий
        processor_thread = threading.Thread(target=self._process_events, daemon=True)
        processor_thread.start()
        
        # Запускаем поток статистики
        stats_thread = threading.Thread(target=self._print_stats, daemon=True)
        stats_thread.start()
        
        return processor_thread, stats_thread
    
    def _scan_existing_logs(self, directory: Path, handler: LogFileHandler):
        """Сканирует существующие лог файлы"""
        for log_file in directory.rglob("*.log"):
            self.stats['files_monitored'].add(str(log_file))
            # Устанавливаем позицию в конец файла
            handler.file_positions[str(log_file)] = log_file.stat().st_size
            
        for jsonl_file in directory.rglob("*.jsonl"):
            self.stats['files_monitored'].add(str(jsonl_file))
            handler.file_positions[str(jsonl_file)] = jsonl_file.stat().st_size
    
    def _process_events(self):
        """Обрабатывает события из очереди"""
        while True:
            try:
                event = self.log_queue.get(timeout=1)
                self._analyze_event(event)
                self.stats['total_logs_processed'] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Processing error: {e}")
    
    def _analyze_event(self, event: Dict):
        """Анализирует событие на важность"""
        content = event['content'].lower()
        file_name = Path(event['file']).name
        
        # Проверяем на важные паттерны
        importance = 0
        matched_patterns = []
        
        for pattern_type, keywords in self.patterns.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    importance += 1
                    matched_patterns.append(pattern_type)
                    break
        
        # Если событие важное, сохраняем
        if importance > 0:
            important_event = {
                'timestamp': event['timestamp'],
                'file': file_name,
                'importance': importance,
                'patterns': matched_patterns,
                'content': event['content'][:500]  # Первые 500 символов
            }
            
            # Добавляем в статистику
            self.stats['important_events'].append(important_event)
            if len(self.stats['important_events']) > 100:
                self.stats['important_events'].pop(0)  # Держим только последние 100
            
            # Записываем в файл
            with open(self.events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(important_event, ensure_ascii=False) + '\n')
            
            # Выводим важное событие
            if importance >= 2:  # Очень важное
                print(f"🔴 IMPORTANT [{file_name}]: {', '.join(matched_patterns)}")
            
            # Специальная обработка для Claude tool use
            if 'claude_tools' in matched_patterns:
                self._process_claude_event(event)
    
    def _process_claude_event(self, event: Dict):
        """Специальная обработка для Claude событий"""
        try:
            # Пытаемся распарсить как JSON
            data = json.loads(event['content'])
            
            if 'toolUseResult' in data and 'filePath' in data['toolUseResult']:
                file_path = data['toolUseResult']['filePath']
                print(f"  📝 Claude modified: {Path(file_path).name}")
                
                # Сохраняем в отдельный файл изменений
                changes_file = self.output_dir / "claude_file_changes.jsonl"
                with open(changes_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'timestamp': event['timestamp'],
                        'file_changed': file_path,
                        'session': data.get('sessionId', 'unknown')
                    }, ensure_ascii=False) + '\n')
                    
        except json.JSONDecodeError:
            pass  # Не JSON, пропускаем
    
    def _print_stats(self):
        """Периодически выводит статистику"""
        while True:
            time.sleep(30)  # Каждые 30 секунд
            
            print("\n📊 Universal Log Monitor Statistics:")
            print(f"  Total logs processed: {self.stats['total_logs_processed']}")
            print(f"  Files monitored: {len(self.stats['files_monitored'])}")
            print(f"  Important events: {len(self.stats['important_events'])}")
            
            if self.stats['important_events']:
                print("\n  Recent important events:")
                for event in self.stats['important_events'][-5:]:
                    print(f"    - [{event['file']}] {', '.join(event['patterns'])}")
    
    def get_aggregated_logs(self, pattern_type: str = None) -> List[Dict]:
        """Получает агрегированные логи по типу паттерна"""
        aggregated = []
        
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if pattern_type is None or pattern_type in event.get('patterns', []):
                            aggregated.append(event)
                    except json.JSONDecodeError:
                        continue
        
        return aggregated
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        print("\n⏹️ Stopping monitors...")
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        # Сохраняем финальную статистику
        stats_file = self.output_dir / f"final_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            stats_copy = self.stats.copy()
            stats_copy['files_monitored'] = list(stats_copy['files_monitored'])
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Stats saved to: {stats_file}")


def main():
    """Главная функция"""
    monitor = UniversalLogMonitor()
    
    try:
        # Запускаем мониторинг
        processor_thread, stats_thread = monitor.start_monitoring()
        
        print("\n✅ Universal Log Monitor is running!")
        print("Press Ctrl+C to stop\n")
        
        # Ждем прерывания
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        monitor.stop_monitoring()
        print("✅ Monitor stopped")


if __name__ == "__main__":
    main()