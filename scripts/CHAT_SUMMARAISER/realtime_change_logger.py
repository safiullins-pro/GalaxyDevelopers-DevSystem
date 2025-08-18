#!/usr/bin/env python3
"""
Real-time Change Logger для Claude
Отслеживает и логирует все изменения файлов в реальном времени
"""

import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import threading
import queue

class RealtimeChangeLogger:
    def __init__(self, watch_log: str, output_dir: str):
        self.watch_log = Path(watch_log)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Очередь изменений
        self.change_queue = queue.Queue()
        
        # Текущий лог изменений
        self.current_log = self.output_dir / f"changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # Индекс файлов и их последних версий
        self.file_index = {}
        self.last_position = 0
        
        # Статистика
        self.stats = {
            'total_changes': 0,
            'files_tracked': set(),
            'start_time': datetime.now(timezone.utc),
            'last_change': None
        }
    
    def start_monitoring(self):
        """
        Начинает мониторинг лог файла Claude
        """
        print(f"🔍 Starting real-time monitoring of: {self.watch_log}")
        print(f"📝 Logging changes to: {self.current_log}")
        
        # Переходим в конец файла
        if self.watch_log.exists():
            self.last_position = self.watch_log.stat().st_size
        
        # Запускаем поток мониторинга
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        # Запускаем поток обработки
        processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        processor_thread.start()
        
        return monitor_thread, processor_thread
    
    def _monitor_loop(self):
        """
        Цикл мониторинга файла
        """
        while True:
            try:
                if self.watch_log.exists():
                    current_size = self.watch_log.stat().st_size
                    
                    if current_size > self.last_position:
                        # Читаем новые строки
                        with open(self.watch_log, 'r', encoding='utf-8') as f:
                            f.seek(self.last_position)
                            
                            for line in f:
                                try:
                                    entry = json.loads(line)
                                    if self._is_file_change(entry):
                                        self.change_queue.put(entry)
                                except json.JSONDecodeError:
                                    continue
                            
                            self.last_position = f.tell()
                
                time.sleep(0.5)  # Проверяем каждые 0.5 секунды
                
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(1)
    
    def _is_file_change(self, entry: Dict) -> bool:
        """
        Проверяет, является ли запись изменением файла
        """
        return 'toolUseResult' in entry and 'filePath' in entry['toolUseResult']
    
    def _process_loop(self):
        """
        Цикл обработки изменений
        """
        while True:
            try:
                # Получаем изменение из очереди
                entry = self.change_queue.get(timeout=1)
                self._process_change(entry)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Process error: {e}")
    
    def _process_change(self, entry: Dict):
        """
        Обрабатывает изменение файла
        """
        result = entry['toolUseResult']
        file_path = result['filePath']
        
        # Создаем запись изменения
        change_record = {
            'timestamp': entry.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'file_path': file_path,
            'action': result.get('action', 'edit'),
            'session_id': entry.get('sessionId', ''),
            'message_uuid': entry.get('uuid', ''),
            'change_size': len(result.get('newString', '')),
            'old_hash': None,
            'new_hash': None
        }
        
        # Вычисляем хэши
        if 'oldString' in result:
            change_record['old_hash'] = hashlib.sha256(
                result['oldString'].encode()
            ).hexdigest()[:12]
        
        if 'newString' in result:
            change_record['new_hash'] = hashlib.sha256(
                result['newString'].encode()
            ).hexdigest()[:12]
        
        # Сохраняем полное изменение
        full_change = {
            **change_record,
            'old_content': result.get('oldString', ''),
            'new_content': result.get('newString', ''),
            'original_file': result.get('originalFile', '')
        }
        
        # Записываем в лог
        with open(self.current_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(full_change, ensure_ascii=False) + '\n')
        
        # Обновляем индекс
        self.file_index[file_path] = {
            'last_change': change_record['timestamp'],
            'last_hash': change_record['new_hash'],
            'total_changes': self.file_index.get(file_path, {}).get('total_changes', 0) + 1
        }
        
        # Обновляем статистику
        self.stats['total_changes'] += 1
        self.stats['files_tracked'].add(file_path)
        self.stats['last_change'] = change_record['timestamp']
        
        # Выводим уведомление
        print(f"📝 Change detected: {Path(file_path).name} [{change_record['new_hash']}]")
        
        # Создаем snapshot каждые 10 изменений
        if self.stats['total_changes'] % 10 == 0:
            self._create_snapshot()
    
    def _create_snapshot(self):
        """
        Создает снимок текущего состояния
        """
        snapshot = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stats': {
                **self.stats,
                'files_tracked': list(self.stats['files_tracked'])
            },
            'file_index': self.file_index
        }
        
        snapshot_file = self.output_dir / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        print(f"📸 Snapshot saved: {snapshot_file.name}")
    
    def get_file_versions(self, file_path: str) -> list:
        """
        Возвращает все версии файла из лога
        """
        versions = []
        
        with open(self.current_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    change = json.loads(line)
                    if change['file_path'] == file_path:
                        versions.append({
                            'timestamp': change['timestamp'],
                            'old_hash': change['old_hash'],
                            'new_hash': change['new_hash'],
                            'size': change['change_size']
                        })
                except json.JSONDecodeError:
                    continue
        
        return versions
    
    def restore_file_at_point(self, file_path: str, target_hash: str) -> Optional[str]:
        """
        Восстанавливает файл по хэшу версии
        """
        with open(self.current_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    change = json.loads(line)
                    if change['file_path'] == file_path and change['new_hash'] == target_hash:
                        # Применяем изменение к оригиналу
                        if change['original_file']:
                            content = change['original_file']
                            if change['old_content'] in content:
                                content = content.replace(
                                    change['old_content'],
                                    change['new_content']
                                )
                            return content
                        else:
                            return change['new_content']
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def print_stats(self):
        """
        Выводит текущую статистику
        """
        print("\n📊 Change Logger Statistics:")
        print(f"Total changes logged: {self.stats['total_changes']}")
        print(f"Files tracked: {len(self.stats['files_tracked'])}")
        print(f"Monitoring since: {self.stats['start_time']}")
        print(f"Last change: {self.stats['last_change']}")
        print("\nTop changed files:")
        
        # Сортируем по количеству изменений
        sorted_files = sorted(
            self.file_index.items(),
            key=lambda x: x[1]['total_changes'],
            reverse=True
        )
        
        for file_path, info in sorted_files[:5]:
            print(f"  - {Path(file_path).name}: {info['total_changes']} changes")


def main():
    # Конфигурация
    claude_log = "/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/42545c12-a4cb-4e8c-a90c-c4feccd0360b.jsonl"
    output_dir = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER/realtime_logs"
    
    # Создаем логгер
    logger = RealtimeChangeLogger(claude_log, output_dir)
    
    # Запускаем мониторинг
    monitor_thread, processor_thread = logger.start_monitoring()
    
    try:
        # Главный цикл
        while True:
            time.sleep(30)  # Каждые 30 секунд
            logger.print_stats()
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitoring...")
        logger._create_snapshot()
        print("✅ Final snapshot saved")


if __name__ == "__main__":
    main()