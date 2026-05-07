# settings.py
# Кодовое название: ConfigurationManager
# Версия: 0.3.4.0

import logging
import tomllib
from pathlib import Path
from typing import Any

class ConfigManager:
    """Менеджер конфигураций для безопасной загрузки и парсинга TOML-файла."""

    def __init__(self, config_file: str = "config.toml") -> None:
        """Инициализация менеджера с привязкой к абсолютному пути."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Инициализация ConfigManager: старт")
        
        # Надежное определение пути: корень проекта находится на 2 уровня выше app/configuration
        self.config_path = Path(__file__).resolve().parents[2] / config_file
        
        self.data: dict[str, Any] = self._load()
        self._logger.info("Конфигурация успешно загружена")

    def _load(self) -> dict[str, Any]:
        """Безопасная загрузка данных из TOML-файла."""
        if not self.config_path.exists():
            self._logger.error(f"Файл конфигурации не найден: {self.config_path}")
            raise FileNotFoundError(f"Конфигурация {self.config_path} не найдена.")
            
        self._logger.debug("Открытие дескриптора файла конфигурации")
        with self.config_path.open("rb") as f:
            return tomllib.load(f)

    @property
    def modules_path(self) -> Path:
        """Возвращает абсолютный путь к директории с модулями."""
        path_str = self.data.get("paths", {}).get("modules", "modules")
        return (self.config_path.parent.parent / path_str).resolve()

    @property
    def schema_path(self) -> Path:
        """Возвращает абсолютный путь к XSD схеме валидации."""
        path_str = self.data.get("paths", {}).get("schema", "schema/module_schema.xsd")
        return (self.config_path.parent.parent / path_str).resolve()

    def get_timeout(self) -> int:
        """Извлекает таймаут для сетевых запросов."""
        timeout = self.data.get("network", {}).get("timeout", 10)
        self._logger.debug(f"Получен сетевой таймаут: {timeout} сек")
        return timeout
        
    def get_secure_context(self) -> SecureContext:
        """
        Формирует и возвращает защищенный контекст с учетными данными.
        Пароли не логируются и не возвращаются в виде открытых словарей.
        """
        self._logger.info("Запрос на формирование защищенного сетевого контекста")
        network_data = self.data.get("network", {})
        
        # Инкапсуляция данных в датакласс.
        # В реальной среде здесь могут быть механизмы расшифровки
        return SecureContext(
            ip_address=network_data.get("ip", "192.168.1.64"),
            username=network_data.get("login", "admin"),
            password=network_data.get("password", "")
        )