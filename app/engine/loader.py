 #Имя файла: loader.py
# Путь: app/engine/logger.py
# Кодовое название: ModuleManager
# Версия: 0.3.5

import logging
import json
from pathlib import Path
from typing import List, Set, Dict, Any

# Настройка логгера для модуля загрузки
logger = logging.getLogger(__name__)

class ModuleManager:
    """
    Отвечает за поиск, индексацию, кэширование и проверку существования 
    XML-модулей в файловой системе, а также управление индексом modules.inf.
    """

    def __init__(self, base_dir: str = "modules", index_file: str = "modules.inf"):
        """
        Инициализация загрузчика.
        :param base_dir: Путь к директории с XML-модулями.
        :param index_file: Имя файла индекса метаданных.
        """
        self._base_dir = Path(base_dir).resolve()
        self._index_path = self._base_dir / index_file
        self._failed_modules: Set[str] = set()
        self._cached_modules: List[str] = []
        
        # Создаем директорию, если она отсутствует (согласно Архитектурному дневнику)
        if not self._base_dir.exists():
            logger.info(f"Директория модулей не найдена. Создаю: {self._base_dir}")
            self._base_dir.mkdir(parents=True)
            
        # Пытаемся загрузить кэш из индекса при старте
        self._load_index()

    def _load_index(self) -> None:
        """Загружает список модулей из индексного файла в память."""
        if self._index_path.exists():
            try:
                with open(self._index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cached_modules = data.get("modules", [])
                logger.debug(f"Индекс загружен. Модулей в кэше: {len(self._cached_modules)}")
            except Exception as e:
                logger.warning(f"Не удалось прочитать индекс {self._index_path}: {e}")
                self._cached_modules = []

    def _save_index(self, modules_list: List[str]) -> None:
        """Сохраняет список модулей в индексный файл."""
        try:
            with open(self._index_path, 'w', encoding='utf-8') as f:
                json.dump({"modules": modules_list}, f, ensure_ascii=False, indent=4)
            logger.debug(f"Индекс успешно обновлен: {self._index_path}")
        except Exception as e:
            logger.error(f"Ошибка при записи индекса {self._index_path}: {e}")

    def get_module_path(self, module_name: str) -> Path:
        """
        Возвращает безопасный путь к файлу модуля.
        Проверяет наличие файла и защищает от Path Traversal.
        """
        logger.debug(f"Запрос пути для модуля: {module_name}")
        
        # Формируем целевой путь
        module_file = (self._base_dir / f"{module_name}.xml").resolve()
        
        # Проверка безопасности: файл должен находиться внутри базовой директории
        if self._base_dir not in module_file.parents:
            logger.error(f"Попытка доступа вне разрешенной директории: {module_name}")
            raise PermissionError("Доступ к файлу запрещен параметрами безопасности")

        if not module_file.exists():
            logger.warning(f"Файл модуля {module_name} не найден на диске")
            raise FileNotFoundError(f"Модуль '{module_name}' не существует")

        return module_file

    def discover_modules(self) -> List[str]:
        """
        Сканирует директорию, обновляет кэш в памяти и файл modules.inf.
        Возвращает список имен найденных XML-файлов.
        """
        logger.debug("Начало сканирования директории модулей")
        valid_modules = []
        
        try:
            for file in self._base_dir.glob("*.xml"):
                logger.debug(f"Обнаружен файл: {file.name}")
                valid_modules.append(file.stem)
            
            # Обновляем кэш и сохраняем индекс
            self._cached_modules = sorted(valid_modules)
            self._save_index(self._cached_modules)
            
            logger.info(f"Сканирование завершено. Найдено модулей: {len(self._cached_modules)}")
            return self._cached_modules
            
        except Exception as e:
            logger.error(f"Ошибка при сканировании директории {self._base_dir}: {e}")
            return self._cached_modules # Возвращаем старый кэш при ошибке

    def get_available_modules(self) -> List[str]:
        """Возвращает список модулей из кэша памяти без обращения к диску."""
        if not self._cached_modules:
            return self.discover_modules()
        return self._cached_modules

    def get_failed_modules(self) -> Set[str]:
        """Возвращает список модулей, которые не прошли проверку при загрузке."""
        return self._failed_modules