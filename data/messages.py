import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin
import datetime


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'messages'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    author = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    text = sql.Column(sql.Text, nullable=False)
    data = sql.Column(sql.DateTime, default=datetime.datetime)
    chat_id = sql.Column(sql.Integer, sql.ForeignKey('chats.id'))
    chat = orm.relationship('Chat', backref='messages')

