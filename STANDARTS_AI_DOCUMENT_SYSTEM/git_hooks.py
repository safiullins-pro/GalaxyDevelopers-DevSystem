#!/usr/bin/env python3
import os
import sys
import json
import redis
import psycopg2
import subprocess
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'developer_control'),
        user=os.getenv('POSTGRES_USER', 'control_admin'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def check_blocked_files():
    """Проверка заблокированных файлов перед коммитом"""
    
    db_conn = get_db_connection()
    
    try:
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True, check=True)
        changed_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ Ошибка получения списка файлов")
        return False
    
    blocked_files = []
    
    with db_conn.cursor() as cur:
        for file_path in changed_files:
            if not file_path:
                continue
                
            # Преобразуем путь к абсолютному, чтобы он соответствовал записям в БД
            # Важно: это должно быть сделано относительно корня проекта, а не текущей директории хука
            # Для простоты, предположим, что хук запускается из корня репозитория
            abs_file_path = os.path.abspath(file_path)
            
            cur.execute("""
                SELECT reason, blocked_at FROM dev_control.blocked_files 
                WHERE file_path = %s AND unblocked_at IS NULL
            """, (abs_file_path,))
            
            blocked_info = cur.fetchone()
            if blocked_info:
                blocked_files.append({
                    'path': file_path,
                    'reason': blocked_info[0],
                    'blocked_at': blocked_info[1]
                })
    
    if blocked_files:
        print("\n⛔ КОММИТ ЗАБЛОКИРОВАН!")
        print("Обнаружены файлы с критичными нарушениями:\n")
        
        for blocked in blocked_files:
            print(f" {blocked['path']}")
            print(f"   Причина: {blocked['reason']}")
            print(f"   Заблокирован: {blocked['blocked_at']}")
            print()
        
        print("Исправьте нарушения и попробуйте снова.")
        return False
    
    return True

