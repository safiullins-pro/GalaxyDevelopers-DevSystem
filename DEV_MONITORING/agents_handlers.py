#!/usr/bin/env python3
"""
🤖 AGENTS API HANDLERS
Обработчики API для AI агентов
"""

import asyncio
from aiohttp import web
from datetime import datetime

class AgentsHandlers:
    """Обработчики для AI агентов"""
    
    def __init__(self, server):
        self.server = server
        self.agent_manager = server.agent_manager
        self.executor = server.executor
    
    async def handle_agents_list(self, request):
        """Получение списка всех агентов"""
        try:
            if not self.agent_manager:
                return web.json_response({"error": "Agents not available"}, status=503)
            
            agents = self.agent_manager.list_agents()
            return web.json_response({"agents": agents})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_agents_status(self, request):
        """Получение статуса всех агентов"""
        try:
            if not self.agent_manager:
                return web.json_response({"error": "Agents not available"}, status=503)
            
            status = self.agent_manager.get_all_status()
            stats = self.agent_manager.get_statistics()
            
            return web.json_response({
                "status": status,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_agent_research(self, request):
        """Запуск ResearchAgent"""
        try:
            if not self.agent_manager:
                return web.json_response({"error": "Agents not available"}, status=503)
            
            data = await request.json()
            task = {
                "type": data.get("task_type", "search"),
                "query": data.get("query", ""),
                "file_path": data.get("file_path", ""),
                "file_types": data.get("file_types", [".py", ".js", ".ts"]),
                "code": data.get("code", "")
            }
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.agent_manager.submit_task,
                "ResearchAgent",
                task
            )
            
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_agent_review(self, request):
        """Запуск ReviewerAgent"""
        try:
            if not self.agent_manager:
                return web.json_response({"error": "Agents not available"}, status=503)
            
            data = await request.json()
            task = {
                "type": data.get("task_type", "review"),
                "file_path": data.get("file_path", ""),
                "file1": data.get("file1", ""),
                "file2": data.get("file2", "")
            }
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.agent_manager.submit_task,
                "ReviewerAgent",
                task
            )
            
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_agent_compose(self, request):
        """Запуск ComposerAgent"""
        try:
            if not self.agent_manager:
                return web.json_response({"error": "Agents not available"}, status=503)
            
            data = await request.json()
            task = {
                "type": data.get("task_type", "document"),
                "file_path": data.get("file_path", ""),
                "project_path": data.get("project_path", ""),
                "doc_type": data.get("doc_type", "auto")
            }
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.agent_manager.submit_task,
                "ComposerAgent",
                task
            )
            
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)