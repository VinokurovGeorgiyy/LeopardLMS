import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class School(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'schools'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, unique=True, nullable=True)
    short_title = sql.Column(sql.String, nullable=True)

    director = sql.Column(sql.Integer, sql.ForeignKey('users.id'))

    index = sql.Column(sql.Integer, nullable=True)
    region = sql.Column(sql.String, nullable=True)
    city = sql.Column(sql.String, nullable=True)
    street = sql.Column(sql.String, nullable=True)
    house = sql.Column(sql.String, nullable=True)

    email = sql.Column(sql.String, nullable=True)
    phone = sql.Column(sql.String, nullable=True)
    photo_url = sql.Column(sql.String, nullable=True)

