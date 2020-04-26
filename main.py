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

import json
import datetime
import os
import hashlib
from random import choice

app = Flask(__name__)
app.config['SECRET_KEY'] = 'We`ll always stay together, You and I...'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
login_manager = LoginManager()
login_manager.init_app(app)

USERS_STATUSES = ['system-manager', 'admin', 'director', 'teacher', 'student']


def get_current_user_courses(sess):
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
    user = sess.query(User).get(user_id)
    if not user:
        abort(404)
    return user


def group_exists(sess, group_id):
    group = sess.query(Group).get(group_id)
    if not group:
        abort(404)
    return group


def school_exists(sess, school_id):
    school = sess.query(School).get(school_id)
    if not school:
        abort(404)
    return school


def course_exists(sess, course_id):
    course = sess.query(Course).get(course_id)
    if not course:
        abort(404)
    return course


def lesson_exists(sess, lesson_id):
    lesson = sess.query(Lesson).get(lesson_id)
    if not lesson:
        abort(404)
    return lesson


def make_hashed_password(string):
    return str(hashlib.blake2b(string.encode()).hexdigest())


def safe_slice(data, start, end):
    try:
        data = data[start:end]
    except Exception:
        data = []
    finally:
        return data


def add_user(session, status):
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
        user.hashed_password = make_hashed_password(str(form.password.data))
        user.status = USERS_STATUSES.index(status) + 1
        session.add(user), session.commit()
        user = session.query(User).filter(User.email == email).first()
        return 'FINISHED', {'user_id': user.id}
    return 'STARTED', {'form': form}


def get_chat_name(session, chat, chat_members, current_user):
    name = chat.title
    if name is None:
        name = [x for x in chat_members if x != current_user.id]
        name = name[0] if name else None
        name = session.query(User).get(name) if name is not None else None
        name = f'{name.first_name} {name.last_name}' if name else None
    return name


def random_string(length):
    obj = 'abcdefghijklmnopqrstuvwxyz'
    obj += obj.upper() + '0123456789'
    return ''.join(choice(obj) for _ in range(length))


def upload_file(file, start, formats, secure_length):
    filename = secure_filename(file.filename)
    file_type = str(filename)[str(filename).rfind('.') + 1:]
    if file_type not in formats.split('|'):
        return {'error': 'Формат файла не поддерживается'}
    number = random_string(secure_length)
    filename = f'{start}-{number}.{file_type}'
    path_to_file = app.config['UPLOAD_FOLDER'] + '/' + filename
    file.save(path_to_file)
    return {'ok': path_to_file}


# --------------------------------------------------
# PAGES
# --------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def homepage():
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
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    user = user_exists(session, user_id)
    rus_statuses = {'system-manager': 'Системный администратор',
                    'admin': 'Администратор', 'director': 'Директор',
                    'teacher': 'Учитель', 'student': 'Ученик'}
    school = session.query(School).get(user.school) if user.school else None
    group = session.query(Group).get(user.group) if user.group else None
    params = {'title': f'{user.last_name} {user.first_name}', 'user': user,
              'status': rus_statuses[USERS_STATUSES[user.status - 1]],
              'school': school, 'group': group, 'current_user': current_user,
              'courses_exist': get_current_user_courses(session)}
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
    return render_template('my_courses.html', data=courses, user=current_user)


@app.route('/school-<int:school_id>')
def school_profile(school_id):
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    school = school_exists(session, school_id)
    director = session.query(User).get(school.director)
    params = {'title': f'{school.short_title}', 'school': school,
              'current_user': current_user, 'director': director}
    return render_template('school.html', **params)


@app.route('/group-<int:group_id>')
def group_profile(group_id):
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
              'current_user': current_user, 'leader': leader, 'group': group}
    return render_template('group.html', **params)


@app.route('/school-<int:sch_id>-<obj>')
def get_school_objects(sch_id, obj):
    return redirect(f'/school-{sch_id}-{obj}-page-1')


@app.route('/school-<int:school_id>-<obj>-page-<int:page_number>')
def get_school_objects_with_page(school_id, obj, page_number):
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
                  'current_user': current_user}
        return render_template('school_groups.html', **params)
    if obj == 'teachers':
        data = sess.query(User).filter(User.school == sch.id)
        data = data.filter(User.status == 4).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'current_user': current_user}
        return render_template('school_teachers.html', **params)
    if obj == 'students':
        data = sess.query(User).filter(User.school == sch.id)
        n = data.filter(User.status == 5).count() // 20 + 1
        data = data.filter(User.status == 5).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        data = [(x, sess.query(Group).get(x.group)) for x in data]
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'n_pages': n, 'current_page': pg}
        return render_template('school_students.html', **params)
    abort(404)


