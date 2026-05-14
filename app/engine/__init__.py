"""
Имя файла: __init__.py
Путь: /app/engine/__init__.py
Кодовое название: ENGINE_INIT
Версия: v.1.0.0
"""

from .orchestrator import Orchestrator
from .loader import ModuleManager
from .validator import XMLValidator
from .resolver import ArgumentResolver
from .logger import setup_logger
from .exporter import XMLExporter

# Экспорт ключевых компонентов ядра системы
__all__ = [
    "Orchestrator",
    "ModuleManager",
    "XMLValidator",
    "ArgumentResolver",
    "setup_logger",
    "XMLExporter"
]
