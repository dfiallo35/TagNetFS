import hashlib
from typing import List

from app.utils.const import *


def encode_message(message: Message):
    return message.value.to_bytes(1, 'big')


def decode_message(value: bytes):
    return Message(int.from_bytes(value, byteorder='big'))


def hashing(bits: int, address: str):
    return int(hashlib.sha256(address.encode('utf-8', 'ignore')).hexdigest(), 16) % (2 ** bits)


def hashing_address(nbits: int, address: List[str]):
    h = [hashing(nbits, '{}:{}'.format(*i.split(':'))) for i in address]
    h.sort()
    return h

def decode_message(value: bytes):
    return Message(int.from_bytes(value, byteorder='big'))