def check_file_placement():
    """Проверка размещения файлов по правилам проекта"""
    
    # Правила размещения файлов: {расширение: [список_допустимых_префиксов_пути]}
    # Пути должны быть относительными от корня репозитория
    # Можно добавить более сложные правила, например, regex для путей
    placement_rules = {
        '.py': ['AGENTS/', 'SCRIPTS/', 'tests/', 'config/', '__pycache__/', 'ARCHIVE/', 'FirstOrder/', 'galaxy-analytics-infrastructure/', 'monitoring/', 'PROCESSES/', 'PROJECT_MANAGEMENT/', 'ROLES/', 'static/', 'templates/', 'ToDo/', 'UNFUCK_THIS_SHIT.md', 'test_all_agents.py', 'stop_infrastructure.sh', 'start_infrastructure.sh', 'run_tests.sh', 'requirements.txt', 'README.md', 'pytest.ini', 'pyproject.toml', 'PHASE_COMPLETION_REPORT.md', 'PROJECT_INDEX.md', 'MID_DEVELOPMENT_STATUS_REPORT.md', 'GIT_STATUS_REPORT.md', 'DOCUMENTATION_SYSTEM_ARCHITECTURE.md', 'Dockerfile.dev_isolation', 'docker-compose.minimal.yml', 'developer_control_schema.sql', 'CRITICAL_TODO_COMPLETION.md', 'conftest.py', 'config_manager.py', 'CLOUD-FUNCTION.code-workspace', 'AUTOPSY_REPORT.json', 'APOLOGY_FOR_BEING_RETARDED.md', 'Полный аудит веб-сайта 2025.audit', '.pre-commit-config.yaml', '.gitignore', '.env.production', '.env.example', '.env', '.dockerignore', 'TASK_LIST_TO_PHASE_4_COMPLETION.md', '07_DELIVERABLES/', '.pytest_cache/', '.github/', '.claude/', '__pycache__/', 'documents_system.egg-info/', 'DOCUMENTATION/', 'docs/', 'DELIVERABLES/', 'data/', 'CONFIGS/', 'backups/', 'ARCHIVE/', 'AGENTS/'],
        '.sql': ['db/', 'sql/', 'developer_control_schema.sql', 'ARCHIVE/'],
        '.md': ['docs/', 'README.md', 'PROJECT_INDEX.md', 'APOLOGY_FOR_BEING_RETARDED.md', 'CRITICAL_TODO_COMPLETION.md', 'DOCUMENTATION_SYSTEM_ARCHITECTURE.md', 'GIT_STATUS_REPORT.md', 'MID_DEVELOPMENT_STATUS_REPORT.md', 'PHASE_COMPLETION_REPORT.md', 'TASK_LIST_TO_PHASE_4_COMPLETION.md', 'UNFUCK_THIS_SHIT.md', 'technical_specification.md', 'CODING_STANDARDS.md', 'DEVELOPER_GUIDELINES.md'],
        '.html': ['templates/', 'static/'],
        '.css': ['static/css/'],
        '.js': ['static/js/'],
        '.ts': ['AGENTS/', 'tests/'], # For TypeScript files
        '.json': ['data/', 'config/', 'AUTOPSY_REPORT.json', 'safari-audit-complete.json.download/', '.claude/'],
        '.yml': ['CONFIGS/', 'docker-compose.minimal.yml'],
        '.sh': ['SCRIPTS/', 'start_infrastructure.sh', 'stop_infrastructure.sh', 'run_tests.sh', 'ARCHIVE/'],
        # Добавьте другие правила по мере необходимости
    }

    try:
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True, check=True)
        changed_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ Ошибка получения списка файлов для проверки размещения")
        return False

    violations = []
    for file_path in changed_files:
        if not file_path:
            continue

        # Пропускаем файлы, которые не должны быть в репозитории (например, из .gitignore)
        # Это упрощенная проверка, более надежная - через git check-ignore
        if any(ignore_pattern in file_path for ignore_pattern in ['.pyc', '__pycache__', '.DS_Store', '.tmp']):
            continue

        found_rule = False
        for ext, allowed_prefixes in placement_rules.items():
            if file_path.endswith(ext):
                found_rule = True
                is_correctly_placed = False
                for prefix in allowed_prefixes:
                    if file_path.startswith(prefix) or (prefix == 'README.md' and file_path == 'README.md') or (prefix == 'technical_specification.md' and file_path == 'technical_specification.md') or (prefix == 'CODING_STANDARDS.md' and file_path == 'CODING_STANDARDS.md') or (prefix == 'DEVELOPER_GUIDELINES.md' and file_path == 'DEVELOPER_GUIDELINES.md') or (prefix == 'developer_control_schema.sql' and file_path == 'developer_control_schema.sql') or (prefix == 'docker-compose.minimal.yml' and file_path == 'docker-compose.minimal.yml') or (prefix == 'start_infrastructure.sh' and file_path == 'start_infrastructure.sh') or (prefix == 'stop_infrastructure.sh' and file_path == 'stop_infrastructure.sh') or (prefix == 'run_tests.sh' and file_path == 'run_tests.sh') or (prefix == 'requirements.txt' and file_path == 'requirements.txt') or (prefix == 'pytest.ini' and file_path == 'pytest.ini') or (prefix == 'pyproject.toml' and file_path == 'pyproject.toml') or (prefix == 'PHASE_COMPLETION_REPORT.md' and file_path == 'PHASE_COMPLETION_REPORT.md') or (prefix == 'PROJECT_INDEX.md' and file_path == 'PROJECT_INDEX.md') or (prefix == 'MID_DEVELOPMENT_STATUS_REPORT.md' and file_path == 'MID_DEVELOPMENT_STATUS_REPORT.md') or (prefix == 'GIT_STATUS_REPORT.md' and file_path == 'GIT_STATUS_REPORT.md') or (prefix == 'DOCUMENTATION_SYSTEM_ARCHITECTURE.md' and file_path == 'DOCUMENTATION_SYSTEM_ARCHITECTURE.md') or (prefix == 'Dockerfile.dev_isolation' and file_path == 'Dockerfile.dev_isolation') or (prefix == 'docker-compose.minimal.yml' and file_path == 'docker-compose.minimal.yml') or (prefix == 'developer_control_schema.sql' and file_path == 'developer_control_schema.sql') or (prefix == 'CRITICAL_TODO_COMPLETION.md' and file_path == 'CRITICAL_TODO_COMPLETION.md') or (prefix == 'conftest.py' and file_path == 'conftest.py') or (prefix == 'config_manager.py' and file_path == 'config_manager.py') or (prefix == 'CLOUD-FUNCTION.code-workspace' and file_path == 'CLOUD-FUNCTION.code-workspace') or (prefix == 'AUTOPSY_REPORT.json' and file_path == 'AUTOPSY_REPORT.json') or (prefix == 'APOLOGY_FOR_BEING_RETARDED.md' and file_path == 'APOLOGY_FOR_BEING_RETARDED.md') or (prefix == 'Полный аудит веб-сайта 2025.audit' and file_path == 'Полный аудит веб-сайта 2025.audit') or (prefix == '.pre-commit-config.yaml' and file_path == '.pre-commit-config.yaml') or (prefix == '.gitignore' and file_path == '.gitignore') or (prefix == '.env.production' and file_path == '.env.production') or (prefix == '.env.example' and file_path == '.env.example') or (prefix == '.env' and file_path == '.env') or (prefix == '.dockerignore' and file_path == '.dockerignore') or (prefix == 'TASK_LIST_TO_PHASE_4_COMPLETION.md' and file_path == 'TASK_LIST_TO_PHASE_4_COMPLETION.md') or (prefix == '07_DELIVERABLES/' and file_path.startswith('07_DELIVERABLES/')) or (prefix == '.pytest_cache/' and file_path.startswith('.pytest_cache/')) or (prefix == '.github/' and file_path.startswith('.github/')) or (prefix == '.claude/' and file_path.startswith('.claude/')) or (prefix == '__pycache__/' and file_path.startswith('__pycache__/')) or (prefix == 'documents_system.egg-info/' and file_path.startswith('documents_system.egg-info/')) or (prefix == 'DOCUMENTATION/' and file_path.startswith('DOCUMENTATION/')) or (prefix == 'docs/' and file_path.startswith('docs/')) or (prefix == 'DELIVERABLES/' and file_path.startswith('DELIVERABLES/')) or (prefix == 'data/' and file_path.startswith('data/')) or (prefix == 'CONFIGS/' and file_path.startswith('CONFIGS/')) or (prefix == 'backups/' and file_path.startswith('backups/')) or (prefix == 'ARCHIVE/' and file_path.startswith('ARCHIVE/')) or (prefix == 'AGENTS/' and file_path.startswith('AGENTS/')):
                        is_correctly_placed = True
                        break
                if not is_correctly_placed:
                    violations.append(f"Файл '{file_path}' с расширением '{ext}' находится в недопустимой директории. Ожидается одна из: {', '.join(allowed_prefixes)}")
                break
        if not found_rule:
            # Если для расширения нет правила, это может быть либо ошибка, либо допустимый файл в корне
            # Для простоты, если нет правила, считаем, что файл должен быть в корне или в известных местах
            if '/' in file_path and not any(file_path.startswith(p) for p in ['docs/', 'templates/', 'static/', 'db/', 'sql/', 'src/', 'tests/', 'scripts/', 'AGENTS/', 'ARCHIVE/', 'CONFIGS/', 'data/', 'DELIVERABLES/', 'DOCUMENTATION/', 'FirstOrder/', 'galaxy-analytics-infrastructure/', 'git-repos/', 'JOURNALS/', 'logs/', 'monitoring/', 'nginx/', 'process-docs/', 'PROCESSES/', 'PROJECT_MANAGEMENT/', 'PROMPTS/', 'REPORTS/', 'ROLES/', 'SCRIPTS/', 'STANDARDS/', 'ToDo/']):
                violations.append(f"Файл '{file_path}' имеет неизвестное расширение или находится в недопустимой директории.")

    if violations:
        print("\n⛔ КОММИТ ЗАБЛОКИРОВАН: Обнаружены нарушения в размещении файлов!\n")
        for v in violations:
            print(f" - {v}")
        print("\nПожалуйста, переместите файлы в соответствующие директории и попробуйте снова.")
        return False
    return True

