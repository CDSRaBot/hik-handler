"""
Модуль сетевого взаимодействия (Network Session).
Реализует транспортный уровень ISAPI с поддержкой Digest-авторизации.
"""

import logging
import requests
import urllib3
from dataclasses import dataclass
from typing import Optional, Any
from requests.auth import HTTPDigestAuth
from app.configuration.security import SecureContext


logger = logging.getLogger(__name__)

# Подавление предупреждений о самоподписанных сертификатах при HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HikvisionNetworkError(Exception):
    """Базовое исключение для сетевых ошибок Hik-handler."""
    pass


class HikvisionClient:
    """
    Клиент для работы с ISAPI (Network Session Manager).
    Реализует паттерн Context Manager для управления временем жизни сессии.
    """

    def __init__(self, context: SecureContext):
        """
        Инициализирует клиента с заданным защищенным контекстом.
        
        Args:
            context: SecureContext с параметрами подключения и авторизации.
        """
        logger.debug("Инициализация HikvisionClient для хоста: %s", context.host)
        self._ctx = context
        self._session: Optional[requests.Session] = None
        self._base_url = f"{self._ctx.scheme}://{self._ctx.host}:{self._ctx.port}"
        logger.info("Сетевой клиент подготовлен. Базовый URL: %s", self._base_url)

    def __enter__(self):
        """
        Открывает сессию при входе в контекстный менеджер.
        Настраивает Digest-авторизацию.
        """
        logger.debug("Открытие сетевой сессии (Context Manager)...")
        self._session = requests.Session()
        self._session.auth = HTTPDigestAuth(self._ctx.user, self._ctx.password)
        logger.info("Сетевая сессия с Digest-авторизацией успешно открыта.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Закрывает сессию при выходе из контекстного менеджера, 
        освобождая сетевые ресурсы.
        """
        logger.debug("Завершение работы сетевой сессии...")
        if self._session:
            self._session.close()
            logger.info("Сетевая сессия корректно закрыта.")

    def execute(
        self, 
        method: str, 
        url_path: str, 
        payload: Optional[str] = None,
        headers: Optional[dict] = None
    ) -> str:
        """
        Выполняет HTTP/HTTPS-запрос к устройству.
        
        Args:
            method: HTTP метод (GET, PUT, POST, DELETE).
            url_path: Путь ISAPI (например, /ISAPI/System/deviceInfo).
            payload: Тело запроса (строка).
            headers: Опциональные HTTP-заголовки. Если не указаны, используется XML.
            
        Returns:
            Текстовый ответ от устройства.
            
        Raises:
            HikvisionNetworkError: При проблемах связи или ошибках протокола.
        """
        logger.debug("Подготовка к выполнению метода execute. Путь: %s", url_path)
        
        if not self._session:
            logger.error("Попытка выполнить запрос без инициализации сессии.")
            raise HikvisionNetworkError("Сессия не инициализирована.")

        full_url = f"{self._base_url}{url_path}"
        # Применяем переданные заголовки или используем XML по умолчанию
        request_headers = headers if headers else {'Content-Type': 'application/xml'}
        
        logger.info("Отправка %s запроса на устройство...", method)
        logger.debug("Детали запроса: URL=%s, Headers=%s", full_url, request_headers)
        
        try:
            response = self._session.request(
                method=method,
                url=full_url,
                data=payload.encode('utf-8') if payload else None,
                timeout=self._ctx.timeout,
                headers=request_headers,
                verify=False  # Отключение проверки SSL для локальных камер
            )
            response.raise_for_status()
            logger.debug("Запрос успешно выполнен. Статус: %s", response.status_code)
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка при выполнении запроса: %s", str(e))
            raise HikvisionNetworkError(f"Ошибка сети: {str(e)}")