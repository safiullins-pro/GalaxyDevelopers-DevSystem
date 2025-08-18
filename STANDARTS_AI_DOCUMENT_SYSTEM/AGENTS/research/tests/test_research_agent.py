import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
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
def research_agent(mock_gemini_research_agent):
    # Передаем фиктивный API-ключ, так как GeminiResearchAgent будет замокан
    return ResearchAgent(gemini_api_key="test_key")


class TestResearchAgent:
    @pytest.mark.asyncio
    async def test_initiate_research_gemini_source(self, research_agent, mock_gemini_research_agent):
        # Мокируем ответ Gemini, который соответствует ожидаемому JSON формату
        mock_gemini_research_agent.research.return_value = {
            "Ключевые факты и определения": "Факт 1",
            "Актуальные данные и статистика": "Данные 1",
            "Лучшие практики и примеры": "Пример 1",
            "Потенциальные проблемы и решения": "Решение 1",
            "Связанные темы для дальнейшего изучения": "Тема 1"
        }

        task_id = await research_agent.initiate_research(query="test query", sources=["gemini"], depth=3)
        assert task_id in research_agent.tasks
        assert research_agent.tasks[task_id]["status"] == "PENDING"
        
        # Даем время на выполнение фоновой задачи
        await asyncio.sleep(0.1)
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "COMPLETED"
        assert len(research_agent.tasks[task_id]["results"]) == 1 # Ожидаем один JSON объект от Gemini
        mock_gemini_research_agent.research.assert_called_once_with(query="test query", use_web=True)

    @pytest.mark.asyncio
    async def test_get_research_status(self, research_agent):
        task_id = "test_task_id"
        research_agent.tasks[task_id] = {"status": "IN_PROGRESS", "progress": 50, "message": "test message"}
        status = await research_agent.get_research_status(task_id)
        assert status["task_id"] == task_id
        assert status["status"] == "IN_PROGRESS"
        assert status["progress"] == 50

    @pytest.mark.asyncio
    async def test_get_research_results_completed(self, research_agent):
        task_id = "test_task_id_completed"
        research_agent.tasks[task_id] = {"status": "COMPLETED", "results": [{"title": "Result 1"}]}
        results = await research_agent.get_research_results(task_id)
        assert results["task_id"] == task_id
        assert results["status"] == "COMPLETED"
        assert len(results["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_research_results_not_completed(self, research_agent):
        task_id = "test_task_id_pending"
        research_agent.tasks[task_id] = {"status": "PENDING", "results": []}
        results = await research_agent.get_research_results(task_id)
        assert results is None

    @pytest.mark.asyncio
    async def test_execute_research_task_failure_gemini(self, research_agent, mock_gemini_research_agent):
        mock_gemini_research_agent.research.side_effect = Exception("Gemini API Error")
        task_id = await research_agent.initiate_research(query="fail query", sources=["gemini"])
        
        await asyncio.sleep(0.1) # Даем время на выполнение фоновой задачи
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Gemini API Error" in status["message"]

    @pytest.mark.asyncio
    async def test_quality_assurance_failure_gemini(self, research_agent, mock_gemini_research_agent):
        # Имитируем сценарий, когда QA проваливается (например, отсутствуют ожидаемые ключи)
        mock_gemini_research_agent.research.return_value = {
            "Неправильный ключ": "Значение"
        }

        task_id = await research_agent.initiate_research(query="qa fail query", sources=["gemini"], depth=3)
        
        await asyncio.sleep(0.1) # Даем время на выполнение фоновой задачи
        
        status = await research_agent.get_research_status(task_id)
        assert status["status"] == "FAILED"
        assert "Quality assurance failed" in status["message"]
        assert "Missing expected key in Gemini results" in status["message"]
