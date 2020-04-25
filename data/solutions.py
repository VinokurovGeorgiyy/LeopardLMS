import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Solution(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'solutions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    lesson = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('lessons.id'))
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)

