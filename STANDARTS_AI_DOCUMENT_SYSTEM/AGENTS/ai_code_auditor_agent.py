#!/usr/bin/env python3
import redis
import json
import time

def main():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True, password='galaxy_redis_secure_2024')
    p = r.pubsub(ignore_subscribe_messages=True)
    p.subscribe('file_changes', 'agent_ping')
    print("AI Code Auditor Agent (Python) запущен и слушает каналы...")

    while True:
        try:
            message = p.get_message(timeout=1)
            if message:
                channel = message['channel']
                data = json.loads(message['data'])
                
                if channel == 'agent_ping' and data.get('agent_id') == 'ai_code_auditor':
                    print("❤️ Получен ping, отвечаю pong...")
                    pong_message = json.dumps({'agent_id': 'ai_code_auditor', 'status': 'alive'})
                    r.lpush('agent_pong', pong_message)

                elif channel == 'file_changes':
                    print(f"📄 Получено изменение файла: {data.get('file_path')}")
                    time.sleep(1) # Эмуляция анализа
                    result = {
                        'tzComplianceScore': 0.9,
                        'qualityScore': 0.85
                    }
                    print("Анализ завершен.")
                    r.publish('analysis_results', json.dumps(result))
            else:
                time.sleep(0.1)
        except redis.exceptions.ConnectionError as e:
            print(f"Ошибка подключения к Redis: {e}. Повторная попытка через 5с...")
            time.sleep(5)
        except Exception as e:
            print(f"Критическая ошибка в агенте: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
