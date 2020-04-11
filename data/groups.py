import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Group(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'groups'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    school_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('schools.id'))
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    leader = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    students = sqlalchemy.Column(sqlalchemy.String, nullable=True)
