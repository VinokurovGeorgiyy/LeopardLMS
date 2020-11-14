import sqlalchemy as sql
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase
from .db_session import create_session
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib
import datetime


class Model:
    def add_obj(self, data, other_id, separator=";"):
        separator = str(separator)
        if not isinstance(other_id, int):
            return False
        data = self.extract_ids(data, separator)
        if other_id not in data:
            data.append(other_id)
            return separator.join(map(str, data))
        return False

    def extract_ids(self, data, separator=";"):
        data = [] if data is None else data.split(separator)
        data = filter(lambda x: x, data)
        return list(map(int, data))

    def get_obj(self, data, model_class, separator=';', only_id=False):
        session = create_session()
        data = self.extract_ids(data, separator)
        if not only_id:
            data = map(session.query(model_class).get, data)
        return list(data)


class User(SqlAlchemyBase, UserMixin, SerializerMixin, Model):
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
    communities = sql.Column(sql.Text, default='')
    courses = sql.Column(sql.Text, default='')

    def add_chat(self, chat_id):
        data = self.add_obj(self.chats, chat_id)
        if data:
            self.chats = data
        return data

    def add_community(self, community_id):
        data = self.add_obj(self.communities, community_id)
        if data:
            self.communities = data
        return data

    def add_course(self, course_id):
        data = self.add_obj(self.courses, course_id)
        if data:
            self.courses = data
        return data

    def add_friend(self, user_id):
        data = self.add_obj(self.friends, user_id)
        if data:
            self.friends = data
        return data

    def check_password(self, password):
        return self.make_hashed_password(password) == self.hashed_password

    def make_hashed_password(self, string):
        return str(hashlib.blake2b(str(string).encode()).hexdigest())

    def get_chats(self, only_id=False):
        return self.get_obj(self.chats, Chat, only_id=only_id)

    def get_communities(self, only_id=False):
        return self.get_obj(self.communities, Community, only_id=only_id)

    def get_courses(self, only_id=False):
        return self.get_obj(self.courses, Course, only_id=only_id)

    def get_friends(self, only_id=False):
        return self.get_obj(self.friends, User, only_id=only_id)

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


class Chat(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'chats'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=True)
    type = sql.Column(sql.String, nullable=False, default='personal')
    admin = sql.Column(sql.Integer, sql.ForeignKey('users.id'), nullable=True)
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')
    messages = orm.relationship('Message', backref='chat')
    main_photo = sql.Column(sql.Text, default='/static/img/profile-photo.jpg')

    def add_moderator(self, user_id):
        data = self.add_obj(self.moderators, user_id)
        if data:
            self.moderators = data
        return data

    def add_user(self, user_id):
        data = self.add_obj(self.users, user_id)
        if data:
            self.users = data
        return data

    def get_photo_url(self, current_user):
        if self.type == 'group':
            return self.main_photo
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return str(others[0].profile_photo)
        return str(current_user.profile_photo)

    def get_title(self, current_user):
        if self.type == 'group':
            return self.title
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return f"{others[0].first_name} {others[0].last_name}"
        return f"{current_user.first_name} {current_user.last_name}"

    def get_moderators(self, only_id=False):
        return self.get_obj(self.moderators, User, only_id=only_id)

    def get_users(self, only_id=False):
        return self.get_obj(self.users, User, only_id=only_id)

    def is_admin(self, user_id):
        return user_id == self.admin and user_id is not None

    def is_moderator(self, user_id):
        moderators = self.extract_ids(self.moderators)
        return user_id in moderators

    def set_admin(self, user_id):
        if not isinstance(user_id, int):
            return False
        self.add_moderator(self.admin)
        self.admin = user_id


class Message(SqlAlchemyBase, SerializerMixin, Model):
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
                  "month": str(writing_date.month).rjust(2, '0'),
                  "day": str(writing_date.day).rjust(2, '0'),
                  "hour": str(writing_date.hour).rjust(2, '0'),
                  "minute": str(writing_date.minute).rjust(2, '0'),
                  "text": message}
        return answer


class Community(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'communities'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    admin = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')
    chats = sql.Column(sql.Text, default='')
    communities = sql.Column(sql.Text, default='')
    main_photo = sql.Column(sql.Text, default='/static/img/profile-photo.jpg')

    def add_chat(self, chat_id):
        data = self.add_obj(self.chats, chat_id)
        if data:
            self.chats = data
        return data

    def add_community(self, community_id):
        data = self.add_obj(self.communities, community_id)
        if data:
            self.communities = data
        return data

    def add_moderator(self, user_id):
        data = self.add_obj(self.moderators, user_id)
        if data:
            self.moderators = data
        return data

    def add_user(self, user_id):
        data = self.add_obj(self.users, user_id)
        if data:
            self.users = data
        return data

    def get_chats(self, only_id=False):
        return self.get_obj(self.chats, Chat, only_id=only_id)

    def get_communities(self, only_id=False):
        return self.get_obj(self.communities, Community, only_id=only_id)

    def get_moderators(self, only_id=False):
        return self.get_obj(self.moderators, User, only_id=only_id)

    def get_users(self, only_id=False):
        return self.get_obj(self.users, User, only_id=only_id)

    def is_admin(self, user_id):
        return user_id == self.admin and user_id is not None

    def is_moderator(self, user_id):
        moderators = self.extract_ids(self.moderators)
        return user_id in moderators

    def set_admin(self, user_id):
        if not isinstance(user_id, int):
            return False
        self.add_moderator(self.admin)
        self.admin = user_id


class Course(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'courses'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    teacher = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    users = sql.Column(sql.Text, default='')
    posts = sql.Column(sql.Text, default='')
    lessons = sql.Column(sql.Text, default='')
    main_photo = sql.Column(sql.Text, default='/static/img/profile-photo.jpg')


