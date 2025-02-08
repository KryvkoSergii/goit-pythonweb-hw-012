import logging

def __get_log_level(log_level):
    match log_level:
        case "DEBUG":
            return logging.DEBUG
        case "INFO":
            return logging.INFO
        case "WARNING":
            return logging.WARNING
        case "ERROR":
            return logging.ERROR
        case "CRITICAL":
            return logging.CRITICAL
        case _:
            raise ValueError(f"Invalid log level {log_level}")


def __build_logger(name: str, log_level: int):
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(ch)
    return logger


def build_logger(name: str, log_level: str):
    return __build_logger(name, __get_log_level(log_level))
