# applogging.py
# from datetime import datetime
import json
import logging
# from multiprocessing import Queue, Process
from typing import Any, Dict, List#, Union, Tuple
from enum import Enum
from rich.console import Console
# from rich.markup import escape
# from rich.logging import RichHandler
# from rich import print as rprint
# from rich.text import Text
# from rich.emoji import Emoji
# import rich.emoji
# import traceback
# from rich.pretty import Pretty
# from rich.panel import Panel
from loguru import logger
from settings import *
import gs

CONSOLE_EXCLUDED_FILES = set()

class Justification(Enum):
    """
    Enum class for text justification.
    """
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'

def section(
    header: str,
    color: str = "red",
    justification: str = "left"
) -> None:
    """
    Creates a formatted section header and logs it with specified color and justification.

    Args:
        header (str): The text to be included in the section header.
        color (str): The color to be used for the log message. Defaults to "red".
        justification (Union[str, Justification]): The text justification; can be "left", "right", or "center"
                                                as a string or Justification enum. Defaults to "left".
    """
    to_justification_enum = lambda j: Justification[j.upper()] if isinstance(j, str) else j

    try:
        # Convert justification to Justification enum if it is a string
        justification_enum = to_justification_enum(justification)
    except KeyError:
        raise ValueError(f"Justification must be one of {', '.join(j.value for j in Justification)}")

    # Determine the justification method
    if justification_enum == Justification.LEFT:
        message = f"{' ' + header + ' ':-<88}"
    elif justification_enum == Justification.RIGHT:
        message = f"{' ' + header + ' ':->88}"
    elif justification_enum == Justification.CENTER:
        message = f"{' ' + header + ' ':-^88}"

    # Log the formatted message with the specified color
    logger.info(f"[{color}]\n✨✨{'':-^90}✨✨\n✨✨{message}✨✨\n✨✨{'':-^90}✨✨[/{color}]")

