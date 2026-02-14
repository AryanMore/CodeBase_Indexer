import logging
import os

def get_logger(name: str):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/orchestrator.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger
