import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Lesson(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'lessons'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    course = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('courses.id'), nullable=True)
    lesson_number = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    theory = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    tasks = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    opened = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
    solutions = sqlalchemy.Column(sqlalchemy.String, nullable=True)
