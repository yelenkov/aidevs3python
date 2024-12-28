import structlog
import logging
import os
import inspect

def setup_logging():
    # Get the name of the calling script
    current_file = inspect.stack()[1].filename
    script_name = os.path.splitext(os.path.basename(current_file))[0]

    # Create the logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Construct the log file path
    log_file_path = os.path.join(logs_dir, f"{script_name}.log")

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up a file handler using the standard logging library
    formatter = logging.Formatter("%(message)s")
    file_handler = logging.FileHandler(log_file_path, mode='a') # Set mode to 'a' for appending
    file_handler.setFormatter(formatter)

    # Get the root logger from the standard logging library
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)