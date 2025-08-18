#!/usr/bin/env python3
"""
🔧 ERROR PIPELINE - Автоматическая обработка ошибок
Анализирует, исправляет и документирует ошибки
by FORGE-2267
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from enum import Enum
from dataclasses import dataclass

from workflow_orchestrator import get_orchestrator
from unified_agent_registry import get_registry, AgentCapability
from context_manager import get_context_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ERROR_PIPELINE')


class ErrorType(Enum):
    """Типы ошибок"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    IMPORT = "import"
    TYPE = "type"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Серьёзность ошибок"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ErrorContext:
    """Контекст ошибки"""
    type: ErrorType
    severity: ErrorSeverity
    file_path: Optional[str]
    line_number: Optional[int]
    error_message: str
    stack_trace: Optional[str]
    timestamp: datetime
    source_system: str
    additional_info: Dict[str, Any]


@dataclass
class ErrorFix:
    """Предложение по исправлению"""
    fix_type: str  # 'code', 'config', 'dependency', 'documentation'
    description: str
    code_changes: Optional[Dict[str, str]]  # old -> new
    file_patches: Optional[List[Dict[str, Any]]]
    confidence: float  # 0.0 - 1.0
    estimated_impact: str
    rollback_plan: Optional[Dict[str, Any]]


