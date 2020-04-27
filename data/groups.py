import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Group(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'groups'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    school_id = sql.Column(sql.Integer, sql.ForeignKey('schools.id'))
    title = sql.Column(sql.String, nullable=True)
    leader = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    photo_url = sql.Column(sql.String, nullable=True)
