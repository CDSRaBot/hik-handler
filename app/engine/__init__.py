"""
Имя файла: __init__.py
Путь: /app/engine/__init__.py
Кодовое название: ENGINE_INIT
Версия: v.0.3.6.0
"""

from .orchestrator import Orchestrator

# Экспортируем только Оркестратор как главный контроллер
__all__ = ["Orchestrator"]