@app.route('/schools')
def get_all_schools():
    return redirect('/schools-page-1')


@app.route('/schools-page-<int:page_number>')
def get_all_schools_with_page(page_number):
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    schools = sorted(session.query(School).all(), key=lambda x: x.short_title)
    schools = safe_slice(schools, 20 * (pg - 1), 20 * pg)
    n = session.query(School).count() // 20 + 1
    schools = [(i, session.query(User).get(i.director)) for i in schools]
    params = {'schools': schools, 'title': 'Школы',
              'n_pages': n, 'current_page': pg}
    return render_template('all_schools.html', **params)


@app.route('/add-school', methods=['GET', 'POST'])
def add_school():
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 2:
        abort(403)
    form = SchoolRegistrationForm()
    params = {'title': 'Регистрация', 'form': form, 'message': ''}
    if form.validate_on_submit():
        session, title = db_session.create_session(), form.title.data
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
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 3:
        abort(403)
    sess = db_session.create_session()
    sch = school_exists(sess, school_id)
    if current_user.id != sch.director and current_user.status > 2:
        abort(403)
    form = GroupRegistrationForm()
    params = {'form': form, 'title': 'Добавление класса', 'message': ''}
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
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school = school_exists(sess, school_id)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    response = add_user(sess, 'teacher')
    if response[0] == 'FINISHED':
        user = sess.query(User).get(response[1]['user_id'])
        user.school = school.id
        sess.commit()
        return redirect(f'/school-{school.id}-teachers')
    if response[0] == 'ERROR':
        return render_template('add_user.html', title='Регистрация',
                               status='Учитель', **response[1])
    return render_template('add_user.html', title='Регистрация',
                           status='Учитель', **response[1])


@app.route('/add-<status>', methods=['GET', 'POST'])
def add_not_school_user(status):
    if not current_user.is_authenticated:
        return redirect('/')
    if status not in USERS_STATUSES[1:]:
        abort(404)
    if current_user.status >= USERS_STATUSES.index(status) + 1:
        abort(403)
    sess = db_session.create_session()
    response = add_user(sess, status)
    name = {'admin': 'Администратор', 'director': 'Директор'}[status]
    if response[0] == 'FINISHED':
        user_id = sess.query(User).get(response[1]['user_id'])
        return redirect(f'/id-{user_id}')
    return render_template('add_user.html', title='Регистрация',
                           status=name, **response[1])


@app.route('/group-<int:group_id>-add-student', methods=['GET', 'POST'])
def add_student_to_group(group_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    group = group_exists(sess, group_id)
    school = school_exists(sess, group.school_id)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    response = add_user(sess, 'student')
    if response[0] == 'FINISHED':
        user = user_exists(sess, response[1]['user_id'])
        user.group, user.school = group.id, school.id
        sess.commit()
        return redirect(f'/group-{group.id}')
    if response[0] == 'ERROR':
        return render_template('add_user.html', title='Регистрация',
                               status='Ученик', **response[1])
    return render_template('add_user.html', title='Регистрация',
                           status='Ученик', **response[1])


@app.route('/chats')
def chats_list():
    chats = get_chats(50)
    if isinstance(chats, list):
        return render_template('chats_list.html', chats=chats)
    abort(404)


def get_chats(last_message_length):
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
            photo = photo.photo_url
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


@app.route('/chat-<int:chat_id>', methods=['GET', 'POST'])
def chat_messages_list(chat_id):
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
              'title': f'Сообщения - {name}', 'chats': chats}
    return render_template('chat.html', **params)


@app.route('/write-message-<int:addressee_id>')
def write_message(addressee_id):
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


@app.route('/del-message-<int:m_id>')
def delete_message(m_id):
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
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school = school_exists(sess, school_id)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    form = CourseRegistrationForm()
    params = {'form': form, 'title': 'Добавление курса', 'message': ''}
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
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    sch = school_exists(sess, school_id)
    if not (current_user.id == sch.director or current_user.status < 3):
        abort(403)
    courses = sess.query(Course).filter(Course.school == sch.id).all()
    data = [(x, sess.query(Group).get(x.group)) for x in courses]
    data = [(x, y, sess.query(User).get(x.teacher)) for x, y in data]
    return render_template('school_courses.html', data=data, sch=sch)


