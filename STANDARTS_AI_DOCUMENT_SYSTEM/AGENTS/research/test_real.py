#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ ТЕСТ ResearchAgent БЕЗ МОКОВ
"""

import asyncio
import os
import sys
sys.path.append('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
from AGENTS.research.research_agent import ResearchAgent

async def test_real_research():
    """Тестируем реальный ResearchAgent с Gemini"""
    
    # Твой реальный API ключ
    api_key = "AIzaSyBerqRh6LgbXMowDY-4IjwGTsN7R1SCsz4"
    
    agent = ResearchAgent(gemini_api_key=api_key)
    
    print("\n🔥 ТЕСТИРУЕМ RESEARCHAGENT С GEMINI 🔥\n")
    
    # Тест 1: Простой запрос
    print("📍 Тест 1: Исследование Multi-Agent систем")
    task_id = await agent.initiate_research(
        query="Как построить Multi-Agent систему для управления документами",
        sources=["gemini"],
        depth=3
    )
    
    # Ждем выполнения
    await asyncio.sleep(5)
    
    # Проверяем статус
    status = await agent.get_research_status(task_id)
    print(f"Статус: {status['status']}")
    print(f"Сообщение: {status.get('message', '')}")
    
    # Получаем результаты
    if status['status'] == 'COMPLETED':
        results = await agent.get_research_results(task_id)
        print(f"Результаты: {results['results'][:500]}...")  # первые 500 символов
    
    # Тест 2: Исследование с контекстом
    print("\n📍 Тест 2: Исследование с контекстом проекта")
    context_docs = [
        "Проект Galaxy Development - система управления документами",
        "Используем 5 агентов: ResearchAgent, ComposerAgent, ReviewerAgent, IntegratorAgent, PublisherAgent",
        "Архитектура: Multi-Agent System с Event-Driven подходом"
    ]
    
    task_id2 = await agent.initiate_research(
        query="Какие паттерны проектирования использовать для агентов",
        sources=["gemini"],
        depth=2
    )
    
    await asyncio.sleep(5)
    
    status2 = await agent.get_research_status(task_id2)
    print(f"Статус: {status2['status']}")
    
    if status2['status'] == 'COMPLETED':
        results2 = await agent.get_research_results(task_id2)
        print(f"Найдено результатов: {len(results2['results'])}")
    
    print("\n✅ ТЕСТЫ ЗАВЕРШЕНЫ!")

if __name__ == "__main__":
    asyncio.run(test_real_research())