import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    last_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    first_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    patronymic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user_statuses.id'), nullable=True)
    school = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('schools.id'), nullable=True)
    group = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('groups.id'), nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)

    photo_url = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def check_password(self, password):
        return str(hashlib.blake2b(str(password).encode()).hexdigest()) == self.hashed_password
