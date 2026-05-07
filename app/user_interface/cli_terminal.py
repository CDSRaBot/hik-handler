# Имя файла: cli_terminal.py
# Путь: app/user_interface/cli_terminal.py - этот файл из репозитория Git
# Кодовое название: Terminal Interface
# Версия: 0.3.5.1

import logging
from typing import NoReturn, Optional

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import clear as clear_screen

# Инициализация логгера уровня модуля
logger = logging.getLogger(__name__)

class CLITerminal:
    """
    Класс реализации интерактивного терминала на базе prompt_toolkit.
    Обеспечивает взаимодействие пользователя с Оркестратором.
    """

    def __init__(self, orchestrator):
        """
        Инициализация терминала.
        
        -- orchestrator: Экземпляр ядра (Orchestrator) для выполнения команд.
        """
        self._orchestrator = orchestrator
        self._session = PromptSession(history=FileHistory('.terminal_history'))
        
        # Список базовых команд для автодополнения
        self._base_commands = [
            'help', 'list', 'run', 'reload', 'status', 'clear', 'exit'
        ]
        
        logger.debug("CLITerminal успешно инициализирован.")

    def _get_completer(self) -> WordCompleter:
        """
        Формирует динамический список автодополнения, включая команды и модули.
        
        :return: Объект WordCompleter.
        """
        # Получаем статус от оркестратора для извлечения списка модулей
        status_data = self._orchestrator.get_status()
        modules = status_data.get('available_modules', [])
        
        return WordCompleter(self._base_commands + modules, ignore_case=True)

    def display_welcome(self) -> None:
        """Выводит приветственное сообщение при старте."""
        print("="*50)
        print("Hik-handler CLI v.0.3.5.1")
        print("Введите 'help' для получения списка команд.")
        print("="*50)

    def request_password(self, prompt_text: str = "Введите пароль: ") -> str:
        """
        Безопасный запрос пароля у пользователя без сохранения в историю.
        
        -- prompt_text: Текст приглашения к вводу.
        :return: Строка введенного пароля.
        """
        logger.debug("Вход в метод request_password.")
        logger.info("Ожидание ввода пароля от пользователя...")
        
        # Используем prompt с маскировкой ввода и без привязки к истории сессии
        password = prompt(prompt_text, is_password=True)
        
        logger.debug("Метод request_password успешно завершен.")
        return password

    def _handle_command(self, user_input: str) -> bool:
        """
        Разбирает и обрабатывает ввод пользователя.
        
        -- user_input: Сырая строка из терминала.
        :return: False, если нужно завершить работу, иначе True.
        """
        parts = user_input.strip().split()
        if not parts:
            return True

        cmd = parts[0].lower()
        args = parts[1:]

        logger.info(f"Обработка команды пользователя: {cmd}")

        if cmd in ['exit', 'quit']:
            print("Завершение работы...")
            return False

        elif cmd == 'help':
            self._show_help()

        elif cmd == 'clear':
            clear_screen()

        elif cmd == 'list':
            modules = self._orchestrator.get_status().get('available_modules', [])
            print(f"Доступные модули: {', '.join(modules) if modules else 'нет'}")

        elif cmd == 'reload':
            self._orchestrator.discover_modules()
            print("Список модулей обновлен.")

        elif cmd == 'status':
            status = self._orchestrator.get_status()
            print(f"Система: {status.get('status')}")
            print(f"Версия ядра: {status.get('version')}")

        elif cmd == 'run':
            if not args:
                print("Ошибка: укажите имя модуля. Пример: run get_device_info")
            else:
                # В данной версии передаем управление Оркестратору
                # В будущем здесь будет логика сбора аргументов
                print(f"Запуск модуля {args[0]}... (функционал в разработке)")
        
        else:
            print(f"Неизвестная команда: {cmd}. Введите 'help'.")

        return True

    def _show_help(self) -> None:
        """Выводит список доступных команд."""
        print("\nДоступные команды:")
        print("  list         - Показать доступные XML модули")
        print("  run <name>   - Выполнить указанный модуль")
        print("  reload       - Пересканировать директорию модулей")
        print("  status       - Состояние системы")
        print("  clear        - Очистить экран")
        print("  help         - Эта справка")
        print("  exit         - Выход\n")

    def run(self) -> None:
        """Запускает основной цикл REPL."""
        self.display_welcome()
        
        logger.info("Запуск основного цикла терминала (REPL).")
        
        try:
            while True:
                # Использование автодополнения и истории сессии
                user_input = self._session.prompt(
                    'hik-handler > ',
                    completer=self._get_completer()
                )
                
                if not self._handle_command(user_input):
                    break
                    
        except KeyboardInterrupt:
            logger.info("Прерывание пользователем (Ctrl+C).")
        except EOFError:
            logger.info("Завершение ввода (Ctrl+D).")
        finally:
            print("\nДо свидания.")
            logger.info("Терминальная сессия закрыта.")