def check_commit_message():
    """Проверка сообщения коммита"""
    commit_msg_file = sys.argv[1] if len(sys.argv) > 1 else '.git/COMMIT_EDITMSG'
    
    try:
        with open(commit_msg_file, 'r', encoding='utf-8') as f:
            commit_msg = f.read().strip()
    except FileNotFoundError:
        print("❌ Файл сообщения коммита не найден")
        return False
    
    # Минимальные требования к сообщению коммита
    if len(commit_msg) < 10:
        print("❌ Сообщение коммита слишком короткое (минимум 10 символов)")
        return False
        
    if not commit_msg[0].isupper():
        print("❌ Сообщение коммита должно начинаться с заглавной буквы")
        return False
        
    return True

def run_auto_formatting():
    """Автоматическое форматирование Python файлов с помощью Black"""
    try:
        # Получаем список Python файлов, которые были изменены и добавлены в стейджинг
        result = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM', '*.py'], 
                              capture_output=True, text=True, check=True)
        python_files = result.stdout.strip().split('\n')
        python_files = [f for f in python_files if f]

        if not python_files:
            print("Нет Python файлов для форматирования.")
            return True

        print(f"Форматирование {len(python_files)} Python файлов с помощью Black...")
        # Запускаем Black для форматирования файлов
        # --quiet чтобы не выводить информацию о каждом файле, если он не изменился
        # --diff чтобы показать изменения, но не применять их сразу
        # --check чтобы только проверить, но не изменять
        # Для применения форматирования, нужно убрать --check и --diff
        format_result = subprocess.run(['black'] + python_files, 
                                       capture_output=True, text=True)
        
        if format_result.returncode == 0:
            print("✅ Python файлы отформатированы.")
            # Если Black изменил файлы, нужно добавить их обратно в стейджинг
            subprocess.run(['git', 'add'] + python_files, check=True)
            return True
        elif format_result.returncode == 1:
            print("⚠️ Black внес изменения в файлы. Они были автоматически добавлены в стейджинг.")
            # Black возвращает 1, если были изменения. Нужно добавить их обратно в стейджинг.
            subprocess.run(['git', 'add'] + python_files, check=True)
            return True
        else:
            print(f"❌ Ошибка при форматировании Black: {format_result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Black не найден. Убедитесь, что он установлен в окружении разработчика.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения Black: {e.stderr}")
        return False

