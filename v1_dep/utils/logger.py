import logging
from colorlog import ColoredFormatter

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# This format colors the WHOLE line
log_format = "%(log_color)s%(levelname)-8s: %(message)s%(reset)s"

formatter = ColoredFormatter(
    log_format,
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'light_blue',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    },
    secondary_log_colors={},
    style='%'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
# Example log messages
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")
