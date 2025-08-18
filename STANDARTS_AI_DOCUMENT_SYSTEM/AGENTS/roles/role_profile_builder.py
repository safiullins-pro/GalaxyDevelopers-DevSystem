#!/usr/bin/env python3
"""
RoleProfileBuilder - Агент для создания профилей ролей с навыками и компетенциями
Автор: GALAXYDEVELOPMENT
Версия: 1.0.0
"""

import json
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class RoleProfileBuilder:
    """Агент для построения профилей ролей"""
    
    # База знаний о ролях и их типичных навыках
    ROLE_KNOWLEDGE_BASE = {
        "Business Analyst": {
            "certifications": ["CBAP", "PMI-PBA", "CCBA", "ECBA", "IIBA AAC"],
            "tools": ["JIRA", "Confluence", "Visio", "Enterprise Architect", "Lucidchart", "Miro", "SharePoint", "Excel"],
            "frameworks": ["BABOK", "PMBOK", "Agile", "Scrum", "BPMN", "UML"],
            "responsibilities": [
                "Requirements gathering and analysis",
                "Process documentation and modeling",
                "Stakeholder management",
                "Gap analysis",
                "Business case development"
            ]
        },
        "System Architect": {
            "certifications": ["TOGAF", "AWS Solutions Architect", "Azure Solutions Architect", "Google Cloud Architect"],
            "tools": ["ArchiMate", "Enterprise Architect", "Visio", "Draw.io", "PlantUML", "C4 Model"],
            "frameworks": ["TOGAF", "Zachman", "DoDAF", "Microservices", "SOA", "Event-Driven Architecture"],
            "responsibilities": [
                "System design and architecture",
                "Technology stack selection",
                "Integration design",
                "Performance optimization",
                "Security architecture"
            ]
        },
        "Technical Lead": {
            "certifications": ["PMP", "CSM", "AWS Certified", "Microsoft Certified"],
            "tools": ["Git", "Docker", "Kubernetes", "Jenkins", "JIRA", "VS Code", "IntelliJ IDEA"],
            "frameworks": ["Agile", "DevOps", "CI/CD", "TDD", "DDD", "Clean Architecture"],
            "responsibilities": [
                "Technical team leadership",
                "Code review and quality assurance",
                "Architecture decisions",
                "Mentoring developers",
                "Sprint planning"
            ]
        },
        "DevOps Engineer": {
            "certifications": ["AWS DevOps", "Docker Certified", "Kubernetes CKA", "Jenkins Certified", "Terraform Associate"],
            "tools": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Prometheus", "Grafana"],
            "frameworks": ["CI/CD", "GitOps", "Infrastructure as Code", "SRE", "DevSecOps"],
            "responsibilities": [
                "CI/CD pipeline management",
                "Infrastructure automation",
                "Monitoring and alerting",
                "Deployment automation",
                "Performance optimization"
            ]
        },
        "QA Engineer": {
            "certifications": ["ISTQB", "CSTE", "CSQA", "Certified Agile Tester"],
            "tools": ["Selenium", "JMeter", "Postman", "TestRail", "JIRA", "Cypress", "Appium", "LoadRunner"],
            "frameworks": ["TDD", "BDD", "Agile Testing", "Risk-Based Testing", "Exploratory Testing"],
            "responsibilities": [
                "Test planning and strategy",
                "Test automation",
                "Performance testing",
                "Security testing",
                "Quality metrics tracking"
            ]
        },
        "Security Specialist": {
            "certifications": ["CISSP", "CEH", "OSCP", "Security+", "GSEC"],
            "tools": ["Burp Suite", "OWASP ZAP", "Metasploit", "Nessus", "Wireshark", "Nmap", "Kali Linux"],
            "frameworks": ["OWASP", "NIST", "ISO 27001", "CIS Controls", "MITRE ATT&CK"],
            "responsibilities": [
                "Security assessments",
                "Penetration testing",
                "Vulnerability management",
                "Security architecture review",
                "Incident response"
            ]
        },
        "iOS Developer": {
            "certifications": ["Apple Certified iOS Developer", "Swift Certification"],
            "tools": ["Xcode", "Swift", "SwiftUI", "UIKit", "TestFlight", "Instruments", "Git", "CocoaPods", "SPM"],
            "frameworks": ["SwiftUI", "UIKit", "Combine", "Core Data", "CloudKit", "ARKit", "Core ML"],
            "responsibilities": [
                "iOS app development",
                "UI/UX implementation",
                "API integration",
                "Performance optimization",
                "App Store deployment"
            ]
        },
        "AI/ML Engineer": {
            "certifications": ["Google Cloud ML Engineer", "AWS ML Specialty", "TensorFlow Developer"],
            "tools": ["TensorFlow", "PyTorch", "Scikit-learn", "Jupyter", "MLflow", "Kubeflow", "Docker"],
            "frameworks": ["Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning", "MLOps"],
            "responsibilities": [
                "Model development and training",
                "Data preprocessing",
                "Model deployment",
                "Performance monitoring",
                "A/B testing"
            ]
        },
        "Database Architect": {
            "certifications": ["Oracle DBA", "Microsoft SQL Server", "MongoDB Certified", "AWS Database Specialty"],
            "tools": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DBeaver", "DataGrip"],
            "frameworks": ["ACID", "CAP Theorem", "Sharding", "Replication", "Data Warehousing"],
            "responsibilities": [
                "Database design",
                "Performance tuning",
                "Backup and recovery",
                "Data migration",
                "Security implementation"
            ]
        },
        "Compliance Officer": {
            "certifications": ["CISA", "CRISC", "ISO 27001 Lead Auditor", "GDPR Practitioner"],
            "tools": ["GRC platforms", "ServiceNow", "Archer", "MetricStream", "Excel", "SharePoint"],
            "frameworks": ["ISO 27001", "GDPR", "SOC 2", "HIPAA", "PCI DSS", "COBIT"],
            "responsibilities": [
                "Compliance monitoring",
                "Risk assessment",
                "Audit coordination",
                "Policy development",
                "Training and awareness"
            ]
        }
    }
    
    def __init__(self):
        self.roles_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/05_ROLES")
        self.roles_dir.mkdir(parents=True, exist_ok=True)
        
        self.journal_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/09_JOURNALS/agents")
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        
        self.profiles_created = []
        
        # Настройка логирования
        self.logger = logging.getLogger('RoleProfileBuilder')
        self.logger.setLevel(logging.DEBUG)
        
        # Логирование в файл
        log_file = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/08_LOGS") / f"role_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Консольный вывод
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # JSON журнал
        self.json_journal = self.journal_dir / f"roles_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        self.logger.info("RoleProfileBuilder initialized")
        self._log_to_journal("AGENT_INIT", {"version": "1.0.0"})
    
    def _log_to_journal(self, operation: str, data: Dict[str, Any]):
        """Журналирование в JSON"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "RoleProfileBuilder",
            "operation": operation,
            "data": data,
            "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
        }
        
        with open(self.json_journal, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _normalize_role_title(self, role_title: str) -> str:
        """Нормализация названия роли"""
        # Убираем лишние символы и приводим к стандартному виду
        role_title = role_title.strip()
        
        # Маппинг альтернативных названий
        role_mappings = {
            "BA": "Business Analyst",
            "Solution Architect": "System Architect",
            "Tech Lead": "Technical Lead",
            "DevOps": "DevOps Engineer",
            "QA": "QA Engineer",
            "Tester": "QA Engineer",
            "Security Engineer": "Security Specialist",
            "iOS/macOS Developer": "iOS Developer",
            "Mobile Developer": "iOS Developer",
            "ML Engineer": "AI/ML Engineer",
            "DBA": "Database Architect",
            "Database Developer": "Database Architect",
            "Compliance Specialist": "Compliance Officer",
            "IT Auditor": "Compliance Officer"
        }
        
        # Проверяем альтернативные названия
        for alt, standard in role_mappings.items():
            if alt.lower() in role_title.lower():
                return standard
        
        # Проверяем стандартные названия
        for standard_role in self.ROLE_KNOWLEDGE_BASE.keys():
            if standard_role.lower() in role_title.lower():
                return standard_role
        
        return role_title
    
    def _enrich_skills(self, base_skills: List[str], role_title: str) -> List[str]:
        """Обогащение списка навыков на основе роли"""
        enriched_skills = list(base_skills)  # Копируем базовые навыки
        
        normalized_role = self._normalize_role_title(role_title)
        
        # Добавляем навыки из базы знаний
        if normalized_role in self.ROLE_KNOWLEDGE_BASE:
            role_info = self.ROLE_KNOWLEDGE_BASE[normalized_role]
            
            # Добавляем фреймворки как навыки
            for framework in role_info.get("frameworks", []):
                skill = f"Knowledge of {framework}"
                if skill not in enriched_skills:
                    enriched_skills.append(skill)
            
            # Добавляем инструменты как навыки
            for tool in role_info.get("tools", [])[:5]:  # Берем топ-5 инструментов
                skill = f"Proficiency in {tool}"
                if skill not in enriched_skills:
                    enriched_skills.append(skill)
        
        # Добавляем универсальные soft skills
        soft_skills = [
            "Communication skills",
            "Problem-solving abilities",
            "Team collaboration",
            "Time management",
            "Analytical thinking"
        ]
        
        for skill in soft_skills:
            if skill not in enriched_skills and len(enriched_skills) < 15:
                enriched_skills.append(skill)
        
        return enriched_skills
    
    def _generate_role_id(self, role_title: str) -> str:
        """Генерация уникального ID для роли"""
        normalized = self._normalize_role_title(role_title)
        timestamp = datetime.now().strftime("%Y%m%d")
        hash_part = hashlib.sha256(f"{normalized}{timestamp}".encode()).hexdigest()[:6]
        
        # Создаем читаемый ID
        prefix = "".join([word[0].upper() for word in normalized.split()])[:3]
        return f"{prefix}_{hash_part}"
    
    async def build_role_profile(self, executor: str, required_skills: List[str] = None) -> Dict:
        """Построение профиля роли"""
        
        self.logger.info(f"Building profile for role: {executor}")
        self._log_to_journal("BUILD_START", {
            "role": executor,
            "skills_provided": len(required_skills) if required_skills else 0
        })
        
        # Нормализация названия роли
        normalized_role = self._normalize_role_title(executor)
        
        # Базовая структура профиля
        profile = {
            "role_id": self._generate_role_id(normalized_role),
            "title": normalized_role,
            "original_title": executor,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        # Обогащение навыков
        if required_skills:
            profile["skills"] = self._enrich_skills(required_skills, normalized_role)
        else:
            profile["skills"] = []
        
        # Добавление информации из базы знаний
        if normalized_role in self.ROLE_KNOWLEDGE_BASE:
            knowledge = self.ROLE_KNOWLEDGE_BASE[normalized_role]
            
            profile["certifications"] = knowledge.get("certifications", [])
            profile["tools"] = knowledge.get("tools", [])
            profile["frameworks"] = knowledge.get("frameworks", [])
            profile["responsibilities"] = knowledge.get("responsibilities", [])
            
            # Добавляем метрики компетенций
            profile["competency_levels"] = self._calculate_competency_levels(profile)
            
            # Добавляем карьерный путь
            profile["career_path"] = self._generate_career_path(normalized_role)
        else:
            # Для неизвестных ролей создаем базовую структуру
            profile["certifications"] = []
            profile["tools"] = []
            profile["frameworks"] = []
            profile["responsibilities"] = []
            profile["competency_levels"] = {
                "technical": "intermediate",
                "leadership": "basic",
                "domain": "intermediate"
            }
        
        # Добавляем требования к опыту
        profile["experience_requirements"] = self._generate_experience_requirements(normalized_role)
        
        # Добавляем связанные роли
        profile["related_roles"] = self._find_related_roles(normalized_role)
        
        # Сохранение профиля
        saved_path = await self._save_profile(profile)
        profile["file_path"] = str(saved_path)
        
        self.profiles_created.append(profile)
        
        self._log_to_journal("BUILD_COMPLETE", {
            "role_id": profile["role_id"],
            "role": normalized_role,
            "skills_count": len(profile["skills"]),
            "certifications_count": len(profile["certifications"])
        })
        
        return profile
    
    def _calculate_competency_levels(self, profile: Dict) -> Dict:
        """Расчет уровней компетенций"""
        levels = {}
        
        # Технический уровень на основе инструментов и фреймворков
        tech_score = len(profile.get("tools", [])) + len(profile.get("frameworks", []))
        if tech_score >= 15:
            levels["technical"] = "expert"
        elif tech_score >= 10:
            levels["technical"] = "advanced"
        elif tech_score >= 5:
            levels["technical"] = "intermediate"
        else:
            levels["technical"] = "basic"
        
        # Лидерский уровень на основе роли
        if "Lead" in profile["title"] or "Manager" in profile["title"] or "Architect" in profile["title"]:
            levels["leadership"] = "advanced"
        elif "Senior" in profile["title"]:
            levels["leadership"] = "intermediate"
        else:
            levels["leadership"] = "basic"
        
        # Доменный уровень на основе сертификаций
        cert_count = len(profile.get("certifications", []))
        if cert_count >= 4:
            levels["domain"] = "expert"
        elif cert_count >= 2:
            levels["domain"] = "advanced"
        elif cert_count >= 1:
            levels["domain"] = "intermediate"
        else:
            levels["domain"] = "basic"
        
        return levels
    
    def _generate_career_path(self, role: str) -> Dict:
        """Генерация карьерного пути"""
        career_paths = {
            "Business Analyst": {
                "junior": "Junior Business Analyst",
                "current": "Business Analyst",
                "senior": "Senior Business Analyst",
                "next": ["Product Owner", "Solution Architect", "Business Analysis Manager"]
            },
            "System Architect": {
                "junior": "Software Developer",
                "current": "System Architect",
                "senior": "Principal Architect",
                "next": ["Enterprise Architect", "CTO", "VP of Engineering"]
            },
            "DevOps Engineer": {
                "junior": "Junior DevOps Engineer",
                "current": "DevOps Engineer",
                "senior": "Senior DevOps Engineer",
                "next": ["DevOps Lead", "Platform Engineer", "SRE Manager"]
            },
            "QA Engineer": {
                "junior": "QA Tester",
                "current": "QA Engineer",
                "senior": "Senior QA Engineer",
                "next": ["QA Lead", "Test Architect", "QA Manager"]
            }
        }
        
        return career_paths.get(role, {
            "junior": f"Junior {role}",
            "current": role,
            "senior": f"Senior {role}",
            "next": [f"{role} Lead", f"{role} Manager"]
        })
    
    def _generate_experience_requirements(self, role: str) -> Dict:
        """Генерация требований к опыту"""
        base_requirements = {
            "minimum_years": 3,
            "preferred_years": 5,
            "required_experience": [
                f"Hands-on experience in {role} role",
                "Working in Agile/Scrum environment",
                "Cross-functional team collaboration"
            ],
            "nice_to_have": [
                "Experience with enterprise-level projects",
                "International team collaboration",
                "Mentoring junior team members"
            ]
        }
        
        # Корректировка на основе роли
        if "Senior" in role or "Lead" in role or "Architect" in role:
            base_requirements["minimum_years"] = 5
            base_requirements["preferred_years"] = 8
        elif "Junior" in role:
            base_requirements["minimum_years"] = 0
            base_requirements["preferred_years"] = 2
        
        return base_requirements
    
    def _find_related_roles(self, role: str) -> List[str]:
        """Поиск связанных ролей"""
        related_mapping = {
            "Business Analyst": ["System Architect", "Product Owner", "Project Manager"],
            "System Architect": ["Technical Lead", "DevOps Engineer", "Business Analyst"],
            "Technical Lead": ["System Architect", "DevOps Engineer", "Development Manager"],
            "DevOps Engineer": ["System Architect", "Technical Lead", "SRE Engineer"],
            "QA Engineer": ["Test Automation Engineer", "Performance Engineer", "Security Tester"],
            "Security Specialist": ["DevOps Engineer", "System Architect", "Compliance Officer"],
            "iOS Developer": ["Mobile Developer", "Frontend Developer", "Full Stack Developer"],
            "AI/ML Engineer": ["Data Scientist", "Data Engineer", "Research Scientist"],
            "Database Architect": ["Data Engineer", "System Architect", "DevOps Engineer"],
            "Compliance Officer": ["Security Specialist", "Risk Manager", "IT Auditor"]
        }
        
        return related_mapping.get(role, [])
    
    async def _save_profile(self, profile: Dict) -> Path:
        """Сохранение профиля роли"""
        
        # Создание подпапки для роли
        role_dir = self.roles_dir / profile["role_id"]
        role_dir.mkdir(exist_ok=True)
        
        # Основной файл профиля
        profile_file = role_dir / "profile.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        # Создание README для роли
        readme_file = role_dir / "README.md"
        readme_content = self._generate_role_readme(profile)
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.logger.info(f"Profile saved to {profile_file}")
        
        return profile_file
    
    def _generate_role_readme(self, profile: Dict) -> str:
        """Генерация README для роли"""
        readme = f"""# {profile['title']}

