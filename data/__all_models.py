import sqlalchemy as sql
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase
from .db_session import create_session
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib
import datetime


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    last_name = sql.Column(sql.String, nullable=False)
    first_name = sql.Column(sql.String, nullable=False)
    patronymic = sql.Column(sql.String, nullable=False)
    email = sql.Column(sql.String, unique=True, nullable=False)
    hashed_password = sql.Column(sql.String, nullable=False)
    profile_photo = sql.Column(sql.Text, default='/static/img/profile-photo.jpg')
    friends = sql.Column(sql.Text, default='')
    chats = sql.Column(sql.Text, default='')

    def check_password(self, password):
        return self.make_hashed_password(password) == self.hashed_password

    def make_hashed_password(self, string):
        return str(hashlib.blake2b(str(string).encode()).hexdigest())

    def add_chat(self, chat_id):
        chats = [] if self.chats is None else self.chats.split(';')
        chats = filter(lambda x: x, chats)
        chats = list(map(int, chats))
        if chat_id not in chats:
            chats.append(chat_id)
            self.chats = ';'.join(map(str, chats))
            return True
        return False

    def add_friend(self, user_id):
        friends = [] if self.friends is None else self.friends.split(';')
        friends = filter(lambda x: x, friends)
        friends = list(map(int, friends))
        if user_id not in friends:
            friends.append(user_id)
            self.friends = ';'.join(map(str, friends))
            return True
        return False

    def get_chats(self, only_id=False):
        session = create_session()
        chats = [] if self.chats is None else self.chats.split(';')
        chats = filter(lambda x: x, chats)
        chats = map(int, chats)
        if not only_id:
            chats = map(session.query(Chat).get, chats)
        return list(chats)

    def get_friends(self, only_id=False):
        session = create_session()
        friends = [] if self.friends is None else self.friends.split(';')
        friends = filter(lambda x: x, friends)
        friends = map(int, friends)
        if not only_id:
            friends = map(session.query(User).get, friends)
        return list(friends)

    def find_personal_chat(self, user_id):
        if user_id == self.id:
            return
        for chat in self.get_chats():
            if chat.type != 'personal':
                continue
            users = chat.get_users(only_id=True)
            if len(users) == 2:
                if user_id not in users:
                    continue
                if self.id not in users:
                    continue
                return chat


class Chat(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'chats'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=True)
    type = sql.Column(sql.String, nullable=False, default='personal')
    users = sql.Column(sql.Text, default='')
    messages = orm.relationship('Message', backref='chat')

    def add_user(self, user_id):
        users = [] if self.users is None else self.users.split(';')
        users = filter(lambda x: x, users)
        users = list(map(int, users))
        if user_id not in users:
            users.append(user_id)
            self.users = ';'.join(map(str, users))
            return True
        return False

    def get_title(self, current_user):
        if self.type == 'group':
            chat_title = self.title
        else:
            others = [i for i in self.get_users() if i.id != current_user.id]
            if others:
                chat_title = f"{others[0].first_name} {others[0].last_name}"
            else:
                chat_title = f"{current_user.first_name} {current_user.last_name}"
        return chat_title

    def get_users(self, only_id=False):
        session = create_session()
        users = [] if self.users is None else self.users.split(';')
        users = filter(lambda x: x, users)
        users = map(int, users)
        if not only_id:
            users = map(session.query(User).get, users)
        return list(users)


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'messages'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    author = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    text = sql.Column(sql.Text, nullable=False)
    date = sql.Column(sql.DateTime, default=datetime.datetime)
    chat_id = sql.Column(sql.Integer, sql.ForeignKey('chats.id'))

    def json_for_messenger(self):
        session = create_session()
        author = session.query(User).get(self.author)
        first_name = author.first_name if author is not None else 'Кто-то'
        last_name = author.last_name if author is not None else 'Какой-то'
        photo = author.profile_photo if author is not None else ''
        timezone = datetime.datetime.now(datetime.timezone.utc).astimezone()
        utc_offset = timezone.utcoffset() // datetime.timedelta(seconds=3600)
        writing_date = self.date + datetime.timedelta(hours=utc_offset)
        message = self.text
        answer = {"message_id": self.id,
                  "author": self.author,
                  "author_first_name": first_name,
                  "author_last_name": last_name,
                  "author_photo": photo,
                  "year": writing_date.year,
                  "month": writing_date.month,
                  "day": writing_date.day,
                  "hour": writing_date.hour,
                  "minute": writing_date.minute,
                  "text": message}
        return answer
