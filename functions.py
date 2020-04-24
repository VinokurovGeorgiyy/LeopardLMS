import hashlib
from data.users import User
from itertools import combinations_with_replacement
from random import choice


def make_hashed_password(string):
    return str(hashlib.blake2b(string.encode()).hexdigest())


def safe_slice(data, start, end):
    try:
        data = data[start:end]
    except Exception:
        data = []
    finally:
        return data


def get_chat_name(session, chat, chat_members, current_user):
    name = chat.title
    if name is None:
        name = [x for x in chat_members if x != current_user.id]
        name = name[0] if name else None
        name = session.query(User).get(name) if name is not None else None
        name = f'{name.first_name} {name.last_name}' if name else None
    return name


def random_string(length):
    obj = 'abcdefghijklmnopqrstuvwxyz'
    obj += obj.upper() + '0123456789'
    return ''.join(choice(obj) for _ in range(length))
