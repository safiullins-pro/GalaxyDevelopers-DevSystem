import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, call
import json

from AGENTS.research.research_agent import ResearchAgent, ProcessLogger
from AGENTS.research.gemini_research_agent import GeminiResearchAgent

# Mock ProcessLogger для тестов
@pytest.fixture(autouse=True)
def mock_process_logger():
    with patch('AGENTS.research.research_agent.ProcessLogger') as MockLogger:
        mock_instance = MockLogger.return_value
        mock_instance.logger = MagicMock() 
        mock_instance.log_operation = MagicMock()
        yield mock_instance

@pytest.fixture
def mock_gemini_research_agent():
    with patch('AGENTS.research.research_agent.GeminiResearchAgent') as MockGeminiAgent:
        mock_instance = MockGeminiAgent.return_value
        mock_instance.research = AsyncMock()
        mock_instance.research_with_context = AsyncMock()
        mock_instance.research_multimodal = AsyncMock()
        mock_instance.research_with_tools = AsyncMock()
        yield mock_instance

@pytest.fixture
def research_agent(mock_gemini_research_agent): # Добавил mock_gemini_research_agent в аргументы
    # Передаем фиктивный API-ключ, так как GeminiResearchAgent будет замокан
    return ResearchAgent(gemini_api_key="test_key", gemini_research_agent=mock_gemini_research_agent)

