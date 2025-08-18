#\!/usr/bin/env python3
"""
💀 ComposerAgent - Агент для генерации документации
by FORGE & ALBERT 🔥
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComposerAgent:
    """Агент для генерации документации по шаблонам"""
    
    def __init__(self, templates_dir: str = None):
        self.project_root = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.templates_dir = Path(templates_dir) if templates_dir else self.project_root / "TEMPLATES"
        self.outputs_dir = self.project_root / "DELIVERABLES" / "generated_docs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.tasks = {}
        logger.info("ComposerAgent initialized")
    
    async def compose_document(self, template_name: str, data: Dict[str, Any]) -> str:
        """Создаёт документ на основе шаблона"""
        task_id = str(uuid.uuid4())
        
        self.tasks[task_id] = {
            "status": "IN_PROGRESS",
            "template": template_name,
            "created": datetime.now().isoformat()
        }
        
        # Запускаем генерацию
        asyncio.create_task(self._generate(task_id, template_name, data))
        
        return task_id
    
    async def _generate(self, task_id: str, template_name: str, data: Dict[str, Any]):
        """Генерирует документ"""
        try:
            # Простая генерация без Jinja пока
            content = f"# {data.get('title', 'Document')}\n\n"
            content += f"Generated: {datetime.now()}\n\n"
            
            for key, value in data.items():
                content += f"## {key}\n{value}\n\n"
            
            # Сохраняем
            filename = f"{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            output_path = self.outputs_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.tasks[task_id]["status"] = "COMPLETED"
            self.tasks[task_id]["result"] = str(output_path)
            
            logger.info(f"Document generated: {output_path}")
            
        except Exception as e:
            self.tasks[task_id]["status"] = "FAILED"
            self.tasks[task_id]["error"] = str(e)
            logger.error(f"Generation failed: {e}")