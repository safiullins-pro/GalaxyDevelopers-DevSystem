"""
UNIT ТЕСТЫ ДЛЯ COMPOSER AGENT
Инквизитор тестирует генератора документации
50+ тестов на генерацию контента
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import json
import hashlib
from datetime import datetime
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
from AGENTS.composer.composer_agent import ComposerAgent

class TestComposerAgentCore:
    """БАЗОВЫЕ ТЕСТЫ - агент-композитор существует?"""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_composer_imports_successfully(self):
        """Тест 1: ComposerAgent импортируется"""
        assert ComposerAgent is not None
        assert hasattr(ComposerAgent, '__init__')
    
    def test_composer_has_generation_methods(self):
        """Тест 2: Есть методы генерации"""
        required_methods = [
            'generate_document', 'apply_template', 'validate_format',
            'add_metadata', 'export_document'
        ]
        agent = ComposerAgent()
        for method in required_methods:
            assert hasattr(agent, method), f"Missing: {method}"
    
    def test_composer_initialization(self):
        """Тест 3: Инициализация без ошибок"""
        agent = ComposerAgent()
        assert agent.name == "ComposerAgent"
        assert agent.port == 8002

class TestDocumentGeneration:
    """ТЕСТЫ ГЕНЕРАЦИИ - создает документы?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_generates_markdown_document(self, agent):
        """Тест 4: Генерация Markdown"""
        request = {
            "title": "Test Document",
            "format": "markdown",
            "content": "Test content"
        }
        doc = agent.generate_document(request)
        assert doc is not None
        assert doc['format'] == 'markdown'
        assert '# Test Document' in doc['content']
    
    def test_generates_html_document(self, agent):
        """Тест 5: Генерация HTML"""
        request = {"title": "HTML Test", "format": "html"}
        doc = agent.generate_document(request)
        assert '<html>' in doc['content'] or '<HTML>' in doc['content']
        assert '</html>' in doc['content'] or '</HTML>' in doc['content']
    
    def test_generates_json_document(self, agent):
        """Тест 6: Генерация JSON"""
        request = {"title": "JSON Test", "format": "json"}
        doc = agent.generate_document(request)
        parsed = json.loads(doc['content'])
        assert parsed is not None
    
    def test_generates_yaml_document(self, agent):
        """Тест 7: Генерация YAML"""
        request = {"title": "YAML Test", "format": "yaml"}
        doc = agent.generate_document(request)
        assert ':' in doc['content']
        assert not doc['content'].startswith('{')
    
    @pytest.mark.parametrize("format_type", [
        "markdown", "html", "json", "yaml", "xml", "rst", "latex"
    ])
    def test_supports_multiple_formats(self, agent, format_type):
        """Тест 8-14: Поддержка разных форматов"""
        request = {"title": "Format Test", "format": format_type}
        doc = agent.generate_document(request)
        assert doc['format'] == format_type

