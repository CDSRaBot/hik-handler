# Имя файла: settings.py
# Путь: app/configuration/settings.py
# Кодовое название: ConfigurationManager
# Версия: 0.3.6

import logging
import tomllib
from pathlib import Path
from typing import Optional, Dict, Any

# Импорт защищенного контекста (предполагается наличие датакласса в security.py)
from app.configuration.security import SecureContext 

# Инициализация логгера уровня модуля (PEP 8, иерархическое логирование)
logger = logging.getLogger(f"hik_handler.{__name__}")


class ConfigManager:
    """
    Класс для управления конфигурацией системы.
    Отвечает за чтение TOML файла и безопасную отдачу параметров.
    """

    def __init__(self, config_path: str = "config.toml"):
        """
        Инициализирует менеджер конфигураций.
        
        :param config_path: Путь к конфигурационному файлу TOML.
        """
        self._config_path: Path = Path(config_path)
        self._config_data: Dict[str, Any] = {}
        
        # Логируем начало инициализации
        logger.debug(f"Инициализация ConfigManager с файлом: {self._config_path.resolve()}")
        self._load_config()

    def _load_config(self) -> None:
        """
        Приватный метод. Читает TOML файл и сохраняет данные в память.
        """
        logger.debug(f"Попытка чтения конфигурации из {self._config_path}")
        try:
            if self._config_path.exists():
                with open(self._config_path, "rb") as f:
                    self._config_data = tomllib.load(f)
                logger.info("Конфигурационный файл успешно загружен.")
            else:
                logger.warning(f"Файл {self._config_path} не найден. Используются значения по умолчанию.")
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            self._config_data = {}

    @property
    def data(self) -> Dict[str, Any]:
        """
        Возвращает все данные конфигурации.
        Необходимо для инициализации внешних систем (например, логгера).
        
        :return: Словарь с данными конфигурации.
        """
        logger.debug("Запрос полного словаря конфигурации")
        return self._config_data

    def get_secure_context(self) -> SecureContext:
        """
        Создает и возвращает объект SecureContext.
        Пароль и учетные данные не передаются наружу в виде словарей.
        Таймаут инкапсулирован непосредственно в контекст подключения.
        
        :return: Экземпляр SecureContext с учетными данными.
        """
        logger.debug("Запрос на получение SecureContext")
        network_cfg = self._config_data.get("network", {})
        
        # Загрузка базовых значений из файла конфигурации
        context = SecureContext(
            host=network_cfg.get("host", "192.168.1.64"),
            user=network_cfg.get("user", "admin"),
            password=network_cfg.get("password", ""),
            timeout=network_cfg.get("timeout", 10)
        )
        logger.info("SecureContext успешно сформирован и передан ядру.")
        return context

    @property
    def data(self) -> Dict[str, Any]:
        """
        Returns raw configuration data for infrastructure components (like Logger).
        """
        return self._config_data
        
    @property
    def modules_path(self) -> Path:
        """
        Возвращает путь к директории с модулями.
        
        :return: Объект Path, указывающий на директорию модулей.
        """
        logger.debug("Запрос пути к директории модулей")
        path_str = self._config_data.get("paths", {}).get("modules_dir", "modules")
        return Path(path_str).resolve()

    @property
    def schema_path(self) -> Path:
        """
        Возвращает путь к директории с XSD схемами.
        
        :return: Объект Path, указывающий на директорию схем.
        """
        logger.debug("Запрос пути к директории схем")
        path_str = self._config_data.get("paths", {}).get("validation_schema") #, "schema")
        return Path(path_str).resolve()