## Role ID: {profile['role_id']}

## Overview
This profile defines the competencies, skills, and requirements for the {profile['title']} role.

## Core Skills
{chr(10).join([f"- {skill}" for skill in profile.get('skills', [])])}

## Required Certifications
{chr(10).join([f"- {cert}" for cert in profile.get('certifications', [])])}

## Tools & Technologies
{chr(10).join([f"- {tool}" for tool in profile.get('tools', [])])}

## Frameworks & Methodologies
{chr(10).join([f"- {framework}" for framework in profile.get('frameworks', [])])}

## Key Responsibilities
{chr(10).join([f"- {resp}" for resp in profile.get('responsibilities', [])])}

## Competency Levels
- Technical: **{profile.get('competency_levels', {}).get('technical', 'N/A')}**
- Leadership: **{profile.get('competency_levels', {}).get('leadership', 'N/A')}**
- Domain: **{profile.get('competency_levels', {}).get('domain', 'N/A')}**

## Experience Requirements
- Minimum: {profile.get('experience_requirements', {}).get('minimum_years', 'N/A')} years
- Preferred: {profile.get('experience_requirements', {}).get('preferred_years', 'N/A')} years

## Career Path
- Previous: {profile.get('career_path', {}).get('junior', 'N/A')}
- Current: **{profile.get('career_path', {}).get('current', 'N/A')}**
- Next: {', '.join(profile.get('career_path', {}).get('next', []))}

