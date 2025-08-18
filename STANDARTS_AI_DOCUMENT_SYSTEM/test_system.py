#!/usr/bin/env python3
import os
import time
import subprocess
import requests
import docker # Added import

print("Script started.")

def test_file_monitoring():
    """Тест мониторинга файлов"""
    print(" Тест 1: Мониторинг файлов")
    
    container_path = "/workspace/target/test_file.py"
    
    print("Connecting to Docker...")
    try:
        socket_path = "/Users/safiullins_pro/.docker/run/docker.sock"
        client = docker.DockerClient(base_url='unix://' + socket_path)
    except docker.errors.DockerException as e:
        print(f"❌ Docker SDK for Python не найден или не может подключиться к Docker-демону: {e}")
        return

    print("Creating test file inside container...")
    # Create the test file with critical content inside the developer_env container
    file_content = """
# Тестовый файл с критичными нарушениями
AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'  # Критичное нарушение, должно быть обнаружено detect-secrets
password = 'secret123'  # Дополнительный паттерн
api_key = 'pk_test_12345'  # Дополнительный паттерн

def test_function():
    return "Hello World"
"""
    
    try:
        developer_env_container = client.containers.get("documentssystem-developer_env-1")
    except docker.errors.NotFound:
        print("❌ Контейнер documentssystem-developer_env-1 не найден.")
        return
        
    # Use exec_run to create the file and sync it to disk
    developer_env_container.exec_run(f"bash -c \"echo '{file_content}' > {container_path} && sync\"")

    print(f"✅ Создан файл: {container_path} (внутри контейнера)")
    
    time.sleep(1) # Added sleep to allow file_monitor to read the content
    
    print("⏳ Ожидаем анализ AI аудитора и блокировку файла...")
    
    # Wait for the file to be blocked
    timeout = 30  # seconds
    start_time = time.time()
    blocked = False
    
    while time.time() - start_time < timeout:
        try:
            # Check if the file is writable inside the container
            exit_code, result = developer_env_container.exec_run(f'test -w {container_path} && echo "writable" || echo "readonly"')
            if "readonly" in result.decode('utf-8'):
                blocked = True
                break
        except docker.errors.ContainerError as e:
            # This can happen if the file doesn't exist yet in the container
            pass
        time.sleep(0.5) # Check every 0.5 seconds

    print("Blocking check loop finished.")
    if blocked:
        print("✅ Файл успешно заблокирован - write failed as expected")
    else:
        print("❌ Файл НЕ заблокирован (ошибка!) - таймаут ожидания блокировки")

def test_git_hooks():
    """Тест Git hooks"""
    print("\n Тест 2: Git hooks")
    
    # Инициализация git если нужно
    if not os.path.exists('.git'):
        subprocess.run(['git', 'init'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
    
    # Add the test file to git staging area
    subprocess.run(['git', 'add', 'workspace/test_file.py'], check=True)
    
    # Attempt to commit the blocked file
    result = subprocess.run(['git', 'commit', '-m', 'Test commit with blocked file'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✅ Git hook успешно заблокировал коммит")
        print(f"Вывод: {result.stdout}")
    else:
        print("❌ Git hook НЕ заблокировал коммит (ошибка!) - commit succeeded")

def test_web_dashboard():
    """Тест веб-дашборда"""
    print("\n Тест 3: Web Dashboard")
    
    try:
        response = requests.get('http://localhost:8080/api/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Web Dashboard работает")
            print(f"Статистика: {stats}")
        else:
            print(f"❌ Web Dashboard недоступен: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Ошибка подключения к Web Dashboard: {e}")

def test_database_connection():
    """Тест подключения к БД"""
    print("\n Тест 4: База данных")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database=os.getenv('POSTGRES_DB', 'developer_control'),
            user=os.getenv('POSTGRES_USER', 'control_admin'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dev_control.file_events")
            count = cur.fetchone()
            print(f"✅ База данных работает. События в БД: {count[0]}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")

def main():
    print(" ТЕСТИРОВАНИЕ СИСТЕМЫ АВТОКОНТРОЛЯ")
    print("="*50)
    
    test_file_monitoring()
    test_git_hooks() 
    test_web_dashboard()
    test_database_connection()
    
    print("\n" + "="*50)
    print(" Тестирование завершено!")
    print("\nЧтобы разблокировать тестовый файл:")
    print("curl -X POST http://localhost:8080/api/unblock_file -H 'Content-Type: application/json' -d '{\"file_path\": \"/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/workspace/test_file.py\"}'")

if __name__ == "__main__":
    main()
