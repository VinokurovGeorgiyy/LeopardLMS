import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Lesson(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'lessons'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    course = sql.Column(sql.Integer, sql.ForeignKey('courses.id'))
    lesson_number = sql.Column(sql.String, nullable=True)
    title = sql.Column(sql.String, nullable=True)
    theory = sql.Column(sql.String, nullable=True)
    tasks = sql.Column(sql.String, nullable=True)
    opened = sql.Column(sql.Boolean, nullable=True)
    solutions = sql.Column(sql.String, nullable=True)
