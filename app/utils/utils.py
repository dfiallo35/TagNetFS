import os
import math
import hashlib
from typing import List
from fastapi import UploadFile



def hash(bits: int, host: str):
    return int(hashlib.sha256(host.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def dirs_to_UploadFile(file_list: str):
    return [UploadFile(file=f, filename=n) for f, n in file_list]


def increse_timeout(timeout: float):
    return timeout * 2
