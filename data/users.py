import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    last_name = sql.Column(sql.String, nullable=True)
    first_name = sql.Column(sql.String, nullable=True)
    patronymic = sql.Column(sql.String, nullable=True)
    email = sql.Column(sql.String, unique=True, nullable=True)
    status = sql.Column(sql.Integer, sql.ForeignKey('user_statuses.id'))
    school = sql.Column(sql.Integer, sql.ForeignKey('schools.id'), nullable=True)
    group = sql.Column(sql.Integer, sql.ForeignKey('groups.id'), nullable=True)
    hashed_password = sql.Column(sql.String)

    photo_url = sql.Column(sql.String, nullable=True)
    chats = sql.Column(sql.String, nullable=True)

    notifications = sql.Column(sql.String, nullable=True)

    def check_password(self, password):
        string = hashlib.blake2b(str(password).encode()).hexdigest()
        return str(string) == self.hashed_password
