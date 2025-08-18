#!/usr/bin/env python3
"""
Version Chain Tracker - отслеживание цепочки изменений файлов
Позволяет восстановить любую версию файла из истории
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class VersionChainTracker:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.version_chains = {}  # file_path -> list of versions
        self.version_index = {}   # hash -> version data
        
    def build_chain(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        """
        Строит цепочку версий для всех файлов
        """
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Фильтр по времени если указан
                    if 'timestamp' in entry:
                        entry_time = datetime.fromisoformat(
                            entry['timestamp'].replace('Z', '+00:00')
                        )
                        
                        if start_time and entry_time < start_time:
                            continue
                        if end_time and entry_time > end_time:
                            continue
                    
                    # Ищем изменения файлов
                    if 'toolUseResult' in entry and 'filePath' in entry['toolUseResult']:
                        self._add_version(entry)
                        
                except json.JSONDecodeError:
                    continue
    
    def _add_version(self, entry: Dict):
        """
        Добавляет версию в цепочку
        """
        result = entry['toolUseResult']
        file_path = result['filePath']
        
        # Создаем версию
        version = {
            'timestamp': entry['timestamp'],
            'file_path': file_path,
            'old_string': result.get('oldString', ''),
            'new_string': result.get('newString', ''),
            'original_file': result.get('originalFile', ''),
            'action': result.get('action', 'edit'),  # edit, create, delete
            'session_id': entry.get('sessionId', ''),
            'message_uuid': entry.get('uuid', ''),
            'parent_hash': None,  # хэш предыдущей версии
            'content_hash': None,  # хэш контента после изменения
            'version_number': 0
        }
        
        # Вычисляем хэш контента
        if version['original_file']:
            # Применяем изменение к оригиналу
            content = version['original_file']
            if version['old_string'] and version['old_string'] in content:
                content = content.replace(version['old_string'], version['new_string'])
            version['result_content'] = content
        else:
            version['result_content'] = version['new_string']
        
        # Хэш результата
        version['content_hash'] = hashlib.sha256(
            version['result_content'].encode()
        ).hexdigest()[:12]
        
        # Добавляем в цепочку
        if file_path not in self.version_chains:
            self.version_chains[file_path] = []
        
        # Связываем с предыдущей версией
        if self.version_chains[file_path]:
            prev_version = self.version_chains[file_path][-1]
            version['parent_hash'] = prev_version['content_hash']
            version['version_number'] = prev_version['version_number'] + 1
        
        self.version_chains[file_path].append(version)
        self.version_index[version['content_hash']] = version
    
    def get_file_history(self, file_path: str) -> List[Dict]:
        """
        Возвращает историю версий файла
        """
        return self.version_chains.get(file_path, [])
    
    def get_version_by_hash(self, content_hash: str) -> Optional[Dict]:
        """
        Получает версию по хэшу
        """
        return self.version_index.get(content_hash)
    
    def get_version_at_time(self, file_path: str, target_time: datetime) -> Optional[Dict]:
        """
        Возвращает версию файла на определенный момент времени
        """
        versions = self.get_file_history(file_path)
        
        for version in reversed(versions):
            version_time = datetime.fromisoformat(
                version['timestamp'].replace('Z', '+00:00')
            )
            if version_time <= target_time:
                return version
        
        return None
    
    def restore_version(self, file_path: str, version_hash: str, output_path: str):
        """
        Восстанавливает конкретную версию файла
        """
        version = self.get_version_by_hash(version_hash)
        if not version:
            raise ValueError(f"Version {version_hash} not found")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(version['result_content'])
        
        return version
    
    def generate_diff_chain(self, file_path: str) -> str:
        """
        Генерирует цепочку diff для файла
        """
        versions = self.get_file_history(file_path)
        
        diff_chain = []
        diff_chain.append(f"# Version Chain for {file_path}\n")
        diff_chain.append(f"Total versions: {len(versions)}\n\n")
        
        for i, version in enumerate(versions):
            diff_chain.append(f"## Version {version['version_number']} [{version['content_hash']}]")
            diff_chain.append(f"Time: {version['timestamp']}")
            
            if version['parent_hash']:
                diff_chain.append(f"Parent: {version['parent_hash']}")
            
            if version['old_string']:
                diff_chain.append("\n### Removed:")
                diff_chain.append("```")
                diff_chain.append(version['old_string'][:500])
                if len(version['old_string']) > 500:
                    diff_chain.append("... truncated ...")
                diff_chain.append("```")
            
            if version['new_string']:
                diff_chain.append("\n### Added:")
                diff_chain.append("```")
                diff_chain.append(version['new_string'][:500])
                if len(version['new_string']) > 500:
                    diff_chain.append("... truncated ...")
                diff_chain.append("```")
            
            diff_chain.append("\n---\n")
        
        return '\n'.join(diff_chain)
    
    def save_version_database(self, output_file: str):
        """
        Сохраняет базу версий в JSON
        """
        database = {
            'generated_at': datetime.now().isoformat(),
            'total_files': len(self.version_chains),
            'total_versions': sum(len(v) for v in self.version_chains.values()),
            'files': {}
        }
        
        for file_path, versions in self.version_chains.items():
            database['files'][file_path] = {
                'versions': len(versions),
                'first_change': versions[0]['timestamp'] if versions else None,
                'last_change': versions[-1]['timestamp'] if versions else None,
                'version_hashes': [v['content_hash'] for v in versions],
                'chain': [
                    {
                        'hash': v['content_hash'],
                        'parent': v['parent_hash'],
                        'timestamp': v['timestamp'],
                        'version': v['version_number']
                    }
                    for v in versions
                ]
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
    
    def generate_graph_viz(self, file_path: str) -> str:
        """
        Генерирует граф версий для визуализации
        """
        versions = self.get_file_history(file_path)
        
        dot = []
        dot.append("digraph versions {")
        dot.append('  rankdir=TB;')
        dot.append('  node [shape=box];')
        
        for version in versions:
            label = f"v{version['version_number']}\\n{version['content_hash'][:8]}\\n{version['timestamp'][:19]}"
            dot.append(f'  "{version["content_hash"]}" [label="{label}"];')
            
            if version['parent_hash']:
                dot.append(f'  "{version["parent_hash"]}" -> "{version["content_hash"]}";')
        
        dot.append("}")
        
        return '\n'.join(dot)


def main():
    # Конфигурация
    log_file = "/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/42545c12-a4cb-4e8c-a90c-c4feccd0360b.jsonl"
    
    print("🔗 Building version chains...")
    tracker = VersionChainTracker(log_file)
    
    # Строим цепочки за последние 24 часа
    start_time = datetime(2025, 8, 12, 0, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 8, 13, 0, 0, 0, tzinfo=timezone.utc)
    
    tracker.build_chain(start_time, end_time)
    
    # Статистика
    print(f"\n📊 Version Chain Statistics:")
    print(f"Files tracked: {len(tracker.version_chains)}")
    print(f"Total versions: {sum(len(v) for v in tracker.version_chains.values())}")
    
    # Сохраняем базу версий
    output_dir = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER")
    
    db_file = output_dir / "version_database.json"
    tracker.save_version_database(db_file)
    print(f"\n💾 Version database saved to: {db_file}")
    
    # Генерируем diff chains для важных файлов
    important_files = [
        "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/index.html",
        "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/css/main.css",
        "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/js/app.js"
    ]
    
    for file_path in important_files:
        if file_path in tracker.version_chains:
            versions = tracker.get_file_history(file_path)
            print(f"\n📝 {Path(file_path).name}: {len(versions)} versions")
            
            # Сохраняем diff chain
            diff_file = output_dir / f"diff_chain_{Path(file_path).stem}.md"
            with open(diff_file, 'w', encoding='utf-8') as f:
                f.write(tracker.generate_diff_chain(file_path))
            
            # Сохраняем граф
            graph_file = output_dir / f"graph_{Path(file_path).stem}.dot"
            with open(graph_file, 'w', encoding='utf-8') as f:
                f.write(tracker.generate_graph_viz(file_path))
            
            # Показываем хэши версий
            for v in versions[-3:]:  # последние 3 версии
                print(f"  - v{v['version_number']} [{v['content_hash']}] at {v['timestamp'][:19]}")
    
    # Пример восстановления версии
    print("\n🔧 Version restoration example:")
    print("To restore any version, use:")
    print("tracker.restore_version('file_path', 'version_hash', 'output_path')")


if __name__ == "__main__":
    main()