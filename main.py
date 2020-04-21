from flask import Flask, render_template, redirect, abort, jsonify, request
from flask_login import LoginManager, login_user, current_user, logout_user

from forms import LoginForm, UserRegistrationForm, SchoolRegistrationForm
from forms import GroupRegistrationForm, ChatForm
from functions import make_hashed_password, safe_slice

from data import db_session
from data.users import User
from data.user_statuses import UserStatus
from data.schools import School
from data.groups import Group
from data.chats import Chat
from data.messages import Message

import json
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'We`ll always stay together, You and I...'
login_manager = LoginManager()
login_manager.init_app(app)

USERS_STATUSES = ['system-manager', 'admin', 'director', 'teacher', 'student']


# --------------------------------------------------
# PAGES
# --------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def homepage():
    if current_user.is_authenticated:
        return redirect(f'/id-{current_user.id}')
    form = LoginForm()
    if form.validate_on_submit():
        session, email = db_session.create_session(), form.email.data
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f'/id-{current_user.id}')
        message = "Неправильный логин или пароль"
        return render_template('login.html', message=message, form=form)
    return render_template('login.html', title='Авторизация', form=form)


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
    user = session.query(User).get(user_id)
    if not user:
        abort(404)
    rus_statuses = {'system-manager': 'Системный администратор',
                    'admin': 'Администратор', 'director': 'Директор',
                    'teacher': 'Учитель', 'student': 'Ученик'}
    school = session.query(School).get(user.school) if user.school else None
    school = school.short_title if school is not None else None
    group = session.query(Group).get(user.group) if user.group else None
    group = group.title if group is not None else None
    params = {'title': f'{user.last_name} {user.first_name}', 'user': user,
              'status': rus_statuses[USERS_STATUSES[user.status - 1]],
              'school': school, 'group': group, 'current_user': current_user}
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


@app.route('/school-<int:school_id>')
def school_profile(school_id):
    if not current_user.is_authenticated:
        return redirect('/')
    session = db_session.create_session()
    school = session.query(School).get(school_id)
    if not school:
        abort(404)
    director = session.query(User).get(school.director)
    params = {'title': f'{school.short_title}', 'school': school,
              'current_user': current_user, 'director': director}
    return render_template('school.html', **params)


@app.route('/group-<int:group_id>')
def group_profile(group_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    group = sess.query(Group).get(group_id)
    if not group:
        abort(404)
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


@app.route('/school-<int:sch_id>-<obj>-page-<int:page_number>')
def get_school_objects_with_page(sch_id, obj, page_number):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    pg = 1 if page_number <= 0 else page_number
    sch = sess.query(School).get(sch_id)
    if not sch:
        abort(404)
    if obj == 'groups':
        data = sess.query(Group).filter(Group.school_id == sch_id)
        data = sorted(data.all(), key=lambda x: x.title)
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        data = [(x, sess.query(User).get(int(x.leader))) for x in data]
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'current_user': current_user}
        return render_template('school_groups.html', **params)
    if obj == 'teachers':
        data = sess.query(User).filter(User.school == sch_id)
        data = data.filter(User.status == 4).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        params = {'data': data, 'sch': sch, 'title': sch.short_title,
                  'current_user': current_user}
        return render_template('school_teachers.html', **params)
    if obj == 'students':
        data = sess.query(User).filter(User.school == sch_id)
        data = data.filter(User.status == 5).all()
        data = sorted(data, key=lambda x: f'{x.last_name} {x.first_name}')
        data = safe_slice(data, 20 * (pg - 1), 20 * pg)
        data = [(x, sess.query(Group).get(x.group)) for x in data]
        params = {'data': data, 'sch': sch, 'title': sch.short_title}
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
    schools = sorted(session.query(School).all(), key=lambda x: x.title)
    schools = safe_slice(schools, 20 * (pg - 1), 20 * pg)
    schools = [(i, session.query(User).get(i.director)) for i in schools]
    return render_template('all_schools.html', title='Школы', schools=schools)


def add_user(status):
    form = UserRegistrationForm()
    if form.validate_on_submit():
        session, email = db_session.create_session(), form.email.data
        exist = session.query(User).filter(User.email == email).first()
        if exist:
            message = 'Пользователь с таким логином уже существует'
            return 'ERROR', {'form': form, 'message': message}
        user = User()
        user.email = form.email.data
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        if form.patronymic.data:
            user.patronymic = form.patronymic.data
        user.hashed_password = make_hashed_password(str(form.password.data))
        user.status = USERS_STATUSES.index(status) + 1
        session.add(user), session.commit()
        user = session.query(User).filter(User.email == email).first()
        return 'FINISHED', {'user_id': user.id}
    return 'STARTED', {'form': form}


