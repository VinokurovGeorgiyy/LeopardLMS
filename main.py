# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, abort, jsonify, request
from flask_login import LoginManager, login_user, current_user, logout_user
from werkzeug.utils import secure_filename

from forms import *

from data import db_session
from data.users import User
from data.user_statuses import UserStatus
from data.schools import School
from data.groups import Group
from data.chats import Chat
from data.messages import Message
from data.courses import Course
from data.lessons import Lesson
from data.solutions import Solution
from data.notifications import Notification

import json
import datetime
import os
import hashlib
from random import choice
USERS_STATUSES = ['system-manager', 'admin', 'director', 'teacher', 'student']


class Application(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        db_session.global_init("db/leopard_lms.sqlite")
        print('--------------------- INITIALISATION ---------------------')
        statuses = USERS_STATUSES[:]
        users = [{'first_name': 'Manager', 'last_name': 'System',
                  'email': 'leopard.hq@yandex.ru', 'status': 1,
                  'hashed_password': '874800ba296315ee2f8e69033aaedbdbb9603b6'
                                     '2b263f1496b9b6a731ebbf18e650fcfaf720dae'
                                     'a9425133959197b1bf769a9c3e568c8127208f7'
                                     'f0989f0d745'}
                 ]
        for title in statuses:
            session, t = db_session.create_session(), title
            exist = session.query(UserStatus).filter(UserStatus.title == t)
            exist = exist.all()
            if not exist:
                status = UserStatus()
                status.title = title
                session.add(status), session.commit()
        for data in users:
            session, email = db_session.create_session(), data['email']
            exist = session.query(User).filter(User.email == email).all()
            if not exist:
                user = User()
                for key, val in data.items():
                    user.__setattr__(key, val)
                session.add(user), session.commit()


app = Application(__name__)
app.config['SECRET_KEY'] = 'We`ll always stay together, You and I...'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
login_manager = LoginManager()
login_manager.init_app(app)


def get_current_user_courses(sess):
    """Возвращает все курсы (предметы), которые есть у пользователя"""
    if current_user.status == 5:
        data = sess.query(Course).filter(Course.group == current_user.group)
        data = [(x, sess.query(User).get(x.teacher)) for x in data.all()]
    elif current_user.status < 5:
        data = sess.query(Course).filter(Course.teacher == current_user.id)
        data = [(x, sess.query(Group).get(x.group)) for x in data.all()]
    else:
        data = []
    return data


def user_exists(sess, user_id):
    """Проверяет, существует ли пользователь. Если нет - сообщает об ошибке"""
    user = sess.query(User).get(user_id)
    if not user:
        abort(404)
    return user


def group_exists(sess, group_id):
    """Проверяет, существует ли группа. Если нет - сообщает об ошибке"""
    group = sess.query(Group).get(group_id)
    if not group:
        abort(404)
    return group


def school_exists(sess, school_id):
    """Проверяет, существует ли школа. Если нет - сообщает об ошибке"""
    school = sess.query(School).get(school_id)
    if not school:
        abort(404)
    return school


def course_exists(sess, course_id):
    """Проверяет, существует ли курс. Если нет - сообщает об ошибке"""
    course = sess.query(Course).get(course_id)
    if not course:
        abort(404)
    return course


def lesson_exists(sess, lesson_id):
    """Проверяет, существует ли урок. Если нет - сообщает об ошибке"""
    lesson = sess.query(Lesson).get(lesson_id)
    if not lesson:
        abort(404)
    return lesson


def make_hashed_password(string):
    """Шифрует пароль"""
    return str(hashlib.blake2b(string.encode()).hexdigest())


def safe_slice(data, start, end):
    """Делает безопасный срез множества"""
    try:
        data = data[start:end]
    except Exception:
        data = []
    finally:
        return data


def add_user(session, status):
    """Добавляет пользователя в систему"""
    form = UserRegistrationForm()
    if form.validate_on_submit():
        session, email = session, form.email.data
        exist = session.query(User).filter(User.email == email).first()
        if exist:
            message = 'Пользователь с таким логином уже существует'
            return 'ERROR', {'form': form, 'message': message}
        user = User()
        user.email, user.last_name = form.email.data, form.last_name.data
        user.first_name = form.first_name.data
        user.patronymic = form.patronymic.data
        correct_password = check_correct_password(str(form.password.data))
        if correct_password.get('error'):
            message = correct_password['error']
            return 'ERROR', {'form': form, 'message': message}
        user.hashed_password = make_hashed_password(str(form.password.data))
        user.status = USERS_STATUSES.index(status) + 1
        session.add(user), session.commit()
        user = session.query(User).filter(User.email == email).first()
        return 'FINISHED', {'user_id': user.id}
    return 'STARTED', {'form': form}


def get_chat_name(session, chat, chat_members, current_user):
    """Возвращает имя чата"""
    name = chat.title
    if name is None:
        name = [x for x in chat_members if x != current_user.id]
        name = name[0] if name else None
        name = session.query(User).get(name) if name is not None else None
        name = f'{name.first_name} {name.last_name}' if name else None
    return name


def get_chats(last_message_length):
    """Возвращает чаты пользователя в удобном формате"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    user = user_exists(sess, current_user.id)
    chats = user.chats.split() if user.chats else []
    chats = [sess.query(Chat).get(int(x)) for x in chats]
    chats = [x for x in chats if x is not None]
    for i in range(len(chats)):
        members = [] if chats[i].members is None else \
            [int(i) for i in chats[i].members.split()]
        if len(members) < 3:
            photo = [x for x in members if x != current_user.id]
            photo = photo[0] if photo else None
            photo = None if photo is None else sess.query(User).get(photo)
            photo = photo.photo_url if photo is not None else ''
            photo = photo if photo else '/static/img/chat-photo.png'
        else:
            photo = chats[i].photo_url
        messages = chats[i].messages.split() if chats[i].messages else []
        last = int(messages[-1]) if messages else ''
        last_message = sess.query(Message).get(last) if last else ''
        last_message = last_message.text if last_message else ''
        last_message = last_message[:last_message_length]
        chat_name = get_chat_name(sess, chats[i], members, current_user)
        chats[i] = chats[i], chat_name, last_message, photo,
    return chats


def random_string(length):
    """Создаёт строку из слечайных символов.
    В основном - для сохранения загруженных на сервер файлов"""
    obj = 'abcdefghijklmnopqrstuvwxyz'
    obj += obj.upper() + '0123456789'
    return ''.join(choice(obj) for _ in range(length))


def upload_file(file, start, formats, secure_length):
    """Сохраняет файл на сервер"""
    filename = secure_filename(file.filename)
    file_type = str(filename)[str(filename).rfind('.') + 1:]
    if file_type not in formats.split('|') and formats != '*':
        return {'error': 'Формат файла не поддерживается'}
    number = random_string(secure_length)
    filename = f'{start}-{current_user.id}-{number}.{file_type}'
    path_to_file = app.config['UPLOAD_FOLDER'] + '/' + filename
    file.save(path_to_file)
    return {'ok': path_to_file}


def get_user_navbar(sess):
    school, group = current_user.school, current_user.group
    status, courses = current_user.status, get_current_user_courses(sess)
    navbar = [{'text': 'Профиль', 'href': '/'},
              {'text': 'Сообщения', 'href': '/chats'},
              {'text': 'Школы', 'href': '/schools'},
              {'text': 'Пользователи', 'href': '/users'}]
    if school:
        navbar.append({'text': 'Моя школа', 'href': '/my-school'})
    if group:
        navbar.append({'text': 'Мой класс', 'href': '/my-group'})
    if status <= 5 and courses:
        navbar.append({'text': 'Мои предметы', 'href': '/my-courses'})
    return navbar


def check_correct_password(password):
    if len(password) < 8:
        return {'error': 'Пароль короче 8 символов'}
    if password.lower() == password or password.upper() == password:
        return {'error': 'Все символы в пароле одного регистра'}
    if not any([x in password for x in '0123456789']):
        return {'error': 'Пароль должен иметь хотя бы одну цифру'}
    return {'ok': 'Success'}


# --------------------------------------------------
# PAGES
# --------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Главная страница + страница авторизации"""
    if current_user.is_authenticated:
        return redirect(f'/id-{current_user.id}')
    form = LoginForm()
    params = {'title': 'Авторизация', 'form': form, 'message': ''}
    if form.validate_on_submit():
        session, email = db_session.create_session(), form.email.data
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            return redirect(f'/id-{current_user.id}')
        params['message'] = "Неправильный логин или пароль"
        return render_template('login.html', **params)
    return render_template('login.html', **params)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/id-<int:user_id>')
def user_profile(user_id):
    """Профиль пользователя"""
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    user = user_exists(session, user_id)
    rus_statuses = {'system-manager': 'Системный администратор',
                    'admin': 'Администратор', 'director': 'Директор',
                    'teacher': 'Учитель', 'student': 'Ученик'}
    school = session.query(School).get(user.school) if user.school else None
    group = session.query(Group).get(user.group) if user.group else None
    data = user.notifications.split() if user.notifications else []
    data = [session.query(Notification).get(int(i)) for i in data if i]
    data = [x for x in data if x is not None]
    right1 = current_user.status == 3 and current_user.school == user.school
    right2 = current_user.status < 3
    right_to_delete = (right1 or right2) and current_user.id != user.id
    params = {'title': f'{user.last_name} {user.first_name}', 'user': user,
              'status': rus_statuses[USERS_STATUSES[user.status - 1]],
              'school': school, 'group': group, 'current_user': current_user,
              'navbar': get_user_navbar(session), 'notifications': data,
              'right_to_delete': right_to_delete}
    return render_template('user.html', **params)


@app.route('/my-school')
def my_school():
    if current_user.school is not None:
        return redirect(f'/school-{current_user.school}')
    abort(404)


@app.route('/my-group')
def my_group():
    if current_user.group is not None:
        return redirect(f'/group-{current_user.group}')
    abort(404)


@app.route('/my-courses')
def my_courses():
    if not current_user.is_authenticated:
        return redirect('/')
    data = get_current_user_courses(db_session.create_session())
    if not data:
        abort(404)
    courses = sorted(data, key=lambda x: x[0].title)
    params = {'navbar': get_user_navbar(db_session.create_session()),
              'data': courses, 'user': current_user, 'title': 'Мои предметы'}
    return render_template('my_courses.html', **params)


@app.route('/school-<int:school_id>')
def school_profile(school_id):
    """Профиль школы"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school = school_exists(sess, school_id)
    director = sess.query(User).get(school.director)
    params = {'navbar': get_user_navbar(sess), 'title': school.short_title,
              'school': school, 'director': director, 'user': current_user}
    return render_template('school.html', **params)


@app.route('/group-<int:group_id>')
def group_profile(group_id):
    """Профиль группы (класса)"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    group = group_exists(sess, group_id)
    leader = sess.query(User).get(group.leader)
    school = sess.query(School).get(group.school_id)
    students = sess.query(User).filter(User.group == group_id)
    students = students.filter(User.status == 5).all()
    students = sorted(students, key=lambda x: f'{x.last_name} {x.first_name}')
    params = {'title': group.title, 'students': students, 'school': school,
              'current_user': current_user, 'leader': leader, 'group': group,
              'navbar': get_user_navbar(sess)}
    return render_template('group.html', **params)


@app.route('/school-<int:sch_id>-<obj>')
def get_school_objects(sch_id, obj):
    return redirect(f'/school-{sch_id}-{obj}-page-1')


@app.route('/school-<int:school_id>-<obj>-page-<int:page_number>')
def get_school_objects_with_page(school_id, obj, page_number):
    """Отображает список классов, учителей, учеников в школе,
    загружая при этом данные в определённом диапазоне"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    sch = school_exists(sess, school_id)
    if obj == 'groups':
        data = sess.query(Group).filter(Group.school_id == sch.id)
        data = sorted(data.all(), key=lambda x: x.title)
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        data = [(x, sess.query(User).get(int(x.leader))) for x in data]
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'user': current_user, 'navbar': get_user_navbar(sess)}
        return render_template('school_groups.html', **params)
    if obj == 'teachers':
        data = sess.query(User).filter(User.school == sch.id)
        data = data.filter(User.status == 4).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'user': current_user, 'navbar': get_user_navbar(sess)}
        return render_template('school_teachers.html', **params)
    if obj == 'students':
        data = sess.query(User).filter(User.school == sch.id)
        n = data.filter(User.status == 5).count() // 20 + 1
        data = data.filter(User.status == 5).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        data = [(x, sess.query(Group).get(x.group)) for x in data]
        params = {'data': data, 'sch': sch, 'n_pages': n, 'current_page': pg,
                  'title': sch.short_title, 'navbar': get_user_navbar(sess)}
        return render_template('school_students.html', **params)
    abort(404)


@app.route('/schools')
def get_all_schools():
    return redirect('/schools-page-1')


@app.route('/schools-page-<int:page_number>')
def get_all_schools_with_page(page_number):
    """Отображает список всех школы в системе"""
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    schools = sorted(session.query(School).all(), key=lambda x: x.short_title)
    schools = safe_slice(schools, 20 * (pg - 1), 20 * pg)
    n = session.query(School).count() // 20 + 1
    schools = [(i, session.query(User).get(i.director)) for i in schools]
    params = {'schools': schools, 'title': 'Школы', 'n_pages': n,
              'current_page': pg, 'navbar': get_user_navbar(session)}
    return render_template('all_schools.html', **params)


@app.route('/add-school', methods=['GET', 'POST'])
def add_school():
    """Позволяет добавить школу в систему"""
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 2:
        abort(403)
    form, session = SchoolRegistrationForm(), db_session.create_session()
    params = {'title': 'Регистрация', 'form': form, 'message': '',
              'navbar': get_user_navbar(session)}
    if form.validate_on_submit():
        title = form.title.data
        exist = session.query(School).filter(School.title == title).first()
        if exist:
            params['message'] = 'Организация с таким именем уже существует'
            return render_template('add_school.html', **params)
        sch, director = School(), form.director.data
        exist = session.query(User).filter(User.id == director).first()
        if not exist:
            params['message'] = f'Пользователя с ID {director} не существует!'
            return render_template('add_school.html', **params)
        if exist.status > 3:
            params['message'] = 'Статус пользователя ниже статуса "Директор"'
            return render_template('add_school.html', **params)
        if exist.school is not None:
            params['message'] = f'Пользователь из другой школы'
            return render_template('add_school.html', **params)
        sch.email, sch.title = form.email.data, form.title.data
        sch.short_title, sch.director = form.short_title.data, director
        sch.index, sch.region = form.index.data, form.region.data
        sch.city, sch.street = form.city.data, form.street.data
        sch.house, sch.phone = form.house.data, form.phone.data
        session.add(sch), session.commit()
        sch = session.query(School).filter(School.title == title).first()
        exist.school = sch.id
        session.commit()
        return redirect(f'/school-{sch.id}')
    return render_template('add_school.html', **params)


@app.route('/school-<int:school_id>-add-group', methods=['GET', 'POST'])
def add_group_to_school(school_id):
    """Добавляет новую группу (класс) в школу"""
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 3:
        abort(403)
    sess = db_session.create_session()
    sch = school_exists(sess, school_id)
    if current_user.id != sch.director and current_user.status > 2:
        abort(403)
    form = GroupRegistrationForm()
    params = {'form': form, 'title': 'Добавление класса', 'message': '',
              'navbar': get_user_navbar(sess)}
    if form.validate_on_submit():
        exist = sess.query(Group).filter(Group.school_id == sch.id)
        exist = exist.filter(Group.title == form.title.data).first()
        if exist:
            params['message'] = 'Такой класс уже существует в данной школе'
            return render_template('add_group.html', **params)
        leader = sess.query(User).get(form.leader.data)
        if not leader:
            params['message'] = f'Пользователя с ID {leader} не существует!'
            return render_template('add_group.html', **params)
        if leader.status > 4:
            params['message'] = 'Статус пользователя ниже статуса "Учитель"'
            return render_template('add_group.html', **params)
        if leader.school != sch.id:
            params['message'] = 'Пользователь не из данной школы'
            return render_template('add_group.html', **params)
        group = Group()
        group.title, group.leader = form.title.data, form.leader.data
        group.school_id = sch.id
        sess.add(group), sess.commit()
        group = sess.query(Group).filter(Group.school_id == sch.id)
        group = group.filter(Group.title == form.title.data).first()
        leader.group = group.id
        sess.commit()
        return redirect(f'/school-{sch.id}-groups')
    return render_template('add_group.html', **params)


@app.route('/school-<int:school_id>-add-teacher', methods=['GET', 'POST'])
def add_teacher_to_school(school_id):
    """Добавляет нового пользователя 'Учитель' в школу"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school, navbar = school_exists(sess, school_id), get_user_navbar(sess)
    params = {'title': 'Регистрация', 'status': 'Учитель', 'navbar': navbar}
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    response = add_user(sess, 'teacher')
    if response[0] == 'FINISHED':
        user = sess.query(User).get(response[1]['user_id'])
        user.school = school.id
        sess.commit()
        return redirect(f'/school-{school.id}-teachers')
    if response[0] == 'ERROR':
        return render_template('add_user.html', **params, **response[1])
    return render_template('add_user.html', **params, **response[1])


@app.route('/add-<status>', methods=['GET', 'POST'])
def add_not_school_user(status):
    """Позволяет добавить 'Администратора' и 'Директора' в систему"""
    if not current_user.is_authenticated:
        return redirect('/')
    if status not in USERS_STATUSES[1:]:
        abort(404)
    if current_user.status >= USERS_STATUSES.index(status) + 1:
        abort(403)
    sess = db_session.create_session()
    response, navbar = add_user(sess, status), get_user_navbar(sess)
    name = {'admin': 'Администратор', 'director': 'Директор'}[status]
    params = {'title': 'Регистрация', 'status': name, 'navbar': navbar}
    if response[0] == 'FINISHED':
        user = sess.query(User).get(response[1]['user_id'])
        return redirect(f'/id-{user.id}')
    return render_template('add_user.html', **params, **response[1])


@app.route('/group-<int:group_id>-add-student', methods=['GET', 'POST'])
def add_student_to_group(group_id):
    """Позволяет добавить нового ученика в класс"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    group, navbar = group_exists(sess, group_id), get_user_navbar(sess)
    school = school_exists(sess, group.school_id)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    params = {'title': 'Регистрация', 'status': 'Ученик', 'navbar': navbar}
    response = add_user(sess, 'student')
    if response[0] == 'FINISHED':
        user = user_exists(sess, response[1]['user_id'])
        user.group, user.school = group.id, school.id
        sess.commit()
        return redirect(f'/group-{group.id}')
    if response[0] == 'ERROR':
        return render_template('add_user.html', **params, **response[1])
    return render_template('add_user.html', **params, **response[1])


@app.route('/chats')
def chats_list():
    """Отображает список чатов пользователя"""
    chats, nav = get_chats(50), get_user_navbar(db_session.create_session())
    params = {'title': 'Сообщения', 'chats': chats, 'navbar': nav}
    if isinstance(chats, list):
        return render_template('chats_list.html', **params)
    abort(404)


@app.route('/chat-<int:chat_id>', methods=['GET', 'POST'])
def chat_messages_list(chat_id):
    """Реализует чат пользователя"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    chat = sess.query(Chat).get(chat_id)
    if not chat:
        abort(404)
    members = [] if chat.members is None else \
        [int(i) for i in chat.members.split()]
    if current_user.id not in members:
        abort(403)
    user = user_exists(sess, current_user.id)
    chats = user.chats.split() if user.chats else []
    if str(chat.id) not in chats:
        chats.append(str(chat.id))
    user.chats = ' '.join(chats)
    sess.commit()
    form, chats = ChatForm(), get_chats(25)
    name = get_chat_name(sess, chat, members, current_user)
    params = {'form': form, 'chat_id': chat_id, 'chat_name': name,
              'title': f'Сообщения - {name}', 'chats': chats,
              'navbar': get_user_navbar(sess)}
    return render_template('chat.html', **params)


@app.route('/write-message-<int:addressee_id>')
def write_message(addressee_id):
    """Создаёт новый личный чат с другим пользователем"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    addressee = user_exists(sess, addressee_id)
    user = user_exists(sess, current_user.id)
    first, second = min(user.id, addressee_id), max(user.id, addressee_id)
    members = f'{first} {second}'
    chat = sess.query(Chat).filter(Chat.members == members).first()
    if not chat:
        chat = Chat()
        chat.members, chat.messages = members, ''
        sess.add(chat), sess.commit()
        chat = sess.query(Chat).filter(Chat.members == members).first()
        chats = user.chats.split() if user.chats else []
        chats.append(str(chat.id))
        user.chats = ' '.join(chats)
        chats = addressee.chats.split() if addressee.chats else []
        chats.append(str(chat.id))
        addressee.chats = ' '.join(chats)
        sess.commit()
    return redirect(f'/chat-{chat.id}')


@app.route('/chat-form', methods=['POST'])
def chat_form():
    """Получает POST запрос от чата пользователя с сообщением и
    сохраняет данное сообщение"""
    if not current_user.is_authenticated:
        return """"""
    data = request.json
    if data:
        message, chat_id = data.get('message'), data.get('chat')
        if not message:
            return """"""
        sess = db_session.create_session()
        chat = sess.query(Chat).get(chat_id)
        if not chat:
            abort(404)
        members = [] if chat.members is None else \
            [int(i) for i in chat.members.split()]
        if current_user.id not in members and members:
            abort(403)
        full_message = Message()
        full_message.text, full_message.writer = message, current_user.id
        full_message.chat = chat.id
        full_message.data = date = datetime.datetime.utcnow()
        sess.add(full_message), sess.commit()
        message = sess.query(Message).filter(Message.chat == chat_id)
        message = message.filter(Message.writer == current_user.id)
        message = message.filter(Message.data == date).first()
        messages = [] if chat.messages is None else \
            [int(i) for i in chat.messages.split()]
        messages.append(message.id)
        chat.messages = ' '.join(map(str, messages))
        sess.commit()
    return """"""


@app.route('/get-all-messages-chat-<int:chat_id>-<int:mode>')
def get_all_messages_in_chat(chat_id, mode):
    """Получает GET запрос для отображения всех сообщений чата
    и формирует ответ в формате HTML"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    chat = sess.query(Chat).get(chat_id)
    if not chat:
        abort(404)
    members = [] if chat.members is None else \
        [int(i) for i in chat.members.split()]
    if current_user.id not in members:
        abort(403)
    messages = [] if chat.messages is None else \
        [sess.query(Message).get(int(i)) for i in chat.messages.split()]
    messages, answer = [i for i in messages if i is not None], ''
    if not mode:
        return f'{len(messages)}'
    for i in range(len(messages)):
        author = sess.query(User).get(messages[i].writer)
        d = datetime.datetime.now(datetime.timezone.utc).astimezone()
        utc_offset = d.utcoffset() // datetime.timedelta(seconds=3600)
        result = messages[i].data + datetime.timedelta(hours=utc_offset)
        photo = author.photo_url if author is not None else ''
        author = author.first_name if author is not None else 'Кто-то'
        text = messages[i].text
        hour, minute = result.hour, result.minute
        date = f'{result.day}.{result.month}.{result.year}'
        photo = '/static/img/user-photo.png' if not photo else photo
        params = {'message': messages[i], 'current_user': current_user,
                  'author': author, 'date': date, 'hour': hour, 'text': text,
                  'photo': photo, 'minute': minute}
        answer += render_template('message.html', **params)
    return answer


@app.route('/del-message-<int:m_id>', methods=['DELETE'])
def delete_message(m_id):
    """Получает DELETE запрос на удаление сообщения и удаляет его из БД"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    message = sess.query(Message).get(m_id)
    if not message:
        return """"""
    chat = sess.query(Chat).get(message.chat)
    if not chat:
        return """"""
    if message.writer != current_user.id:
        return """"""
    members = [] if chat.members is None else \
        [int(i) for i in chat.members.split()]
    if current_user.id not in members:
        return """"""
    messages = [] if chat.messages is None else \
        [int(i) for i in chat.messages.split()]
    if message.id in messages:
        messages.remove(message.id)
        chat.messages = ' '.join(map(str, messages))
        sess.delete(message)
        sess.commit()
    return """"""


@app.route('/school-<int:school_id>-add-course', methods=['GET', 'POST'])
def add_course_to_school(school_id):
    """Позволяет добавить новый курс (предмет) в школу.
    Каждый курс предназначен для определённой группы учеников. Например,
    Курс Математика для 10 класса"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school = school_exists(sess, school_id)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    form = CourseRegistrationForm()
    params = {'form': form, 'title': 'Добавление курса', 'message': '',
              'navbar': get_user_navbar(sess)}
    if form.validate_on_submit():
        course = Course()
        course.title, course.school = form.title.data, school_id
        teacher = sess.query(User).get(form.teacher.data)
        if not teacher:
            params['message'] = f'Пользователь с ID {teacher.id} не найден!'
            return render_template('add_course.html', **params)
        if teacher.status > 4:
            params['message'] = 'Статус пользователя ниже статуса "Учитель"'
            return render_template('add_course.html', **params)
        if teacher.school != school_id:
            params['message'] = 'Пользователь не из данной школы'
            return render_template('add_course.html', **params)
        course.teacher, course.group = teacher.id, form.group.data
        sess.add(course), sess.commit()
        return redirect(f'/school-{school_id}-courses')
    return render_template('add_course.html', **params)


@app.route('/school-<int:school_id>-courses')
def get_school_courses(school_id):
    """Отображает все курсы в школе"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    sch = school_exists(sess, school_id)
    if not (current_user.id == sch.director or current_user.status < 3):
        abort(403)
    courses = sess.query(Course).filter(Course.school == sch.id).all()
    data = [(x, sess.query(Group).get(x.group)) for x in courses]
    data = [(x, y, sess.query(User).get(x.teacher)) for x, y in data]
    params = {'title': sch.short_title, 'data': data, 'sch': sch,
              'navbar': get_user_navbar(sess)}
    return render_template('school_courses.html', **params)


@app.route('/course-<int:course_id>')
def course_profile(course_id):
    """Отображает информацию об определённом курсе"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    course = course_exists(sess, course_id)
    sch = school_exists(sess, course.school)
    if not (current_user.id in [course.teacher, sch.director] or
            current_user.group == course.group and current_user.status == 5):
        abort(403)
    lessons = sess.query(Lesson).filter(Lesson.course == course.id)
    if current_user.status == 5:
        lessons = lessons.filter(Lesson.opened)
    lessons = sorted(lessons.all(), key=lambda x: x.lesson_number,
                     reverse=current_user.status == 5)
    rights = current_user.id in [course.teacher, sch.director]
    right_delete = current_user.id == sch.director or current_user.status < 3
    params = {'course': course, 'lessons': lessons, 'rights': rights,
              'title': course.title, 'navbar': get_user_navbar(sess),
              'right_to_delete': right_delete}
    return render_template('course.html', **params)


@app.route('/course-<int:course_id>-add-lesson', methods=['GET', 'POST'])
def add_lesson_to_course(course_id):
    """Позволяет добавить в курс новый урок"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    course = course_exists(sess, course_id)
    sch = school_exists(sess, course.school)
    if current_user.id not in [course.teacher, sch.director]:
        abort(403)
    form = LessonRegistrationForm()
    if form.validate_on_submit():
        lesson = Lesson()
        lesson.course, lesson.title = course_id, form.title.data
        lesson.lesson_number = form.lesson_number.data
        sess.add(lesson), sess.commit()
        return redirect(f'/course-{course_id}')
    params = {'title': 'Добавление урока', 'navbar': get_user_navbar(sess)}
    return render_template('add_lesson.html', **params, form=form)


@app.route('/lesson-<int:lesson_id>-open')
def open_lesson(lesson_id):
    """Делает урок доступным для просмотра учащимися группы курса"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if current_user.id not in [course.teacher, sch.director]:
        abort(403)
    lesson.opened = True
    text = f'Открыт новый урок: {course.title} - {lesson.title}'
    notify = Notification()
    notify.theme, notify.text = 'success', text
    sess.add(notify), sess.commit()
    notify = sess.query(Notification).filter(Notification.text == text).first()
    users = sess.query(User).filter(User.group == course.group).all()
    for user in users:
        user.notifications = user.notifications if user.notifications else ''
        user.notifications += f' {notify.id}' if notify is not None else ''
    sess.commit()
    return redirect(f'/course-{lesson.course}')


@app.route('/lesson-<int:lesson_id>-<mode>', methods=['GET', 'POST'])
def lesson_profile(lesson_id, mode):
    """Отображает информацию разделов урока"""
    if not current_user.is_authenticated:
        return redirect('/')
    if mode not in ['theory', 'task']:
        abort(404)
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if not (current_user.id in [course.teacher, sch.director] or
            current_user.group == course.group and current_user.status == 5):
        abort(403)
    right = current_user.id in [course.teacher, sch.director]
    params = {'lesson': lesson, 'right_of_edit': right, 'course': course,
              'title': lesson.title, 'navbar': get_user_navbar(sess)}
    if mode == 'theory':
        return render_template('lesson_theory.html', **params)
    form = LoadSolution()
    if form.validate_on_submit():
        file, message = form.doc.data, form.message.data
        path = upload_file(file, 'DOC', '*', 15).get('ok') if file else None
        if path or message:
            solution = Solution()
            solution.author, solution.lesson = current_user.id, lesson_id
            solution.message, solution.url = message, path
            solution.date = date = datetime.datetime.utcnow()
            sess.add(solution), sess.commit()
            solution = sess.query(Solution).filter(Solution.date == date)
            solution = solution.filter(Solution.author == current_user.id)
            solution = solution.filter(Solution.lesson == lesson_id).first()
            solutions = lesson.solutions.split() if lesson.solutions else []
            solutions.append(str(solution.id))
            lesson.solutions = ' '.join(solutions)
            sess.commit()
            return redirect(f'/lesson-{lesson_id}-task')
    return render_template('lesson_task.html', **params, form=form)


@app.route('/get-all-solutions-lesson-<int:lesson_id>-<int:mode>')
def get_all_solutions_from_lesson(lesson_id, mode):
    """Получает GET запрос для получения всех решений задания данного урока,
    отправленных учениками, а также сообщений чата задания"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if not (current_user.id in [course.teacher, sch.director] or
            current_user.group == course.group and current_user.status == 5):
        abort(403)
    solutions = lesson.solutions.split() if lesson.solutions else []
    solutions = [sess.query(Solution).get(int(i)) for i in solutions]
    solutions, answer = [x for x in solutions if x is not None], ''
    if not mode:
        return f'{len(solutions)}'
    for i in solutions:
        author = sess.query(User).get(i.author) if i.author else None
        if current_user.id != course.teacher:
            if author.id != current_user.id and author.id != course.teacher:
                continue
        photo = author.photo_url if author is not None else ''
        author = f'{author.first_name} {author.last_name}' if author else '?'
        d = datetime.datetime.now(datetime.timezone.utc).astimezone()
        utc_offset = d.utcoffset() // datetime.timedelta(seconds=3600)
        result = i.date + datetime.timedelta(hours=utc_offset)
        photo = '/static/img/user-photo.png' if not photo else photo
        params = {'author': author, 'photo': photo, 'date': result, 'data': i}
        answer += render_template('solution.html', **params)
    return answer


@app.route('/lesson-<int:lesson_id>-add-<material>', methods=['GET', 'POST'])
def add_theory_to_lesson(lesson_id, material):
    """Позволяет учителю создавать и редактировать материал урока"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if current_user.id not in [course.teacher, sch.director]:
        abort(403)
    form = EditLessonForm()
    if form.validate_on_submit():
        if material == 'theory':
            lesson.theory = form.code.data
        else:
            lesson.tasks = form.code.data
        sess.commit()
        return redirect(f'/lesson-{lesson_id}-{material}')
    params = {'title': 'Редактор', 'form': form, 'data': material,
              'lesson': lesson, 'navbar': get_user_navbar(sess)}
    return render_template('edit_lesson.html', **params)


@app.route('/lesson-<int:lesson_id>-get-<material>')
def get_theory_of_lesson(lesson_id, material):
    """Получает GET запрос на получения материала урока и возвращает ответ.
    Это необходимо для отображения строковых данных в виде HTML блока
    на странице урока"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = sess.query(Lesson).get(lesson_id)
    if not lesson or material not in ['theory', 'task']:
        abort(404)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if not (current_user.id in [course.teacher, sch.director] or
            current_user.group == course.group and current_user.status == 5):
        abort(403)
    if material == 'theory':
        return lesson.theory if lesson.theory else "Теория отсутствует"
    return lesson.tasks if lesson.tasks else "Задание отсутствует"


@app.route('/edit-my-profile', methods=['GET', 'POST'])
def edit_profile():
    """Позволяет пользователю редактировать часть своей информации,
    содержащейся в профиле: Фото, ФИО, пароль"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess, form = db_session.create_session(), UserProfileEditForm()
    user, navbar = user_exists(sess, current_user.id), get_user_navbar(sess)
    params = {'form': form, 'user': user, 'message': '', 'navbar': navbar}
    if form.validate_on_submit():
        file, path_to_file = form.photo.data, user.photo_url
        if file:
            answer = upload_file(file, 'IMG', 'jpg|png|bmp', 15)
            if 'error' in answer:
                params['message'] = answer['error']
                return render_template('edit_profile.html', **params)
            path_to_file = answer['ok']
        else:
            if form.url.data:
                path_to_file = form.url.data
        user.photo_url, user.last_name = path_to_file, form.last_name.data
        user.first_name = form.first_name.data
        user.patronymic = form.patronymic.data
        sess.commit()
        return redirect('/')
    return render_template('edit_profile.html', **params)


@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Позволяет пользователю отредактировать свой текущий пароль"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    user = user_exists(sess, current_user.id)
    form = ChangePasswordForm()
    params = {'title': 'Изменение пароля', 'form': form, 'text': '',
              'navbar': get_user_navbar(sess)}
    if form.validate_on_submit():
        if user.hashed_password != make_hashed_password(str(form.old.data)):
            params['text'] = 'Неправильный старый пароль'
            return render_template('change_password.html', **params)
        correct_password = check_correct_password(str(form.password.data))
        if correct_password.get('error'):
            params['text'] = correct_password['error']
            return render_template('change_password.html', **params)
        user.hashed_password = make_hashed_password(str(form.password.data))
        sess.commit()
        return redirect('/')
    return render_template('change_password.html', **params)


@app.route('/users')
def get_all_users():
    return redirect('/users-page-1')


@app.route('/users-page-<int:page_number>')
def get_all_users_with_page(page_number):
    """Отображает список всех пользователей в системе"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    n = sess.query(User).count() // 20 + 1
    data = sess.query(User).all()
    data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
    data = safe_slice(data, 20 * (pg - 1), 20 * pg)
    params = {'data': data, 'title': 'Пользователи', 'n_pages': n,
              'current_page': pg, 'navbar': get_user_navbar(sess)}
    return render_template('all_users.html', **params)


@app.route('/edit-school-<int:sch_id>', methods=['GET', 'POST'])
def edit_school(sch_id):
    """Позволяет отредактировать информацию о школе"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    sch = school_exists(sess, sch_id)
    if current_user.status > 2:
        abort(403)
    form = SchoolProfileEditForm()
    params = {'title': 'Настройки', 'form': form, 'sch': sch, 'message': '',
              'navbar': get_user_navbar(sess)}
    if form.validate_on_submit():
        file, path_to_file = form.photo.data, sch.photo_url
        if file:
            answer = upload_file(file, 'IMG', 'jpg|png|bmp', 15)
            if 'error' in answer:
                params['message'] = answer['error']
                return render_template('edit_school.html', **params)
            path_to_file = answer['ok']
        sch.photo_url, sch.short_title = path_to_file, form.short_title.data
        sch.index, sch.region = form.index.data, form.region.data
        sch.city, sch.street = form.city.data, form.street.data
        sch.house, sch.phone = form.house.data, form.phone.data
        director = form.director.data
        exist = sess.query(User).filter(User.id == director).first()
        if not exist:
            params['message'] = f'Пользователя с ID {director} не существует!'
            return render_template('edit_school.html', **params)
        if exist.status > 3:
            params['message'] = f'Статус пользователя ниже статуса "Директор"'
            return render_template('edit_school.html', **params)
        if exist.school is not None and exist.school != sch_id:
            params['message'] = f'Пользователь из другой школы'
            return render_template('edit_school.html', **params)
        sch.director, exist.school = director, sch_id
        sess.commit()
        return redirect(f'/school-{sch_id}')
    return render_template('edit_school.html', **params)


@app.route('/del-notify-<int:notify>', methods=['DELETE'])
def delete_notify(notify):
    """Получает DELETE запрос и удаляет уведомление у пользователя"""
    sess = db_session.create_session()
    user = sess.query(User).get(current_user.id)
    data = user.notifications.split() if user.notifications else []
    data = [x for x in data if str(notify) != x]
    user.notifications = ' '.join(data)
    sess.commit()
    return """"""


@app.route('/del-user-<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    """Позволяет удалить пользователя"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    user = user_exists(sess, user_id)
    right = current_user.status == 3 and current_user.school == user.school
    if not (right or current_user.status < 3) or current_user.id == user.id:
        abort(403)
    form = DeleteForm()
    if form.validate_on_submit():
        sess.delete(user), sess.commit()
        return redirect('/')
    params = {'title': 'Удаление', 'form': form, 'obj': 'пользователя'}
    name = f'{user.last_name} {user.first_name}'
    return render_template('delete.html', **params, obj_name=name)


@app.route('/del-course-<int:course_id>', methods=['GET', 'POST'])
def delete_course(course_id):
    """Позволяет удалить курс"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    course = course_exists(sess, course_id)
    school = school_exists(sess, course.school)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    form = DeleteForm()
    lessons = sess.query(Lesson).filter(Lesson.course == course.id).all()
    if form.validate_on_submit():
        for lesson in lessons:
            sess.delete(lesson)
        sess.delete(course), sess.commit()
        return redirect(f'/school-{school.id}-courses')
    params = {'title': 'Удаление', 'form': form, 'obj': 'курс'}
    return render_template('delete.html', **params, obj_name=course.title)


@app.route('/del-lesson-<int:lesson_id>', methods=['GET', 'POST'])
def delete_lesson(lesson_id):
    """Позволяет удалить урок"""
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if current_user.id not in [course.teacher, sch.director]:
        abort(403)
    form = DeleteForm()
    if form.validate_on_submit():
        sess.delete(lesson), sess.commit()
        return redirect(f'/course-{course.id}')
    params = {'title': 'Удаление', 'form': form, 'obj': 'урок'}
    return render_template('delete.html', **params, obj_name=lesson.title)


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------
@app.errorhandler(405)
def method_not_allowed(error):
    params = {'navbar': get_user_navbar(db_session.create_session())}
    return render_template('error.html', code=405, title='Ошибка', **params)


@app.errorhandler(404)
def not_found(error):
    params = {'navbar': get_user_navbar(db_session.create_session())}
    return render_template('error.html', code=404, title='Ошибка', **params)


@app.errorhandler(403)
def forbidden(error):
    params = {'navbar': get_user_navbar(db_session.create_session())}
    return render_template('error.html', code=403, title='Ошибка', **params)


@app.errorhandler(500)
def server_error(error):
    params = {'navbar': get_user_navbar(db_session.create_session())}
    return render_template('error.html', code=500, title='Ошибка', **params)


if __name__ == '__main__':
    main()
