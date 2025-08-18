#!/usr/bin/env python3
"""
RoleIdMapper - Маппинг названий ролей на их ID в системе
РЕШАЕТ ПРОБЛЕМУ: System Architect + Technical Lead → SA_2a6c2a + TL_6de9b7
Автор: GALAXYDEVELOPMENT
Версия: 1.0.0
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

class RoleIdMapper:
    """Маппер ролей на их ID"""
    
    def __init__(self):
        self.roles_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/05_ROLES")
        self.role_map = {}  # title -> role_id
        self.reverse_map = {}  # role_id -> full profile
        
        # Загружаем все существующие роли
        self._load_all_roles()
    
    def _load_all_roles(self):
        """Загрузка всех ролей из файловой системы"""
        
        if not self.roles_dir.exists():
            print("❌ Roles directory not found!")
            return
        
        for role_dir in self.roles_dir.iterdir():
            if role_dir.is_dir():
                profile_file = role_dir / "profile.json"
                
                if profile_file.exists():
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile = json.load(f)
                        
                        role_id = profile.get("role_id")
                        title = profile.get("title")
                        original_title = profile.get("original_title")
                        
                        if role_id and title:
                            # Основное название
                            self.role_map[title] = role_id
                            
                            # Оригинальное название (если отличается)
                            if original_title and original_title != title:
                                self.role_map[original_title] = role_id
                            
                            # Обратная связь
                            self.reverse_map[role_id] = profile
                            
                            print(f"✅ Loaded role: {title} → {role_id}")
                    
                    except Exception as e:
                        print(f"❌ Error loading role from {profile_file}: {e}")
        
        print(f"📊 Total roles loaded: {len(self.role_map)}")
    
    def normalize_role_name(self, role_name: str) -> str:
        """Нормализация названия роли"""
        
        # Убираем лишние пробелы
        role_name = role_name.strip()
        
        # Альтернативные названия
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
            "IT Auditor": "Compliance Officer",
            "AI": "AI Specialist",
            "UX": "UX Designer",
            "UI": "UI Designer"
        }
        
        # Проверяем альтернативные названия
        for alt, standard in role_mappings.items():
            if alt.lower() == role_name.lower():
                return standard
        
        return role_name
    
    def parse_executor(self, executor: str) -> List[str]:
        """Парсинг составных исполнителей типа 'System Architect + Technical Lead'"""
        
        if not executor:
            return []
        
        # Разделители для составных ролей
        separators = [' + ', '+', ' and ', '&', ' / ', '/']
        
        roles = [executor]  # Начинаем с исходной строки
        
        # Применяем все разделители
        for separator in separators:
            new_roles = []
            for role in roles:
                if separator in role:
                    new_roles.extend([r.strip() for r in role.split(separator)])
                else:
                    new_roles.append(role)
            roles = new_roles
        
        # Нормализуем каждую роль
        normalized_roles = []
        for role in roles:
            normalized = self.normalize_role_name(role)
            if normalized:
                normalized_roles.append(normalized)
        
        return normalized_roles
    
    def get_role_ids(self, executor: str) -> List[Dict[str, str]]:
        """Получение ID ролей для исполнителя"""
        
        roles = self.parse_executor(executor)
        result = []
        
        for role in roles:
            role_id = self.role_map.get(role)
            
            if role_id:
                result.append({
                    "role": role,
                    "role_id": role_id,
                    "found": True
                })
            else:
                result.append({
                    "role": role,
                    "role_id": None,
                    "found": False
                })
        
        return result
    
    def get_role_profile(self, role_id: str) -> Optional[Dict]:
        """Получение полного профиля роли по ID"""
        return self.reverse_map.get(role_id)
    
    def create_role_mapping_json(self) -> str:
        """Создание JSON маппинга всех ролей"""
        
        mapping = {
            "role_mapping": {},
            "reverse_mapping": {},
            "statistics": {
                "total_roles": len(self.role_map),
                "role_ids": list(self.reverse_map.keys())
            }
        }
        
        # Прямой маппинг: название → ID
        mapping["role_mapping"] = self.role_map
        
        # Обратный маппинг: ID → краткая информация
        for role_id, profile in self.reverse_map.items():
            mapping["reverse_mapping"][role_id] = {
                "title": profile.get("title"),
                "original_title": profile.get("original_title"),
                "skills_count": len(profile.get("skills", [])),
                "certifications_count": len(profile.get("certifications", [])),
                "competency_level": profile.get("competency_levels", {}).get("technical", "unknown")
            }
        
        # Сохраняем в файл
        mapping_file = self.roles_dir.parent / "00_PROJECT_MANAGEMENT" / "ROLE_MAPPING.json"
        mapping_file.parent.mkdir(exist_ok=True)
        
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Role mapping saved to: {mapping_file}")
        
        return str(mapping_file)
    
    def test_executor_parsing(self):
        """Тестирование парсинга исполнителей"""
        
        test_cases = [
            "Business Analyst",
            "System Architect + Technical Lead",
            "DevOps Engineer + Integration Architect", 
            "QA Engineer + Test Automation Engineer",
            "iOS Developer + Swift Developer",
            "AI/ML Engineer + Python Developer",
            "Security Specialist + Penetration Tester",
            "Solution Architect",  # Альтернативное название
            "Tech Lead",  # Сокращение
            "BA"  # Аббревиатура
        ]
        
        print("\n" + "="*60)
        print("🧪 TESTING EXECUTOR PARSING")
        print("="*60)
        
        for executor in test_cases:
            print(f"\n📋 Executor: '{executor}'")
            
            # Парсим роли
            roles = self.parse_executor(executor)
            print(f"   Parsed roles: {roles}")
            
            # Получаем ID
            role_ids = self.get_role_ids(executor)
            
            for role_info in role_ids:
                status = "✅" if role_info["found"] else "❌"
                role_id = role_info["role_id"] or "NOT_FOUND"
                print(f"   {status} {role_info['role']} → {role_id}")
        
        print("="*60)
    
    def create_process_role_matrix(self, project_config: Dict) -> Dict:
        """Создание матрицы процесс → роли"""
        
        matrix = {
            "processes": [],
            "role_assignments": {},
            "missing_roles": [],
            "statistics": {
                "total_processes": 0,
                "roles_found": 0,
                "roles_missing": 0
            }
        }
        
        for phase in project_config.get("phases", []):
            phase_id = phase.get("phase_id")
            
            for process in phase.get("microprocesses", []):
                process_id = process.get("id")
                process_name = process.get("name")
                executor = process.get("executor", "")
                
                # Получаем ID ролей
                role_ids = self.get_role_ids(executor)
                
                process_info = {
                    "process_id": process_id,
                    "process_name": process_name,
                    "phase_id": phase_id,
                    "executor": executor,
                    "assigned_roles": []
                }
                
                for role_info in role_ids:
                    if role_info["found"]:
                        process_info["assigned_roles"].append({
                            "role": role_info["role"],
                            "role_id": role_info["role_id"]
                        })
                        matrix["statistics"]["roles_found"] += 1
                    else:
                        matrix["missing_roles"].append({
                            "process_id": process_id,
                            "role": role_info["role"]
                        })
                        matrix["statistics"]["roles_missing"] += 1
                
                matrix["processes"].append(process_info)
                matrix["statistics"]["total_processes"] += 1
        
        # Сохраняем матрицу
        matrix_file = self.roles_dir.parent / "00_PROJECT_MANAGEMENT" / "PROCESS_ROLE_MATRIX.json"
        
        with open(matrix_file, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Process-Role matrix saved to: {matrix_file}")
        
        return matrix


def main():
    """Тестирование RoleIdMapper"""
    
    print("🚀 ROLE ID MAPPER - РЕШАЕМ ПРОБЛЕМУ ПОИСКА РОЛЕЙ!")
    
    mapper = RoleIdMapper()
    
    # Создаем маппинг
    mapping_file = mapper.create_role_mapping_json()
    
    # Тестируем парсинг
    mapper.test_executor_parsing()
    
    # Загружаем конфигурацию проекта для создания матрицы
    config_path = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ ToDo/9d7e2139-7cfe-4512-99c0-70b4247b038f.jsonl  —  _Users_safiullins_pro_.claude_projects_-Volumes-Z7S-development-GalaxyAnalitics---------AppsScript-AnaliticsSystem.json")
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            project_config = json.load(f)
        
        # Создаем матрицу процесс → роли
        matrix = mapper.create_process_role_matrix(project_config)
        
        print(f"\n📊 PROCESS-ROLE MATRIX STATISTICS:")
        print(f"   Total processes: {matrix['statistics']['total_processes']}")
        print(f"   Roles found: {matrix['statistics']['roles_found']}")
        print(f"   Roles missing: {matrix['statistics']['roles_missing']}")
        
        if matrix['missing_roles']:
            print(f"\n⚠️ MISSING ROLES:")
            for missing in matrix['missing_roles'][:5]:  # Показываем первые 5
                print(f"   - {missing['role']} (needed for {missing['process_id']})")
    
    print(f"\n✅ SOLUTION READY!")
    print(f"📁 Use files:")
    print(f"   - ROLE_MAPPING.json")
    print(f"   - PROCESS_ROLE_MATRIX.json")


if __name__ == "__main__":
    main()