# Define InterceptHandler to redirect standard logging to Loguru
class InterceptHandler(
    logging.Handler
):
    """
    Intercept logging messages and redirect them to Loguru.
    """
    def emit(
        self,
        record
    ) -> None:
        """
        Emit a record.

        This function is called whenever a message is logged. It retrieves the
        corresponding Loguru level for the record's levelname, and logs the
        message with the specified level using Loguru's logger.

        Args:
            record (logging.LogRecord): The log record to emit.

        Returns:
            None
        """         
        # print("InterceptHandler processing")
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def add_ip_to_record(
    record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adds the current IP address to the log record.
    """
    record["extra"]["current_ip"] = getattr(gs, 'current_ip', 'N/A')
    return record

def ip_filter(
    record: Dict[str, Any]
) -> bool:
    """
    Filter function to add current IP to the log record.
    """
    record["extra"]["current_ip"] = gs.current_ip
    return True

SHOW_SECOND_LINE = True
ONLY_ERRORS = False # don't like this
def rich_formatter(
    record: Dict[str, Any]
) -> str:
    """
    Custom formatter to use rich for coloring and formatting log messages.
    """

    # NOTSET=0, DEBUG=10, INFO=20, WARN=30, ERROR=40, CRITICAL=50

    # If ONLY_ERRORS is True, only show ERROR and CRITICAL logs
    # if ONLY_ERRORS and record["level"].no < 40:  # ERROR level has a numeric value of 40
    #     return ""

    time_str = record["time"].strftime('%H:%M:%S.%f')[:-3]
    level = record["level"].name
    function = f"[dodger_blue1]{record['function']}[/dodger_blue1]"
    file_line = f"{record['file'].name}:{function}:{record['line']}"
    message = record["message"][:750] + "..." if len(record["message"]) > 750 else record["message"]
    # ip = record["extra"].get("current_ip", "N/A")
    # ip_color = "green" if ip == gs.initial_ip else "red"
    # ip_str = f"[{ip_color}]{ip:<15}[/{ip_color}]"
    ip = record["extra"].get("current_ip", "N/A")
    ip_color = "green" if ip == getattr(gs, 'initial_ip', None) else "red"
    ip_str = f"[{ip_color}]{ip:<15}[/{ip_color}]"

    colors = {
        "INFO": "dodger_blue1",
        "DEBUG": "bright_yellow",
        "WARNING": "orange1",
        "ERROR": "red",
        "CRITICAL": "bright_red"
    }

    colored = colors.get(level, "bright_white")
    leveled = f"[{colored}]{level:<7}[/{colored}]"

    # rich.from_markup()
    # pretty = Pretty(f"{leveled} : {message}")
    # panel = Panel(pretty, border_style=colored, expand=False)

    # # Render the panel to a string
    # with gs.console.capture() as capture:
    #     gs.console.print(panel,markup=False)
    # panel_str = capture.get().strip()
    panel_str = f"{leveled} | {ip_str} : {message}"
    second_line = f"\n[small][bold][italic]{time_str} | {file_line}[/italic][/bold][/small]" if SHOW_SECOND_LINE else ""
    return f"{panel_str}{second_line}"

def setup_logger() -> None:
    """
    Sets up a logger with the specified configuration.
    """
    global logger
    # Initialize rich console
    gs.console = Console()
    # Remove any existing handlers
    logger.remove()

    # Patch the logger to include the current IP address
    logger = logger.patch(add_ip_to_record)

    # Add a handler for file logging (this will log everything)
    logger.add(
        "app.log",
        format="{time: YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[current_ip]:<15} | {file}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        filter=ip_filter,
        enqueue=True
    )

    # Add a rich handler for console logs with rich color formatting (this will respect exclusions)
    logger.add(
        lambda msg: gs.console.print(rich_formatter(msg.record)),
        level="DEBUG",
        filter=console_filter,
        serialize=False
    )
    # logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # sqlalchemy.engine / .pool / .dialects / .orm
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # Disable standard logging to capture third-party logs like urllib3
    logging.getLogger().disabled = True

    # Redirect standard logging to the Loguru logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # return logger

def shutdown_logger():
    """
    Shutdown the logger.

    This function shuts down the logger gracefully by removing all handlers 
    and performing cleanup operations, ensuring the logger object is valid 
    and supports the required methods.

    Returns:
        None
    """
    if isinstance(logger, logging.Logger) and hasattr(logger, 'remove') and callable(getattr(logger, 'remove')):
        logger.remove()

    if hasattr(logging, 'shutdown') and callable(logging.shutdown):
        logging.shutdown()

def log_webdriver_activity(
    main_url
) -> None:
    """
    Logs the initial cookies, initial page source, network activity specific to the main URL, and elapsed time of the WebDriver activity.

    Args:
        main_url (str): The main URL to log network activity for.

    Returns:
        None

    Raises:
        None

    Description:
        This function logs the initial cookies, initial page source, network activity specific to the main URL, and elapsed time of the WebDriver activity. 
        It captures the initial cookies using the `get_cookies()` method of the current WebDriver instance. It logs the cookies and their values.
        It captures the initial page source using the `page_source` attribute of the current WebDriver instance and logs the length of the page source. 
        It logs the first 1000 characters of the page source.
        It captures the network activity logs using the `get_log()` method of the current WebDriver instance and logs the URL, status code, and response headers of the network activity specific to the main URL.
        It calculates the elapsed time of the network activity specific to the main URL and logs it.
    """
    try:
        # Log initial cookies
        cookies = gs.current_driver.get_cookies()
        logger.info(f"⚠️📄🌎🚧 Initial Cookies: {cookies}")
        for cookie in cookies:
            logger.info(f"⚠️📄🌎🚧 Cookie:: {cookie['name']}: {cookie['value']}")

        # Capture and log the initial page source
        page_source = gs.current_driver.page_source
        logger.info(f"⚠️📄🌎🚧 Initial Page Source Length: {len(page_source)}")
        logger.info(f"⚠️📄🌎🚧 Initial Page Source: {page_source[:1000]}...")  # Log the first 1000 characters

        # Log network activity specific to the main URL
        logs = gs.current_driver.get_log('performance')
        for log in logs:
            log_entry = json.loads(log['message'])['message']
            if log_entry['method'] == 'Network.responseReceived':
                response = log_entry['params']['response']
                if response['url'] == main_url:
                    logger.info(f"⚠️📄🌎🚧 URL: {response['url']}")
                    logger.info(f"⚠️📄🌎🚧 Status Code: {response['status']}")
                    logger.info("⚠️📄🌎🚧 Response Headers:")
                    for header, value in response['headers'].items():
                        logger.info(f"⚠️📄🌎🚧 {header}: {value}")
                    break

        # Log elapsed time
        for log in logs:
            log_entry = json.loads(log['message'])['message']
            if log_entry['method'] == 'Network.loadingFinished':
                elapsed_time = log_entry['params']['timestamp'] - log_entry['params']['requestTime']
                logger.info(f"⚠️📄🌎🚧 Elapsed Time: {elapsed_time}")
                break

    except Exception as e:
        logger.error(f"Error logging WebDriver activity: {e}")

def exclude_files_from_console(
    filenames: List[str]
) -> None:
    """
    Adds multiple files to the list of files excluded from console logging.
    
    Args:
        filenames (List[str]): A list of filenames to exclude (e.g., ['utils.py', 'mixins.py'])
    """
    for filename in filenames:
        exclude_file_from_console(filename)

def exclude_file_from_console(
    filename: str
) -> None:
    """
    Adds a file to the list of files excluded from console logging.
    
    Args:
        filename (str): The name of the file to exclude (e.g., 'utils.py', 'mixins.py')
    """
    CONSOLE_EXCLUDED_FILES.add(filename)

def console_filter(
    record: Dict[str, Any]
) -> bool:
    """
    Filter function to exclude logs from specific files for console output.
    
    Args:
        record (Dict[str, Any]): The log record.
    
    Returns:
        bool: True if the log should be displayed in the console, False otherwise.
    """
    return record["file"].name not in CONSOLE_EXCLUDED_FILES