class TestResearchAgentP4:
    def test_agent_import_and_existence(self):
        # Тест существования: агент вообще импортируется?
        assert ResearchAgent is not None
        assert GeminiResearchAgent is not None

    def test_agent_initialization(self, research_agent): # Используем research_agent fixture
        # Тест инициализации: агент рождается без эксепшенов?
        assert research_agent.gemini_api_key == "test_key"
        # Проверяем, что замоканный агент используется (mock_gemini_research_agent)
        assert isinstance(research_agent.gemini_research_agent, MagicMock)
        assert research_agent.tasks == {}

    @pytest.mark.asyncio
    async def test_initiate_research_basic_flow(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = {
            "Ключевые факты и определения": "Факт 1: test query", # Добавлено для релевантности
            "Актуальные данные и статистика": "Данные 1",
            "Лучшие практики и примеры": "Пример 1",
            "Потенциальные проблемы и решения": "Решение 1",
            "Связанные темы для дальнейшего изучения": "Тема 1"
        }
        query = "test query"
        sources = ["gemini"]
        depth = 1

        task_id = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        
        assert task_id is not None # Убедимся, что task_id не None
        assert task_id in research_agent.tasks
        task_info = research_agent.tasks[task_id]
        assert task_info["status"] == "PENDING"
        assert task_info["query"] == query
        assert task_info["sources"] == sources
        assert task_info["depth"] == depth
        assert task_info["results"] == []
        assert task_info["progress"] == 0
        assert task_info["message"] == "Research initiated." # Ожидаем это сообщение

        # Даем время на выполнение фоновой задачи
        await asyncio.sleep(1.0)

        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "COMPLETED" # Ожидаем COMPLETED
        assert len(research_agent.tasks[task_id]["results"]) == 1
        mock_gemini_research_agent.research.assert_called_once_with(query=query, use_web=True)

    @pytest.mark.asyncio
    async def test_initiate_research_multiple_sources(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = {
            "Ключевые факты и определения": "Факт 1: another query", # Добавлено для релевантности
            "Актуальные данные и статистика": "Данные 1",
            "Лучшие практики и примеры": "Пример 1",
            "Потенциальные проблемы и решения": "Решение 1",
            "Связанные темы для дальнейшего изучения": "Тема 1"
        }
        query = "another query"
        sources = ["gemini", "web"] # Добавляем "web" для проверки
        depth = 2

        task_id = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        
        assert task_id is not None
        assert task_id in research_agent.tasks
        task_info = research_agent.tasks[task_id]
        assert task_info["status"] == "PENDING"
        assert task_info["query"] == query
        assert task_info["sources"] == ["gemini"] # Ожидаем, что "web" будет отфильтрован
        assert task_info["depth"] == depth

        await asyncio.sleep(1.0)

        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "COMPLETED"
        # Ожидаем, что research будет вызван с use_web=True, так как "web" в источниках
        mock_gemini_research_agent.research.assert_called_once_with(query=query, use_web=True)

    @pytest.mark.asyncio
    async def test_initiate_research_no_sources(self, research_agent):
        query = "query without sources"
        sources = []
        depth = 1

        task_id = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        
        assert task_id is not None
        assert task_id in research_agent.tasks
        task_info = research_agent.tasks[task_id]
        assert task_info["status"] == "FAILED"
        assert "No valid research sources provided" in task_info["message"]

    @pytest.mark.asyncio
    async def test_initiate_research_invalid_source(self, research_agent):
        query = "query with invalid source"
        sources = ["invalid_source"]
        depth = 1

        task_id = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        
        assert task_id is not None
        assert task_id in research_agent.tasks
        task_info = research_agent.tasks[task_id]
        assert task_info["status"] == "FAILED"
        assert "No valid research sources provided" in task_info["message"]

    @pytest.mark.asyncio
    async def test_get_research_status_non_existent_task(self, research_agent):
        status = await research_agent.get_research_status("non_existent_task")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_research_results_non_existent_task(self, research_agent):
        results = await research_agent.get_research_results("non_existent_task")
        assert results is None

    @pytest.mark.asyncio
    async def test_execute_research_task_quality_assurance_failure(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = {"Неправильный ключ": "Значение"}
        task_id = await research_agent.initiate_research(query="qa fail query", sources=["gemini"], depth=3)
        
        await asyncio.sleep(1.0)
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Quality assurance failed" in status["message"]
        assert "Missing expected key in Gemini results" in status["message"]

    @pytest.mark.asyncio
    async def test_execute_research_task_json_decode_error(self, research_agent, mock_gemini_research_agent):
        # Имитируем, что Gemini возвращает невалидный JSON (строку, которая не является JSON)
        mock_gemini_research_agent.research.return_value = "This is not a JSON string"
        task_id = await research_agent.initiate_research(query="json error query", sources=["gemini"], depth=3)
        
        await asyncio.sleep(1.0)
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Research task failed: Failed to decode JSON from Gemini results." in status["message"]

    @pytest.mark.asyncio
    async def test_execute_research_task_empty_gemini_result(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = {}
        task_id = await research_agent.initiate_research(query="empty result query", sources=["gemini"], depth=3)
        
        await asyncio.sleep(1.0)
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Research task failed: Gemini returned empty or invalid results." in status["message"]

    @pytest.mark.asyncio
    async def test_execute_research_task_none_gemini_result(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = None
        task_id = await research_agent.initiate_research(query="none result query", sources=["gemini"], depth=3)
        
        await asyncio.sleep(1.0)
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Research task failed: Gemini returned empty or invalid results." in status["message"]

    @pytest.mark.asyncio
    async def test_execute_research_task_idempotency(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.return_value = {
            "Ключевые факты и определения": "Факт 1: idempotency test", # Добавлено для релевантности
            "Актуальные данные и статистика": "Данные 1",
            "Лучшие практики и примеры": "Пример 1",
            "Потенциальные проблемы и решения": "Решение 1",
            "Связанные темы для дальнейшего изучения": "Тема 1"
        }
        query = "idempotency test"
        sources = ["gemini"]
        depth = 1

        task_id_1 = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        await asyncio.sleep(1.0)
        status_1 = await research_agent.get_research_status(task_id_1)
        assert status_1["status"] == "COMPLETED"

        # Повторный вызов с теми же параметрами должен создать новую задачу
        task_id_2 = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        await asyncio.sleep(1.0)
        status_2 = await research_agent.get_research_status(task_id_2)
        assert status_2["status"] == "COMPLETED"
        
        assert task_id_1 != task_id_2 # Должны быть разные ID задач
        assert len(research_agent.tasks) == 2 # Должны быть две задачи в списке

    @pytest.mark.asyncio
    async def test_process_logger_integration(self, research_agent, mock_gemini_research_agent, mock_process_logger):
        mock_gemini_research_agent.research.return_value = {
            "Ключевые факты и определения": "Факт 1: logger test", # Добавлено для релевантности
            "Актуальные данные и статистика": "Данные 1",
            "Лучшие практики и примеры": "Пример 1",
            "Потенциальные проблемы и решения": "Решение 1",
            "Связанные темы для дальнейшего изучения": "Тема 1"
        }
        query = "logger test"
        sources = ["gemini"]
        depth = 1

        task_id = await research_agent.initiate_research(query=query, sources=sources, depth=depth)
        await asyncio.sleep(1.0)

        # Проверяем, что log_operation был вызван с правильными аргументами
        mock_process_logger.log_operation.assert_any_call(
            "RESEARCH_INITIATED", {"task_id": task_id, "query": query, "sources": sources}
        )
        mock_process_logger.log_operation.assert_any_call(
            "RESEARCH_COMPLETED", {"task_id": task_id, "results_count": 1}
        )
        
        # Проверяем, что логгирование ошибок также работает
        mock_gemini_research_agent.research.side_effect = Exception("Test Error")
        task_id_fail = await research_agent.initiate_research(query="fail logger", sources=["gemini"])
        await asyncio.sleep(1.0)
        mock_process_logger.log_operation.assert_any_call(
            "RESEARCH_FAILED", {"task_id": task_id_fail, "error": "Test Error"}
        )