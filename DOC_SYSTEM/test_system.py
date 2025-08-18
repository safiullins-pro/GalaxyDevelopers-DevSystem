#!/usr/bin/env python3

import sys
from pathlib import Path
import json

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.file_monitor import FileMonitor
from analyzers.dependency_analyzer import DependencyAnalyzer
from generators.doc_generator import DocumentationGenerator
from validators.validation_agent import ValidationAgent

def test_system():
    """Test all system components"""
    
    print("🚀 Тестирование системы GalaxyDevSystem AutoDoc")
    print("=" * 50)
    
    # Test 1: File Monitor
    print("\n📁 Тестируем File Monitor...")
    try:
        monitor = FileMonitor()
        metadata = monitor.scan_directory()
        print(f"✅ File Monitor: Найдено {len(metadata)} файлов")
        
        # Show some examples
        if metadata:
            first_file = list(metadata.keys())[0]
            print(f"   Пример файла: {first_file}")
            print(f"   Размер: {metadata[first_file].get('size', 0)} байт")
    except Exception as e:
        print(f"❌ File Monitor ошибка: {e}")
    
    # Test 2: Dependency Analyzer
    print("\n🔗 Тестируем Dependency Analyzer...")
    try:
        analyzer = DependencyAnalyzer()
        analyzer.build_dependency_graph()
        
        stats = {
            'total_files': len(analyzer.file_dependencies),
            'orphaned_files': len(analyzer.orphaned_files),
            'circular_deps': len(analyzer.circular_dependencies)
        }
        
        print(f"✅ Dependency Analyzer:")
        print(f"   Всего файлов: {stats['total_files']}")
        print(f"   Orphaned файлов: {stats['orphaned_files']}")
        print(f"   Циклических зависимостей: {stats['circular_deps']}")
        
        if analyzer.orphaned_files:
            print(f"   Примеры orphaned: {list(analyzer.orphaned_files)[:3]}")
            
    except Exception as e:
        print(f"❌ Dependency Analyzer ошибка: {e}")
    
    # Test 3: Documentation Generator
    print("\n📚 Тестируем Documentation Generator...")
    try:
        doc_gen = DocumentationGenerator()
        
        # Test on this file
        test_file = Path(__file__)
        doc_data = doc_gen.generate_file_documentation(test_file)
        
        print(f"✅ Documentation Generator:")
        print(f"   Файл: {doc_data['file_name']}")
        print(f"   Строк кода: {doc_data['content_analysis']['lines_of_code']}")
        print(f"   Функций: {len(doc_data['content_analysis']['functions'])}")
        print(f"   Теги: {', '.join(doc_data['tags'])}")
        
    except Exception as e:
        print(f"❌ Documentation Generator ошибка: {e}")
    
    # Test 4: Validation Agent
    print("\n✅ Тестируем Validation Agent...")
    try:
        validator = ValidationAgent()
        
        # Test on this file
        results = validator.validate_file(Path(__file__))
        
        passed = sum(1 for r in results if r.get('passed', True))
        failed = len(results) - passed
        
        print(f"✅ Validation Agent:")
        print(f"   Проверок пройдено: {passed}")
        print(f"   Проверок провалено: {failed}")
        
        if failed > 0:
            for result in results:
                if not result.get('passed', True):
                    print(f"   ⚠️  {result['rule']}: {result['message']}")
                    
    except Exception as e:
        print(f"❌ Validation Agent ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Тестирование завершено!")

if __name__ == "__main__":
    test_system()