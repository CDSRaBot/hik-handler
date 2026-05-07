"""
Имя файла: hik-handler.py
Путь: /hik-handler.py
Кодовое название: ENTRY_POINT
Версия: v.0.3.6.0
"""

import logging
import sys
from app.engine.orchestrator import Orchestrator

# Настройка базового логгера для точки входа
logger = logging.getLogger(__name__)

def main():
    """
    Основная функция запуска приложения.
    Инициализирует ядро через фабричный метод bootstrap и запускает цикл.
    """
    logger.info("Запуск приложения Hik-handler...")
    
    try:
        logger.info("--- Старт сессии Hik-handler ---")
        
        # Инициализация ядра системы (Control Plane)
        # Метод bootstrap берет на себя создание NetworkClient и ConfigManager
        orchestrator = Orchestrator.bootstrap("config.toml")
        
        # Проверка режима запуска: интеграция (аргументы) или терминал
        if len(sys.argv) > 1:
            logger.info("Запуск в режиме интеграции (headless).")
            # Выполнение одиночной команды из аргументов командной строки
            # Аргументы передаются без первого элемента (имени самого скрипта)
            orchestrator.execute_headless(sys.argv[1:])
        else:
            # Стандартный интерактивный режим (REPL терминал)
            logger.info("Запуск интерактивного терминала.")
            orchestrator.run_command()
        
    except KeyboardInterrupt:
        # Тихий выход при прерывании пользователем
        logger.info("Приложение остановлено пользователем.")
        sys.exit(0)
    except Exception as e:
        # Логирование критической ошибки перед завершением
        logger.exception(f"Критическая ошибка при работе приложения: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()