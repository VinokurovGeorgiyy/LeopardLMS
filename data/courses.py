import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Course(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'courses'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    school = sql.Column(sql.Integer, sql.ForeignKey('schools.id'))
    teacher = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    group = sql.Column(sql.Integer, sql.ForeignKey('groups.id'))
    title = sql.Column(sql.String, nullable=True)
    lessons = sql.Column(sql.String, nullable=True)
