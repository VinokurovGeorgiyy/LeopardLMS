import sqlalchemy as sql
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase
from .db_session import create_session
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import hashlib
import datetime

_CREATOR_TYPES = {1: "USER", 2: "GROUP", 3: "COURSE"}

ALERT_TYPES = {100: "APPLICATION_FRIENDSHIP",
               101: "APPLICATION_GROUP_MEMBERSHIP",
               200: "INVITATION_CHAT_MEMBERSHIP",
               201: "INVITATION_COURSE_MEMBERSHIP",
               202: "INVITATION_GROUP_MEMBERSHIP",
               300: "NOTIFICATION_DANGER",
               301: "NOTIFICATION_INFO",
               302: "NOTIFICATION_SUCCESS",
               303: "NOTIFICATION_WARNING"}
CHAT_TYPES = {1: "PERSONAL", 2: "GROUP"}
COURSE_TYPES = {1: "OPENED", 2: "CLOSED"}
GROUP_TYPES = {1: "OPENED", 2: "CLOSED"}
USER_TYPES = {1: "USER", 2: "ADMIN"}

URLS = {"PROFILE_PHOTO_URL": "/static/img/profile-photo.jpg"}


class Model:
    def _add_obj(self, data, other_id, separator=";"):
        if not isinstance(other_id, int):
            return False
        separator = str(separator)
        data = self._extract_ids(data, separator)
        if other_id not in data:
            data.append(other_id)
            return self._compact_ids(data, separator)
        return False

    def _add_defined_obj(self, attribute, item_id, separator=";"):
        if not hasattr(self, attribute):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute '{attribute}'")
        data = self._add_obj(self.__getattribute__(attribute), item_id, separator)
        if data:
            self.__setattr__(attribute, data)
        return data

    def _compact_ids(self, data, separator=";"):
        return str(separator).join(map(str, data))

    def _delete_obj(self, data, item_id, separator=";"):
        data = self._get_obj(data, None, only_id=True, separator=separator)
        if item_id in data:
            data.remove(item_id)
            return self._compact_ids(data, separator)
        return None

    def _delete_defined_obj(self, attribute, item_id, separator=";"):
        if not hasattr(self, attribute):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute '{attribute}'")
        data = self._delete_obj(self.__getattribute__(attribute), item_id, separator)
        if data is not None:
            self.__setattr__(attribute, data)
        return data

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

    def _get_defined_obj(self, attribute, model_class, separator=';', only_id=False):
        if not hasattr(self, attribute):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute '{attribute}'")
        return self._get_obj(self.__getattribute__(attribute), model_class, separator, only_id)

    def add_alert(self, item_id):
        return self._add_defined_obj('alerts', item_id)

    def add_chat(self, item_id):
        return self._add_defined_obj('chats', item_id)

    def add_course(self, item_id):
        return self._add_defined_obj('courses', item_id)

    def add_group(self, item_id):
        return self._add_defined_obj('groups', item_id)

    def add_moderator(self, item_id):
        return self._add_defined_obj('moderators', item_id)

    def add_post(self, item_id):
        return self._add_defined_obj('posts', item_id)

    def add_user(self, item_id):
        return self._add_defined_obj('users', item_id)

    def check_admin(self, user_id):
        if not hasattr(self, 'admin'):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute 'admin'")
        return user_id == self.admin and user_id is not None

    def check_moderator(self, user_id):
        if not hasattr(self, 'moderators'):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute 'moderators'")
        return user_id in self.get_moderators(only_id=True)

    def delete_alert(self, item_id):
        return self._delete_defined_obj('alerts', item_id)

    def delete_chat(self, item_id):
        return self._delete_defined_obj('chats', item_id)

    def delete_course(self, item_id):
        return self._delete_defined_obj('courses', item_id)

    def delete_group(self, item_id):
        return self._delete_defined_obj('groups', item_id)

    def delete_moderator(self, item_id):
        return self._delete_defined_obj('moderators', item_id)

    def delete_post(self, item_id):
        return self._delete_defined_obj('posts', item_id)

    def delete_user(self, item_id):
        return self._delete_defined_obj('users', item_id)

    def get_alerts(self, only_id=False):
        return self._get_defined_obj('alerts', Alert, only_id=only_id)

    def get_chats(self, only_id=False):
        return self._get_defined_obj('chats', Chat, only_id=only_id)

    def get_courses(self, only_id=False):
        return self._get_defined_obj('courses', Course, only_id=only_id)

    def get_groups(self, only_id=False):
        return self._get_defined_obj('groups', Group, only_id=only_id)

    def get_moderators(self, only_id=False):
        return self._get_defined_obj('moderators', User, only_id=only_id)

    def get_posts(self, only_id=False):
        return self._get_defined_obj('posts', Post, only_id=only_id)

    def get_users(self, only_id=False):
        return self._get_defined_obj('users', User, only_id=only_id)

    def set_admin(self, user_id):
        if not hasattr(self, 'admin'):
            raise AttributeError(f"Class {self.__class__.__name__} "
                                 f"does not have attribute 'admin'")
        if not isinstance(user_id, int):
            return False
        self.add_moderator(self.admin)
        self.admin = user_id
        return True


