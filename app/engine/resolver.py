"""
Имя файла: resolver.py
Путь: app/engine/resolver.py
Кодовое название: ArgumentResolver
Версия: v.0.3.6.0

Модуль для разрешения (подстановки) аргументов в строковых шаблонах.
Использует стандартный класс string.Template для обеспечения безопасности
и минимизации использования регулярных выражений.
"""
import logging
from string import Template
from typing import Any, Dict


# Инициализируем логгер для модуля
logger = logging.getLogger(__name__)


class ArgumentResolver:
    """
    Класс для обработки динамических параметров в XML и URL.
    """

    def resolve(self, template: str, arguments: Dict[str, Any]) -> str:
        """
        Заменяет все вхождения ${key} на значения из словаря arguments.

        Args:
            template: Строка с шаблонами (например, "/ISAPI/Proxy/channels/${id}").
            arguments: Словарь с фактическими значениями.

        Returns:
            Строка с подставленными значениями.

        Raises:
            KeyError: Если в шаблоне указана переменная, отсутствующая в словаре.
        """
        # Логируем начало процедуры в режиме DEBUG
        logger.debug("Starting argument resolution for template")
        
        # Создаем объект шаблона из входящей строки
        # string.Template использует синтаксис ${var} по умолчанию
        templ = Template(template)
        
        try:
            # Выполняем подстановку параметров
            # substitute выбрасывает KeyError, если в словаре нет нужного ключа
            result = templ.substitute(arguments)
            
            # Информируем об успешном завершении процедуры
            logger.info("Arguments resolved successfully")
            return result
            
        except KeyError as e:
            # Извлекаем имя отсутствующего ключа для информативности
            missing_key = e.args[0]
            error_msg = f"Ошибка резолвера: Аргумент '{missing_key}' отсутствует в данных"
            
            # Логируем критическую ошибку подстановки
            logger.error(error_msg)
            # Согласно PEP 20, ошибки никогда не должны проходить молча
            raise KeyError(error_msg) from e
        except Exception as e:
            # Обработка непредвиденных исключений
            logger.error(f"Unexpected error during resolution: {e}")
            raise