#!/usr/bin/env python3
"""
TemplateCollectorAgent - Агент для сбора шаблонов документов из различных источников
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
import re
from urllib.parse import urlparse

class TemplateCollectorAgent:
    """Агент для сбора шаблонов документов"""
    
    TEMPLATE_SOURCES = {
        "github": {
            "repos": [
                "https://github.com/microsoft/azure-docs",
                "https://github.com/atlassian/confluence-templates",
                "https://github.com/pmbok/project-templates",
                "https://github.com/ISO-TC/document-templates"
            ]
        },
        "standard_templates": {
            "inventory_catalog": {
                "format": "xlsx",
                "template_type": "spreadsheet",
                "sources": [
                    "ISO 15489 Inventory Template",
                    "DIRKS Asset Register Template"
                ]
            },
            "coverage_matrix": {
                "format": "pdf",
                "template_type": "document",
                "sources": [
                    "ITIL Coverage Matrix Template",
                    "COBIT Controls Matrix"
                ]
            },
            "gaps_analysis": {
                "format": "md",
                "template_type": "markdown",
                "sources": [
                    "COBIT Gap Analysis Template",
                    "ISO 27001 Gap Assessment"
                ]
            },
            "api_specs": {
                "format": "yaml",
                "template_type": "openapi",
                "sources": [
                    "OpenAPI 3.0 Template",
                    "Swagger Specification Template"
                ]
            },
            "database_schema": {
                "format": "sql",
                "template_type": "database",
                "sources": [
                    "PostgreSQL Schema Template",
                    "Database Design Template"
                ]
            }
        }
    }
    
    def __init__(self):
        self.templates_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/03_TEMPLATES")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.journal_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/09_JOURNALS/agents")
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache = {}
        self.templates_collected = []
        
        # Настройка логирования
        self.logger = logging.getLogger('TemplateCollector')
        self.logger.setLevel(logging.DEBUG)
        
        # Файловый хендлер
        log_file = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/08_LOGS") / f"template_collector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Консольный хендлер
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Формат
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # JSON журнал
        self.json_journal = self.journal_dir / f"templates_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        self.logger.info("TemplateCollectorAgent initialized")
        self._log_to_journal("AGENT_INIT", {"version": "1.0.0"})
    
    def _log_to_journal(self, operation: str, data: Dict[str, Any]):
        """Журналирование в JSON"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "TemplateCollector",
            "operation": operation,
            "data": data,
            "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
        }
        
        with open(self.json_journal, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    async def collect_template(self, deliverable_name: str, deliverable_format: str) -> Dict:
        """Сбор шаблона для конкретного deliverable"""
        
        self.logger.info(f"Collecting template for: {deliverable_name}")
        self._log_to_journal("COLLECT_START", {
            "deliverable": deliverable_name,
            "format": deliverable_format
        })
        
        # Определение типа шаблона
        template_key = deliverable_name.replace('.', '_').lower()
        
        # Проверка кэша
        if template_key in self.cache:
            self.logger.debug(f"Cache hit for {template_key}")
            return self.cache[template_key]
        
        # Генерация шаблона на основе типа
        template_data = await self._generate_template(deliverable_name, deliverable_format)
        
        # Сохранение шаблона
        saved_path = self._save_template(template_data)
        
        # Кэширование
        self.cache[template_key] = template_data
        self.templates_collected.append(template_data)
        
        self._log_to_journal("COLLECT_SUCCESS", {
            "deliverable": deliverable_name,
            "saved_to": str(saved_path)
        })
        
        return template_data
    
    async def _generate_template(self, deliverable_name: str, format_type: str) -> Dict:
        """Генерация шаблона на основе типа deliverable"""
        
        template_data = {
            "deliverable": deliverable_name,
            "format": format_type,
            "created_at": datetime.now().isoformat(),
            "template_id": hashlib.sha256(deliverable_name.encode()).hexdigest()[:12]
        }
        
        # Определение содержимого на основе формата
        if format_type == "xlsx":
            template_data.update(self._generate_excel_template(deliverable_name))
        elif format_type == "pdf":
            template_data.update(self._generate_pdf_template(deliverable_name))
        elif format_type == "md":
            template_data.update(self._generate_markdown_template(deliverable_name))
        elif format_type == "yaml":
            template_data.update(self._generate_yaml_template(deliverable_name))
        elif format_type == "json":
            template_data.update(self._generate_json_template(deliverable_name))
        elif format_type == "sql":
            template_data.update(self._generate_sql_template(deliverable_name))
        elif format_type == "swift":
            template_data.update(self._generate_swift_template(deliverable_name))
        elif format_type == "py":
            template_data.update(self._generate_python_template(deliverable_name))
        else:
            template_data.update(self._generate_generic_template(deliverable_name))
        
        return template_data
    
    def _generate_excel_template(self, name: str) -> Dict:
        """Генерация шаблона Excel"""
        return {
            "type": "spreadsheet",
            "structure": {
                "sheets": [
                    {
                        "name": "Inventory",
                        "columns": [
                            "ID", "Document Name", "Type", "Category", 
                            "Owner", "Status", "Last Updated", "Version",
                            "Compliance", "Retention Period", "Notes"
                        ]
                    },
                    {
                        "name": "Metadata",
                        "columns": [
                            "Field", "Description", "Required", "Format", "Example"
                        ]
                    },
                    {
                        "name": "Coverage",
                        "columns": [
                            "Requirement", "Document", "Section", "Status", "Gap"
                        ]
                    }
                ]
            },
            "formulas": [
                "COUNTIF for status tracking",
                "VLOOKUP for cross-references",
                "Conditional formatting for gaps"
            ]
        }
    
    def _generate_pdf_template(self, name: str) -> Dict:
        """Генерация шаблона PDF документа"""
        return {
            "type": "document",
            "structure": {
                "sections": [
                    "Executive Summary",
                    "Scope and Objectives",
                    "Current State Analysis",
                    "Gap Identification",
                    "Risk Assessment",
                    "Recommendations",
                    "Implementation Plan",
                    "Appendices"
                ],
                "formatting": {
                    "font": "Arial",
                    "size": 11,
                    "margins": "1 inch",
                    "headers": True,
                    "footers": True,
                    "page_numbers": True
                }
            }
        }
    
    def _generate_markdown_template(self, name: str) -> Dict:
        """Генерация шаблона Markdown"""
        
        if "gaps" in name.lower():
            content = """# Gap Analysis Report

## Executive Summary
[Brief overview of gaps identified]

## Methodology
- Current state assessment approach
- Target state definition
- Gap identification process

## Current State
### Documentation
- [ ] Process documentation complete
- [ ] Standards compliance verified
- [ ] Roles and responsibilities defined

### Technology
- [ ] Infrastructure documented
- [ ] Integrations mapped
- [ ] Security controls implemented

## Target State
[Description of desired future state]

## Gaps Identified

| Gap ID | Category | Current | Target | Priority | Impact |
|--------|----------|---------|--------|----------|--------|
| GAP001 | Process  | Manual  | Automated | High | Critical |
| GAP002 | Compliance | Partial | Full | Medium | Major |

## Risk Assessment
[Risks associated with gaps]

## Recommendations
1. **Immediate Actions**
   - Action item 1
   - Action item 2

2. **Short-term (1-3 months)**
   - Action item 3
   - Action item 4

3. **Long-term (3-6 months)**
   - Action item 5
   - Action item 6

## Implementation Timeline
```mermaid
gantt
    title Gap Remediation Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Task 1 :a1, 2025-01-01, 30d
    Task 2 :a2, after a1, 20d
```

## Appendices
- Appendix A: Detailed gap descriptions
- Appendix B: Supporting documentation"""
        else:
            content = """# Document Title

## Overview
[Brief description]

## Table of Contents
1. [Section 1](#section-1)
2. [Section 2](#section-2)
3. [Section 3](#section-3)

## Section 1
[Content]

## Section 2
[Content]

## Section 3
[Content]

## References
- Reference 1
- Reference 2"""
        
        return {
            "type": "markdown",
            "content": content,
            "metadata": {
                "syntax": "GitHub Flavored Markdown",
                "extensions": ["tables", "mermaid", "checkboxes"]
            }
        }
    
    def _generate_yaml_template(self, name: str) -> Dict:
        """Генерация шаблона YAML"""
        
        if "api" in name.lower():
            content = """openapi: 3.0.0
info:
  title: GALAXYDEVELOPMENT API
  version: 1.0.0
  description: Document Management System API
  
servers:
  - url: https://api.galaxydevelopment.com/v1
    description: Production server
  - url: https://staging-api.galaxydevelopment.com/v1
    description: Staging server

paths:
  /documents:
    get:
      summary: List all documents
      operationId: listDocuments
      tags:
        - Documents
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Document'
                  
components:
  schemas:
    Document:
      type: object
      required:
        - id
        - name
        - type
      properties:
        id:
          type: string
        name:
          type: string
        type:
          type: string
        created_at:
          type: string
          format: date-time"""
        else:
            content = """# Configuration Template
version: '1.0'

metadata:
  name: template_name
  description: Template description
  author: GALAXYDEVELOPMENT
  
settings:
  key1: value1
  key2: value2
  
data:
  - item1
  - item2
  - item3"""
        
        return {
            "type": "yaml",
            "content": content,
            "metadata": {
                "parser": "PyYAML",
                "version": "1.2"
            }
        }
    
    def _generate_json_template(self, name: str) -> Dict:
        """Генерация шаблона JSON"""
        return {
            "type": "json",
            "content": {
                "template_name": name,
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "structure": {
                    "metadata": {
                        "id": "string",
                        "name": "string",
                        "description": "string",
                        "tags": ["array"]
                    },
                    "data": {
                        "fields": []
                    },
                    "validation": {
                        "required": [],
                        "rules": {}
                    }
                }
            }
        }
    
    def _generate_sql_template(self, name: str) -> Dict:
        """Генерация шаблона SQL"""
        content = """-- GALAXYDEVELOPMENT Database Schema Template
-- Version: 1.0.0
-- Generated: {date}

-- Create database
CREATE DATABASE IF NOT EXISTS galaxydevelopment;
USE galaxydevelopment;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    content TEXT,
    metadata JSON,
    version INT DEFAULT 1,
    status ENUM('draft', 'review', 'approved', 'published') DEFAULT 'draft',
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
);

-- Processes table
CREATE TABLE IF NOT EXISTS processes (
    id VARCHAR(36) PRIMARY KEY,
    phase_id VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    executor_role VARCHAR(100),
    methodology JSON,
    deliverables JSON,
    dependencies JSON,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phase (phase_id),
    INDEX idx_executor (executor_role)
);

-- Standards table
CREATE TABLE IF NOT EXISTS standards (
    id VARCHAR(36) PRIMARY KEY,
    standard_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    checklist JSON,
    protocol JSON,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_standard_type (standard_type)
);

-- Templates table
CREATE TABLE IF NOT EXISTS templates (
    id VARCHAR(36) PRIMARY KEY,
    deliverable_name VARCHAR(255) NOT NULL,
    format VARCHAR(50),
    content TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_deliverable (deliverable_name)
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    skills JSON,
    certifications JSON,
    tools JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_title (title)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(100),
    changes JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_timestamp (timestamp)
);

-- Views
CREATE VIEW document_summary AS
SELECT 
    type,
    status,
    COUNT(*) as count,
    MAX(updated_at) as last_updated
FROM documents
GROUP BY type, status;

-- Stored procedures
DELIMITER //
CREATE PROCEDURE GetProcessDependencies(IN process_id VARCHAR(36))
BEGIN
    SELECT 
        p1.id,
        p1.name,
        p2.id as depends_on_id,
        p2.name as depends_on_name
    FROM processes p1
    LEFT JOIN processes p2 ON JSON_CONTAINS(p1.dependencies, JSON_QUOTE(p2.id))
    WHERE p1.id = process_id;
END //
DELIMITER ;""".format(date=datetime.now().isoformat())
        
        return {
            "type": "sql",
            "content": content,
            "metadata": {
                "database": "PostgreSQL",
                "version": "14.0"
            }
        }
    
    def _generate_swift_template(self, name: str) -> Dict:
        """Генерация шаблона Swift"""
        content = """//
//  {name}.swift
//  GALAXYDEVELOPMENT
//
//  Created on {date}
//  Copyright © 2025 GALAXYDEVELOPMENT. All rights reserved.
//

import Foundation
import SwiftUI

// MARK: - Model

struct DocumentModel: Codable, Identifiable {{
    let id: String
    let name: String
    let type: DocumentType
    var content: String
    var metadata: [String: Any]?
    let createdAt: Date
    var updatedAt: Date
    
    enum DocumentType: String, Codable {{
        case process
        case standard
        case template
        case deliverable
    }}
}}

// MARK: - View Model

@MainActor
class DocumentViewModel: ObservableObject {{
    @Published var documents: [DocumentModel] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let service = DocumentService()
    
    func loadDocuments() async {{
        isLoading = true
        defer {{ isLoading = false }}
        
        do {{
            documents = try await service.fetchDocuments()
        }} catch {{
            errorMessage = error.localizedDescription
        }}
    }}
    
    func saveDocument(_ document: DocumentModel) async throws {{
        try await service.saveDocument(document)
        await loadDocuments()
    }}
}}

// MARK: - Service

class DocumentService {{
    private let baseURL = "https://api.galaxydevelopment.com/v1"
    
    func fetchDocuments() async throws -> [DocumentModel] {{
        // Implementation
        return []
    }}
    
    func saveDocument(_ document: DocumentModel) async throws {{
        // Implementation
    }}
}}

// MARK: - View

struct DocumentView: View {{
    @StateObject private var viewModel = DocumentViewModel()
    
    var body: some View {{
        NavigationStack {{
            List(viewModel.documents) {{ document in
                DocumentRow(document: document)
            }}
            .navigationTitle("Documents")
            .task {{
                await viewModel.loadDocuments()
            }}
            .overlay {{
                if viewModel.isLoading {{
                    ProgressView()
                }}
            }}
        }}
    }}
}}

struct DocumentRow: View {{
    let document: DocumentModel
    
    var body: some View {{
        HStack {{
            VStack(alignment: .leading) {{
                Text(document.name)
                    .font(.headline)
                Text(document.type.rawValue)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }}
            Spacer()
            Text(document.updatedAt, style: .date)
                .font(.caption2)
        }}
        .padding(.vertical, 4)
    }}
}}""".format(name=name.replace('.swift', ''), date=datetime.now().strftime('%Y-%m-%d'))
        
        return {
            "type": "swift",
            "content": content,
            "metadata": {
                "platform": "iOS/macOS",
                "swift_version": "5.9",
                "frameworks": ["SwiftUI", "Foundation"]
            }
        }
    
    def _generate_python_template(self, name: str) -> Dict:
        """Генерация шаблона Python"""
        content = '''#!/usr/bin/env python3
"""
{name}
GALAXYDEVELOPMENT Document Management System
Created: {date}
"""

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document model"""
    id: str
    name: str
    type: str
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {{
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Document':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            content=data.get("content", ""),
            metadata=data.get("metadata", {{}}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


class DocumentService:
    """Service for document operations"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"DocumentService initialized with path: {{self.base_path}}")
    
    async def save_document(self, document: Document) -> bool:
        """Save document to storage"""
        try:
            file_path = self.base_path / f"{{document.id}}.json"
            with open(file_path, 'w') as f:
                json.dump(document.to_dict(), f, indent=2)
            logger.info(f"Document saved: {{document.id}}")
            return True
        except Exception as e:
            logger.error(f"Error saving document: {{e}}")
            return False
    
    async def load_document(self, document_id: str) -> Optional[Document]:
        """Load document from storage"""
        try:
            file_path = self.base_path / f"{{document_id}}.json"
            if not file_path.exists():
                logger.warning(f"Document not found: {{document_id}}")
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            document = Document.from_dict(data)
            logger.info(f"Document loaded: {{document_id}}")
            return document
        except Exception as e:
            logger.error(f"Error loading document: {{e}}")
            return None
    
    async def list_documents(self) -> List[Document]:
        """List all documents"""
        documents = []
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                documents.append(Document.from_dict(data))
            except Exception as e:
                logger.error(f"Error loading {{file_path}}: {{e}}")
        
        logger.info(f"Listed {{len(documents)}} documents")
        return documents


async def main():
    """Main function for testing"""
    service = DocumentService()
    
    # Create test document
    test_doc = Document(
        id="test_001",
        name="Test Document",
        type="template",
        content="This is a test document",
        metadata={{"author": "GALAXYDEVELOPMENT", "version": "1.0"}}
    )
    
    # Save document
    await service.save_document(test_doc)
    
    # Load document
    loaded_doc = await service.load_document("test_001")
    if loaded_doc:
        print(f"Loaded: {{loaded_doc.name}}")
    
    # List all documents
    all_docs = await service.list_documents()
    print(f"Total documents: {{len(all_docs)}}")


if __name__ == "__main__":
    asyncio.run(main())
'''.format(name=name.replace('.py', ''), date=datetime.now().strftime('%Y-%m-%d'))
        
        return {
            "type": "python",
            "content": content,
            "metadata": {
                "python_version": "3.9+",
                "dependencies": ["asyncio", "dataclasses", "pathlib"]
            }
        }
    
    def _generate_generic_template(self, name: str) -> Dict:
        """Генерация универсального шаблона"""
        return {
            "type": "generic",
            "content": f"# Template for {name}\n\n[Content placeholder]\n",
            "metadata": {
                "format": "text",
                "encoding": "utf-8"
            }
        }
    
    def _save_template(self, template_data: Dict) -> Path:
        """Сохранение шаблона в файл"""
        
        deliverable = template_data["deliverable"]
        format_type = template_data["format"]
        
        # Создание подпапки для типа
        type_dir = self.templates_dir / format_type.upper()
        type_dir.mkdir(exist_ok=True)
        
        # Имя файла
        filename = f"{deliverable.replace('.', '_')}_template.json"
        filepath = type_dir / filename
        
        # Сохранение
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Template saved to {filepath}")
        
        return filepath
    
    async def collect_all_templates(self, deliverables_list: List[str]) -> Dict:
        """Сбор шаблонов для списка deliverables"""
        
        self.logger.info(f"Starting collection of {len(deliverables_list)} templates")
        self._log_to_journal("BULK_COLLECT_START", {"count": len(deliverables_list)})
        
        results = {
            "collected": [],
            "failed": [],
            "total": len(deliverables_list)
        }
        
        for deliverable in deliverables_list:
            try:
                # Определение формата из имени файла
                if '.' in deliverable:
                    format_type = deliverable.split('.')[-1]
                else:
                    format_type = "generic"
                
                template = await self.collect_template(deliverable, format_type)
                results["collected"].append(deliverable)
                
                # Небольшая задержка
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Failed to collect template for {deliverable}: {e}")
                results["failed"].append({"deliverable": deliverable, "error": str(e)})
        
        # Генерация отчета
        report = self.generate_report()
        
        self._log_to_journal("BULK_COLLECT_COMPLETE", {
            "collected": len(results["collected"]),
            "failed": len(results["failed"])
        })
        
        return results
    
    def generate_report(self) -> Dict:
        """Генерация отчета о собранных шаблонах"""
        
        report = {
            "agent": "TemplateCollectorAgent",
            "generated_at": datetime.now().isoformat(),
            "templates_collected": len(self.templates_collected),
            "cache_size": len(self.cache),
            "templates_by_format": {}
        }
        
        # Группировка по форматам
        for template in self.templates_collected:
            format_type = template.get("format", "unknown")
            if format_type not in report["templates_by_format"]:
                report["templates_by_format"][format_type] = 0
            report["templates_by_format"][format_type] += 1
        
        # Сохранение отчета
        report_path = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/10_REPORTS") / f"templates_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report saved to {report_path}")
        self._log_to_journal("REPORT_GENERATED", report)
        
        return report


async def main():
    """Тестовый запуск агента"""
    
    agent = TemplateCollectorAgent()
    
    # Тестовые deliverables из процесса P1.1
    test_deliverables = [
        "inventory_catalog.xlsx",
        "coverage_matrix.pdf",
        "gaps_analysis.md",
        "api_specs.yaml",
        "database_schema.sql",
        "DocumentModel.swift",
        "document_service.py"
    ]
    
    # Сбор всех шаблонов
    results = await agent.collect_all_templates(test_deliverables)
    
    print("\n" + "="*50)
    print("TEMPLATE COLLECTION COMPLETED")
    print("="*50)
    print(f"Templates collected: {len(results['collected'])}")
    print(f"Failed: {len(results['failed'])}")
    print("="*50)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())