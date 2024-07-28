"""Common functions"""
import configparser
import logging
from datetime import datetime


def get_config(path):
    """Get config file"""
    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_logger():
    """Get logger"""
    logger = logging.getLogger('apartment_logger')
    logging.basicConfig(level=logging.INFO)
    return logger
