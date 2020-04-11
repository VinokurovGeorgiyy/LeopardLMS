import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class School(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'schools'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)

    director = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    groups = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    teachers = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    students = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    index = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    region = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    street = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    house = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    phone = sqlalchemy.Column(sqlalchemy.String, nullable=True)

