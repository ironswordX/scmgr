import logging
def logger(debug=False):
    class ColoredFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: "\033[36m",     # Cyan
            logging.INFO: "\033[32m",      # Green
            logging.WARNING: "\033[33m",   # Yellow
            logging.ERROR: "\033[31m",     # Red
            logging.CRITICAL: "\033[35m",  # Magenta
        }
        RESET = "\033[0m"
        def format(self, record):
            message = super().format(record)
            color = self.COLORS.get(record.levelno, "")
            return f"{color}{message}{self.RESET}"

    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter("[%(levelname)s]: %(message)s")
    )
    log = logging.getLogger("scmgr")
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    log.addHandler(handler)
    return log