class ErrorPipeline:
    """Pipeline обработки ошибок"""
    
    def __init__(self):
        self.orchestrator = None
        self.registry = None
        self.context_manager = None
        
        # История ошибок для обучения
        self.error_history: List[ErrorContext] = []
        self.fix_history: List[Tuple[ErrorContext, ErrorFix, bool]] = []
        
        # Паттерны ошибок
        self.error_patterns = self._init_error_patterns()
        
        logger.info("🔧 Error Pipeline initialized")
    
    async def initialize(self):
        """Инициализация pipeline"""
        self.orchestrator = await get_orchestrator()
        self.registry = await get_registry()
        self.context_manager = get_context_manager()
        
        logger.info("✅ Error Pipeline ready")
    
    def _init_error_patterns(self) -> Dict[ErrorType, List[re.Pattern]]:
        """Инициализация паттернов для определения типов ошибок"""
        return {
            ErrorType.SYNTAX: [
                re.compile(r"SyntaxError:"),
                re.compile(r"unexpected EOF"),
                re.compile(r"invalid syntax"),
                re.compile(r"unexpected indent")
            ],
            ErrorType.IMPORT: [
                re.compile(r"ImportError:"),
                re.compile(r"ModuleNotFoundError:"),
                re.compile(r"cannot import name"),
                re.compile(r"No module named")
            ],
            ErrorType.TYPE: [
                re.compile(r"TypeError:"),
                re.compile(r"AttributeError:"),
                re.compile(r"object has no attribute"),
                re.compile(r"not subscriptable")
            ],
            ErrorType.RUNTIME: [
                re.compile(r"RuntimeError:"),
                re.compile(r"ValueError:"),
                re.compile(r"KeyError:"),
                re.compile(r"IndexError:")
            ],
            ErrorType.SECURITY: [
                re.compile(r"SecurityError:"),
                re.compile(r"PermissionError:"),
                re.compile(r"sql injection", re.I),
                re.compile(r"XSS vulnerability", re.I)
            ],
            ErrorType.PERFORMANCE: [
                re.compile(r"TimeoutError:"),
                re.compile(r"MemoryError:"),
                re.compile(r"maximum recursion depth"),
                re.compile(r"performance degradation", re.I)
            ]
        }
    
    async def process_error(
        self,
        error_data: Dict[str, Any],
        auto_fix: bool = True
    ) -> Dict[str, Any]:
        """Обработка ошибки"""
        logger.info(f"🔍 Processing error: {error_data.get('type', 'unknown')}")
        
        # Создаём контекст ошибки
        error_context = self._create_error_context(error_data)
        
        # Сохраняем в историю
        self.error_history.append(error_context)
        
        # Создаём memory snapshot
        snapshot = self.context_manager.create_memory_snapshot(
            f"error_{error_context.type.value}",
            f"severity_{error_context.severity.value}"
        )
        
        # Анализируем ошибку
        analysis = await self._analyze_error(error_context)
        
        # Ищем похожие исправления в истории
        similar_fixes = self._find_similar_fixes(error_context)
        
        # Генерируем исправление
        fix = await self._generate_fix(error_context, analysis, similar_fixes)
        
        # Применяем исправление если auto_fix
        if auto_fix and fix.confidence > 0.7:
            success = await self._apply_fix(error_context, fix)
        else:
            success = False
            logger.info(f"Auto-fix disabled or low confidence ({fix.confidence})")
        
        # Сохраняем в историю
        self.fix_history.append((error_context, fix, success))
        
        # Обновляем документацию
        if success:
            await self._update_documentation(error_context, fix)
        
        # Возвращаем результат
        return {
            'error_context': self._error_context_to_dict(error_context),
            'analysis': analysis,
            'fix': self._fix_to_dict(fix),
            'applied': success,
            'snapshot_id': snapshot['id']
        }
    
    def _create_error_context(self, error_data: Dict[str, Any]) -> ErrorContext:
        """Создание контекста ошибки из данных"""
        # Определяем тип ошибки
        error_type = self._detect_error_type(error_data.get('message', ''))
        
        # Определяем серьёзность
        severity = self._assess_severity(error_type, error_data)
        
        # Извлекаем путь и номер строки
        file_path, line_number = self._extract_location(error_data)
        
        return ErrorContext(
            type=error_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            error_message=error_data.get('message', 'Unknown error'),
            stack_trace=error_data.get('stack_trace'),
            timestamp=datetime.now(),
            source_system=error_data.get('source', 'unknown'),
            additional_info=error_data.get('additional_info', {})
        )
    
    def _detect_error_type(self, error_message: str) -> ErrorType:
        """Определение типа ошибки по сообщению"""
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.search(error_message):
                    return error_type
        return ErrorType.UNKNOWN
    
    def _assess_severity(
        self,
        error_type: ErrorType,
        error_data: Dict[str, Any]
    ) -> ErrorSeverity:
        """Оценка серьёзности ошибки"""
        # Критические типы
        if error_type in [ErrorType.SECURITY, ErrorType.RUNTIME]:
            return ErrorSeverity.CRITICAL
        
        # Проверяем ключевые слова
        message = error_data.get('message', '').lower()
        if any(word in message for word in ['critical', 'fatal', 'emergency']):
            return ErrorSeverity.CRITICAL
        elif any(word in message for word in ['high', 'important', 'major']):
            return ErrorSeverity.HIGH
        elif any(word in message for word in ['medium', 'moderate', 'warning']):
            return ErrorSeverity.MEDIUM
        elif any(word in message for word in ['low', 'minor', 'info']):
            return ErrorSeverity.LOW
        
        # По умолчанию
        return ErrorSeverity.MEDIUM
    
    def _extract_location(
        self,
        error_data: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[int]]:
        """Извлечение пути к файлу и номера строки"""
        file_path = error_data.get('file_path')
        line_number = error_data.get('line_number')
        
        # Пробуем извлечь из stack trace
        if not file_path and error_data.get('stack_trace'):
            match = re.search(
                r'File "([^"]+)", line (\d+)',
                error_data['stack_trace']
            )
            if match:
                file_path = match.group(1)
                line_number = int(match.group(2))
        
        return file_path, line_number
    
    async def _analyze_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Анализ ошибки через агентов"""
        # Запускаем анализ через ResearchAgent
        result = await self.registry.execute_task(
            AgentCapability.ANALYZE,
            {
                'type': 'analyze',
                'error_type': error_context.type.value,
                'error_message': error_context.error_message,
                'file_path': error_context.file_path,
                'line_number': error_context.line_number,
                'stack_trace': error_context.stack_trace
            }
        )
        
        if result['success']:
            return result['result']
        
        # Fallback анализ
        return {
            'cause': 'Unable to determine exact cause',
            'impact': 'Unknown impact',
            'suggestions': ['Manual review required']
        }
    
    def _find_similar_fixes(self, error_context: ErrorContext) -> List[ErrorFix]:
        """Поиск похожих исправлений в истории"""
        similar_fixes = []
        
        for past_error, past_fix, success in self.fix_history:
            if not success:
                continue
            
            # Сравниваем типы ошибок
            if past_error.type == error_context.type:
                similarity = self._calculate_similarity(past_error, error_context)
                if similarity > 0.7:
                    similar_fixes.append(past_fix)
        
        return similar_fixes[:3]  # Топ-3 похожих исправления
    
    def _calculate_similarity(
        self,
        error1: ErrorContext,
        error2: ErrorContext
    ) -> float:
        """Расчёт похожести двух ошибок"""
        score = 0.0
        
        # Тип ошибки
        if error1.type == error2.type:
            score += 0.3
        
        # Файл
        if error1.file_path == error2.file_path:
            score += 0.2
        
        # Похожесть сообщений
        if error1.error_message and error2.error_message:
            # Простое сравнение по словам
            words1 = set(error1.error_message.lower().split())
            words2 = set(error2.error_message.lower().split())
            if words1 and words2:
                jaccard = len(words1 & words2) / len(words1 | words2)
                score += 0.5 * jaccard
        
        return min(score, 1.0)
    
    async def _generate_fix(
        self,
        error_context: ErrorContext,
        analysis: Dict[str, Any],
        similar_fixes: List[ErrorFix]
    ) -> ErrorFix:
        """Генерация исправления"""
        # Используем ComposerAgent для генерации fix
        result = await self.registry.execute_task(
            AgentCapability.COMPOSE,
            {
                'type': 'compose',
                'template': 'error_fix',
                'error_context': self._error_context_to_dict(error_context),
                'analysis': analysis,
                'similar_fixes': [self._fix_to_dict(f) for f in similar_fixes]
            }
        )
        
        if result['success'] and 'fix' in result['result']:
            fix_data = result['result']['fix']
            return ErrorFix(
                fix_type=fix_data.get('type', 'code'),
                description=fix_data.get('description', 'Generated fix'),
                code_changes=fix_data.get('code_changes'),
                file_patches=fix_data.get('file_patches'),
                confidence=fix_data.get('confidence', 0.5),
                estimated_impact=fix_data.get('impact', 'unknown'),
                rollback_plan=fix_data.get('rollback_plan')
            )
        
        # Fallback fix
        return ErrorFix(
            fix_type='manual',
            description='Manual intervention required',
            code_changes=None,
            file_patches=None,
            confidence=0.0,
            estimated_impact='unknown',
            rollback_plan=None
        )
    
    async def _apply_fix(
        self,
        error_context: ErrorContext,
        fix: ErrorFix
    ) -> bool:
        """Применение исправления"""
        logger.info(f"🔨 Applying fix: {fix.description}")
        
        try:
            if fix.fix_type == 'code' and fix.file_patches:
                # Применяем патчи к файлам
                for patch in fix.file_patches:
                    file_path = Path(patch['file'])
                    if file_path.exists():
                        # Создаём backup
                        backup_path = file_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                        file_path.rename(backup_path)
                        
                        # Применяем изменения
                        with open(file_path, 'w') as f:
                            f.write(patch['content'])
                        
                        logger.info(f"✅ Patched {file_path}")
            
            elif fix.fix_type == 'config' and fix.code_changes:
                # Обновляем конфигурации
                for config_key, new_value in fix.code_changes.items():
                    logger.info(f"Config update: {config_key} = {new_value}")
            
            # Проверяем через ReviewAgent
            review_result = await self.registry.execute_task(
                AgentCapability.REVIEW,
                {
                    'type': 'review',
                    'fix_applied': True,
                    'error_context': self._error_context_to_dict(error_context),
                    'fix': self._fix_to_dict(fix)
                }
            )
            
            if review_result['success']:
                logger.info("✅ Fix applied and validated")
                return True
            else:
                logger.warning("Fix applied but validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            
            # Пробуем rollback
            if fix.rollback_plan:
                await self._execute_rollback(fix.rollback_plan)
            
            return False
    
    async def _execute_rollback(self, rollback_plan: Dict[str, Any]):
        """Выполнение отката изменений"""
        logger.info("🔄 Executing rollback")
        
        try:
            if 'restore_files' in rollback_plan:
                for file_info in rollback_plan['restore_files']:
                    backup_path = Path(file_info['backup'])
                    original_path = Path(file_info['original'])
                    
                    if backup_path.exists():
                        original_path.unlink(missing_ok=True)
                        backup_path.rename(original_path)
                        logger.info(f"Restored {original_path}")
            
            logger.info("✅ Rollback completed")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    async def _update_documentation(
        self,
        error_context: ErrorContext,
        fix: ErrorFix
    ):
        """Обновление документации после исправления"""
        # Создаём запись об ошибке и исправлении
        doc_content = f"""