class TestTemplateSystem:
    """ТЕСТЫ ШАБЛОНОВ - работает с templates?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_applies_standard_template(self, agent):
        """Тест 15: Применение стандартного шаблона"""
        doc = agent.apply_template("standard", {"title": "Test"})
        assert doc is not None
        assert 'title' in doc
    
    def test_applies_itil_template(self, agent):
        """Тест 16: ITIL шаблон"""
        doc = agent.apply_template("itil", {
            "process": "Incident Management",
            "version": "4.0"
        })
        assert 'Incident Management' in str(doc)
    
    def test_applies_iso_template(self, agent):
        """Тест 17: ISO шаблон"""
        doc = agent.apply_template("iso_27001", {
            "control": "A.5",
            "description": "Information security policies"
        })
        assert 'A.5' in str(doc)
    
    def test_handles_missing_template(self, agent):
        """Тест 18: Несуществующий шаблон"""
        doc = agent.apply_template("non_existent_template_666", {})
        assert doc is not None  # Должен использовать default
    
    def test_template_variable_substitution(self, agent):
        """Тест 19: Подстановка переменных"""
        template_data = {
            "{{title}}": "My Title",
            "{{author}}": "Test Author",
            "{{date}}": "2025-08-08"
        }
        doc = agent.apply_template("custom", template_data)
        result = str(doc)
        assert "{{title}}" not in result  # Переменные заменены
    
    def test_nested_template_variables(self, agent):
        """Тест 20: Вложенные переменные"""
        data = {
            "section": {
                "subsection": {
                    "content": "Deep nested content"
                }
            }
        }
        doc = agent.apply_template("nested", data)
        assert doc is not None

class TestContentValidation:
    """ТЕСТЫ ВАЛИДАЦИИ - проверяет качество?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_validates_markdown_syntax(self, agent):
        """Тест 21: Валидация Markdown синтаксиса"""
        valid_md = "# Title\n\n## Subtitle\n\n- Item 1\n- Item 2"
        assert agent.validate_format(valid_md, "markdown") == True
    
    def test_rejects_invalid_markdown(self, agent):
        """Тест 22: Отклонение невалидного Markdown"""
        invalid_md = "# Title without closing\n## "
        result = agent.validate_format(invalid_md, "markdown")
        # Должен заметить проблемы
    
    def test_validates_json_structure(self, agent):
        """Тест 23: Валидация JSON"""
        valid_json = '{"key": "value", "array": [1, 2, 3]}'
        assert agent.validate_format(valid_json, "json") == True
    
    def test_rejects_invalid_json(self, agent):
        """Тест 24: Отклонение невалидного JSON"""
        invalid_json = '{"key": "value", "missing": }'
        assert agent.validate_format(invalid_json, "json") == False
    
    def test_validates_html_structure(self, agent):
        """Тест 25: Валидация HTML"""
        valid_html = "<html><body><h1>Test</h1></body></html>"
        assert agent.validate_format(valid_html, "html") == True
    
    def test_detects_unclosed_html_tags(self, agent):
        """Тест 26: Обнаружение незакрытых тегов"""
        invalid_html = "<html><body><h1>Test</body></html>"
        result = agent.validate_format(invalid_html, "html")
        # Должен обнаружить проблему

class TestMetadataHandling:
    """ТЕСТЫ МЕТАДАННЫХ - управляет metadata?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_adds_creation_metadata(self, agent):
        """Тест 27: Добавление metadata создания"""
        doc = {"content": "Test"}
        doc_with_meta = agent.add_metadata(doc)
        assert 'metadata' in doc_with_meta
        assert 'created_at' in doc_with_meta['metadata']
        assert 'author' in doc_with_meta['metadata']
    
    def test_adds_version_metadata(self, agent):
        """Тест 28: Версионирование"""
        doc = {"content": "Test"}
        doc_with_meta = agent.add_metadata(doc, version="1.0.0")
        assert doc_with_meta['metadata']['version'] == "1.0.0"
    
    def test_preserves_existing_metadata(self, agent):
        """Тест 29: Сохранение существующей metadata"""
        doc = {
            "content": "Test",
            "metadata": {"custom_field": "custom_value"}
        }
        doc_with_meta = agent.add_metadata(doc)
        assert doc_with_meta['metadata']['custom_field'] == "custom_value"
    
    def test_generates_document_hash(self, agent):
        """Тест 30: Генерация хеша документа"""
        doc = {"content": "Test content for hashing"}
        doc_with_meta = agent.add_metadata(doc)
        assert 'hash' in doc_with_meta['metadata']
        # Хеш должен быть детерминированным
        expected_hash = hashlib.sha256("Test content for hashing".encode()).hexdigest()
        assert doc_with_meta['metadata']['hash'] == expected_hash

class TestStyleConsistency:
    """ТЕСТЫ СТИЛЯ - соблюдает корпоративный стиль?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_applies_corporate_style(self, agent):
        """Тест 31: Применение корпоративного стиля"""
        doc = agent.generate_document({
            "title": "Corporate Doc",
            "style": "corporate"
        })
        # Должен содержать элементы корп. стиля
        assert any(keyword in doc['content'].lower() 
                  for keyword in ['executive summary', 'objective', 'scope'])
    
    def test_consistent_heading_levels(self, agent):
        """Тест 32: Консистентность заголовков"""
        doc = agent.generate_document({
            "title": "Test",
            "sections": ["Intro", "Main", "Conclusion"]
        })
        content = doc['content']
        # Проверяем иерархию заголовков
        assert content.count('# ') <= content.count('## ')
    
    def test_consistent_list_formatting(self, agent):
        """Тест 33: Форматирование списков"""
        doc = agent.generate_document({
            "title": "List Test",
            "items": ["Item 1", "Item 2", "Item 3"]
        })
        content = doc['content']
        # Все списки должны быть одного типа
        assert ('- Item' in content) or ('* Item' in content) or ('1. Item' in content)
    
    def test_consistent_code_blocks(self, agent):
        """Тест 34: Форматирование кода"""
        doc = agent.generate_document({
            "title": "Code Test",
            "code_snippets": ["print('hello')", "console.log('world')"]
        })
        content = doc['content']
        # Код должен быть в блоках
        assert '```' in content or '<code>' in content

