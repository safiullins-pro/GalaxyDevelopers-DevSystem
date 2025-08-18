#!/usr/bin/env python3
"""
Business Analyst Agent for P1.1 Task Execution
GALAXYDEVELOPMENT Document Management System
Role: Automated document analysis and inventory
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from collections import defaultdict

class BusinessAnalystAgent:
    """AI Agent performing Business Analyst role for document analysis"""
    
    def __init__(self, task_file: str):
        """Initialize agent with task definition"""
        self.task_file = Path(task_file)
        self.task = self._load_task()
        self.results = {
            "task_id": self.task["task_id"],
            "started_at": datetime.now().isoformat(),
            "agent": "BusinessAnalystAgent v1.0",
            "steps_completed": []
        }
        
    def _load_task(self) -> Dict:
        """Load task definition from JSON"""
        with open(self.task_file, 'r') as f:
            return json.load(f)
    
    def execute_step_1_inventory(self) -> Dict:
        """Step 1: Инвентаризация документов"""
        print("🔍 Step 1: Инвентаризация документов...")
        inventory = []
        
        for directory in self.task["input_directories"]:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        inventory.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "extension": file_path.suffix,
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                            "directory": str(file_path.parent.relative_to(Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")))
                        })
        
        output_path = Path(self.task["output_directory"]) / "raw_inventory.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Найдено {len(inventory)} файлов")
        return {"files_found": len(inventory), "output": str(output_path)}
    
    def execute_step_2_categorize(self) -> Dict:
        """Step 2: Классификация по категориям"""
        print("📂 Step 2: Классификация по категориям...")
        
        # Load inventory
        inventory_path = Path(self.task["output_directory"]) / "raw_inventory.json"
        with open(inventory_path, 'r') as f:
            inventory = json.load(f)
        
        # Categorize
        categories = defaultdict(list)
        
        for item in inventory:
            # Determine category based on directory and file type
            if "TEMPLATES" in item["directory"] or "03_TEMPLATES" in item["directory"]:
                category = "templates"
            elif "PROCESSES" in item["directory"] or "01_PROCESSES" in item["directory"]:
                category = "processes"
            elif "ROLES" in item["directory"] or "05_ROLES" in item["directory"]:
                category = "roles"
            elif "STANDARDS" in item["directory"] or "02_STANDARDS" in item["directory"]:
                category = "standards"
            elif "CHECKLIST" in item["directory"] or "04_CHECKLIST" in item["directory"]:
                category = "checklists"
            elif "AGENTS" in item["directory"] or "06_AGENTS" in item["directory"]:
                category = "agents"
            elif item["extension"] in [".md", ".txt", ".pdf"]:
                category = "documentation"
            elif item["extension"] in [".py", ".js", ".sh"]:
                category = "scripts"
            elif item["extension"] in [".json", ".yaml", ".yml"]:
                category = "configs"
            else:
                category = "other"
            
            categories[category].append(item)
        
        # Save categorized inventory
        categorized = {
            "total_files": len(inventory),
            "categories": {k: len(v) for k, v in categories.items()},
            "details": dict(categories),
            "analyzed_at": datetime.now().isoformat()
        }
        
        output_path = Path(self.task["output_directory"]) / "categorized_inventory.json"
        with open(output_path, 'w') as f:
            json.dump(categorized, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Категоризировано: {categorized['categories']}")
        return {"categories": categorized["categories"], "output": str(output_path)}
    
    def execute_step_3_quality(self) -> Dict:
        """Step 3: Анализ качества"""
        print("⭐ Step 3: Анализ качества документов...")
        
        # Load categorized inventory
        inventory_path = Path(self.task["output_directory"]) / "categorized_inventory.json"
        with open(inventory_path, 'r') as f:
            categorized = json.load(f)
        
        quality_scores = []
        
        for category, files in categorized["details"].items():
            for file_info in files:
                score = 10  # Start with perfect score
                
                # Deduct points for issues
                if file_info["size"] < 100:  # Too small
                    score -= 2
                if "TODO" in file_info["name"] or "temp" in file_info["name"]:
                    score -= 3
                if file_info["extension"] == "":  # No extension
                    score -= 2
                
                # Check age (older than 30 days reduces score)
                modified_date = datetime.fromisoformat(file_info["modified"])
                age_days = (datetime.now() - modified_date).days
                if age_days > 30:
                    score -= min(3, age_days // 30)
                
                quality_scores.append({
                    "file": file_info["name"],
                    "path": file_info["path"],
                    "category": category,
                    "score": max(1, score),
                    "age_days": age_days,
                    "size": file_info["size"]
                })
        
        # Calculate statistics
        avg_score = sum(q["score"] for q in quality_scores) / len(quality_scores)
        
        quality_report = {
            "total_documents": len(quality_scores),
            "average_score": round(avg_score, 2),
            "high_quality": len([q for q in quality_scores if q["score"] >= 8]),
            "medium_quality": len([q for q in quality_scores if 5 <= q["score"] < 8]),
            "low_quality": len([q for q in quality_scores if q["score"] < 5]),
            "scores": quality_scores
        }
        
        output_path = Path(self.task["output_directory"]) / "quality_scores.json"
        with open(output_path, 'w') as f:
            json.dump(quality_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Средний балл качества: {avg_score:.2f}/10")
        return {"average_score": avg_score, "output": str(output_path)}
    
    def execute_step_4_gaps(self) -> Dict:
        """Step 4: Выявление пробелов"""
        print("🔎 Step 4: Выявление пробелов в документации...")
        
        # ITIL 4 required processes
        itil_processes = [
            "Incident Management",
            "Problem Management",
            "Change Enablement",
            "Service Request Management",
            "Service Level Management",
            "Service Configuration Management",
            "IT Asset Management",
            "Release Management",
            "Deployment Management",
            "Continual Improvement",
            "Monitoring and Event Management",
            "Service Desk",
            "Knowledge Management",
            "Service Validation and Testing",
            "Service Catalog Management"
        ]
        
        # ISO 27001 required documents
        iso_documents = [
            "Information Security Policy",
            "Risk Assessment Methodology",
            "Statement of Applicability",
            "Risk Treatment Plan",
            "Access Control Policy",
            "Business Continuity Plan",
            "Incident Response Plan",
            "Asset Inventory",
            "Acceptable Use Policy",
            "Data Classification Policy"
        ]
        
        # Load current inventory
        inventory_path = Path(self.task["output_directory"]) / "categorized_inventory.json"
        with open(inventory_path, 'r') as f:
            categorized = json.load(f)
        
        # Find what we have
        existing_files = []
        for category, files in categorized["details"].items():
            existing_files.extend([f["name"].lower() for f in files])
        
        # Check for gaps
        missing_itil = []
        missing_iso = []
        
        for process in itil_processes:
            found = any(process.lower().replace(" ", "_") in fname or 
                       process.lower().replace(" ", "-") in fname 
                       for fname in existing_files)
            if not found:
                missing_itil.append(process)
        
        for doc in iso_documents:
            found = any(doc.lower().replace(" ", "_") in fname or
                       doc.lower().replace(" ", "-") in fname
                       for fname in existing_files)
            if not found:
                missing_iso.append(doc)
        
        gaps_report = {
            "analysis_date": datetime.now().isoformat(),
            "total_gaps": len(missing_itil) + len(missing_iso),
            "itil_gaps": {
                "missing_count": len(missing_itil),
                "missing_processes": missing_itil
            },
            "iso_27001_gaps": {
                "missing_count": len(missing_iso),
                "missing_documents": missing_iso
            },
            "recommendations": [
                f"Создать шаблон для процесса '{p}'" for p in missing_itil[:5]
            ] + [
                f"Разработать документ '{d}'" for d in missing_iso[:5]
            ]
        }
        
        output_path = Path(self.task["output_directory"]) / "missing_documents.json"
        with open(output_path, 'w') as f:
            json.dump(gaps_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Найдено {gaps_report['total_gaps']} пробелов")
        return {"total_gaps": gaps_report["total_gaps"], "output": str(output_path)}
    
    def execute_step_5_matrix(self) -> Dict:
        """Step 5: Создание матрицы покрытия"""
        print("📊 Step 5: Создание матрицы покрытия...")
        
        # Load all previous results
        gaps_path = Path(self.task["output_directory"]) / "missing_documents.json"
        quality_path = Path(self.task["output_directory"]) / "quality_scores.json"
        
        with open(gaps_path, 'r') as f:
            gaps = json.load(f)
        with open(quality_path, 'r') as f:
            quality = json.load(f)
        
        # Create coverage matrix
        matrix = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_documents": quality["total_documents"],
                "average_quality": quality["average_score"],
                "itil_coverage": f"{(15 - len(gaps['itil_gaps']['missing_processes'])) / 15 * 100:.1f}%",
                "iso_coverage": f"{(10 - len(gaps['iso_27001_gaps']['missing_documents'])) / 10 * 100:.1f}%"
            },
            "coverage_details": {
                "templates": {"found": 0, "required": 50, "coverage": "0%"},
                "processes": {"found": 0, "required": 47, "coverage": "0%"},
                "roles": {"found": 0, "required": 35, "coverage": "0%"},
                "standards": {"found": 0, "required": 10, "coverage": "0%"}
            },
            "quality_distribution": {
                "high": quality["high_quality"],
                "medium": quality["medium_quality"],
                "low": quality["low_quality"]
            }
        }
        
        # Count actual files per category
        categorized_path = Path(self.task["output_directory"]) / "categorized_inventory.json"
        with open(categorized_path, 'r') as f:
            categorized = json.load(f)
        
        for cat, count in categorized["categories"].items():
            if cat in matrix["coverage_details"]:
                matrix["coverage_details"][cat]["found"] = count
                required = matrix["coverage_details"][cat]["required"]
                matrix["coverage_details"][cat]["coverage"] = f"{min(100, count/required*100):.1f}%"
        
        output_path = Path(self.task["output_directory"]) / "coverage_matrix.json"
        with open(output_path, 'w') as f:
            json.dump(matrix, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Матрица покрытия создана")
        return {"matrix_created": True, "output": str(output_path)}
    
    def generate_deliverables(self):
        """Generate final deliverables"""
        print("\n📦 Генерация финальных документов...")
        
        # 1. Generate Excel catalog
        inventory_path = Path(self.task["output_directory"]) / "categorized_inventory.json"
        with open(inventory_path, 'r') as f:
            categorized = json.load(f)
        
        # Flatten for Excel
        rows = []
        for category, files in categorized["details"].items():
            for file_info in files:
                rows.append({
                    "Category": category,
                    "File Name": file_info["name"],
                    "Path": file_info["path"],
                    "Size (bytes)": file_info["size"],
                    "Modified": file_info["modified"],
                    "Extension": file_info["extension"]
                })
        
        df = pd.DataFrame(rows)
        excel_path = Path(self.task["output_directory"]) / "inventory_catalog.xlsx"
        df.to_excel(excel_path, index=False)
        print(f"✅ Excel каталог создан: {excel_path}")
        
        # 2. Generate Markdown gaps analysis
        gaps_path = Path(self.task["output_directory"]) / "missing_documents.json"
        with open(gaps_path, 'r') as f:
            gaps = json.load(f)
        
        md_content = f"""# Анализ пробелов в документации
