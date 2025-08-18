import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StyleValidator:
    """
    Класс для валидации стиля сгенерированного контента.
    """
    def __init__(self):
        logger.info("StyleValidator initialized.")

    def validate_markdown_style(self, content: str) -> (bool, str):
        """
        Проверяет базовый стиль Markdown контента.
        
        Args:
            content (str): Сгенерированный Markdown контент.
            
        Returns:
            (bool, str): True и сообщение об успехе, если стиль соответствует, иначе False и сообщение об ошибке.
        """
        errors = []

        # Пример 1: Проверка наличия заголовка первого уровня
        if not content.strip().startswith('# '):
            errors.append("Content should start with a top-level heading (#).")

        # Пример 2: Проверка на двойные пробелы
        if "  " in content:
            errors.append("Content contains double spaces.")

        # Пример 3: Проверка на пустые строки в начале/конце
        if content.startswith('\n') or content.endswith('\n'):
            errors.append("Content should not start or end with a newline.")

        if errors:
            return False, "; ".join(errors)
        else:
            return True, "Markdown style is valid."

    def validate_code_style(self, content: str, language: str) -> (bool, str):
        """
        Проверяет базовый стиль кода.
        
        Args:
            content (str): Сгенерированный код.
            language (str): Язык программирования (например, "python", "javascript").
            
        Returns:
            (bool, str): True и сообщение об успехе, если стиль соответствует, иначе False и сообщение об ошибке.
        """
        errors = []

        if language.lower() == "python":
            # Пример: Проверка на PEP8 (очень базовая)
            if "\t" in content: # Проверка на табы вместо пробелов
                errors.append("Python code should use spaces instead of tabs (PEP8).")
            if "print(" in content: # Пример: избегать print в продакшн коде
                errors.append("Python code contains print statements. Consider using logging.")
        elif language.lower() == "javascript":
            if ";;" in content: # Пример: двойные точки с запятой
                errors.append("JavaScript code contains double semicolons.")
        else:
            return True, f"No specific style validation for {language}."

        if errors:
            return False, "; ".join(errors)
        else:
            return True, f"{language} code style is valid."

# Пример использования (для тестирования)
async def main():
    validator = StyleValidator()
    
    # Тест Markdown
    md_content_good = "# My Document\n\nThis is a test.\n"
    md_content_bad = "  # My Document\n\nThis is a test.\n\n"
    
    status, msg = validator.validate_markdown_style(md_content_good)
    print(f"Good Markdown: Status={status}, Message={msg}")
    
    status, msg = validator.validate_markdown_style(md_content_bad)
    print(f"Bad Markdown: Status={status}, Message={msg}")

    # Тест Python
    py_content_good = "def hello():\n    print('Hello') # Это будет ошибка по правилу\n"
    py_content_bad = "def hello():\n\tprint('Hello')\n"

    status, msg = validator.validate_code_style(py_content_good, "python")
    print(f"Good Python: Status={status}, Message={msg}")

    status, msg = validator.validate_code_style(py_content_bad, "python")
    print(f"Bad Python: Status={status}, Message={msg}")

if __name__ == "__main__":
    asyncio.run(main())