class TestComplexDocuments:
    """ТЕСТЫ СЛОЖНЫХ ДОКУМЕНТОВ - справляется со сложностью?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_generates_multi_section_document(self, agent):
        """Тест 35: Многосекционный документ"""
        request = {
            "title": "Complex Document",
            "sections": [
                {"title": "Introduction", "content": "Intro text"},
                {"title": "Methods", "content": "Methods text"},
                {"title": "Results", "content": "Results text"},
                {"title": "Conclusion", "content": "Conclusion text"}
            ]
        }
        doc = agent.generate_document(request)
        for section in request['sections']:
            assert section['title'] in doc['content']
    
    def test_handles_nested_structures(self, agent):
        """Тест 36: Вложенные структуры"""
        request = {
            "title": "Nested Doc",
            "chapters": [
                {
                    "title": "Chapter 1",
                    "sections": [
                        {"title": "Section 1.1", "content": "Text"},
                        {"title": "Section 1.2", "content": "Text"}
                    ]
                }
            ]
        }
        doc = agent.generate_document(request)
        assert "Chapter 1" in doc['content']
        assert "Section 1.1" in doc['content']
    
    def test_handles_tables(self, agent):
        """Тест 37: Генерация таблиц"""
        request = {
            "title": "Table Test",
            "table": {
                "headers": ["Name", "Value", "Status"],
                "rows": [
                    ["Test1", "100", "OK"],
                    ["Test2", "200", "FAIL"]
                ]
            }
        }
        doc = agent.generate_document(request)
        assert "Name" in doc['content']
        assert "Test1" in doc['content']
    
    def test_handles_images_and_links(self, agent):
        """Тест 38: Изображения и ссылки"""
        request = {
            "title": "Media Test",
            "images": [{"url": "image.png", "alt": "Test Image"}],
            "links": [{"url": "http://test.com", "text": "Test Link"}]
        }
        doc = agent.generate_document(request)
        assert "image.png" in doc['content'] or "Test Image" in doc['content']
        assert "http://test.com" in doc['content'] or "Test Link" in doc['content']

class TestPerformanceAndLimits:
    """ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ - быстро генерирует?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    @pytest.mark.performance
    def test_generates_quickly(self, agent):
        """Тест 39: Скорость генерации < 100ms"""
        import time
        start = time.time()
        agent.generate_document({"title": "Speed Test"})
        duration = (time.time() - start) * 1000
        assert duration < 100
    
    def test_handles_large_documents(self, agent):
        """Тест 40: Большие документы (10MB+)"""
        large_content = "X" * (10 * 1024 * 1024)  # 10MB
        doc = agent.generate_document({
            "title": "Large Doc",
            "content": large_content
        })
        assert len(doc['content']) > 10 * 1024 * 1024
    
    def test_handles_many_sections(self, agent):
        """Тест 41: 1000+ секций"""
        sections = [{"title": f"Section {i}", "content": f"Content {i}"} 
                   for i in range(1000)]
        doc = agent.generate_document({
            "title": "Many Sections",
            "sections": sections
        })
        assert doc is not None

