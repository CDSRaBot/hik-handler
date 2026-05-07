# Имя файла: security.py
# Кодовое название: Security Context
# Версия: 0.3.5.0

import logging
from dataclasses import dataclass

# Инициализация логгера уровня модуля
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SecureContext:
    """
    Защищенный контекст для хранения учетных данных и параметров сети устройства.
    
    Использует frozen=True для обеспечения неизменяемости (Immutability).
    После инициализации ни один компонент системы не сможет случайно 
    или намеренно подменить IP (параметр host), логин, пароль или таймаут.
    """
    host: str
    user: str
    password: str
    port: int = 80
    timeout: int = 10
    scheme: str = "http"
    
    # Расширение для контекста выполнения (Orchestrator)
    module_name: Optional[str] = None
    params: Optional[dict] = None

    def __post_init__(self):
        """
        Логирование факта успешного создания безопасного контекста.
        Вызывается автоматически после инициализации датакласса.
        """
        logger.debug(f"SecureContext успешно инициализирован для хоста: {self.host}")

    def get_auth(self) -> tuple[str, str]:
        """
        Возвращает кортеж для Basic/Digest аутентификации в NetworkClient.
        Инкапсулирует логику доступа к учетным данным.
        
        :return: Кортеж (пользователь, пароль)
        """
        logger.debug(f"Запрошены данные авторизации для хоста: {self.host}")
        return (self.user, self.password)

    def __repr__(self) -> str:
        """
        Переопределение строкового представления объекта (Security Guard).
        Предотвращает случайную утечку пароля при использовании print() 
        или записи объекта в лог-файл (Traceback дампы).
        """
        pwd_mask = "***" if self.password else "EMPTY"
        return f"SecureContext(host='{self.host}', user='{self.user}', password='{pwd_mask}', timeout={self.timeout})"