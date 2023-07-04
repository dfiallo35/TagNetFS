from fastapi import UploadFile
from os.path import join
from io import BytesIO

from app.utils.utils import decode

def dirs_to_UploadFile(file_list: list[tuple]):
    return [UploadFile(file=f, filename=n) for f, n in file_list]

def dir_to_UploadFile(file: tuple):
    return UploadFile(file=file[0], filename=file[1])

def copy_file(file: UploadFile, path: str):
    with open(join(path, file.filename), 'wb') as f:
        f.write(decode(file.file['data']))
    return file.filename

def get_file(filepath:str):
    with open(filepath, 'rb') as f:
        return f.read()

def copy_files(files: list[UploadFile], path: str):
    return [copy_file(file, path) for file in files]


def file_to_bytes(file):
    return BytesIO(file.read())