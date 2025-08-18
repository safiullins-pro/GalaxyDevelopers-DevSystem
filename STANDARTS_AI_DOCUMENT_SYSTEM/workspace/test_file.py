
# Тестовый файл с критичными нарушениями
AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'  # Критичное нарушение, должно быть обнаружено detect-secrets
password = 'secret123'  # Дополнительный паттерн
api_key = 'pk_test_12345'  # Дополнительный паттерн

def test_function():
    return "Hello World"
