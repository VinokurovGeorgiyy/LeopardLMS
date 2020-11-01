def is_correct_password(password):
    if len(password) < 8:
        return {'error': 'Пароль короче 8 символов'}
    if password.lower() == password or password.upper() == password:
        return {'error': 'Все символы в пароле одного регистра'}
    if not any([x in password for x in '0123456789']):
        return {'error': 'Пароль должен иметь хотя бы одну цифру'}
    return {'ok': 'Success'}
