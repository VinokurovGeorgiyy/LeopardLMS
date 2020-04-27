import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Chat(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'chats'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=True)
    members = sql.Column(sql.TEXT, nullable=True)
    messages = sql.Column(sql.TEXT, nullable=True)
    photo_url = sql.Column(sql.String, nullable=True)

