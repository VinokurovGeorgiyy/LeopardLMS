import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Course(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'courses'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    school = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('schools.id'), nullable=True)
    teacher = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=True)
    group = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('groups.id'), nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    lessons = sqlalchemy.Column(sqlalchemy.String, nullable=True)
