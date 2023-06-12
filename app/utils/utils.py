import os
# import yaml
import hashlib
from time import sleep
from typing import List, Dict
from fastapi import UploadFile


CONFIG_PATH = 'config.yml'


def hash(bits: int, host: str):
    return int(hashlib.sha256(host.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def dirs_to_UploadFile(file_list: str):
    return [UploadFile(file=f, filename=n) for f, n in file_list]


def increse_timeout(timeout: float):
    return timeout * 2


# def get_configs():
#     with open(CONFIG_PATH, 'r') as file:
#         config = yaml.load(file, Loader=yaml.FullLoader)
#     return config


# def set_configs(data: Dict):
#     with open(CONFIG_PATH, 'w') as file:
#         yaml.dump(data, file)


