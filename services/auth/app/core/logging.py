import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('auth.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def get_logger():
    return logger