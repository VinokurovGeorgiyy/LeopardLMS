import hashlib


def make_hashed_password(string):
    return str(hashlib.blake2b(string.encode()).hexdigest())
