from app.utils.const import *



def encode_message(message: Message):
    return message.value.to_bytes(1, 'big')

def decode_message(value: bytes):
    return Message(int.from_bytes(value, byteorder='big'))