## Related Roles
{chr(10).join([f"- {role}" for role in profile.get('related_roles', [])])}

---
*Generated: {profile.get('created_at', 'N/A')}*
*Version: {profile.get('version', '1.0.0')}*
"""
        return readme
    
    async def process_all_roles(self, process_config: Dict) -> Dict:
        """Обработка всех ролей из конфигурации процессов"""
        
        self.logger.info("Processing all roles from configuration")
        self._log_to_journal("BULK_PROCESS_START", {"source": "process_config"})
        
        results = {
            "processed": [],
            "failed": [],
            "unique_roles": set()
        }
        
        # Извлечение всех уникальных ролей
        for phase in process_config.get("phases", []):
            for process in phase.get("microprocesses", []):
                executor = process.get("executor", "")
                if executor:
                    # Разделяем составные роли (например "System Architect + Technical Lead")
                    roles = [r.strip() for r in executor.split("+")]
                    for role in roles:
                        results["unique_roles"].add(role)
        
        # Создание профилей для каждой уникальной роли
        for role in results["unique_roles"]:
            try:
                # Ищем навыки для этой роли в процессах
                role_skills = []
                for phase in process_config.get("phases", []):
                    for process in phase.get("microprocesses", []):
                        if role in process.get("executor", ""):
                            role_skills.extend(process.get("required_skills", []))
                
                # Убираем дубликаты
                role_skills = list(set(role_skills))
                
                # Создаем профиль
                profile = await self.build_role_profile(role, role_skills)
                results["processed"].append(role)
                
                # Небольшая задержка
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Failed to process role {role}: {e}")
                results["failed"].append({"role": role, "error": str(e)})
        
        # Генерация итогового отчета
        report = self.generate_report()
        
        self._log_to_journal("BULK_PROCESS_COMPLETE", {
            "processed": len(results["processed"]),
            "failed": len(results["failed"]),
            "unique_roles": len(results["unique_roles"])
        })
        
        return results
    
    def generate_report(self) -> Dict:
        """Генерация отчета о созданных профилях"""
        
        report = {
            "agent": "RoleProfileBuilder",
            "generated_at": datetime.now().isoformat(),
            "profiles_created": len(self.profiles_created),
            "roles_by_competency": {
                "expert": [],
                "advanced": [],
                "intermediate": [],
                "basic": []
            },
            "statistics": {
                "avg_skills_per_role": 0,
                "avg_certifications_per_role": 0,
                "avg_tools_per_role": 0
            }
        }
        
        # Анализ созданных профилей
        total_skills = 0
        total_certs = 0
        total_tools = 0
        
        for profile in self.profiles_created:
            # Группировка по компетенциям
            tech_level = profile.get("competency_levels", {}).get("technical", "basic")
            if tech_level in report["roles_by_competency"]:
                report["roles_by_competency"][tech_level].append(profile["title"])
            
            # Статистика
            total_skills += len(profile.get("skills", []))
            total_certs += len(profile.get("certifications", []))
            total_tools += len(profile.get("tools", []))
        
        # Средние значения
        if self.profiles_created:
            report["statistics"]["avg_skills_per_role"] = round(total_skills / len(self.profiles_created), 2)
            report["statistics"]["avg_certifications_per_role"] = round(total_certs / len(self.profiles_created), 2)
            report["statistics"]["avg_tools_per_role"] = round(total_tools / len(self.profiles_created), 2)
        
        # Сохранение отчета
        report_path = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/10_REPORTS") / f"roles_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report saved to {report_path}")
        self._log_to_journal("REPORT_GENERATED", report)
        
        return report


async def main():
    """Тестовый запуск агента"""
    
    builder = RoleProfileBuilder()
    
    # Тестовые роли из процесса P1
    test_roles = [
        {
            "executor": "Business Analyst",
            "skills": [
                "Аналитическое мышление и критическое мышление",
                "Навыки работы с процессным моделированием (BPMN)",
                "Коммуникационные навыки для интервьюирования",
                "Опыт работы с системами документооборота (Confluence, SharePoint)",
                "Понимание бизнес-процессов и требований"
            ]
        },
        {
            "executor": "System Architect + Technical Lead",
            "skills": [
                "Глубокие знания IT-инфраструктуры и системной архитектуры",
                "Опыт работы с облачными платформами (AWS, Azure, GCP)",
                "Знание современных технологий и фреймворков",
                "Навыки системного администрирования",
                "Понимание принципов DevOps и CI/CD"
            ]
        },
        {
            "executor": "DevOps Engineer",
            "skills": [
                "Опыт работы с системами интеграции (API, webhooks, message queues)",
                "Знание DevOps практик и инструментов",
                "Навыки автоматизации и orchestration",
                "Понимание cloud технологий и контейнеризации",
                "Опыт работы с системами мониторинга"
            ]
        }
    ]
    
    # Создание профилей
    for role_data in test_roles:
        executor = role_data["executor"]
        skills = role_data["skills"]
        
        # Обработка составных ролей
        if "+" in executor:
            roles = [r.strip() for r in executor.split("+")]
            for role in roles:
                profile = await builder.build_role_profile(role, skills)
                print(f"Created profile for: {profile['title']} (ID: {profile['role_id']})")
        else:
            profile = await builder.build_role_profile(executor, skills)
            print(f"Created profile for: {profile['title']} (ID: {profile['role_id']})")
    
    # Генерация отчета
    report = builder.generate_report()
    
    print("\n" + "="*50)
    print("ROLE PROFILE BUILDING COMPLETED")
    print("="*50)
    print(f"Profiles created: {report['profiles_created']}")
    print(f"Average skills per role: {report['statistics']['avg_skills_per_role']}")
    print(f"Average certifications: {report['statistics']['avg_certifications_per_role']}")
    print(f"Average tools: {report['statistics']['avg_tools_per_role']}")
    print("="*50)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())