@app.route('/add-<string:status>', methods=['GET', 'POST'])
def add_user_variable(status):
    if not current_user.is_authenticated or current_user.is_authenticated:
        return redirect('/')
    if status not in USERS_STATUSES[1:]:
        abort(404)
    if current_user.status >= USERS_STATUSES.index(status) + 1:
        abort(403)
    rus_statuses = {'admin': 'Администратор', 'director': 'Директор',
                    'teacher': 'Учитель', 'student': 'Ученик'}
    form = UserRegistrationForm()
    if form.validate_on_submit():
        session, email = db_session.create_session(), form.email.data
        exist = session.query(User).filter(User.email == email).first()
        if exist:
            message = 'Пользователь с таким логином уже существует'
            params = {'title': 'Регистрация', 'status': rus_statuses[status],
                      'form': form, 'message': message}
            return render_template('add_user.html', **params)
        user = User()
        user.email = form.email.data
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        if form.patronymic.data:
            user.patronymic = form.patronymic.data
        user.hashed_password = make_hashed_password(str(form.password.data))
        user.status = USERS_STATUSES.index(status) + 1
        session.add(user), session.commit()
        user = session.query(User).filter(User.email == email).first()
        return redirect(f'/id-{user.id}')
    return render_template('add_user.html', title='Регистрация',
                           status=rus_statuses[status], form=form)


@app.route('/add-school', methods=['GET', 'POST'])
def add_school():
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 2:
        abort(403)
    form = SchoolRegistrationForm()
    if form.validate_on_submit():
        session, title = db_session.create_session(), form.title.data
        exist = session.query(School).filter(School.title == title).first()
        if exist:
            text = 'Организация с таким наименованием уже существует'
            params = {'title': 'Регистрация', 'form': form, 'message': text}
            return render_template('add_school.html', **params)
        school, director = School(), form.director.data
        exist = session.query(User).filter(User.id == director).first()
        if not exist:
            text = f'Пользователя с ID {form.director.data} не существует!'
            params = {'title': 'Регистрация', 'form': form, 'message': text}
            return render_template('add_school.html', **params)
        if exist.status > 3:
            text = f'Статус пользователя ниже статуса "Директор"'
            params = {'title': 'Регистрация', 'form': form, 'message': text}
            return render_template('add_school.html', **params)
        if exist.school is not None:
            text = f'Пользователь - директор другой школы: ID {exist.school}'
            params = {'title': 'Регистрация', 'form': form, 'message': text}
            return render_template('add_school.html', **params)
        school.email = form.email.data
        school.title = form.title.data
        school.short_title = form.short_title.data
        school.director = form.director.data
        school.index = form.index.data
        school.region = form.region.data
        school.city = form.city.data
        school.street = form.street.data
        school.house = form.house.data
        school.phone = form.phone.data
        session.add(school), session.commit()
        school = session.query(School).filter(School.title == title).first()
        exist.school = school.id
        session.commit()
        return redirect(f'/school-{school.id}')
    return render_template('add_school.html', title='Регистрация', form=form)


@app.route('/school-<int:sch_id>-add-group', methods=['GET', 'POST'])
def add_group_to_school(sch_id):
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 3:
        abort(403)
    sess = db_session.create_session()
    sch = sess.query(School).get(sch_id)
    if not sch:
        abort(404)
    if current_user.id != sch.director and current_user.status > 2:
        abort(403)
    form = GroupRegistrationForm()
    if form.validate_on_submit():
        exist = sess.query(Group).filter(Group.school_id == sch_id)
        exist = exist.filter(Group.title == form.title.data).first()
        if exist:
            text = 'Такой класс уже существует в данной школе'
            params = {'message': text, 'form': form,
                      'title': 'Добавление класса'}
            return render_template('add_group.html', **params)
        leader = sess.query(User).get(form.leader.data)
        if not leader:
            text = f'Пользователя с ID {form.leader.data} не существует!'
            params = {'message': text, 'form': form,
                      'title': 'Добавление класса'}
            return render_template('add_group.html', **params)
        if leader.status > 4:
            text = f'Статус пользователя ниже статуса "Преподаватель"'
            params = {'message': text, 'form': form,
                      'title': 'Добавление класса'}
            return render_template('add_group.html', **params)
        if leader.school != sch_id:
            text = f'Пользователь не из данной школы'
            params = {'message': text, 'form': form,
                      'title': 'Добавление класса'}
            return render_template('add_group.html', **params)
        group = Group()
        group.title, group.leader = form.title.data, form.leader.data
        group.school_id = sch_id
        sess.add(group), sess.commit()
        group = sess.query(Group).filter(Group.school_id == sch_id)
        group = group.filter(Group.title == form.title.data).first()
        leader.group = group.id
        sess.commit()
        return redirect(f'/school-{sch_id}-groups')
    params = {'form': form, 'title': 'Добавление класса'}
    return render_template('add_group.html', **params)


