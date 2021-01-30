def is_correct_password(password):
    if len(password) < 8:
        return {'error': 'Short password'}
    if password.lower() == password or password.upper() == password:
        return {'error': 'Only one case'}
    if not any([x in password for x in '0123456789']):
        return {'error': 'No digits'}
    return {'ok': 'Success'}
