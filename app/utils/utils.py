import os
import base64
import yaml
import logging
import hashlib
from math import ceil, floor
import json

CONFIG_PATH_YML = 'configs.yml'
CONFIG_PATH_JSON = 'configs.json'


def encode(data: bytes):
    return base64.b64encode(data)

def decode(data: bytes):
    return base64.b64decode(data)

def read_config_json(filepath = CONFIG_PATH_JSON):
    with open(filepath, 'r') as file:
        json_data = json.load(file)
    return json_data

def write_configs(data, filepath = CONFIG_PATH_YML):
    with open(filepath, 'w') as file:
        yaml.dump(data, file)

def read_configs(filepath = CONFIG_PATH_YML):
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def hash(bits: int, host: str):
    return int(hashlib.sha256(host.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)

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


def generate_worker_uri(id: str, ip: str, port: int):
    return f'PYRO:{id}@{ip}:{port}'

def get_ip_from_uri(uri: str):
    return uri.split('@')[1].split(':')[0]