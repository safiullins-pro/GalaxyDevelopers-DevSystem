#!/usr/bin/env python3

from flask import Flask, jsonify
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_monitor import FileMonitor
from analyzers.dependency_analyzer import DependencyAnalyzer
from validators.validation_agent import ValidationAgent

app = Flask(__name__)

@app.route('/', methods=['GET'])
def docs_status():
    """
    Простой эндпойнт: 0/1 - порядок в документации или нет
    """
    try:
        # Инициализация компонентов
        monitor = FileMonitor()
        analyzer = DependencyAnalyzer()
        validator = ValidationAgent()
        
        # Сканируем проект
        metadata = monitor.scan_directory()
        
        # Строим граф зависимостей
        analyzer.build_dependency_graph()
        
        # Проверяем документацию
        validation_results = validator.validate_project(metadata)
        
        # ЖЕСТКОЕ ПРАВИЛО: 1 файл не задокументирован = статус 0
        
        total_files = len(metadata)
        orphaned_count = len(analyzer.orphaned_files)
        circular_count = len(analyzer.circular_dependencies)
        critical_errors = validation_results.get('critical', 0)
        
        # Проверяем каждый файл на документацию
        undocumented_files = []
        for file_path, results in validation_results['files'].items():
            for result in results:
                if (result.get('rule') == 'require_documentation' and 
                    not result.get('passed', True)):
                    undocumented_files.append(file_path)
                    break
        
        undocumented_count = len(undocumented_files)
        
        # СТАТУС: 0 если ХОТЯ БЫ ОДИН файл не задокументирован
        status = 1 if undocumented_count == 0 else 0
        
        return jsonify({
            "status": status,
            "details": {
                "total_files": total_files,
                "undocumented_files": undocumented_count,
                "orphaned_files": orphaned_count,
                "circular_dependencies": circular_count,
                "critical_errors": critical_errors
            }
        })
        
    except Exception as e:
        # Если что-то сломалось - значит нет порядка
        return jsonify({
            "status": 0,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=37778, debug=False)