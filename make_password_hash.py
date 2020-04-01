import hashlib
print(str(hashlib.blake2b(str(input()).encode()).hexdigest()))
