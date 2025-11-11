import logging
import logging.config
import os

def setup_logging(config_path='logging.conf', log_dir="logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    

    logging.config.fileConfig(config_path)
    
    # Get and return the root logger
    return logging.getLogger()

logger = setup_logging()

