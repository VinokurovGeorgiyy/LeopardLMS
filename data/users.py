import sqlalchemy as sql
from .db_session import SqlAlchemyBase
from .db_session import create_session
import sqlalchemy.orm as orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib

users_chats = sql.Table(
    'users_chats', SqlAlchemyBase.metadata,
    sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')),
    sql.Column('chat_id', sql.Integer, sql.ForeignKey('chats.id'))
)


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    last_name = sql.Column(sql.String, nullable=False)
    first_name = sql.Column(sql.String, nullable=False)
    patronymic = sql.Column(sql.String, nullable=False)
    email = sql.Column(sql.String, unique=True, nullable=False)
    hashed_password = sql.Column(sql.String, nullable=False)
    profile_photo = sql.Column(sql.Text, default='/static/img/profile-photo.jpg')
    chats = orm.relationship('Chat', secondary=users_chats, backref='users')
    friends = sql.Column(sql.Text, default='')

    def check_correct_password(self, password):
        if len(password) < 8:
            return {'error': 'Пароль короче 8 символов'}
        if password.lower() == password or password.upper() == password:
            return {'error': 'Все символы в пароле одного регистра'}
        if not any([x in password for x in '0123456789']):
            return {'error': 'Пароль должен иметь хотя бы одну цифру'}
        return {'ok': 'Success'}

    def check_password(self, password):
        return self.make_hashed_password(password) == self.hashed_password

    def make_hashed_password(self, string):
        return str(hashlib.blake2b(str(string).encode()).hexdigest())

    def add_friend(self, user_id):
        friends = self.friends.split(';')
        friends = filter(lambda x: x, friends)
        friends = list(map(int, friends))
        if user_id not in friends:
            friends.append(user_id)
            self.friends = ';'.join(map(str, friends))
            return True
        return False

    def get_friends(self, only_id=False):
        session = create_session()
        friends = self.friends.split(';')
        friends = filter(lambda x: x, friends)
        friends = map(int, friends)
        if not only_id:
            friends = map(session.query(User).get, friends)
        return list(friends)
