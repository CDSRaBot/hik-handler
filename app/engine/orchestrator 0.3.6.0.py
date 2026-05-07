# Имя файла: orchestrator.py
# Путь: app/engine/orchestrator.py
# Кодовое название: Orchestrator
# Версия: v.0.3.6.0

import logging
from typing import Any, Dict, List, Optional

# Импорты внутренних компонентов системы
#from app.configuration.settings import ConfigManager
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
        client: HikvisionClient
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
        self._version = "0.3.6.0"
        
        logger.info(f"Orchestrator v.{self._version} инициализирован")
        logger.debug(f"Зависимости: loader={type(loader)}, client={type(client)}")

    @classmethod
    def bootstrap(cls, config_path: str = "config.toml") -> 'Orchestrator':
        """
        Фабричный метод для автоматизированной сборки Оркестратора.
        Инкапсулирует подготовку конфигурации и создание всех зависимостей.
        """
        logger.info("Orchestrator: Запуск процедуры bootstrap...")

        try:
            # 1. Загрузка конфигурации (отложенный импорт для избежания циклов)
            logger.debug("Bootstrap: Инициализация ConfigManager")
            from app.configuration.settings import ConfigManager
            config = ConfigManager(config_path="config.toml")

            # 2. Подготовка движка (Engine)
            
            logger.debug("Инициализация компонентов через bootstrap")
            # Гарантируем использование параметра config_path из аргументов метода
            config = ConfigManager(config_path=config_path)
        
            # Формируем путь к основному файлу схемы
            xsd_path = str(config.schema_path / "module_schema.xsd")
        
            loader = ModuleManager(config.modules_path)
            # Передаем обязательный путь к схеме в валидатор
            validator = XMLValidator(xsd_path)
            resolver = ArgumentResolver()

            # 3. Настройка сетевого слоя
            logger.debug("Bootstrap: Подготовка сетевого клиента Hikvision")
            credentials = config.get_secure_context()
            client = HikvisionClient(credentials)

            # 4. Сборка объекта
            instance = cls(
                loader=loader,
                validator=validator,
                resolver=resolver,
                client=client,
                base_context=credentials
            )

            logger.info("Orchestrator: Система успешно собрана.")
            return instance

        except Exception as e:
            logger.critical(f"Orchestrator: Ошибка при выполнении bootstrap: {e}")
            raise RuntimeError("Не удалось инициализировать ядро системы.") from e

    def run_command(self, context: SecureContext) -> Dict[str, Any]:
        """
        Выполняет полный цикл обработки команды.
        Если context не передан, используется базовый контекст из настроек.
        """
        # Выбираем контекст: переданный или базовый
        target_context = context or self._base_context
        
        logger.info(f"Исполнение команды: {target_context.module_name or 'Default'}")
        logger.debug(f"Параметры контекста: {target_context}")
        
        try:
            # Если имя модуля не задано (простой вызов REPL без команды), 
            # возвращаем статус готовности
            if not target_context.module_name:
                logger.debug("Вызов run_command без указания модуля (REPL Mode)")
                return {"status": "ready", "message": "Ожидание ввода команды (--help для справки):"}

            # 1. Определение пути к модулю
            module_xml = self._loader.get_module_path(target_context.module_name)
            
            # 2. XSD-валидация
            self._validator.validate(module_xml)
            
            # 3. Разрешение аргументов
            resolved_context = self._resolver.resolve(target_context)
            
            # 4. Сетевое взаимодействие
            response = self._client.execute(resolved_context)
            
            logger.info(f"Команда {target_context.module_name} успешно выполнена")
            return {
                "status": "success",
                "module": target_context.module_name,
                "data": response
            }

        except Exception as e:
            logger.error(f"Ошибка при выполнении {target_context.module_name}: {e}")
            return {
                "status": "error", 
                "message": str(e)
            }

    def execute_headless(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        base_context: SecureContext
    ) -> Dict[str, Any]:
        """
        Выполняет команду в автоматическом режиме (Headless).
        Использует логику run_command для обеспечения целостности процесса.
        
        -- module_name: Имя модуля.
        -- params: Словарь параметров.
        -- base_context: Базовый контекст безопасности.
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
            host=base_context.host,
            user=base_context.user,
            password=base_context.password,
            timeout=base_context.timeout,
            module_name=module_name,
            params=params
        )

        return self.run_command(context)

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