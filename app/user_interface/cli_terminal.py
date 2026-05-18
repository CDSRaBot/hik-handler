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
            'help', 'list', 'run', 'connect', 'disconnect', 'reload', 'status', 'clear', 'exit'
        ]

        # Detailed help descriptions for commands
        self._command_descriptions: Dict[str, str] = {
            'list': 'Shows all available XML modules located in the modules directory.',
            'connect': 'Initializes a new session. Usage: <i>connect login:password@host</i>.',
            'disconnect': 'Terminates the current session context.',
            'run': 'Executes a specific module. Usage: <i>run &lt;name&gt; [args]</i>.\n'
                   'Arguments are passed as key=value. Example: <i>run my_module export=csv</i>.',
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
        print_formatted_text(HTML("<b>Type 'help' to see available commands.</b>"))
        print_formatted_text(HTML("<b>To connect to a device, run:</b> <i>connect login:password@host</i>\n"))
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
            self._cmd_disconnect()
            return False
        elif command == 'clear':
            logger.debug("Clear command received.")
            clear_screen()
        elif command == 'help':
            self._cmd_help(args[0] if args else None)
        elif command == 'list':
            self._cmd_list()
        elif command == 'connect':
            self._cmd_connect(args)
        elif command == 'disconnect':
            self._cmd_disconnect()
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

    def _cmd_disconnect(self) -> None:
        """Terminates active session."""
        self._orchestrator.disconnect()
        print_formatted_text(HTML("<ansiyellow>Session terminated.</ansiyellow>"))
        logger.info("Terminal: Session disconnected.")

    def _handle_connection_error(self, e: Exception) -> None:
        """Translates technical exceptions into human-readable markers."""
        err_str = str(e).lower()
        if "401" in err_str or "unauthorized" in err_str:
            msg = "Error: Invalid login or password."
        elif "403" in err_str or "forbidden" in err_str:
            msg = "Error: Access forbidden. Check account permissions."
        elif "timeout" in err_str or "connection" in err_str:
            msg = "Error: Device unreachable. Check IP, network, or power."
        else:
            msg = f"Error: Connection failed. ({e})"
        
        print_formatted_text(HTML(f"<ansired>{msg}</ansired>"))

    def _cmd_connect(self, args: List[str]) -> None:
        """Parses connection string and initializes session."""
        self._cmd_disconnect() # Implicitly disconnect before new session
        if not args:
            print_formatted_text(HTML("<ansired>Error: Connection string required. Usage: connect 'login:password@host'</ansired>"))
            return

        conn_str = args[0]
        try:
            # Parse user:pass@host
            if '@' not in conn_str or ':' not in conn_str:
                raise ValueError("Invalid format. Use 'login:password@host'")
            
            auth, host = conn_str.split('@', 1)
            user, password = auth.split(':', 1)
            
            from app.configuration.security import SecureContext
            context = SecureContext(host=host, user=user, password=password)
            
            # Connection verification (Strict)
            logger.info(f"Terminal: Verifying connection to {host}...")
            from app.communication.session import HikvisionClient
            try:
                with HikvisionClient(context) as conn:
                    # Attempt a real request to verify credentials and connectivity
                    conn.execute(method="GET", url_path="/ISAPI/System/deviceInfo")
                
                # If we reached here, verification is successful
                self._orchestrator.set_context(context)
                print_formatted_text(HTML("<ansigreen>Connected: Device verified and authorized.</ansigreen>"))
                logger.info(f"Terminal: Session initialized for host: {host}")
                
            except Exception as e:
                # Analyze failure reason (Network or Auth)
                err_str = str(e).lower()
                if "401" in err_str or "unauthorized" in err_str:
                    msg = "Not connected: not authorized. Check login and password."
                else:
                    msg = f"Not connected: device verification failed. ({e})"
                
                # We log this as a warning with full error detail, but it's an expected failure type
                logger.warning(f"Terminal: Connection verification failed for {host}: {e}")
                
                # Use standard library to escape special characters for HTML output
                from html import escape
                print_formatted_text(HTML(f"<ansired>{escape(msg)}</ansired>"))
            
        except ValueError as e:
            # This is for shlex or logic errors during parsing
            logger.error(f"Terminal: Connection string parsing failed: {e}")
            print_formatted_text(HTML(f"<ansired>Syntax error: {e}</ansired>"))
        except Exception:
            # Truly unexpected errors (bugs in code, OS-level issues)
            logger.exception("Terminal: Unexpected system error during connection setup")
            print_formatted_text(HTML("<ansired>Internal system error. Check logs for details.</ansired>"))

    def _cmd_run(self, args: List[str]) -> None:
        """Executes the specified module via Orchestrator."""
        # Session check
        if not self._orchestrator._base_context:
            print_formatted_text(HTML("<ansiyellow>Error: No active session. Please 'connect' first.</ansiyellow>"))
            return

        logger.debug("Executing _cmd_run with raw args: %s", args)
        # ... (rest of method unchanged) ...
        if not args:
            error_msg = "Module name required. Usage: run &lt;module_name&gt; [key=value...]"
            logger.warning(f"Run command failed: Module name required.")
            print_formatted_text(HTML(f"<ansired>Error: {error_msg}</ansired>"))
            return
        
        module_name = args[0]
        params = {}
        
        for arg in args[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                params[key.strip()] = value.strip()
                logger.debug(f"Parsed argument: {key.strip()} = {value.strip()}")
            else:
                logger.warning(f"Ignoring invalid argument format in module '{module_name}': '{arg}'. Expected key=value.")
        
        logger.info(f"Initiating execution for module '{module_name}' with {len(params)} parameters.")
        
        try:
            # CORRECTED: Passing 'params' as a single dictionary argument, not as **kwargs
            success = self._orchestrator.execute_headless(module_name, params)
            
            if success:
                logger.info(f"Execution successful for module '{module_name}'.")
                print_formatted_text(HTML(f"<ansigreen>Success: Module '{module_name}' executed.</ansigreen>"))
            else:
                logger.error(f"Execution failed for module '{module_name}' (Orchestrator returned False).")
                print_formatted_text(HTML(f"<ansired>Failure: Module '{module_name}' failed to execute. Check logs for details.</ansired>"))
                
        except Exception as e:
            logger.exception(f"Critical error during execution of module '{module_name}': {str(e)}")
            self._handle_connection_error(e)

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