@app.route('/school-<int:sch_id>-add-teacher', methods=['GET', 'POST'])
def add_teacher_to_school(sch_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    school = sess.query(School).get(sch_id)
    if not school:
        abort(404)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    response = add_user('teacher')
    if response[0] == 'FINISHED':
        user = sess.query(User).get(response[1]['user_id'])
        user.school = school.id
        sess.commit()
        return redirect(f'/school-{sch_id}-teachers')
    if response[0] == 'ERROR':
        return render_template('add_user.html', title='Регистрация',
                               status='Преподаватель', **response[1])
    return render_template('add_user.html', title='Регистрация',
                           status='Преподаватель', **response[1])


@app.route('/group-<int:group_id>-add-student', methods=['GET', 'POST'])
def add_student_to_group(group_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    group = sess.query(Group).get(group_id)
    if not group:
        abort(404)
    school = sess.query(School).get(group.school_id)
    if not school:
        abort(500)
    if current_user.id != school.director or current_user.status > 3:
        abort(403)
    response = add_user('student')
    if response[0] == 'FINISHED':
        user = sess.query(User).get(response[1]['user_id'])
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
    return render_template('chats_list.html')


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
    form = ChatForm()
    return render_template('chat.html', form=form, chat_id=chat_id)


@app.route('/write-message-<int:addressee_id>')
def write_message(addressee_id):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    addressee = sess.query(User).get(addressee_id)
    if not addressee:
        abort(404)
    members = f'{min(current_user.id, addressee_id)}' \
              f' {max(current_user.id, addressee_id)}'
    chat = sess.query(Chat).filter(Chat.members == members).first()
    if not chat:
        chat = Chat()
        chat.members, chat.messages = members, ''
        sess.add(chat), sess.commit()
        chat = sess.query(Chat).filter(Chat.members == members).first()
    return redirect(f'/chat-{chat.id}')


@app.route('/chat-form', methods=['POST'])
def chat_form():
    if not current_user.is_authenticated:
        return """"""
    data = request.json
    if data:
        message, chat_id = data.get('message'), data.get('chat')
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


@app.route('/get-all-messages-chat-<int:chat_id>-starts-with-<start>')
def get_all_messages_in_chat(chat_id, start):
    if not current_user.is_authenticated:
        return redirect('/')
    sess = db_session.create_session()
    start = -1 if start == 'last' else int(start) if start.isdigit() else 0
    chat = sess.query(Chat).get(chat_id)
    if not chat:
        abort(404)
    members = [] if chat.members is None else \
        [int(i) for i in chat.members.split()]
    if current_user.id not in members:
        abort(403)
    messages = [] if chat.messages is None else \
        [sess.query(Message).get(int(i)) for i in chat.messages.split()]
    messages, answer = [i for i in messages if i is not None][start:], ''
    for i in range(len(messages)):
        author = sess.query(User).get(messages[i].writer)
        photo = author.photo_url if author is not None else ''
        author = author.first_name if author is not None else 'Кто-то'
        text = messages[i].text
        photo = '/static/img/user-photo.png' if not photo else photo
        answer += f'<div class="message">' \
                  f'<img src="{photo}" width="40" height="40" style="border-radius: 20px">' \
                  f'<div style="margin-left: 15px">' \
                  f'<h6 style="margin-bottom: 0px"><b>{author}</b></h6><p>{text}</p>' \
                  f'</div>' \
                  f'</div>'
    return answer


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
    for user_data in users:
        session = db_session.create_session()
        exist = session.query(User).filter(User.email == user_data['email'])
        exist = exist.all()
        if not exist:
            user = User()
            for key, val in user_data.items():
                user.__setattr__(key, val)
            session.add(user), session.commit()
    app.run(port=8080, host='127.0.0.1')


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------
@app.errorhandler(405)
def method_not_allowed(error):
    render_template('error.html', code=405)


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404)


@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', code=403)


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', code=500)


if __name__ == '__main__':
    main()