## Error Fix Report

**Date:** {error_context.timestamp.isoformat()}
**Error Type:** {error_context.type.value}
**Severity:** {error_context.severity.value}

### Error Details
- **Message:** {error_context.error_message}
- **File:** {error_context.file_path}
- **Line:** {error_context.line_number}

### Fix Applied
- **Type:** {fix.fix_type}
- **Description:** {fix.description}
- **Confidence:** {fix.confidence}
- **Impact:** {fix.estimated_impact}

### Lessons Learned
This error was automatically detected and fixed by the Error Pipeline.
"""
        
        # Используем PublisherAgent для сохранения
        await self.registry.execute_task(
            AgentCapability.PUBLISH,
            {
                'type': 'publish',
                'content': doc_content,
                'filename': f"error_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                'channels': ['local', 'git']
            }
        )
    
    def _error_context_to_dict(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Конвертация ErrorContext в словарь"""
        return {
            'type': error_context.type.value,
            'severity': error_context.severity.value,
            'file_path': error_context.file_path,
            'line_number': error_context.line_number,
            'error_message': error_context.error_message,
            'stack_trace': error_context.stack_trace,
            'timestamp': error_context.timestamp.isoformat(),
            'source_system': error_context.source_system,
            'additional_info': error_context.additional_info
        }
    
    def _fix_to_dict(self, fix: ErrorFix) -> Dict[str, Any]:
        """Конвертация ErrorFix в словарь"""
        return {
            'fix_type': fix.fix_type,
            'description': fix.description,
            'code_changes': fix.code_changes,
            'file_patches': fix.file_patches,
            'confidence': fix.confidence,
            'estimated_impact': fix.estimated_impact,
            'rollback_plan': fix.rollback_plan
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        total_errors = len(self.error_history)
        total_fixes = len(self.fix_history)
        successful_fixes = sum(1 for _, _, success in self.fix_history if success)
        
        error_by_type = {}
        for error in self.error_history:
            error_by_type[error.type.value] = error_by_type.get(error.type.value, 0) + 1
        
        error_by_severity = {}
        for error in self.error_history:
            error_by_severity[error.severity.value] = error_by_severity.get(error.severity.value, 0) + 1
        
        return {
            'total_errors': total_errors,
            'total_fixes': total_fixes,
            'successful_fixes': successful_fixes,
            'fix_success_rate': successful_fixes / total_fixes if total_fixes > 0 else 0,
            'errors_by_type': error_by_type,
            'errors_by_severity': error_by_severity
        }


# Глобальный error pipeline
error_pipeline = None


async def get_error_pipeline() -> ErrorPipeline:
    """Получить глобальный error pipeline"""
    global error_pipeline
    if error_pipeline is None:
        error_pipeline = ErrorPipeline()
        await error_pipeline.initialize()
    return error_pipeline


if __name__ == '__main__':
    async def test():
        """Тестирование error pipeline"""
        pipeline = await get_error_pipeline()
        
        # Тестовая ошибка
        test_error = {
            'type': 'syntax_error',
            'message': 'SyntaxError: unexpected EOF while parsing',
            'file_path': '/test/file.py',
            'line_number': 42,
            'stack_trace': 'File "/test/file.py", line 42\n    def test(\n           ^\nSyntaxError: unexpected EOF while parsing',
            'source': 'galaxy_monitoring'
        }
        
        # Обрабатываем ошибку
        result = await pipeline.process_error(test_error, auto_fix=False)
        
        print(json.dumps(result, indent=2))
        
        # Статистика
        stats = pipeline.get_error_statistics()
        print(f"\nError Statistics: {json.dumps(stats, indent=2)}")
    
    asyncio.run(test())