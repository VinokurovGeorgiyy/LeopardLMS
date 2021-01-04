import sqlalchemy as sql
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase
from .db_session import create_session
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib
import datetime

CHAT_TYPES = {1: "PERSONAL", 2: "GROUP"}
COURSE_TYPES = {1: "OPENED", 2: "CLOSED"}
GROUP_TYPES = {1: "OPENED", 2: "CLOSED"}
NOTIFICATION_TYPES = {1: "NONE", 2: "FRIENDSHIP"}
POST_TYPES = {1: "PERSONAL", 2: "GROUP", 3: "COURSE"}
USER_STATUSES = {1: "USER", 2: "ADMIN"}

URLS = {"PROFILE_PHOTO_URL": "/static/img/profile-photo.jpg"}


class Model:
    def _add_obj(self, data, other_id, separator=";"):
        separator = str(separator)
        if not isinstance(other_id, int):
            return False
        data = self._extract_ids(data, separator)
        if other_id not in data:
            data.append(other_id)
            return self._compact_ids(data, separator)
        return False

    def _compact_ids(self, data, separator=";"):
        return separator.join(map(str, data))

    def _delete_obj(self, data, item_id, separator=";"):
        data = self._get_obj(data, None, only_id=True, separator=separator)
        if item_id in data:
            data.remove(item_id)
            return self._compact_ids(data, separator)
        return None

    def _extract_ids(self, data, separator=";"):
        data = [] if data is None else data.split(separator)
        data = filter(lambda x: x, data)
        return list(map(int, data))

    def _get_obj(self, data, model_class, separator=';', only_id=False):
        session = create_session()
        data = self._extract_ids(data, separator)
        if not only_id:
            data = map(session.query(model_class).get, data)
        return list(filter(lambda x: x is not None, data))

    def add_course(self, course_id):
        if not hasattr(self, 'courses'):
            return
        data = self._add_obj(self.courses, course_id)
        if data:
            self.courses = data
        return data

    def add_group(self, group_id):
        if not hasattr(self, 'groups'):
            return
        data = self._add_obj(self.groups, group_id)
        if data:
            self.groups = data
        return data

    def add_moderator(self, user_id):
        if not hasattr(self, 'moderators'):
            return
        data = self._add_obj(self.moderators, user_id)
        if data:
            self.moderators = data
        return data

    def add_user(self, user_id):
        if not hasattr(self, 'users'):
            return
        data = self._add_obj(self.users, user_id)
        if data:
            self.users = data
        return data

    def check_admin(self, user_id):
        if not hasattr(self, 'admin'):
            return False
        return user_id == self.admin and user_id is not None

    def check_moderator(self, user_id):
        if not hasattr(self, 'moderators'):
            return False
        moderators = self._extract_ids(self.moderators)
        return user_id in moderators

    def get_courses(self, only_id=False):
        if not hasattr(self, 'courses'):
            return []
        return self._get_obj(self.courses, Course, only_id=only_id)

    def get_groups(self, only_id=False):
        if not hasattr(self, 'groups'):
            return []
        return self._get_obj(self.groups, Group, only_id=only_id)

    def get_moderators(self, only_id=False):
        if not hasattr(self, 'moderators'):
            return []
        return self._get_obj(self.moderators, User, only_id=only_id)

    def get_users(self, only_id=False):
        if not hasattr(self, 'users'):
            return []
        return self._get_obj(self.users, User, only_id=only_id)

    def set_admin(self, user_id):
        if not hasattr(self, 'admin'):
            return False
        if not isinstance(user_id, int):
            return False
        self.add_moderator(self.admin)
        self.admin = user_id


