#\!/usr/bin/env python3
"""
💀 ReviewerAgent - Агент валидации по стандартам
Проверяет соответствие ISO 27001, ITIL 4, COBIT
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

class ReviewerAgent:
    """Агент для валидации документов по стандартам"""
    
    def __init__(self):
        self.project_root = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.standards_dir = self.project_root / "STANDARDS"
        self.reports_dir = self.project_root / "REPORTS" / "compliance"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем стандарты
        self.standards = {
            "ISO_27001": self._load_iso_27001(),
            "ITIL_4": self._load_itil_4(),
            "COBIT": self._load_cobit()
        }
        
        self.tasks = {}
        logger.info("ReviewerAgent initialized")
    
    def _load_iso_27001(self) -> Dict:
        """Загружает требования ISO 27001"""
        return {
            "controls": [
                "A.5 Information security policies",
                "A.6 Organization of information security",
                "A.7 Human resource security",
                "A.8 Asset management",
                "A.9 Access control",
                "A.10 Cryptography",
                "A.11 Physical and environmental security",
                "A.12 Operations security",
                "A.13 Communications security",
                "A.14 System acquisition, development and maintenance",
                "A.15 Supplier relationships",
                "A.16 Information security incident management",
                "A.17 Information security aspects of business continuity",
                "A.18 Compliance"
            ]
        }
    
    def _load_itil_4(self) -> Dict:
        """Загружает практики ITIL 4"""
        return {
            "practices": [
                "Incident Management",
                "Problem Management",
                "Change Enablement",
                "Service Request Management",
                "Service Level Management",
                "Service Configuration Management",
                "IT Asset Management",
                "Monitoring and Event Management",
                "Release Management",
                "Service Desk",
                "Continual Improvement"
            ]
        }
    
    def _load_cobit(self) -> Dict:
        """Загружает процессы COBIT"""
        return {
            "domains": [
                "EDM - Evaluate, Direct and Monitor",
                "APO - Align, Plan and Organize",
                "BAI - Build, Acquire and Implement",
                "DSS - Deliver, Service and Support",
                "MEA - Monitor, Evaluate and Assess"
            ]
        }
    
    async def validate_document(
        self,
        document_path: str,
        standards: List[str] = None
    ) -> str:
        """Валидирует документ по стандартам"""
        task_id = str(uuid.uuid4())
        
        if not standards:
            standards = ["ISO_27001", "ITIL_4", "COBIT"]
        
        self.tasks[task_id] = {
            "status": "IN_PROGRESS",
            "document": document_path,
            "standards": standards,
            "created": datetime.now().isoformat()
        }
        
        # Запускаем валидацию
        asyncio.create_task(self._perform_validation(task_id, document_path, standards))
        
        return task_id
    
    async def _perform_validation(
        self,
        task_id: str,
        document_path: str,
        standards: List[str]
    ):
        """Выполняет валидацию"""
        try:
            doc_path = Path(document_path)
            if not doc_path.exists():
                raise FileNotFoundError(f"Document not found: {document_path}")
            
            content = doc_path.read_text(encoding='utf-8')
            
            results = {
                "document": document_path,
                "validation_time": datetime.now().isoformat(),
                "compliance": {}
            }
            
            # Проверяем по каждому стандарту
            for standard in standards:
                if standard in self.standards:
                    compliance = self._check_compliance(content, standard)
                    results["compliance"][standard] = compliance
            
            # Общий score
            scores = [c["score"] for c in results["compliance"].values()]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            # Сохраняем отчёт
            report_path = self.reports_dir / f"compliance_{task_id}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.tasks[task_id]["status"] = "COMPLETED"
            self.tasks[task_id]["results"] = results
            self.tasks[task_id]["report_path"] = str(report_path)
            
            logger.info(f"Validation completed: {document_path}, Score: {results['overall_score']:.1f}%")
            
        except Exception as e:
            self.tasks[task_id]["status"] = "FAILED"
            self.tasks[task_id]["error"] = str(e)
            logger.error(f"Validation failed: {e}")
    
    def _check_compliance(self, content: str, standard: str) -> Dict:
        """Проверяет соответствие стандарту"""
        content_lower = content.lower()
        result = {
            "standard": standard,
            "checks": [],
            "issues": [],
            "score": 0
        }
        
        if standard == "ISO_27001":
            controls = self.standards[standard]["controls"]
            found = 0
            for control in controls:
                control_key = control.split()[0].lower()  # A.5, A.6, etc
                if control_key in content_lower or control.lower() in content_lower:
                    found += 1
                    result["checks"].append(f"✅ {control}")
                else:
                    result["issues"].append(f"❌ Missing: {control}")
            
            result["score"] = (found / len(controls)) * 100
            
        elif standard == "ITIL_4":
            practices = self.standards[standard]["practices"]
            found = 0
            for practice in practices:
                if practice.lower() in content_lower:
                    found += 1
                    result["checks"].append(f"✅ {practice}")
                else:
                    result["issues"].append(f"❌ Missing: {practice}")
            
            result["score"] = (found / len(practices)) * 100
            
        elif standard == "COBIT":
            domains = self.standards[standard]["domains"]
            found = 0
            for domain in domains:
                domain_key = domain.split()[0].lower()  # EDM, APO, etc
                if domain_key in content_lower:
                    found += 1
                    result["checks"].append(f"✅ {domain}")
                else:
                    result["issues"].append(f"❌ Missing: {domain}")
            
            result["score"] = (found / len(domains)) * 100
        
        return result
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Получает статус задачи валидации"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        return self.tasks[task_id]
    
    async def validate_batch(
        self,
        documents: List[str],
        standards: List[str] = None
    ) -> List[str]:
        """Валидирует несколько документов"""
        task_ids = []
        
        for doc in documents:
            task_id = await self.validate_document(doc, standards)
            task_ids.append(task_id)
            await asyncio.sleep(0.1)  # Небольшая задержка
        
        logger.info(f"Batch validation started: {len(task_ids)} documents")
        return task_ids

if __name__ == "__main__":
    async def test_reviewer():
        """Тестируем ReviewerAgent"""
        agent = ReviewerAgent()
        
        print("🔍 ТЕСТИРУЕМ REVIEWERAGENT\n")
        
        # Создаём тестовый документ
        test_doc = Path("/tmp/test_document.md")
        test_doc.write_text("""
        # Test Document
        
        ## ISO 27001 Compliance
        - A.5 Information security policies: Implemented
        - A.9 Access control: Configured
        
        ## ITIL 4 Practices
        - Incident Management process defined
        - Change Enablement workflow established
        
        ## COBIT Framework
        - APO processes documented
        - DSS delivery mechanisms in place
        """)
        
        # Запускаем валидацию
        task_id = await agent.validate_document(str(test_doc))
        
        # Ждём результат
        await asyncio.sleep(2)
        
        status = await agent.get_task_status(task_id)
        print(f"Статус: {status['status']}")
        
        if status.get('results'):
            print(f"Overall Score: {status['results']['overall_score']:.1f}%")
            for std, comp in status['results']['compliance'].items():
                print(f"{std}: {comp['score']:.1f}%")
        
        print("\n✅ ReviewerAgent работает\!")
    
    asyncio.run(test_reviewer())