def check_commit_message_for_task_id():
    """Проверка сообщения коммита на наличие ID задачи (например, [TASK-123])"""
    commit_msg_file = sys.argv[1] if len(sys.argv) > 1 else '.git/COMMIT_EDITMSG'
    
    try:
        with open(commit_msg_file, 'r', encoding='utf-8') as f:
            commit_msg = f.read().strip()
    except FileNotFoundError:
        print("❌ Файл сообщения коммита не найден")
        return False
    
    # Пример паттерна для ID задачи: [TASK-123], [BUG-456], [FEATURE-789]
    # Можно настроить под вашу систему управления задачами
    task_id_pattern = r"^\[(TASK|BUG|FEATURE)-\d+\]"
    
    if not re.match(task_id_pattern, commit_msg):
        print("\n⛔ КОММИТ ЗАБЛОКИРОВАН: Сообщение коммита должно начинаться с ID задачи.")
        print("   Пример: [TASK-123] Описание задачи")
        return False
        
    return True

def main():
    hook_type = os.path.basename(sys.argv[0])
    
    if hook_type == 'pre-commit':
        if not check_blocked_files():
            sys.exit(1)
        if not check_file_placement():
            sys.exit(1)
        if not run_auto_formatting(): # Автоматическое форматирование
            sys.exit(1)
    elif hook_type == 'commit-msg':
        if not check_commit_message():
            sys.exit(1)
        if not check_commit_message_for_task_id(): # Проверка ID задачи в сообщении коммита
            sys.exit(1)
    
    print("✅ Все проверки пройдены. Коммит разрешен.")
    sys.exit(0)

if __name__ == "__main__":
    main()