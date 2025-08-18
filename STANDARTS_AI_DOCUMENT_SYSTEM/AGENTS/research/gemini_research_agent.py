import google.generativeai as genai
from pathlib import Path
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GeminiResearchAgent:
    """
    ResearchAgent, использующий Gemini API для исследования.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key for Gemini is required.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')  # для сложных задач
        self.docs_path = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        logger.info("GeminiResearchAgent initialized.")

    async def research(self, query: str, use_web: bool = True) -> Optional[Dict[str, Any]]:
        """
        Выполняет исследование с Gemini.
        """
        prompt = f"""
        Ты ResearchAgent. Проведи глубокое исследование по теме: {query}

        {'Используй актуальную информацию из интернета.' if use_web else 'Используй только свои знания.'}

        Предоставь:
        1. Ключевые факты и определения
        2. Актуальные данные и статистику
        3. Лучшие практики и примеры
        4. Потенциальные проблемы и решения
        5. Связанные темы для дальнейшего изучения

        Формат ответа: структурированный JSON
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
                tools=['google_search_retrieval'] if use_web else []
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error during Gemini research: {e}")
            return None

    async def research_with_context(self, query: str, documents: List[str]) -> Optional[str]:
        """
        Исследование с контекстом из документов.
        """
        context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])

        prompt = f"""
        Контекст из проекта:
        {context}

        Задача: {query}

        Проанализируй предоставленные документы и ответь на задачу.
        Используй ТОЛЬКО информацию из документов.
        """

        try:
            response = self.pro_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini research with context: {e}")
            return None

    async def research_multimodal(self, query: str, images: Optional[List[str]] = None, pdfs: Optional[List[str]] = None) -> Optional[str]:
        """
        Исследование с картинками и PDF.
        """
        parts = [query]

        if images:
            for img_path in images:
                img = genai.upload_file(path=img_path)
                parts.append(img)

        if pdfs:
            for pdf_path in pdfs:
                pdf = genai.upload_file(path=pdf_path)
                parts.append(pdf)

        try:
            response = self.model.generate_content(parts)
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini multimodal research: {e}")
            return None

    async def research_with_tools(self, query: str) -> Optional[str]:
        """
        Исследование с function calling.
        """
        # Gemini поддерживает function calling!
        tools = [
            {
                "function_declarations": [
                    {
                        "name": "search_documentation",
                        "description": "Search in project documentation",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "category": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "analyze_code",
                        "description": "Analyze code structure",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        ]

        try:
            response = self.model.generate_content(
                query,
                tools=tools
            )

            # Обработка function calls
            for part in response.parts:
                if fn := part.function_call:
                    # Выполни функцию
                    result = await self.execute_function(fn.name, fn.args)
                    # Продолжи диалог с результатом
                    response = self.model.generate_content(
                        [query, result],
                        tools=tools
                    )

            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini research with tools: {e}")
            return None

    async def execute_function(self, function_name: str, args: Dict[str, Any]) -> str:
        """
        Имитация выполнения функций, которые Gemini может вызвать.
        В реальной системе здесь будет логика вызова реальных функций.
        """
        logger.info(f"Executing mocked function: {function_name} with args: {args}")
        if function_name == "search_documentation":
            # Здесь можно добавить реальную логику поиска по документации
            return f"Mocked search results for query '{args.get('query')}' in category '{args.get('category')}'"
        elif function_name == "analyze_code":
            # Здесь можно добавить реальную логику анализа кода
            return f"Mocked code analysis for file '{args.get('file_path')}'"
        return "Unknown function"

    def load_process_docs(self, process_id: str) -> List[str]:
        """
        Загружает документы, связанные с конкретным процессом.
        Имитация загрузки из папок 00-13.
        """
        docs = []
        # Пример: поиск markdown файлов в папке 00_DOCUMENTATION
        for path in self.docs_path.rglob(f"**/*{process_id}*.md"):
            try:
                docs.append(path.read_text())
            except Exception as e:
                logger.warning(f"Could not read file {path}: {e}")
        return docs

    async def research_process(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Исследует конкретный процесс (P1.1, P2.3, etc).
        """
        docs = self.load_process_docs(process_id)

        prompt = f"""
        Ты ResearchAgent для процесса {process_id}.

        Документы проекта:
        {docs}

        Задачи:
        1. Проанализируй текущее состояние процесса
        2. Найди все пробелы и проблемы
        3. Предложи улучшения
        4. Создай план действий
        5. Оцени соответствие стандартам (ITIL, ISO, COBIT)

        Ответ в формате JSON с полями:
        - current_state
        - gaps
        - improvements
        - action_plan
        - compliance_score
        """
        try:
            response = self.pro_model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error researching process {process_id}: {e}")
            return None

    async def research_agent_implementation(self, agent_name: str) -> Optional[str]:
        """
        Исследует как реализовать конкретного агента.
        """
        prompt = f"""
        Создай детальный план реализации {agent_name}.

        Контекст: Multi-Agent System для управления документацией

        Требования:
        - Python 3.11+
        - Асинхронная архитектура
        - Integration с другими агентами
        - Error handling и retry logic
        - Monitoring и logging

        Предоставь:
        1. Архитектуру агента
        2. Основные классы и методы
        3. Примеры кода
        4. Интеграционные точки
        5. Тестовые сценарии
        """
        try:
            response = self.pro_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.9,
                    "max_output_tokens": 16384
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Error researching agent implementation for {agent_name}: {e}")
            return None

# Пример использования (для тестирования)
async def main():
    # ВНИМАНИЕ: Замените 'YOUR_GEMINI_API_KEY' на ваш реальный API ключ
    # Рекомендуется использовать переменные окружения для хранения ключей
    api_key = "YOUR_GEMINI_API_KEY" 
    
    if api_key == "YOUR_GEMINI_API_KEY":
        logger.warning("Using placeholder API key. Please replace with your actual Gemini API key.")
        return

    agent = GeminiResearchAgent(api_key=api_key)
    
    print("\n" + "="*50)
    print("GEMINI RESEARCH AGENT TEST")
    print("="*50)

    # Тест 1: Базовое исследование с веб-поиском
    query_web = "Latest advancements in quantum computing"
    results_web = await agent.research(query_web, use_web=True)
    if results_web:
        print(f"\n--- Results for '{query_web}' (Web Search) ---")
        print(json.dumps(results_web, indent=2, ensure_ascii=False))
    else:
        print(f"Failed to get results for '{query_web}'.")

    # Тест 2: Исследование без веб-поиска (только знания модели)
    query_no_web = "Define blockchain technology"
    results_no_web = await agent.research(query_no_web, use_web=False)
    if results_no_web:
        print(f"\n--- Results for '{query_no_web}' (No Web Search) ---")
        print(json.dumps(results_no_web, indent=2, ensure_ascii=False))
    else:
        print(f"Failed to get results for '{query_no_web}'.")

    # Тест 3: Исследование процесса (имитация загрузки документов)
    # Для этого теста убедитесь, что у вас есть файлы, содержащие 'P1.1' в названии
    # в директории DocumentsSystem или ее поддиректориях.
    query_process = "P1.1"
    process_results = await agent.research_process(query_process)
    if process_results:
        print(f"\n--- Results for Process '{query_process}' ---")
        print(json.dumps(process_results, indent=2, ensure_ascii=False))
    else:
        print(f"Failed to get results for process '{query_process}'.")

    print("\n" + "="*50)
    print("GEMINI RESEARCH AGENT TEST COMPLETED")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())