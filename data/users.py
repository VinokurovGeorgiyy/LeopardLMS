import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib


users_communities = sql.Table(
    'users_communities', SqlAlchemyBase.metadata,
    sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')),
    sql.Column('community_id', sql.Integer, sql.ForeignKey('communities.id'))
)

users_courses = sql.Table(
    'users_courses', SqlAlchemyBase.metadata,
    sql.Column('user_id', sql.Integer, sql.ForeignKey('users.id')),
    sql.Column('course_id', sql.Integer, sql.ForeignKey('courses.id'))
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
    communities = orm.relationship('Community', secondary=users_communities, backref='users')
    courses = orm.relationship('Course', secondary=users_courses, backref='users')

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