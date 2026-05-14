"""
Имя файла: __init__.py
Путь: /app/communication/__init__.py
Кодовое название: COMM_INIT
Версия: v.1.0.0
"""

from .session import HikvisionClient, HikvisionNetworkError

# Экспорт компонентов транспортного слоя
__all__ = ["HikvisionClient", "HikvisionNetworkError"]

# Примечание: импорты внутри модулей могут использоваться для 
# предотвращения преждевременной инициализации ресурсов.