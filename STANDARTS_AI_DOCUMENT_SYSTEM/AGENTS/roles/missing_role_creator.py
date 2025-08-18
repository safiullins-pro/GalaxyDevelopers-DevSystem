#!/usr/bin/env python3
"""
MissingRoleCreator - Создание недостающих ролей
РЕШАЕТ: AI, UX, Database Architect, UI Designer и других
Автор: GALAXYDEVELOPMENT
"""

import json
from pathlib import Path
from datetime import datetime
import random
import string

class MissingRoleCreator:
    def __init__(self):
        self.roles_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/05_ROLES")
        
    def generate_role_id(self, title: str) -> str:
        """Генерация ID роли"""
        # Берем первые буквы каждого слова
        words = title.replace("/", " ").replace("-", " ").split()
        prefix = "".join([word[0].upper() for word in words[:2]])
        
        # Добавляем случайные символы
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        return f"{prefix}_{suffix}"
    
    def create_missing_roles(self):
        """Создание всех недостающих ролей"""
        
        missing_roles = [
            "AI Specialist",
            "UX Designer", 
            "UI Designer",
            "Database Architect",
            "Penetration Tester",
            "Data Scientist",
            "Machine Learning Engineer",
            "Cloud Architect",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer"
        ]
        
        print("🔧 CREATING MISSING ROLES...")
        
        for role_title in missing_roles:
            self.create_role_profile(role_title)
        
        print(f"✅ Created {len(missing_roles)} missing roles!")
    
    def create_role_profile(self, title: str):
        """Создание профиля роли"""
        
        role_id = self.generate_role_id(title)
        role_dir = self.roles_dir / role_id
        role_dir.mkdir(exist_ok=True)
        
        # Базовые навыки по типу роли
        skills_map = {
            "AI Specialist": [
                "Machine Learning algorithms", "Deep Learning", "Neural Networks",
                "Python/R programming", "Data analysis", "Model deployment",
                "TensorFlow/PyTorch", "Data preprocessing", "Feature engineering"
            ],
            "UX Designer": [
                "User research", "Persona development", "User journey mapping",
                "Wireframing", "Prototyping", "Usability testing",
                "Information architecture", "Design thinking", "Accessibility"
            ],
            "UI Designer": [
                "Visual design", "Typography", "Color theory", "Layout design",
                "Design systems", "Figma/Sketch", "Responsive design",
                "Icon design", "Brand consistency"
            ],
            "Database Architect": [
                "Database design", "Data modeling", "SQL optimization", 
                "Performance tuning", "Data warehousing", "ETL processes",
                "PostgreSQL/MySQL", "MongoDB", "Data governance"
            ],
            "Penetration Tester": [
                "Security assessment", "Vulnerability scanning", "Network security",
                "Web application testing", "Social engineering", "Risk analysis",
                "Security tools", "Compliance testing", "Report writing"
            ]
        }
        
        # Создаем профиль
        profile = {
            "role_id": role_id,
            "title": title,
            "original_title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "skills": skills_map.get(title, ["Professional skills", "Domain expertise", "Team collaboration"]),
            "certifications": self.get_certifications(title),
            "tools": self.get_tools(title),
            "frameworks": self.get_frameworks(title),
            "responsibilities": self.get_responsibilities(title),
            "competency_levels": {
                "technical": "advanced",
                "leadership": "basic", 
                "domain": "expert"
            },
            "career_path": {
                "junior": f"Junior {title}",
                "current": title,
                "senior": f"Senior {title}",
                "next": [f"{title} Lead", f"{title} Manager"]
            },
            "experience_requirements": {
                "minimum_years": 3,
                "preferred_years": 5,
                "required_experience": [
                    f"Hands-on experience in {title} role",
                    "Working in Agile/Scrum environment",
                    "Cross-functional team collaboration"
                ],
                "nice_to_have": [
                    "Experience with enterprise-level projects",
                    "International team collaboration",
                    "Mentoring junior team members"
                ]
            },
            "related_roles": self.get_related_roles(title)
        }
        
        # Сохраняем профиль
        profile_file = role_dir / "profile.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        # Создаем README
        readme_content = f"""# {title} ({role_id})

## Overview
Role profile for {title} position in GALAXYDEVELOPMENT system.

## Key Responsibilities
{chr(10).join('- ' + resp for resp in profile['responsibilities'])}

## Required Skills
{chr(10).join('- ' + skill for skill in profile['skills'][:5])}

## Tools & Technologies
{chr(10).join('- ' + tool for tool in profile['tools'])}

---
Generated by GALAXYDEVELOPMENT Document Management System
Created: {profile['created_at']}
"""
        
        readme_file = role_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"   ✅ {title} → {role_id}")
    
    def get_certifications(self, title: str) -> list:
        cert_map = {
            "AI Specialist": ["AWS ML", "Google Cloud ML", "Microsoft AI"],
            "UX Designer": ["UX Design Certification", "Google UX Design"],
            "UI Designer": ["Adobe Certified", "Figma Certified"],
            "Database Architect": ["Oracle Certified", "PostgreSQL Certified", "MongoDB Certified"],
            "Penetration Tester": ["CISSP", "CEH", "OSCP", "GIAC"]
        }
        return cert_map.get(title, ["Professional Certification"])
    
    def get_tools(self, title: str) -> list:
        tools_map = {
            "AI Specialist": ["Python", "TensorFlow", "PyTorch", "Jupyter", "Docker"],
            "UX Designer": ["Figma", "Sketch", "Adobe XD", "Miro", "InVision"],
            "UI Designer": ["Figma", "Sketch", "Adobe Creative Suite", "Zeplin"],
            "Database Architect": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "InfluxDB"],
            "Penetration Tester": ["Nmap", "Burp Suite", "Metasploit", "Wireshark", "Kali Linux"]
        }
        return tools_map.get(title, ["Professional Tools"])
    
    def get_frameworks(self, title: str) -> list:
        frameworks_map = {
            "AI Specialist": ["Scikit-learn", "Keras", "MLflow", "Kubeflow"],
            "UX Designer": ["Design Thinking", "Human-Centered Design", "Lean UX"],
            "UI Designer": ["Design Systems", "Material Design", "Apple HIG"],
            "Database Architect": ["Data Modeling", "ACID", "CAP Theorem"],
            "Penetration Tester": ["OWASP", "NIST", "PTES"]
        }
        return frameworks_map.get(title, ["Professional Frameworks"])
    
    def get_responsibilities(self, title: str) -> list:
        resp_map = {
            "AI Specialist": ["Model development", "Data analysis", "Algorithm optimization", "Research", "Documentation"],
            "UX Designer": ["User research", "Journey mapping", "Wireframing", "Usability testing", "Design strategy"],
            "UI Designer": ["Visual design", "Component design", "Design systems", "Asset creation", "Style guides"],
            "Database Architect": ["Schema design", "Performance tuning", "Data modeling", "Migration planning", "Optimization"],
            "Penetration Tester": ["Security testing", "Vulnerability assessment", "Risk analysis", "Report creation", "Compliance"]
        }
        return resp_map.get(title, ["Professional responsibilities"])
    
    def get_related_roles(self, title: str) -> list:
        related_map = {
            "AI Specialist": ["Data Scientist", "ML Engineer", "Python Developer"],
            "UX Designer": ["UI Designer", "Product Manager", "User Researcher"],
            "UI Designer": ["UX Designer", "Frontend Developer", "Visual Designer"],
            "Database Architect": ["Backend Developer", "Data Engineer", "System Architect"],
            "Penetration Tester": ["Security Specialist", "IT Auditor", "Compliance Officer"]
        }
        return related_map.get(title, ["Related professional roles"])


def main():
    print("🚀 CREATING MISSING ROLES!")
    
    creator = MissingRoleCreator()
    creator.create_missing_roles()
    
    print("✅ ALL MISSING ROLES CREATED!")


if __name__ == "__main__":
    main()