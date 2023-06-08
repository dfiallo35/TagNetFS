from fastapi import UploadFile
from os.path import join
from io import BytesIO

def copy_file(file: UploadFile, path: str):
    with open(join(path, file.filename), 'w') as f:
        f.write(file.file)
    return file.filename


def copy_files(files: list[UploadFile], path: str):
    return [copy_file(file, path) for file in files]


def file_to_bytes(file):
    return BytesIO(file.read())