class Alert(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'alerts'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    type = sql.Column(sql.Integer, nullable=False)
    creator_id = sql.Column(sql.Integer, nullable=False)
    creator_type = sql.Column(sql.Integer, nullable=False)
    recipients = sql.Column(sql.Text, default='')
    recipient_type = sql.Column(sql.Integer, nullable=False)

    def add_recipient(self, item_id):
        data = self._add_obj(self.recipients, item_id)
        if data:
            self.recipients = data
        return data

    def cancel(self):
        session = create_session()
        creator_class = self.get_creator_class()
        creator = session.query(creator_class).get(self.creator_id)
        if creator is not None:
            creator.delete_alert(self.id)
        for item_id in self.get_recipients(only_id=True):
            recipient_class = self.get_recipient_class()
            item = session.query(recipient_class).get(item_id)
            if item is not None:
                item.delete_alert(self.id)
                session.commit()

    def check_creator(self, item_id):
        return self.creator_id == item_id

    def check_recipient(self, item_id):
        return item_id in self.get_recipients(only_id=True)

    def delete_recipient(self, item_id):
        data = self._delete_obj(self.recipients, item_id)
        if data is not None:
            self.recipients = data
        return data

    def get_creator(self, only_id=False):
        if only_id:
            return self.creator_id
        model_class = self.get_creator_class()
        return create_session().query(model_class).get(self.creator_id)

    def get_creator_type(self):
        return _CREATOR_TYPES.get(self.creator_type, "USER")

    def get_creator_class(self):
        if self.get_creator_type() == "USER":
            return User
        if self.get_creator_type() == "GROUP":
            return Group
        if self.get_creator_type() == "COURSE":
            return Course
        return User

    def get_recipient_type(self):
        return _CREATOR_TYPES.get(self.recipient_type, "USER")

    def get_recipient_class(self):
        if self.get_recipient_type() == "USER":
            return User
        if self.get_recipient_type() == "GROUP":
            return Group
        if self.get_recipient_type() == "COURSE":
            return Course
        return User

    def get_recipients(self, only_id=False):
        if only_id:
            return self._get_obj(self.recipients, None, only_id=only_id)
        model_class = self.get_recipient_class()
        return self._get_obj(self.recipients, model_class, only_id=only_id)

    def get_type(self):
        return ALERT_TYPES.get(self.type, "NOTIFICATION_INFO")

    def is_application_friendship(self):
        return self.get_type() == "APPLICATION_FRIENDSHIP"

    def is_application_group_membership(self):
        return self.get_type() == "APPLICATION_GROUP_MEMBERSHIP"

    def is_invitation_chat_membership(self):
        return self.get_type() == "INVITATION_CHAT_MEMBERSHIP"

    def is_invitation_course_membership(self):
        return self.get_type() == "INVITATION_COURSE_MEMBERSHIP"

    def is_invitation_group_membership(self):
        return self.get_type() == "INVITATION_GROUP_MEMBERSHIP"

    def is_notification_danger(self):
        return self.get_type() == "NOTIFICATION_DANGER"

    def is_notification_info(self):
        return self.get_type() == "NOTIFICATION_INFO"

    def is_notification_success(self):
        return self.get_type() == "NOTIFICATION_SUCCESS"

    def is_notification_warning(self):
        return self.get_type() == "NOTIFICATION_WARNING"

    def set_creator_type(self, name):
        for key, value in _CREATOR_TYPES.items():
            if value == name.upper():
                self.creator_type = key
                return key
        self.creator_type = self.set_creator_type("USER")
        return self.creator_type

    def set_recipient_type(self, name):
        for key, value in _CREATOR_TYPES.items():
            if value == name.upper():
                self.recipient_type = key
                return key
        self.recipient_type = self.set_recipient_type("USER")
        return self.recipient_type

    def set_type(self, name):
        for key, value in ALERT_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("NOTIFICATION_INFO")
        return self.type

    def to_json(self):
        data = {"id": self.id}
        creator = self.get_creator()
        recipients = self.get_recipients()
        if self.is_application_friendship():
            data["creator"] = {"id": self.creator_id, "first_name": "???",
                               "last_name": "???", "profile_photo_url": "",
                               "name": "???"}
            data["recipient"] = {"id": 0, "first_name": "???", "name": "???",
                                 "last_name": "???", "profile_photo_url": ""}
        if creator:
            data["creator"] = creator.to_json()
        if recipients:
            data["recipient"] = recipients[0].to_json()
        return data


class Chat(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'chats'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=True)
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')
    messages = orm.relationship('Message', backref='chat')

    def check_user(self, user_id):
        return user_id in self.get_users(only_id=True)

    def get_profile_photo_url(self, current_user):
        if self.is_group():
            if self.profile_photo:
                return self.profile_photo
            return URLS.get("PROFILE_PHOTO_URL", "")
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return others[0].get_profile_photo_url()
        return current_user.get_profile_photo_url()

    def get_title(self, current_user):
        if self.is_group():
            return self.title
        others = [i for i in self.get_users() if i.id != current_user.id]
        if others:
            return f"{others[0].first_name} {others[0].last_name}"
        return f"{current_user.first_name} {current_user.last_name}"

    def get_type(self):
        return CHAT_TYPES.get(self.type, "GROUP")

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
        return self.type


class Course(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'courses'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=False)
    alerts = sql.Column(sql.Integer, default='')
    moderators = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')
    posts = sql.Column(sql.Text, default='')
    lessons = orm.relationship('Lesson', backref='course')

    def check_user(self, user_id):
        return user_id in self.get_users(only_id=True)

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS.get("PROFILE_PHOTO_URL", "")

    def get_type(self):
        return COURSE_TYPES.get(self.type, "OPENED")

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
        return self.type

    def to_json(self):
        data = {"id": self.id, "title": self.title, "type": self.get_type(),
                "description": self.description,
                "profile_photo_url": self.get_profile_photo_url()}
        return data


class Group(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'groups'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    description = sql.Column(sql.Text, default='')
    type = sql.Column(sql.Integer, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    admin = sql.Column(sql.Integer, nullable=False)
    moderators = sql.Column(sql.Text, default='')
    alerts = sql.Column(sql.Text, default='')
    users = sql.Column(sql.Text, default='')
    posts = sql.Column(sql.Text, default='')
    groups = sql.Column(sql.Text, default='')
    courses = sql.Column(sql.Text, default='')

    def check_user(self, user_id):
        return user_id in self.get_users(only_id=True)

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS.get("PROFILE_PHOTO_URL", "")

    def get_type(self):
        return GROUP_TYPES.get(self.type, "OPENED")

    def is_closed(self):
        return self.get_type() == "CLOSED"

    def is_opened(self):
        return self.get_type() == "OPENED"

    def membership_alert_exists(self, user_id):
        for item in self.get_alerts():
            if item.is_application_group_membership():
                if item.check_creator(user_id):
                    if item.check_recipient(self.id):
                        return item
        return None

    def set_type(self, name):
        for key, value in GROUP_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("OPENED")
        return self.type

    def to_json(self):
        data = {"id": self.id, "title": self.title, "type": self.get_type(),
                "description": self.description,
                "profile_photo_url": self.get_profile_photo_url()}
        return data


class Lesson(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'lessons'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    title = sql.Column(sql.String, nullable=False)
    course_id = sql.Column(sql.Integer, sql.ForeignKey('courses.id'))
    opened = sql.Column(sql.Boolean, default=False)


class Message(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'messages'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    author = sql.Column(sql.Integer, sql.ForeignKey('users.id'))
    text = sql.Column(sql.Text, nullable=False)
    date = sql.Column(sql.DateTime, default=datetime.datetime)
    chat_id = sql.Column(sql.Integer, sql.ForeignKey('chats.id'))

    def to_json(self):
        author = create_session().query(User).get(self.author)
        timezone = datetime.datetime.now(datetime.timezone.utc).astimezone()
        utc_offset = timezone.utcoffset() // datetime.timedelta(seconds=3600)
        writing_date = self.date + datetime.timedelta(hours=utc_offset)
        data = {"id": self.id,
                "author": {"id": self.author, "first_name": "???",
                           "last_name": "???", "profile_photo_url": ""},
                "date": {"year": writing_date.year,
                         "month": str(writing_date.month).rjust(2, '0'),
                         "day": str(writing_date.day).rjust(2, '0'),
                         "hour": str(writing_date.hour).rjust(2, '0'),
                         "minute": str(writing_date.minute).rjust(2, '0')},
                "text": self.text}
        if author:
            data["author"] = author.to_json()
        return data


class Post(SqlAlchemyBase, SerializerMixin, Model):
    __tablename__ = 'posts'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    creator_id = sql.Column(sql.Integer, nullable=False)
    creator_type = sql.Column(sql.Integer, nullable=False)
    date = sql.Column(sql.DateTime, default=datetime.datetime)
    content = sql.Column(sql.Text, default='')

    def check_creator(self, item):
        creator = self.get_creator()
        if creator is None or item is None:
            return False
        if type(item) != type(creator):
            return False
        if item.id != creator.id:
            return False
        return True

    def get_creator(self, only_id=False):
        if only_id:
            return self.creator_id
        creator = _CREATOR_TYPES.get(self.creator_type)
        if creator == "USER":
            return create_session().query(User).get(self.creator_id)
        if creator == "GROUP":
            return create_session().query(Group).get(self.creator_id)
        if creator == "COURSE":
            return create_session().query(Course).get(self.creator_id)
        return None


class User(SqlAlchemyBase, SerializerMixin, UserMixin, Model):
    __tablename__ = 'users'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    type = sql.Column(sql.Integer, nullable=False)
    email = sql.Column(sql.String, unique=True, nullable=False)
    hashed_password = sql.Column(sql.String, nullable=False)
    first_name = sql.Column(sql.String, nullable=False)
    last_name = sql.Column(sql.String, nullable=False)
    profile_photo = sql.Column(sql.Text, default='')

    blocked = sql.Column(sql.Boolean, default=False)

    alerts = sql.Column(sql.Text, default='')
    chats = sql.Column(sql.Text, default='')
    courses = sql.Column(sql.Text, default='')
    friends = sql.Column(sql.Text, default='')
    groups = sql.Column(sql.Text, default='')
    posts = sql.Column(sql.Text, default='')

    def add_friend(self, item_id):
        data = self._add_obj(self.friends, item_id)
        if data:
            self.friends = data
        return data

    def check_friend(self, user_id):
        return user_id in self.get_friends(only_id=True)

    def check_password(self, password):
        return self.make_password(password) == self.hashed_password

    def delete_friend(self, item_id):
        data = self._delete_obj(self.friends, item_id)
        if data is not None:
            self.friends = data
        return data

    def find_personal_chat(self, user_id):
        if user_id == self.id:
            return
        for chat in self.get_chats():
            if not chat.is_personal():
                continue
            users = chat.get_users(only_id=True)
            if len(users) == 2 and user_id in users and self.id in users:
                return chat

    def friendship_alert_exists(self, user_id):
        for item in self.get_alerts():
            if item.is_application_friendship():
                if item.check_creator(self.id):
                    if item.check_recipient(user_id):
                        return item
        return None

    def get_friends(self, only_id=False):
        return self._get_obj(self.friends, User, only_id=only_id)

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo
        return URLS.get("PROFILE_PHOTO_URL", "")

    def get_type(self):
        return USER_TYPES.get(self.type, "USER")

    def is_admin(self):
        return self.get_type() == "ADMIN"

    def is_blocked(self):
        return self.blocked

    def is_user(self):
        return self.get_type() == "USER"

    def make_password(self, string):
        return str(hashlib.blake2b(str(string).encode()).hexdigest())

    def set_type(self, name):
        for key, value in USER_TYPES.items():
            if value == name.upper():
                self.type = key
                return key
        self.type = self.set_type("USER")
        return self.type

    def to_json(self):
        data = {"id": self.id, "name": f"{self.first_name} {self.last_name}",
                "first_name": self.first_name, "last_name": self.last_name,
                "profile_photo_url": self.get_profile_photo_url()}
        return data
