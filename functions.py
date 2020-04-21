import hashlib


def make_hashed_password(string):
    return str(hashlib.blake2b(string.encode()).hexdigest())


def safe_slice(data, start, end):
    try:
        data = data[start:end]
    except Exception:
        data = []
    finally:
        return data