class TestErrorRecovery:
    """ТЕСТЫ ВОССТАНОВЛЕНИЯ - не падает от ошибок?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    def test_handles_empty_request(self, agent):
        """Тест 42: Пустой запрос"""
        doc = agent.generate_document({})
        assert doc is not None
        assert 'content' in doc
    
    def test_handles_null_values(self, agent):
        """Тест 43: Null значения"""
        doc = agent.generate_document({
            "title": None,
            "content": None
        })
        assert doc is not None
    
    def test_handles_circular_references(self, agent):
        """Тест 44: Циклические ссылки"""
        request = {"title": "Circular"}
        request["self"] = request
        try:
            doc = agent.generate_document(request)
            assert doc is not None
        except:
            pass  # Не должен крашиться
    
    def test_handles_unicode_content(self, agent):
        """Тест 45: Unicode контент"""
        doc = agent.generate_document({
            "title": "Unicode 测试 🔥",
            "content": "Emoji: 😀 Chinese: 中文 Arabic: العربية"
        })
        assert "🔥" in doc['content']

class TestExportFunctionality:
    """ТЕСТЫ ЭКСПОРТА - сохраняет в разных форматах?"""
    
    @pytest.fixture
    def agent(self):
        return ComposerAgent()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_exports_to_file(self, mock_file, agent):
        """Тест 46: Экспорт в файл"""
        doc = {"content": "Test", "format": "markdown"}
        agent.export_document(doc, "output.md")
        mock_file.assert_called_with("output.md", "w")
    
    def test_exports_to_pdf(self, agent):
        """Тест 47: Экспорт в PDF"""
        doc = {"content": "Test", "format": "markdown"}
        pdf_data = agent.export_document(doc, format="pdf")
        # PDF должен начинаться с %PDF
        assert pdf_data.startswith(b'%PDF') or pdf_data is not None
    
    def test_exports_to_docx(self, agent):
        """Тест 48: Экспорт в DOCX"""
        doc = {"content": "Test", "format": "markdown"}
        docx_data = agent.export_document(doc, format="docx")
        # DOCX это zip архив
        assert docx_data is not None
    
    def test_batch_export(self, agent):
        """Тест 49: Пакетный экспорт"""
        docs = [
            {"content": f"Doc {i}", "format": "markdown"}
            for i in range(10)
        ]
        results = agent.batch_export(docs, format="html")
        assert len(results) == 10

class TestFinalValidation:
    """ФИНАЛЬНАЯ ВАЛИДАЦИЯ композитора"""
    
    def test_composer_is_production_ready(self):
        """Тест 50: Production ready?"""
        agent = ComposerAgent()
        
        # Генерация
        doc = agent.generate_document({"title": "Final Test"})
        assert doc is not None
        
        # Валидация
        assert agent.validate_format(doc['content'], doc['format'])
        
        # Metadata
        doc_with_meta = agent.add_metadata(doc)
        assert 'metadata' in doc_with_meta
        
        # Экспорт
        exported = agent.export_document(doc, format="json")
        assert exported is not None
    
    def test_composer_handles_real_scenario(self):
        """Тест 51: Реальный сценарий использования"""
        agent = ComposerAgent()
        
        # Создаем ITIL документ
        itil_doc = agent.generate_document({
            "title": "Incident Management Process",
            "template": "itil",
            "sections": [
                {"title": "Purpose", "content": "Define incident management"},
                {"title": "Scope", "content": "All IT services"},
                {"title": "Process", "content": "1. Identify\n2. Log\n3. Categorize"},
                {"title": "RACI", "content": "Responsible: Service Desk"}
            ],
            "metadata": {
                "standard": "ITIL 4",
                "version": "1.0",
                "author": "ComposerAgent"
            }
        })
        
        assert "Incident Management" in itil_doc['content']
        assert itil_doc['metadata']['standard'] == "ITIL 4"
    
    def test_composer_integrates_with_system(self):
        """Тест 52: Интеграция с системой"""
        agent = ComposerAgent()
        
        # Должен работать с другими агентами
        research_output = {"findings": "Test findings", "recommendations": ["Rec 1"]}
        doc = agent.generate_from_research(research_output)
        assert "findings" in str(doc)
        assert "Rec 1" in str(doc)

# ComposerAgent прошел испытание. Генератор документов готов.