Generated: {datetime.now().isoformat()}

## Резюме
- **Всего пробелов найдено:** {gaps['total_gaps']}
- **Пробелы ITIL 4:** {gaps['itil_gaps']['missing_count']}
- **Пробелы ISO 27001:** {gaps['iso_27001_gaps']['missing_count']}

## Отсутствующие процессы ITIL 4

{chr(10).join(f"- [ ] {p}" for p in gaps['itil_gaps']['missing_processes'])}

## Отсутствующие документы ISO 27001

{chr(10).join(f"- [ ] {d}" for d in gaps['iso_27001_gaps']['missing_documents'])}

## Рекомендации

{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(gaps['recommendations']))}

## Следующие шаги
1. Приоритизировать создание критических документов
2. Назначить ответственных за каждый пробел
3. Установить сроки устранения пробелов
4. Провести повторный аудит через 30 дней
"""
        
        md_path = Path(self.task["output_directory"]) / "gaps_analysis.md"
        with open(md_path, 'w') as f:
            f.write(md_content)
        print(f"✅ Markdown анализ создан: {md_path}")
        
        # 3. Generate PDF placeholder (would need reportlab in real implementation)
        pdf_placeholder = {
            "type": "PDF_PLACEHOLDER",
            "content": "Coverage Matrix PDF would be generated here with proper PDF library",
            "matrix_data": json.load(open(Path(self.task["output_directory"]) / "coverage_matrix.json"))
        }
        
        pdf_path = Path(self.task["output_directory"]) / "coverage_matrix.pdf.json"
        with open(pdf_path, 'w') as f:
            json.dump(pdf_placeholder, f, indent=2)
        print(f"✅ PDF матрица (placeholder) создана: {pdf_path}")
        
        return True
    
    def execute(self):
        """Execute all task steps"""
        print(f"\n🚀 BUSINESS ANALYST AGENT STARTING")
        print(f"📋 Task: {self.task['task_name']}")
        print(f"⏱️  Deadline: {self.task['deadline']}")
        print("━" * 50)
        
        try:
            # Execute methodology steps
            step1 = self.execute_step_1_inventory()
            self.results["steps_completed"].append({"step": 1, "result": step1})
            
            step2 = self.execute_step_2_categorize()
            self.results["steps_completed"].append({"step": 2, "result": step2})
            
            step3 = self.execute_step_3_quality()
            self.results["steps_completed"].append({"step": 3, "result": step3})
            
            step4 = self.execute_step_4_gaps()
            self.results["steps_completed"].append({"step": 4, "result": step4})
            
            step5 = self.execute_step_5_matrix()
            self.results["steps_completed"].append({"step": 5, "result": step5})
            
            # Generate final deliverables
            self.generate_deliverables()
            
            # Mark task complete
            self.results["completed_at"] = datetime.now().isoformat()
            self.results["status"] = "COMPLETED"
            
            # Save execution report
            report_path = Path(self.task["output_directory"]) / "execution_report.json"
            with open(report_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print("\n" + "═" * 50)
            print("✅ TASK P1.1 COMPLETED SUCCESSFULLY!")
            print(f"📁 Results saved to: {self.task['output_directory']}")
            print("═" * 50)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            self.results["error"] = str(e)
            self.results["status"] = "FAILED"
            return False


if __name__ == "__main__":
    # Run the agent
    task_file = "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ACTIVE_TASKS/P1.1_Document_Analysis_Task.json"
    
    agent = BusinessAnalystAgent(task_file)
    success = agent.execute()
    
    sys.exit(0 if success else 1)