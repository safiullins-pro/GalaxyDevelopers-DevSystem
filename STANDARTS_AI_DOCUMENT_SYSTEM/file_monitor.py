#!/usr/bin/env python3
import os
import time
import json
import redis
import psycopg2
import hashlib
from datetime import datetime
import logging
import random # Added for retry logic

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Новые функции для надежного чтения файлов ---
def read_file_with_retry(filepath, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            # Wait for file to stabilize before reading
            if not wait_for_file_complete(filepath):
                raise Exception(f"File {filepath} did not stabilize.")
            
            if os.path.getsize(filepath) > 0:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[:10000]  # Первые 10К символов
        except (OSError, IOError) as e:
            logger.warning(f"Attempt {attempt + 1} to read {filepath} failed: {e}")
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
    raise Exception(f"Failed to read {filepath} after {max_attempts} attempts")

def wait_for_file_complete(filepath, timeout=10): # Reduced timeout for faster testing
    start_time = time.time()
    last_size = -1
    
    while time.time() - start_time < timeout:
        try:
            current_size = os.path.getsize(filepath)
            if current_size == last_size and current_size > 0:
                return True  # File stabilized
            last_size = current_size
            time.sleep(0.5) # Check every 0.5 seconds
        except OSError:
            time.sleep(0.1) # File might not exist yet
    
    return False
# --- Конец новых функций ---

class FileMonitor: # Renamed class
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        
        self.db_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'developer_control'),
            user=os.getenv('POSTGRES_USER', 'control_admin'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        # Получаем ID разработчика
        self.developer_id = self.get_or_create_developer()
        self.monitored_path = '/workspace/target'
        self.processed_files = set() # To keep track of processed files

    def get_or_create_developer(self):
        """Получить или создать разработчика в БД"""
        username = os.getenv('USER', 'developer')
        container_id = os.getenv('HOSTNAME', 'unknown')
        
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dev_control.developers (username, container_id, workspace_path)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                container_id = %s, workspace_path = %s
                RETURNING id
            """, (username, container_id, self.monitored_path, container_id, self.monitored_path))
            
            developer_id = cur.fetchone()[0]
            self.db_conn.commit()
            return developer_id

    def record_file_event(self, filepath, event_type, file_content): # Modified signature
        """Записать событие файла в БД"""
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dev_control.file_events 
                (developer_id, file_path, event_type, file_content)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (self.developer_id, filepath, event_type, file_content))
            
            file_event_id = cur.fetchone()[0]
            self.db_conn.commit()
            return file_event_id
            
    def send_to_ai_analyzer(self, filepath, file_event_id, event_type): # Modified signature
        """Отправить событие AI анализатору через Redis"""
        message = {
            'file_event_id': file_event_id,
            'developer_id': self.developer_id,
            'file_path': filepath, # Used filepath
            'event_type': event_type,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.redis_client.lpush('ai_analysis_queue', json.dumps(message))
            logger.info(f"Событие отправлено AI анализатору: {filepath}")
        except Exception as e:
            logger.error(f"Ошибка отправки в Redis: {e}")

    def poll_for_changes(self): # New polling method
        logger.info(f"✅ File Monitor активен. Мониторинг {self.monitored_path}")
        while True:
            try:
                current_files = set()
                for root, _, files in os.walk(self.monitored_path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        # Ignore temporary files
                        if any(temp in filepath for temp in ['.git', '__pycache__', '.pyc', '.tmp', '.swp', '._']):
                            continue
                        current_files.add(filepath)
                
                new_files = current_files - self.processed_files
                
                for filepath in new_files:
                    logger.info(f"New file detected: {filepath}")
                    try:
                        file_content = read_file_with_retry(filepath)
                        file_event_id = self.record_file_event(filepath, 'created', file_content)
                        self.send_to_ai_analyzer(filepath, file_event_id, 'created')
                    except Exception as e:
                        logger.error(f"Error processing new file {filepath}: {e}")
                
                self.processed_files = current_files
                time.sleep(5) # Poll every 5 seconds
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                time.sleep(5) # Wait before retrying

def main():
    """Главная функция мониторинга"""
    logger.info(" Запуск File Monitor...")
    
    monitor = FileMonitor() # Instantiated the new class
    monitor.poll_for_changes() # Called the polling method

if __name__ == "__main__":
    main()