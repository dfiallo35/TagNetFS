import os
from os.path import join, isfile, isdir
import shutil as sh
import json

import warnings as wr


def copy(file_path: str, dst: str):
    if not isfile(file_path):
        wr.warn('{} does not exist'.format(file_path))
    
    os.makedirs(dst, exist_ok=True)
    sh.copy(file_path, dst)


def json_write(path: str, name: str, data: dict):
    if not name.endswith('.json'):
        name = name + '.json'
    
    os.makedirs(path, exist_ok=True)
    
    with open(join(path, name), 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True, separators=(',', ': '))


def json_read(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def create_tag_files():
    path = './config/'
    os.makedirs(path, exist_ok=True)

    json_write(path, 'tags', {})
    json_write(path, 'files', {})


def exist_config():
    path = './config'
    return isdir(path) and isfile(join(path, 'tags.json')) and isfile(join(path, 'files.json'))
    

def update_json():
    ...


def add_file():
    ...

