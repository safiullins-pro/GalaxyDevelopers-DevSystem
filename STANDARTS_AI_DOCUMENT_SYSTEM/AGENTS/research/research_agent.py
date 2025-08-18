#!/usr/bin/env python3
"""
ResearchAgent - Агент для поиска, сбора и синтеза информации из различных источников, используя Gemini AI.
Автор: GALAXYDEVELOPMENT
Версия: 1.0.0
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import uuid
from pathlib import Path

# Импорт новых модулей
from .gemini_research_agent import GeminiResearchAgent

# Настройка логирования (можно перенести в централизованную систему логирования)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessLogger:
    """Система журналирования всех операций"""
    
    def __init__(self, log_dir: str = "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка основного логгера
        self.logger = logging.getLogger('ResearchAgent')
        self.logger.setLevel(logging.DEBUG)
        
        # Файл для детального журнала
        fh = logging.FileHandler(self.log_dir / f'research_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh.setLevel(logging.DEBUG)
        
        # Консольный вывод
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # JSON журнал для структурированных данных
        self.json_log_path = self.log_dir / f'research_journal_{datetime.now().strftime("%Y%m%d")}.jsonl'
    
    def log_operation(self, operation_type: str, data: Dict[str, Any]):
        """Журналирование операции в JSON формате"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "data": data,
            "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        }
        
        with open(self.json_log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        self.logger.info(f"Operation logged: {operation_type}")
        return entry

class ResearchAgent:
    """Агент для поиска, сбора и синтеза информации."""
    
    def __init__(self, gemini_api_key: str, gemini_research_agent: Optional[GeminiResearchAgent] = None):
        self.logger = ProcessLogger()
        self.gemini_api_key = gemini_api_key
        self.gemini_research_agent = gemini_research_agent if gemini_research_agent else GeminiResearchAgent(api_key=gemini_api_key)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/data/research_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.logger.info("ResearchAgent initialized")
        self.logger.log_operation("AGENT_INIT", {"agent": "ResearchAgent", "version": "1.0.0"})

    async def initiate_research(self, query: str, sources: List[str], depth: int = 3, filters: Optional[Dict[str, Any]] = None) -> str:
        """Инициирует задачу исследования и возвращает task_id."""
        task_id = str(uuid.uuid4())

        # Validate sources immediately
        valid_sources = [s for s in sources if s in ["gemini", "internal_kb", "iso_standards"]]
        if not valid_sources:
            self.tasks[task_id] = {
                "query": query,
                "sources": sources,
                "depth": depth,
                "filters": filters,
                "status": "FAILED",
                "progress": 0,
                "results": [],
                "message": "No valid research sources provided."
            }
            self.logger.log_operation("RESEARCH_INITIATED_FAILED", {"task_id": task_id, "query": query, "sources": sources, "error": "No valid research sources provided."})
            return task_id

        self.tasks[task_id] = {
            "query": query,
            "sources": valid_sources, # Use valid_sources
            "depth": depth,
            "filters": filters,
            "status": "PENDING",
            "progress": 0,
            "results": [],
            "message": "Research initiated." # Изменено
        }
        self.logger.log_operation("RESEARCH_INITIATED", {"task_id": task_id, "query": query, "sources": valid_sources})
        
        # Запускаем задачу исследования в фоновом режиме
        asyncio.create_task(self._execute_research_task(task_id))
        
        return task_id

    async def get_research_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статус задачи исследования."""
        status_info = self.tasks.get(task_id)
        if status_info:
            self.logger.log_operation("GET_STATUS", {"task_id": task_id, "status": status_info["status"]})
            return {
                "task_id": task_id,
                "status": status_info["status"],
                "progress": status_info["progress"],
                "message": status_info["message"]
            }
        self.logger.logger.warning(f"Research task {task_id} not found.")
        return None

    async def get_research_results(self, task_id: str) -> Optional[List[Dict[str, Any]]]:
        """Возвращает результаты завершенной задачи исследования."""
        task_info = self.tasks.get(task_id)
        if task_info and task_info["status"] == "COMPLETED":
            self.logger.log_operation("GET_RESULTS", {"task_id": task_id, "results_count": len(task_info["results"])})
            return {
                "task_id": task_id,
                "status": task_info["status"],
                "results": task_info["results"]
            }
        elif task_info and task_info["status"] != "COMPLETED":
            self.logger.logger.warning(f"Research task {task_id} not yet completed. Current status: {task_info['status']}")
            return None # Или поднять исключение, как в API-spec
        self.logger.logger.warning(f"Research task {task_id} not found.")
        return None

    async def _execute_research_task(self, task_id: str):
        """Выполняет основную логику исследования для заданной задачи."""
        task = self.tasks[task_id]
        query = task["query"]
        sources = task["sources"]
        depth = task["depth"]
        filters = task["filters"]
        
        self.logger.logger.info(f"Executing research task {task_id} for query: {query}")
        task["status"] = "IN_PROGRESS"
        task["message"] = "Starting research..."
        task["progress"] = 5
        
        all_results = []
        
        try:
            # Используем GeminiResearchAgent для выполнения исследования
            if "gemini" in sources:
                task["message"] = "Fetching data from Gemini AI."
                task["progress"] = 20
                gemini_raw_results = await self.gemini_research_agent.research(query=query, use_web=True) # Используем веб-поиск Gemini
                logger.debug(f"DEBUG: _execute_research_task - gemini_raw_results: {gemini_raw_results}") # DEBUG
                
                # ПЕРЕМЕЩЕННАЯ ПРОВЕРКА: Если результаты Gemini пустые или некорректные, сразу завершаем задачу
                if gemini_raw_results is None or gemini_raw_results == {}:
                    task["status"] = "FAILED"
                    task["message"] = "Research task failed: Gemini returned empty or invalid results."
                    self.logger.logger.warning("Gemini returned empty or invalid results.")
                    self.logger.log_operation("RESEARCH_FAILED", {"task_id": task_id, "error": "Gemini returned empty or invalid results."})
                    logger.debug(f"DEBUG: _execute_research_task - Returning due to empty/invalid Gemini results. Message: {task['message']}") # DEBUG
                    return # IMPORTANT: Return here to prevent further execution
                elif not isinstance(gemini_raw_results, dict): # Обработка случаев, когда это не словарь
                    task["status"] = "FAILED"
                    task["message"] = "Research task failed: Failed to decode JSON from Gemini results."
                    self.logger.logger.error(f"Gemini returned unexpected format: {type(gemini_raw_results)}")
                    self.logger.log_operation("RESEARCH_FAILED", {"task_id": task_id, "error": "Failed to decode JSON from Gemini results."})
                    logger.debug(f"DEBUG: _execute_research_task - Returning due to unexpected Gemini results format. Message: {task['message']}") # DEBUG
                    return # IMPORTANT: Return here to prevent further execution
                
                # Если результаты валидны, добавляем их
                all_results.append(gemini_raw_results)
                self.logger.logger.info(f"Fetched results from Gemini AI.")
                task["progress"] = 50
            
            logger.debug(f"DEBUG: _execute_research_task - all_results before final check: {all_results}") # DEBUG
            # Проверка на пустые результаты после сбора всех данных
            if not all_results:
                task["status"] = "FAILED"
                task["message"] = "Research task failed: No results collected from any source."
                self.logger.logger.warning("No results collected from any source.")
                self.logger.log_operation("RESEARCH_FAILED", {"task_id": task_id, "error": "No results collected from any source."})
                logger.debug(f"DEBUG: _execute_research_task - Returning due to no results collected.") # DEBUG
                return

            if "internal_kb" in sources:
                task["message"] = "Searching internal knowledge base."
                # Здесь будет логика для поиска во внутренней базе знаний
                # Пример: internal_kb_data = await self._fetch_from_internal_kb(query, filters)
                # processed_internal_kb = self.data_processor.process_internal_kb_data(internal_kb_data, query)
                # all_results.extend(processed_internal_kb)
                self.logger.logger.info("Internal KB search not yet implemented.")
                task["progress"] = 70

            if "iso_standards" in sources:
                task["message"] = "Searching ISO standards."
                # Здесь будет логика для поиска по стандартам ISO
                # Пример: iso_data = await self._fetch_from_iso_standards(query, filters)
                # processed_iso = self.data_processor.process_iso_standards_data(iso_data, query)
                # all_results.extend(processed_iso)
                self.logger.logger.info("ISO standards search not yet implemented.")
                task["progress"] = 80

            # Применяем фильтры и сортировку, если необходимо
            # all_results = self._apply_filters_and_sort(all_results, filters)
            
            logger.debug(f"DEBUG: _execute_research_task - Calling _perform_quality_assurance with results: {all_results}. Current task message: {task['message']}") # DEBUG
            # Выполняем проверку качества
            quality_check_status, quality_message = self._perform_quality_assurance(all_results, query, depth)
            if not quality_check_status:
                task["status"] = "FAILED"
                task["message"] = f"Quality assurance failed: {quality_message}"
                self.logger.logger.error(f"Research task {task_id} failed due to quality issues: {quality_message}")
                self.logger.log_operation("RESEARCH_FAILED_QUALITY", {"task_id": task_id, "error": quality_message})
                logger.debug(f"DEBUG: _execute_research_task - Returning due to QA failure. Message: {task['message']}") # DEBUG
                return

            task["results"] = all_results
            task["status"] = "COMPLETED"
            task["progress"] = 100
            task["message"] = "Research task completed successfully."
            self.logger.log_operation("RESEARCH_COMPLETED", {"task_id": task_id, "results_count": len(all_results)})
            
        except Exception as e:
            task["status"] = "FAILED"
            task["message"] = f"Research task failed: {str(e)}"
            task["progress"] = 100
            self.logger.logger.error(f"Research task {task_id} failed: {e}")
            self.logger.log_operation("RESEARCH_FAILED", {"task_id": task_id, "error": str(e)})

    def _perform_quality_assurance(self, results: List[Dict[str, Any]], query: str, depth: int) -> (bool, str):
        """Выполняет проверку качества полученных результатов."""
        self.logger.logger.info(f"Performing quality assurance for query: {query}")
        self.logger.logger.debug(f"QA: Received results: {results}") # Добавлено для отладки

        # Явная проверка на пустые результаты
        if not results or not isinstance(results, list) or len(results) == 0:
            self.logger.logger.debug("QA: No results or malformed results from Gemini.")
            return False, "No results or malformed results from Gemini."
        
        # Ensure the first result is a dictionary before proceeding
        if not isinstance(results[0], dict):
            self.logger.logger.debug("QA: Gemini results are not in the expected dictionary format.") # Добавлено для отладки
            return False, "Gemini results are not in the expected dictionary format."

        # 1. Проверка полноты (базовая)
        # Поскольку Gemini возвращает один JSON объект, проверка полноты будет другой.
        # Мы ожидаем, что Gemini вернет JSON с определенными ключами.
        expected_keys = ["Ключевые факты и определения", "Актуальные данные и статистика", "Лучшие практики и примеры", "Потенциальные проблемы и решения", "Связанные темы для дальнейшего изучения"]
        for key in expected_keys:
            if key not in results[0]:
                self.logger.logger.debug(f"QA: Missing expected key in Gemini results: {key}") # Добавлено для отладки
                return False, f"Missing expected key in Gemini results: {key}"

        # 2. Проверка релевантности (базовая) - РАСКОММЕНТИРОВАНО
        # Для Gemini, релевантность будет оцениваться по наличию ключевых слов запроса в сгенерированном тексте.
        # Это очень базовая проверка, можно улучшить с помощью более сложного анализа.
        try:
            gemini_content = json.dumps(results[0]).lower() # РАСКОММЕНТИРОВАНО
        except TypeError:
            self.logger.logger.debug("QA: Could not dump results[0] to JSON for relevance check.")
            return False, "Could not process Gemini results for relevance check."

        query_words = set(query.lower().split()) # РАСКОММЕНТИРОВАНО
        
        # Проверяем, что query_words не пуст, чтобы избежать деления на ноль
        if not query_words:
            self.logger.logger.debug("QA: Query words are empty, skipping relevance check.")
            return True, "Quality assurance passed (relevance check skipped due to empty query)."

        relevant_words_count = sum(1 for word in query_words if word in gemini_content) # РАСКОММЕНТИРОВАНО
        if relevant_words_count < len(query_words) / 2: # Если меньше половины слов запроса найдено # РАСКОММЕНТИРОВАНО
            self.logger.logger.debug("QA: Gemini results do not seem highly relevant to the query.") # Добавлено для отладки # РАСКОММЕНТИРОВАНО
            return False, "Gemini results do not seem highly relevant to the query." # РАСКОММЕНТИРОВАНО

        # 3. Проверка согласованности (очень базовая, можно улучшить с помощью LLM)
        # Просто проверяем, что нет пустых значений для основных полей
        for key in expected_keys:
            if not results[0].get(key):
                self.logger.logger.debug(f"QA: Key '{key}' in Gemini results has empty content.") # Добавлено для отладки
                return False, f"Key '{key}' in Gemini results has empty content."

        self.logger.logger.info("Quality assurance passed.")
        return True, "Quality assurance passed."


async def main():
    """Тестовый запуск агента"""
    
    # ВНИМАНИЕ: Замените 'YOUR_GEMINI_API_KEY' на ваш реальный API ключ
    # Рекомендуется использовать использовать переменные окружения для хранения ключей
    gemini_api_key = "YOUR_GEMINI_API_KEY" 
    
    if gemini_api_key == "YOUR_GEMINI_API_KEY":
        logger.warning("Using placeholder API key. Please replace with your actual Gemini API key.")
        return

    agent = ResearchAgent(gemini_api_key=gemini_api_key)
    
    # Тестовый сценарий: инициирование исследования
    print("\n" + "="*50)
    print("INITIATING RESEARCH TASK")
    print("="*50)
    query = "Latest trends in AI ethics and governance"
    sources = ["gemini"] # Используем Gemini
    task_id = await agent.initiate_research(query=query, sources=sources, depth=3)
    print(f"Research task initiated with ID: {task_id}")
    
    # Ожидание завершения задачи и проверка статуса
    while True:
        status = await agent.get_research_status(task_id)
        if status:
            print(f"Task {task_id} Status: {status['status']}, Progress: {status['progress']}% - {status['message']}")
            if status["status"] == "COMPLETED" or status["status"] == "FAILED":
                break
        else:
            print(f"Task {task_id} not found.")
            break
        await asyncio.sleep(2) # Проверяем статус каждые 2 секунды
        
    # Получение результатов
    if status and status["status"] == "COMPLETED":
        print("\n" + "="*50)
        print("FETCHING RESEARCH RESULTS")
        print("="*50)
        results = await agent.get_research_results(task_id)
        if results and results["results"]:
            print(f"Found {len(results['results'])} results:")
            for i, res in enumerate(results["results"]):
                print(f"--- Result {i+1} ---")
                # Поскольку Gemini возвращает один JSON объект, выводим его целиком
                print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print("No results found or task not completed.")
    else:
        print("Research task did not complete successfully.")

    print("\n" + "="*50)
    print("RESEARCH AGENT TEST COMPLETED")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())