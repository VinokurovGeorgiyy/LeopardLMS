import sqlalchemy
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Chat(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'chats'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    members = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    messages = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
