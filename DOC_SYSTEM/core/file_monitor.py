#!/usr/bin/env python3

import os
import sys
import time
import hashlib
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import threading
import queue
import logging

class FileMonitor(FileSystemEventHandler):
    def __init__(self, config_path: str = "../config/system.config.yaml"):
        self.config = self._load_config(config_path)
        self.project_root = Path(self.config['system']['project_root'])
        self.metadata_cache: Dict[str, Dict] = {}
        self.file_hashes: Dict[str, str] = {}
        self.event_queue = queue.Queue()
        self.observers: List[Observer] = []
        self.running = False
        self.lock = threading.Lock()
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.project_root / 'DOC_SYSTEM' / self.config['logging']['file']
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict:
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _calculate_hash(self, file_path: Path) -> str:
        algorithm = self.config['hashing']['algorithm']
        hasher = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _should_ignore(self, path: Path) -> bool:
        path_str = str(path)
        for pattern in self.config['monitoring']['file_watcher']['ignore_patterns']:
            if pattern.replace('**', '').replace('*', '') in path_str:
                return True
        return False
    
    def _should_watch(self, path: Path) -> bool:
        if not path.is_file():
            return False
            
        path_str = str(path)
        for pattern in self.config['monitoring']['file_watcher']['watch_patterns']:
            if path_str.endswith(pattern.replace('*', '')):
                return True
        return False
    
    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self._should_ignore(file_path) and self._should_watch(file_path):
                self.event_queue.put({
                    'type': 'created',
                    'path': str(file_path),
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info(f"File created: {file_path}")
                self._update_metadata(file_path, 'created')
    
    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self._should_ignore(file_path) and self._should_watch(file_path):
                new_hash = self._calculate_hash(file_path)
                old_hash = self.file_hashes.get(str(file_path))
                
                if new_hash != old_hash:
                    self.event_queue.put({
                        'type': 'modified',
                        'path': str(file_path),
                        'timestamp': datetime.now().isoformat(),
                        'old_hash': old_hash,
                        'new_hash': new_hash
                    })
                    self.logger.info(f"File modified: {file_path}")
                    self._update_metadata(file_path, 'modified')
                    self.file_hashes[str(file_path)] = new_hash
    
    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if not self._should_ignore(file_path):
                self.event_queue.put({
                    'type': 'deleted',
                    'path': str(file_path),
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info(f"File deleted: {file_path}")
                self._update_metadata(file_path, 'deleted')
                
                with self.lock:
                    self.file_hashes.pop(str(file_path), None)
                    self.metadata_cache.pop(str(file_path), None)
    
    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            src_path = Path(event.src_path)
            dest_path = Path(event.dest_path)
            
            if not self._should_ignore(src_path) and not self._should_ignore(dest_path):
                self.event_queue.put({
                    'type': 'moved',
                    'src_path': str(src_path),
                    'dest_path': str(dest_path),
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info(f"File moved: {src_path} -> {dest_path}")
                self._update_metadata(dest_path, 'moved', old_path=src_path)
                
                with self.lock:
                    if str(src_path) in self.file_hashes:
                        self.file_hashes[str(dest_path)] = self.file_hashes.pop(str(src_path))
                    if str(src_path) in self.metadata_cache:
                        self.metadata_cache[str(dest_path)] = self.metadata_cache.pop(str(src_path))
    
    def _update_metadata(self, file_path: Path, action: str, **kwargs):
        # СТРОГАЯ ПРОВЕРКА: только чтение, никаких изменений основного проекта
        if not file_path.exists() and action != 'deleted':
            return
            
        relative_path = file_path.relative_to(self.project_root)
        
        # ЗАЩИТА: не трогаем критические папки проекта
        path_str = str(relative_path)
        protected_dirs = ['src/', 'interface/', 'SCRIPTS/', 'config/', 'ТАБЛИЦЫ/', 'API/', 'AGENTS/']
        if any(path_str.startswith(protected) for protected in protected_dirs):
            # Только читаем, не изменяем
            pass
        
        metadata = {
            'path': str(relative_path),
            'absolute_path': str(file_path),
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'hash': self._calculate_hash(file_path) if file_path.exists() else None,
            'extension': file_path.suffix,
            'name': file_path.name,
            'parent': str(file_path.parent.relative_to(self.project_root)),
            'read_only': True,  # ТОЛЬКО ЧТЕНИЕ
            **kwargs
        }
        
        with self.lock:
            self.metadata_cache[str(file_path)] = metadata
        
        # Сохраняем метаданные ТОЛЬКО в DOC_SYSTEM
        self._save_metadata()
    
    def _save_metadata(self):
        storage_config = self.config['storage']
        
        if storage_config['type'] in ['hybrid', 'json']:
            json_path = self.project_root / 'DOC_SYSTEM' / storage_config['json']['path']
            json_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.lock:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata_cache, f, indent=2, ensure_ascii=False)
        
        if storage_config['type'] in ['hybrid', 'yaml']:
            yaml_path = self.project_root / 'DOC_SYSTEM' / storage_config['yaml']['path']
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.lock:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.metadata_cache, f, allow_unicode=True, sort_keys=False)
    
    def scan_directory(self, directory: Path = None) -> Dict[str, Dict]:
        if directory is None:
            directory = self.project_root
        
        self.logger.info(f"Scanning directory: {directory}")
        file_metadata = {}
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and not self._should_ignore(file_path) and self._should_watch(file_path):
                relative_path = file_path.relative_to(self.project_root)
                file_hash = self._calculate_hash(file_path)
                
                self.file_hashes[str(file_path)] = file_hash
                
                metadata = {
                    'path': str(relative_path),
                    'absolute_path': str(file_path),
                    'size': file_path.stat().st_size,
                    'hash': file_hash,
                    'extension': file_path.suffix,
                    'name': file_path.name,
                    'parent': str(file_path.parent.relative_to(self.project_root)),
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                }
                
                file_metadata[str(file_path)] = metadata
        
        with self.lock:
            self.metadata_cache.update(file_metadata)
        
        self._save_metadata()
        self.logger.info(f"Scan complete. Found {len(file_metadata)} files")
        
        return file_metadata
    
    def start_monitoring(self):
        if self.running:
            self.logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.logger.info("Starting file monitoring")
        
        # Initial scan
        self.scan_directory()
        
        # Start file watcher if enabled
        if self.config['monitoring']['file_watcher']['enabled']:
            observer = Observer()
            observer.schedule(self, str(self.project_root), recursive=True)
            observer.start()
            self.observers.append(observer)
            self.logger.info("File watcher started")
        
        # Start event processor
        event_thread = threading.Thread(target=self._process_events, daemon=True)
        event_thread.start()
        
        self.logger.info("File monitoring started successfully")
    
    def stop_monitoring(self):
        self.running = False
        
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        self.logger.info("File monitoring stopped")
    
    def _process_events(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self._handle_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    def _handle_event(self, event: Dict):
        # Here we'll integrate with other components
        # For now, just log the event
        self.logger.debug(f"Processing event: {event}")
        
        # Trigger documentation generation if needed
        if self.config['documentation']['auto_generate']:
            self._trigger_documentation_update(event)
        
        # Check for orphaned files
        if self.config['dependency_analysis']['detect_orphans']:
            self._check_orphaned_files(event)
    
    def _trigger_documentation_update(self, event: Dict):
        # Placeholder for documentation trigger
        pass
    
    def _check_orphaned_files(self, event: Dict):
        # Placeholder for orphan detection
        pass
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        with self.lock:
            return self.metadata_cache.get(file_path)
    
    def get_all_metadata(self) -> Dict[str, Dict]:
        with self.lock:
            return self.metadata_cache.copy()
    
    def get_files_by_extension(self, extension: str) -> List[Dict]:
        with self.lock:
            return [
                metadata for metadata in self.metadata_cache.values()
                if metadata.get('extension') == extension
            ]
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        events = []
        while not self.event_queue.empty() and len(events) < limit:
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events


if __name__ == "__main__":
    monitor = FileMonitor()
    
    try:
        monitor.start_monitoring()
        print("File monitoring started. Press Ctrl+C to stop...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping file monitor...")
        monitor.stop_monitoring()
        print("File monitor stopped.")