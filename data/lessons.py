import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Lesson(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'lessons'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    theory = sql.Column(sql.Text, nullable=False)
    task = sql.Column(sql.Text, nullable=False)
    course_id = sql.Column(sql.Integer, sql.ForeignKey('courses.id'))
    course = orm.relationship('Course', backref='lessons')

