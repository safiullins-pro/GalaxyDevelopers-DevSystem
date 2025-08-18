#!/usr/bin/env python3
import json
import redis
import psycopg2
import requests
import time
import logging
from datetime import datetime
import hashlib
import re
import os
import subprocess
import tempfile

# Для Telegram уведомлений
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AICodeAuditor:
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
        
        # Настройка Telegram бота
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.telegram_bot = None
        if self.telegram_bot_token:
            self.telegram_bot = Bot(self.telegram_bot_token)
            logger.info("✅ Telegram бот инициализирован.")
        else:
            logger.warning("❌ TELEGRAM_BOT_TOKEN не установлен. Уведомления Telegram будут отключены.")

        # Загружаем техническое задание
        self.load_technical_specification()
        
        # Загружаем критичные паттерны из БД
        self.load_critical_patterns_from_db()

        # Добавляем тестовый критичный паттерн напрямую для проверки блокировки
        self.critical_patterns.append(r'AKIAIOSFODNN7EXAMPLE')

        # Список запрещенных лицензий (пример)
        self.forbidden_licenses = ['GPL', 'AGPL', 'LGPL'] # Вы можете настроить этот список
        
    def load_technical_specification(self):
        """Загрузка технического задания"""
        try:
            with open('/app/tz.md', 'r', encoding='utf-8') as f:
                self.technical_spec = f.read()
            logger.info("✅ Техническое задание загружено")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки ТЗ: {e}")
            self.technical_spec = ""

    def load_critical_patterns_from_db(self):
        """Загрузка критичных паттернов из таблицы dev_control.agent_rules"""
        self.critical_patterns = []
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("SELECT rule_value FROM dev_control.agent_rules WHERE rule_type = %s AND is_active = TRUE", ('critical_pattern',))
                for row in cur.fetchall():
                    self.critical_patterns.append(row[0])
            logger.info(f"✅ Загружено {len(self.critical_patterns)} критичных паттернов из БД.")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки критичных паттернов из БД: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            self.critical_patterns = []

    def send_telegram_notification(self, message):
        """Отправка уведомления в Telegram"""
        if not self.telegram_bot or not self.telegram_chat_id:
            logger.warning("Telegram бот или ID чата не настроены. Уведомление не отправлено.")
            return
        try:
            self.telegram_bot.send_message(chat_id=self.telegram_chat_id, text=message)
            logger.info("✅ Уведомление Telegram отправлено.")
        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки Telegram уведомления: {e}")

    def check_advanced_secrets(self, file_content, file_path):
        """Расширенное сканирование секретов с помощью detect-secrets"""
        violations = []
        if not file_content:
            return violations

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Изменено: удален аргумент --output -
            result = subprocess.run(['detect-secrets', 'scan', '--all-files', tmp_file_path],
                                    capture_output=True, text=True, check=True)
            
            scan_output = json.loads(result.stdout)
            
            for filename, findings in scan_output.get('results', {}).items():
                for finding in findings:
                    violations.append({
                        'type': 'ADVANCED_SECRET',
                        'pattern': finding.get('type', 'unknown'),
                        'matches': finding.get('hashed_secret', 'N/A'),
                        'file_path': file_path,
                        'severity': 'critical',
                        'description': f"Обнаружен потенциальный секрет типа '{finding.get('type', 'unknown')}' в строке {finding.get('line_number', 'N/A')}."
                    })
        except FileNotFoundError:
            logger.error("❌ detect-secrets не найден. Убедитесь, что он установлен.")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ошибка выполнения detect-secrets: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга вывода detect-secrets: {e}")
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

        return violations

    def check_license_compliance(self, file_path):
        """Проверка лицензий зависимостей (запускается при анализе requirements.txt) """
        violations = []
        if os.path.basename(file_path) != 'requirements.txt':
            return violations

        logger.info(f"Запуск проверки лицензий для {file_path}...")
        try:
            result = subprocess.run(['pip-licenses', '--format', 'json'],
                                    capture_output=True, text=True, check=True)
            licenses_data = json.loads(result.stdout)

            for pkg in licenses_data:
                license_name = pkg.get('License', 'UNKNOWN')
                if any(forbidden_lic in license_name for forbidden_lic in self.forbidden_licenses):
                    violations.append({
                        'type': 'LICENSE_VIOLATION',
                        'pattern': license_name,
                        'matches': pkg.get('Name', 'N/A'),
                        'file_path': file_path,
                        'severity': 'critical',
                        'description': f"Зависимость '{pkg.get('Name', 'N/A')}' использует запрещенную лицензию: {license_name}."
                    })
        except FileNotFoundError:
            logger.error("❌ pip-licenses не найден. Убедитесь, что он установлен.")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ошибка выполнения pip-licenses: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга вывода pip-licenses: {e}")

        return violations

    def check_naming_conventions(self, file_content, file_path):
        """Проверка соглашений по именованию (базовая) для Python файлов"""
        violations = []
        if not file_path.endswith('.py'):
            return violations

        lines = file_content.split('\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            class_match = re.search(r'^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if class_match:
                class_name = class_match.group(1)
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                    violations.append({
                        'type': 'NAMING_CONVENTION',
                        'pattern': 'PascalCase for classes',
                        'matches': class_name,
                        'file_path': file_path,
                        'severity': 'medium',
                        'description': f"Имя класса '{class_name}' в строке {line_num} не соответствует PascalCase."
                    })
            
            func_match = re.search(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if func_match:
                func_name = func_match.group(1)
                if not re.match(r'^[a-z_][a-z0-9_]*$', func_name):
                    violations.append({
                        'type': 'NAMING_CONVENTION',
                        'pattern': 'snake_case for functions',
                        'matches': func_name,
                        'file_path': file_path,
                        'severity': 'medium',
                        'description': f"Имя функции '{func_name}' в строке {line_num} не соответствует snake_case."
                    })

        return violations

    def analyze_code(self, file_content, file_path):
        """AI анализ кода"""
        analysis_result = {
            'tz_compliance_score': 0.0,
            'quality_score': 0.0,
            'security_score': 0.0,
            'violations': [],
            'recommendations': [],
            'is_critical': False
        }
        
        critical_violations = self.check_critical_patterns(file_content, file_path)
        if critical_violations:
            analysis_result['violations'].extend(critical_violations)
            analysis_result['is_critical'] = True
            analysis_result['security_score'] = 0.0
        else:
            analysis_result['security_score'] = 8.5
            
        advanced_secret_violations = self.check_advanced_secrets(file_content, file_path)
        if advanced_secret_violations:
            analysis_result['violations'].extend(advanced_secret_violations)
            analysis_result['is_critical'] = True
            analysis_result['security_score'] = 0.0

        license_violations = self.check_license_compliance(file_path)
        if license_violations:
            analysis_result['violations'].extend(license_violations)
            analysis_result['is_critical'] = True
            analysis_result['security_score'] = 0.0

        naming_violations = self.check_naming_conventions(file_content, file_path)
        if naming_violations:
            analysis_result['violations'].extend(naming_violations)

        tz_score = self.check_tz_compliance(file_content)
        analysis_result['tz_compliance_score'] = tz_score
        
        quality_score = self.check_code_quality(file_content, file_path)
        analysis_result['quality_score'] = quality_score
        
        recommendations = self.generate_recommendations(analysis_result['violations'])
        analysis_result['recommendations'] = recommendations
        
        return analysis_result
        
    def check_critical_patterns(self, file_content, file_path):
        """Проверка критичных паттернов безопасности"""
        violations = []
        
        for pattern in self.critical_patterns:
            matches = re.findall(pattern, file_content, re.IGNORECASE)
            if matches:
                violations.append({
                    'type': 'CRITICAL_SECURITY',
                    'pattern': pattern,
                    'matches': matches,
                    'file_path': file_path,
                    'severity': 'critical',
                    'description': f"Обнаружен критичный паттерн безопасности: {pattern}"
                })
                
        return violations
        
    def check_tz_compliance(self, file_content):
        """Проверка соответствия техническому заданию"""
        if not self.technical_spec:
            return 5.0
            
        tz_words = set(re.findall(r'\b\w+\b', self.technical_spec.lower()))
        code_words = set(re.findall(r'\b\w+\b', file_content.lower()))
        
        if not tz_words:
            return 5.0
            
        intersection = len(tz_words.intersection(code_words))
        union = len(tz_words.union(code_words))
        
        similarity = (intersection / union) * 10 if union > 0 else 0
        return min(similarity, 10.0)
        
    def check_code_quality(self, file_content, file_path):
        """Проверка качества кода"""
        score = 10.0
        lines = file_content.split('\n')
        
        long_lines = [i for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            score -= min(len(long_lines) * 0.1, 2.0)
            
        if not any(line.strip().startswith('#') or '"""' in line for line in lines):
            score -= 1.0
            
        max_indent = max((len(line) - len(line.lstrip()) for line in lines if line.strip()), default=0)
        if max_indent > 16:
            score -= 1.5
            
        return max(score, 0.0)
        
    def generate_recommendations(self, violations):
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        for violation in violations:
            if violation['type'] == 'CRITICAL_SECURITY':
                recommendations.append(
                    f"КРИТИЧНО: Удалите {violation['pattern']} из кода. "
                    f"Используйте переменные окружения или конфигурационные файлы."
                )
            elif violation['type'] == 'ADVANCED_SECRET':
                recommendations.append(
                    f"КРИТИЧНО: Обнаружен потенциальный секрет. "
                    f"Переместите чувствительные данные в безопасное хранилище (например, переменные окружения, Vault)."
                )
            elif violation['type'] == 'LICENSE_VIOLATION':
                recommendations.append(
                    f"КРИТИЧНО: Обнаружена зависимость с запрещенной лицензией ({violation['pattern']}). "
                    f"Замените зависимость или получите соответствующее разрешение."
                )
            elif violation['type'] == 'NAMING_CONVENTION':
                recommendations.append(
                    f"Рекомендация: Исправьте нарушение соглашения по именованию: {violation['description']}"
                )
                
        return recommendations

    def save_analysis_result(self, file_event_id, analysis_result):
        """Сохранение результата анализа в БД"""
        # Ограничиваем значения score до 9.99, чтобы избежать numeric field overflow
        tz_score = min(analysis_result['tz_compliance_score'], 9.99)
        quality_score = min(analysis_result['quality_score'], 9.99)
        security_score = min(analysis_result['security_score'], 9.99)

        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dev_control.ai_analysis 
                (file_event_id, tz_compliance_score, quality_score, security_score, 
                 violations, recommendations, is_blocked)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                file_event_id,
                tz_score,
                quality_score, 
                security_score,
                json.dumps(analysis_result['violations']),
                '\n'.join(analysis_result['recommendations']),
                analysis_result['is_critical']
            ))
            
            analysis_id = cur.fetchone()
            self.db_conn.commit()
            
            if analysis_result['is_critical']:
                self.block_file(file_event_id, analysis_result['violations'])
                notification_message = f"☠СКРИТИЧНОЕ НАРУШЕНИЕ ОБНАРУЖЕНО!\nФайл: {analysis_result['file_path']}\nНарушения: {len(analysis_result['violations'])} шт.\nПодробности в дашборде: http://localhost:8080"
                self.send_telegram_notification(notification_message)
                
            return analysis_id
            
    def block_file(self, file_event_id, violations):
        """Блокировка файла при критичных нарушениях"""
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT file_path, developer_id FROM dev_control.file_events 
                WHERE id = %s
            """, (file_event_id,))
            
            file_info = cur.fetchone()
            if not file_info:
                return
                
            file_path, developer_id = file_info
            
            cur.execute("""
                INSERT INTO dev_control.blocked_files (file_path, developer_id, reason)
                VALUES (%s, %s, %s)
            """, (
                file_path,
                developer_id,
                f"Критичные нарушения: {len(violations)} шт."
            ))
            
            for violation in violations:
                cur.execute("""
                    INSERT INTO dev_control.violations 
                    (file_event_id, violation_type, severity, description)
                    VALUES (%s, %s, %s, %s)
                """, (
                    file_event_id,
                    violation['type'],
                    violation['severity'],
                    violation['description']
                ))
            
            self.db_conn.commit()
            
            try:
                import os, stat
                # Removed path conversion, using file_path directly
                logger.info(f"Attempting to chmod: {file_path}") # Changed log
                os.chmod(file_path, stat.S_IREAD)
                logger.warning(f" ФАЙЛ ЗАБЛОКИРОВАН: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка блокировки файла: {e}")

    def process_analysis_queue(self):
        """Обработка очереди анализа"""
        logger.info(" AI Auditor запущен...")
        
        while True:
            message = self.redis_client.brpop('ai_analysis_queue', timeout=5)
            if not message:
                continue

            _, message_data = message
            task = json.loads(message_data)
            
            try:
                logger.info(f" Анализ файла: {task['file_path']}")
                
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        SELECT file_content FROM dev_control.file_events 
                        WHERE id = %s
                    """, (task['file_event_id'],))
                    
                    result = cur.fetchone()
                    if not result:
                        logger.error(f"Событие {task['file_event_id']} не найдено")
                        continue
                        
                    file_content = result[0] or ""
                
                logger.info(f"File content: {file_content}") # Added log
                
                analysis_result = self.analyze_code(file_content, task['file_path'])
                
                self.save_analysis_result(task['file_event_id'], analysis_result)
                
                if analysis_result['is_critical']:
                    logger.warning(f"☠ КРИТИЧНЫЕ НАРУШЕНИЯ в {task['file_path']}")
                else:
                    logger.info(f"✅ Анализ завершен: {task['file_path']}")
                
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        UPDATE dev_control.file_events 
                        SET processed = TRUE 
                        WHERE id = %s
                    """, (task['file_event_id'],))
                    self.db_conn.commit()
                    
            except Exception as e:
                logger.error(f"Ошибка обработки задачи для file_event_id {task.get('file_event_id')}: {e}")
                if self.db_conn:
                    self.db_conn.rollback()
                time.sleep(1)

if __name__ == "__main__":
    auditor = AICodeAuditor()
    auditor.process_analysis_queue()