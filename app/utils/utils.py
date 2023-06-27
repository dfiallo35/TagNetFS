import os
import yaml
import logging
import hashlib
from time import sleep
from math import ceil, floor
from typing import List, Dict
from fastapi import UploadFile


CONFIG_PATH = 'config.yml'


def hash(bits: int, host: str):
    return int(hashlib.sha256(host.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def dirs_to_UploadFile(file_list: str):
    return [UploadFile(file=f, filename=n) for f, n in file_list]


def increse_timeout(timeout: float):
    return timeout * 2


def split(l: list, n: int):
    x = [[] for _ in range(n)]
    for i, item in enumerate(l):
        x[i%n].append(item)
    return x


def divide(servers: int, divisions: int):
    if servers % divisions > 1 or servers < divisions:
        return ceil(servers / divisions)
    return floor(servers / divisions)

def log(
        name: str,
        level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        file: str = None
    ) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(name)s - %(message)s')
    logger.setLevel(level)
    if file:
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        fh = logging.FileHandler(file)
        fh.setLevel(file_level)
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def get_configs():
    with open(CONFIG_PATH, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def set_configs(data: Dict):
    with open(CONFIG_PATH, 'w') as file:
        yaml.dump(data, file)


