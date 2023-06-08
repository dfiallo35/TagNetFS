import hashlib
from typing import List
from fastapi import UploadFile


def hash_addr(bits: int, address: str):
    return int(hashlib.sha256(address.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def hash(bits: int, host: str):
    return int(hashlib.sha256(host.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def hashing_address(nbits: int, address: List[str]):
    h = [hash(nbits, '{}:{}'.format(*i.split(':'))) for i in address]
    h.sort()
    return h


def dir_to_UploadFile(path: str):
    ...

