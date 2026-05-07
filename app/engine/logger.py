# Имя файла: logger.py
# Путь: app/engine/logger.py
# Кодовое название: LogManager
# Версия: 0.3.6

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any

def setup_logger(config: Any) -> logging.Logger:
    """
    Инициализирует и настраивает логгер hik_handler.
    
    Аргументы:
        config (Any): Объект конфигурации, содержащий атрибут data.
        
    Возвращает:
        logging.Logger: Настроенный объект логгера (Singleton).
    """
    # Безопасное извлечение данных конфигурации
    config_data = getattr(config, "data", {}) if config else {}
    log_settings = config_data.get("logging", {})
    
    # Определение пути к логам из config [paths][log_dir]
    log_dir = config_data.get("paths", {}).get("log_dir", "logs")
    log_dir_path = Path(log_dir)
    
    # Создание директории логов, если она отсутствует
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Получение экземпляра логгера
    logger = logging.getLogger("hik_handler")
    
    # Установка уровня логирования (по умолчанию INFO)
    log_level = log_settings.get("level", "INFO").upper()
    logger.setLevel(log_level)

    # Настройка формата сообщений
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Путь к файлу лога
    log_file = log_dir_path / "hik-handler.log"
    
    # Настройка ротации файлов (параметры из config.toml)
    # max_size_mb конвертируется в байты для RotatingFileHandler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_settings.get("max_size_mb", 5) * 1024 * 1024,
        backupCount=log_settings.get("backup_count", 3),
        encoding='utf-8'
    )
    handler.setFormatter(formatter)
    
    # Защита от дублирования обработчиков
    if not logger.handlers:
        logger.addHandler(handler)
        # Информационное логирование старта
        logger.info("Система логирования инициализирована")
        # Детальное логирование параметров в режиме DEBUG
        logger.debug(
            f"Файл: {log_file}, Уровень: {log_level}, "
            f"Ротация: {log_settings.get('max_size_mb')}MB"
        )

    return logger