import sqlalchemy as sql
from .db_session import SqlAlchemyBase
import sqlalchemy.orm as orm
from sqlalchemy_serializer import SerializerMixin


class Notification(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'notifications'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    theme = sql.Column(sql.String, nullable=True)
    text = sql.Column(sql.String, nullable=True)
