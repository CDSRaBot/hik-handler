# Имя файла: orchestrator.py
# Путь: app/engine/orchestrator.py - from GIT
# Кодовое название: Orchestrator
# Версия: v.0.3.8.0

import logging
from typing import Any, Dict, List, Optional

# Импорты внутренних компонентов системы
from app.configuration.security import SecureContext
from app.engine.loader import ModuleManager
from app.engine.validator import XMLValidator
from app.engine.resolver import ArgumentResolver
from app.communication.session import HikvisionClient

# Настройка логгера для данного модуля
logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Ядро системы. Координирует работу всех слоев: 
    загрузку, валидацию и выполнение команд.
    """
    
    def __init__(
        self, 
        loader: ModuleManager, 
        validator: XMLValidator,
        resolver: ArgumentResolver,
        client: HikvisionClient,
        base_context: SecureContext
    ):
        """
        Инициализация оркестратора через внедрение зависимостей.
        
        -- loader: Компонент для поиска и загрузки модулей.
        -- validator: Компонент для XSD-валидации XML-команд.
        -- resolver: Компонент для обработки аргументов команд.
        -- client: Сетевой клиент для связи с оборудованием.
        -- base_context: Базовый контекст безопасности из конфигурации.
        """
        logger.debug("Инициализация Orchestrator: старт")
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._version = "0.3.8.0"
        logger.info("Orchestrator успешно инициализирован.")

    @classmethod
    def bootstrap(cls, base_context: SecureContext) -> "Orchestrator":
        """
        Фабричный метод сборки зависимостей (Composition Root).
        Инициализирует все подсистемы и возвращает готовый к работе Оркестратор.
        """
        logger.debug("Вызов фабричного метода bootstrap: сборка компонентов")
        
        loader = ModuleManager()
        validator = XMLValidator()
        resolver = ArgumentResolver()
        client = HikvisionClient()
        
        return cls(
            loader=loader,
            validator=validator,
            resolver=resolver,
            client=client,
            base_context=base_context
        )

    def execute_headless(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str] = None
    ) -> bool:
        """
        Выполняет команду в автоматическом режиме (без интерактивного терминала).
        
        -- module_name: Имя модуля для выполнения.
        -- params: Словарь параметров.
        -- connect_str: Опциональная строка подключения вида user:password@host
        """
        logger.info(f"Headless: запрос модуля '{module_name}'")
        logger.debug(f"Headless параметры: {params}")

        # Парсинг опциональной строки подключения --connect
        if connect_str:
            logger.debug("Парсинг кастомных учетных данных через строковые методы")
            
            # rpartition('@') безопасно отделяет хост, даже если пароль содержит '@'
            credentials, separator, host = connect_str.rpartition('@')
            
            # partition(':') отделяет имя пользователя от пароля по первому двоеточию
            user, colon, password = credentials.partition(':')
            
            # Валидация успешности парсинга всех компонентов
            if not (separator and colon and host and user and password):
                logger.error("Неверный формат флага --connect. Ожидается user:password@host")
                return False
        else:
            host = self._base_context.host
            user = self._base_context.user
            password = self._base_context.password

        # Создаем обновленный контекст для конкретной команды
        context = SecureContext(
            host=host,
            user=user,
            password=password,
            timeout=self._base_context.timeout,
            module_name=module_name,
            params=params
        )

        return self.run_command(context)

    def run_command(self, context: SecureContext) -> bool:
        """
        Основной метод выполнения команды.
        """
        logger.debug(f"Выполнение команды: {context.module_name}")
        
        module_data = self._loader.get_module(context.module_name)
        if not module_data:
            logger.error(f"Модуль {context.module_name} не найден")
            return False

        if not self._validator.validate(module_data):
             logger.error(f"Модуль {context.module_name} не прошел валидацию")
             return False

        payload = self._resolver.resolve(module_data, context.params)
        response = self._client.send(payload, context)
        
        return response is not None

    def discover_modules(self) -> List[str]:
        """
        Сканирует директорию на наличие новых XML-модулей.
        """
        logger.info("Поиск новых модулей в системе...")
        modules = self._loader.discover_modules()
        logger.debug(f"Найдено модулей: {len(modules)}")
        return modules

    def reload_modules(self) -> bool:
        """
        Принудительная перезагрузка списка модулей.
        """
        logger.info("Инициирована перезагрузка модулей...")
        result = self._loader.reload_modules()
        if result:
            logger.info("Модули успешно перезагружены.")
        return result

    def get_status(self) -> Dict[str, str]:
        """
        Возвращает текущую версию и состояние готовности системы.
        """
        logger.debug("Запрос статуса системы")
        return {
            "version": self._version,
            "status": "ready"
        }