# File: cli_terminal.py
# Path: app/user_interface/cli_terminal.py
# Internal Name: Terminal Interface
# Version: 1.0.0 Frozen

import logging
import shlex
from typing import NoReturn, Optional, List, Dict

from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import clear as clear_screen

# Module-level logger initialization
logger = logging.getLogger(f"hik_handler.{__name__}")

class CLITerminal:
    """
    Interactive terminal implementation based on prompt_toolkit.
    Provides robust user interaction with the Orchestrator with detailed tracing.
    """

    def __init__(self, orchestrator):
        """
        Terminal initialization.
        
        -- orchestrator: Core instance (Orchestrator) for command execution.
        """
        logger.debug("Initializing CLITerminal with orchestrator: %s", type(orchestrator).__name__)
        self._orchestrator = orchestrator
        self._session = PromptSession(history=FileHistory('.terminal_history'))
        
        # Base commands for autocompletion
        self._base_commands = [
            'help', 'list', 'run', 'reload', 'status', 'clear', 'exit'
        ]

        # Detailed help descriptions for commands
        self._command_descriptions: Dict[str, str] = {
            'list': 'Shows all available XML modules located in the modules directory.',
            'run': 'Executes a specific module. Usage: <i>run &lt;name&gt; [args]</i>.\n'
                   'Arguments are passed to the module as key=value pairs.',
            'reload': 'Rescans the modules directory and reloads available modules.',
            'status': 'Displays system health, connection status, and loaded modules.',
            'clear': 'Clears the terminal screen.',
            'exit': 'Exits the application gracefully.'
        }
        logger.info("Terminal Interface initialized successfully.")

    def display_welcome(self) -> None:
        """Displays the welcome banner."""
        logger.debug("Executing display_welcome")
        clear_screen()
        print_formatted_text(HTML("<ansiblue><b>Hik-handler CLI Terminal</b></ansiblue>"))
        print_formatted_text(HTML("<b>Type 'help' to see available commands.</b>\n"))
        logger.debug("Welcome banner displayed.")

    def _get_completer(self) -> WordCompleter:
        """Returns a dynamically updating autocompleter."""
        logger.debug("Building autocompleter with base commands")
        return WordCompleter(self._base_commands, ignore_case=True)

    def _handle_command(self, command_str: str) -> bool:
        """
        Processes a single command string.
        Returns False if the application should exit, True otherwise.
        """
        logger.debug("Executing _handle_command with input: '%s'", command_str)
        if not command_str.strip():
            return True

        try:
            parts = shlex.split(command_str, posix=True)
            logger.debug("Command parsed by shlex into parts: %s", parts)
        except ValueError as e:
            logger.error("Failed to parse command: %s", e)
            print_formatted_text(HTML(f"<ansired>Syntax error in command: {e}</ansired>"))
            return True

        command = parts[0].lower()
        args = parts[1:]

        if command == 'exit':
            logger.debug("Exit command received.")
            return False
        elif command == 'clear':
            logger.debug("Clear command received.")
            clear_screen()
        elif command == 'help':
            self._cmd_help(args[0] if args else None)
        elif command == 'list':
            self._cmd_list()
        elif command == 'run':
            self._cmd_run(args)
        elif command == 'reload':
            self._cmd_reload()
        elif command == 'status':
            self._cmd_status()
        else:
            logger.warning("Unknown command input: %s", command)
            print_formatted_text(HTML(f"<ansired>Unknown command: {command}</ansired>"))

        return True

    def _cmd_list(self) -> None:
        """Handles the 'list' command."""
        logger.debug("Executing _cmd_list")
        print("Available modules: [mocked]")
        logger.info("Module list displayed.")

def _cmd_list(self) -> None:
        """Shows all available XML modules indexed in memory."""
        logger.debug("Executing 'list' command")
        modules = self._orchestrator.get_available_modules()
        
        if not modules:
            print_formatted_text(HTML("<ansiyellow>No modules found in cache. Use 'reload' to scan disk.</ansiyellow>"))
            return
        
        print_formatted_text(HTML("\n<ansicyan><b>Available XML Modules:</b></ansicyan>"))
        for idx, name in enumerate(modules, 1):
            print(f"  {idx}. {name}")
        print()

    def _cmd_run(self, args: List[str]) -> None:
        """Helper to prepare and execute a run command."""
        # This will be handled in the next iteration of orchestrator integration
        logger.info("Command 'run' is still under development for direct CLI execution.")
        print_formatted_text(HTML("<ansiyellow>Command 'run' is not fully implemented yet.</ansiyellow>"))

    def _cmd_reload(self) -> None:
        """Force refresh of the module indexing system."""
        logger.debug("Executing 'reload' command")
        print_formatted_text(HTML("<ansicyan>Scanning modules directory...</ansicyan>"))
        
        # Trigger full disk discovery via orchestrator
        modules = self._orchestrator.discover_modules()
        
        print_formatted_text(HTML(f"<ansigreen>Success. Found {len(modules)} module(s).</ansigreen>"))
        logger.info("Module index manually reloaded via CLI.")

    def _cmd_status(self) -> None:
        """Displays system health and metrics."""
        logger.debug("Executing 'status' command")
        status = self._orchestrator.get_status()
        
        print_formatted_text(HTML("\n<ansicyan><b>Hik-handler System Status:</b></ansicyan>"))
        print(f"  Version: {status.get('version', 'Unknown')}")
        print(f"  Engine:  {status.get('engine', 'Unknown')}")
        
        metrics = status.get('metrics', {})
        print(f"  Indexed Modules: {metrics.get('indexed_modules', 0)}")
        print()
        
    def _cmd_help(self, command: Optional[str] = None) -> None:
        """Handles the 'help' command."""
        logger.debug("Executing _cmd_help for command: %s", command)
        if not command:
            print_formatted_text(HTML("\n<ansigreen><b>Available Commands:</b></ansigreen>"))
            print("  list               - Show available XML modules")
            print("  run <name> [args]  - Execute module with arguments")
            print("  reload             - Rescan modules directory")
            print("  status             - System health and loaded data")
            print("  clear              - Clear terminal screen")
            print("  help [command]     - This help message or detailed info")
            print("  exit               - Exit application\n")
            logger.info("General help message displayed.")
        else:
            description = self._command_descriptions.get(command.lower())
            if description:
                print_formatted_text(HTML(f"\n<ansicyan><b>Command: {command}</b></ansicyan>"))
                print(f"  {description}\n")
                logger.info("Detailed help displayed for command: %s", command)
            else:
                print_formatted_text(HTML(f"<ansired>No detailed help available for '{command}'.</ansired>"))
                logger.warning("Help requested for unknown command: %s", command)

    def run(self) -> None:
        """Runs the main REPL loop."""
        logger.debug("Starting main REPL loop")
        self.display_welcome()
        
        try:
            while True:
                user_input = self._session.prompt(
                    'hik-handler > ',
                    completer=self._get_completer()
                )
                
                if not self._handle_command(user_input):
                    break
                    
        except (KeyboardInterrupt, EOFError):
            logger.debug("REPL loop interrupted by user.")
        finally:
            print_formatted_text(HTML("\n<ansiyellow>Goodbye.</ansiyellow>"))
            logger.info("Terminal session closed.")