class Notification(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'notifications'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    type = sql.Column(sql.Integer, nullable=False)
    sender = sql.Column(sql.Integer, nullable=True)  # user, group or course
    recipients = sql.Column(sql.Text, default='')  # users

    def add_recipient(self, item_id):
        data = self._add_obj(self.recipients, item_id)
        if data:
            self.recipients = data
        return data

    def cancel(self):
        session = create_session()
        for item_id in self.get_recipients(only_id=True):
            item = session.query(User).get(item_id)
            item.delete_notification(self.id)
            session.commit()

    def get_sender(self, only_id=False):
        session = create_session()
        if only_id:
            return self.sender
        if self.is_friendship():
            return session.query(User).get(self.sender)

    def get_recipients(self, only_id=False):
        return self._get_obj(self.recipients, User, only_id=only_id)

    def get_type(self):
        return NOTIFICATION_TYPES[self.type]

    def is_friendship(self):
        return self.get_type() == "FRIENDSHIP"

    def send(self):
        session = create_session()
        for item_id in self.get_recipients(only_id=True):
            item = session.query(User).get(item_id)
            item.add_notification(self.id)
            session.commit()

    def set_type(self, name):
        for key, value in NOTIFICATION_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("NONE")
        return False


class User(SqlAlchemyBase, UserMixin, SerializerMixin, Model):
    __tablename__ = 'users'

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    last_name = sql.Column(sql.String, nullable=False)
    first_name = sql.Column(sql.String, nullable=False)
    patronymic = sql.Column(sql.String, nullable=True)
    email = sql.Column(sql.String, unique=True, nullable=False)
    hashed_password = sql.Column(sql.String, nullable=False)
    status = sql.Column(sql.Integer, nullable=False)
    blocked = sql.Column(sql.Boolean, default=False)
    profile_photo = sql.Column(sql.Text, default='')

    friends = sql.Column(sql.Text, default='')
    notifications = sql.Column(sql.Text, default='')
    posts = orm.relationship('Post', backref='user')
    chats = sql.Column(sql.Text, default='')
    groups = sql.Column(sql.Text, default='')
    courses = sql.Column(sql.Text, default='')

    def add_chat(self, chat_id):
        data = self._add_obj(self.chats, chat_id)
        if data:
            self.chats = data
        return data

    def add_friend(self, user_id):
        data = self._add_obj(self.friends, user_id)
        if data:
            self.friends = data
        return data

    def add_notification(self, notification_id):
        data = self._add_obj(self.notifications, notification_id)
        if data:
            self.notifications = data
        return data

    def check_password(self, password):
        return self.make_password(password) == self.hashed_password

    def delete_friend(self, item_id):
        data = self._delete_obj(self.friends, item_id)
        if data is not None:
            self.friends = data
        return data

    def delete_notification(self, item_id):
        data = self._delete_obj(self.notifications, item_id)
        if data is not None:
            self.notifications = data
        return data

    def find_personal_chat(self, user_id):
        if user_id == self.id:
            return
        for chat in self.get_chats():
            if not chat.is_personal():
                continue
            users = chat.get_users(only_id=True)
            if len(users) == 2:
                if user_id not in users:
                    continue
                if self.id not in users:
                    continue
                return chat

    def friendship_notification_exists(self, user_id):
        for item in self.get_notifications():
            if item.is_friendship():
                if item.sender == self.id and user_id in item.get_recipients(True):
                    return item
        return None

    def get_chats(self, only_id=False):
        return self._get_obj(self.chats, Chat, only_id=only_id)

    def get_friends(self, only_id=False):
        return self._get_obj(self.friends, User, only_id=only_id)

    def get_notifications(self, only_id=False):
        return self._get_obj(self.notifications, Notification, only_id=only_id)

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS["PROFILE_PHOTO_URL"]

    def get_status(self):
        return USER_STATUSES[self.status]

    def is_admin(self):
        return self.get_status() == "ADMIN"

    def is_blocked(self):
        return self.blocked

    def is_user(self):
        return self.get_status() == "USER"

    def make_password(self, string):
        return str(hashlib.blake2b(str(string).encode()).hexdigest())

    def set_status(self, name):
        for key, value in USER_STATUSES.items():
            if value == name.upper():
                self.status = key
                return key
        self.status = self.set_status("USER")
        return False


class Chat(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'chats'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=True)
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=True)  # user
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')

    messages = orm.relationship('Message', backref='chat')

    def get_profile_photo_url(self, current_user):
        if self.is_group():
            if self.profile_photo:
                return self.profile_photo
            return URLS["PROFILE_PHOTO_URL"]
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return str(others[0].get_profile_photo_url())
        return str(current_user.get_profile_photo_url())

    def get_title(self, current_user):
        if self.is_group():
            return self.title
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return f"{others[0].first_name} {others[0].last_name}"
        return f"{current_user.first_name} {current_user.last_name}"

    def get_type(self):
        return CHAT_TYPES[self.type]

    def is_group(self):
        return self.get_type() == "GROUP"

    def is_personal(self):
        return self.get_type() == "PERSONAL"

    def set_type(self, name):
        for key, value in CHAT_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("GROUP")
        return False


class Message(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'messages'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    author = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    text = sql.Column(sql.Text, nullable=False)
    date = sql.Column(sql.DateTime, default=datetime.datetime)
    chat_id = sql.Column(sql.Integer, sql.ForeignKey('chats.id'))

    def get_json(self):
        session = create_session()
        author = session.query(User).get(self.author)
        first_name = author.first_name if author is not None else 'NONE'
        last_name = author.last_name if author is not None else 'NONE'
        photo = author.get_profile_photo_url() if author is not None else ''

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


class Post(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'posts'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    type = sql.Column(sql.Integer, nullable=False)

    user_id = sql.Column(sql.Integer, sql.ForeignKey('users.id'), nullable=True)
    course_id = sql.Column(sql.Integer, sql.ForeignKey('courses.id'), nullable=True)
    group_id = sql.Column(sql.Integer, sql.ForeignKey('groups.id'), nullable=True)

    date = sql.Column(sql.DateTime, default=datetime.datetime)
    content = sql.Column(sql.Text, default='')

    def get_type(self):
        return POST_TYPES[self.type]

    def is_course(self):
        return self.get_type() == "COURSE"

    def is_group(self):
        return self.get_type() == "GROUP"

    def is_personal(self):
        return self.get_type() == "PERSONAL"

    def set_type(self, name):
        for key, value in POST_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("PERSONAL")
        return False


class Group(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'groups'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=False)  # user
    parent_group = sql.Column(sql.Integer, nullable=True)
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')

    posts = orm.relationship('Post', backref='group')
    groups = sql.Column(sql.Text, default='')
    courses = sql.Column(sql.Text, default='')

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS["PROFILE_PHOTO_URL"]

    def get_type(self):
        return GROUP_TYPES[self.type]

    def is_closed(self):
        return self.get_type() == "CLOSED"

    def is_opened(self):
        return self.get_type() == "OPENED"

    def set_type(self, name):
        for key, value in GROUP_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("OPENED")
        return False


class Course(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'courses'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=False)  # user
    parent_group = sql.Column(sql.Integer, nullable=True)
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')

    posts = orm.relationship('Post', backref='course')
    lessons = orm.relationship('Lesson', backref='course')

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS["PROFILE_PHOTO_URL"]

    def get_type(self):
        return COURSE_TYPES[self.type]

    def is_closed(self):
        return self.get_type() == "CLOSED"

    def is_opened(self):
        return self.get_type() == "OPENED"

    def set_type(self, name):
        for key, value in COURSE_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("OPENED")
        return False


class Lesson(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'lessons'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    course_id = sql.Column(sql.Integer, sql.ForeignKey('courses.id'))
    opened = sql.Column(sql.Boolean, default=False)