@app.route('/course-<int:course_id>')
def course_profile(course_id):
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
    params = {'course': course, 'lessons': lessons, 'rights': rights}
    return render_template('course.html', **params)


@app.route('/course-<int:course_id>-add-lesson', methods=['GET', 'POST'])
def add_lesson_to_course(course_id):
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
    return render_template('add_lesson.html', form=form)


@app.route('/lesson-<int:lesson_id>-open')
def open_lesson(lesson_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if current_user.id not in [course.teacher, sch.director]:
        abort(403)
    lesson.opened = True
    sess.commit()
    return redirect(f'/course-{lesson.course}')


@app.route('/lesson-<int:lesson_id>')
def lesson_profile(lesson_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    lesson = lesson_exists(sess, lesson_id)
    course = course_exists(sess, lesson.course)
    sch = school_exists(sess, course.school)
    if not (current_user.id in [course.teacher, sch.director] or
            current_user.group == course.group and current_user.status == 5):
        abort(403)
    right = current_user.id in [course.teacher, sch.director]
    return render_template('lesson.html', lesson=lesson, right_of_edit=right)


@app.route('/lesson-<int:lesson_id>-add-<material>', methods=['GET', 'POST'])
def add_theory_to_lesson(lesson_id, material):
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
        return redirect(f'/lesson-{lesson_id}')
    return render_template('edit_lesson.html', title='Редактор', form=form,
                           data=material, lesson=lesson)


@app.route('/lesson-<int:lesson_id>-get-<material>')
def get_theory_of_lesson(lesson_id, material):
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
    if not current_user.is_authenticated:
        return redirect('/')
    sess, form = db_session.create_session(), UserProfileEditForm()
    user = user_exists(sess, current_user.id)
    params = {'form': form, 'user': user, 'message': ''}
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
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    user = user_exists(sess, current_user.id)
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if user.hashed_password != make_hashed_password(str(form.old.data)):
            params = {'title': 'Изменение пароля', 'form': form,
                      'text': 'Неправильный старый пароль'}
            return render_template('change_password.html', **params)
        user.hashed_password = make_hashed_password(str(form.password.data))
        sess.commit()
        return redirect('/')
    params = {'title': 'Изменение пароля', 'form': form}
    return render_template('change_password.html', **params)


@app.route('/users')
def get_all_users():
    return redirect('/users-page-1')


@app.route('/users-page-<int:page_number>')
def get_all_users_with_page(page_number):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    n = sess.query(User).count() // 20 + 1
    data = sess.query(User).all()
    data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
    data = safe_slice(data, 20 * (pg - 1), 20 * pg)
    return render_template('all_users.html', data=data, title='Пользователи',
                           n_pages=n, current_page=pg)


@app.route('/edit-school-<int:sch_id>', methods=['GET', 'POST'])
def edit_school(sch_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    sch = school_exists(sess, sch_id)
    if current_user.status > 2:
        abort(403)
    form = SchoolProfileEditForm()
    params = {'title': 'Настройки', 'form': form, 'sch': sch, 'message': ''}
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


def main():
    db_session.global_init("db/leopard_lms.sqlite")
    statuses = USERS_STATUSES[:]
    users = [{'first_name': 'Manager', 'last_name': 'System',
              'email': 'leopard.hq@yandex.ru', 'status': 1,
              'hashed_password': '874800ba296315ee2f8e69033aaedbdbb9603b62b26'
                                 '3f1496b9b6a731ebbf18e650fcfaf720daea9425133'
                                 '959197b1bf769a9c3e568c8127208f7f0989f0d745'}
             ]
    for title in statuses:
        session = db_session.create_session()
        exist = session.query(UserStatus).filter(UserStatus.title == title)
        exist = exist.all()
        if not exist:
            status = UserStatus()
            status.title = title
            session.add(status), session.commit()
    for data in users:
        session = db_session.create_session()
        exist = session.query(User).filter(User.email == data['email']).all()
        if not exist:
            user = User()
            for key, val in data.items():
                user.__setattr__(key, val)
            session.add(user), session.commit()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------
@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('error.html', code=405, title='Ошибка')


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404, title='Ошибка')


@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', code=403, title='Ошибка')


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', code=500, title='Ошибка')


if __name__ == '__main__':
    main()
