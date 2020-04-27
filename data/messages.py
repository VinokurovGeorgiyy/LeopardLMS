import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin
import datetime


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'messages'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    writer = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    chat = sql.Column(sql.Integer, sql.ForeignKey('chats.id'))
    text = sql.Column(sql.Text, nullable=True)
    data = sql.Column(sql.DateTime, default=datetime.datetime)
