from flask import Flask, render_template, redirect, request, abort

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField, DateTimeField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Optional

from flask_login import LoginManager, login_user, current_user, logout_user

from data import db_session
from data.users import User
from data.user_statuses import UserStatus
from data.schools import School

import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'One adventure will change to worlds'

login_manager = LoginManager()
login_manager.init_app(app)

USERS_STATUSES = ['system-manager', 'admin', 'director', 'teacher', 'student']


def make_hashed_password(string):
    return str(hashlib.blake2b(string.encode()).hexdigest())


class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')


class AdminRegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество (при наличии)', validators=[])
    email = StringField('Логин (Email)', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать')


class UserRegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество (при наличии)', validators=[])
    email = StringField('Логин (Email)', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать')


class SchoolRegistrationForm(FlaskForm):
    title = StringField('Полное наименование организации', validators=[DataRequired()])
    director = IntegerField('ID директора', validators=[DataRequired()])
    address = StringField('Почтовый адрес', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('', validators=[DataRequired()])
    submit = SubmitField('Добавить школу')


@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return render_template('index.html', title='Leopard LMS', current_user=current_user)
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/add_<string:status>', methods=['GET', 'POST'])
def add_user(status):
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status > 4:
        abort(403)
    if status not in USERS_STATUSES[1:]:
        abort(404)
    if current_user.status >= USERS_STATUSES.index(status) + 1:
        abort(403)
    rus_statuses = {'admin': 'Администратор', 'director': 'Директор',
                    'teacher': 'Учитель', 'student': 'Ученик'}
    form = UserRegistrationForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        exist = session.query(User).filter(User.email == form.email.data).first()
        if exist:
            message = 'Пользователь с таким логином уже существует'
            return render_template('add_user.html', title='Регистрация',
                                   status=status.upper(), form=form, message=message)
        user = User()
        user.email = form.email.data
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        if form.patronymic.data:
            user.patronymic = form.patronymic.data
        user.hashed_password = make_hashed_password(str(form.password.data))
        user.status = USERS_STATUSES.index(status) + 1
        session.add(user), session.commit()
        user = session.query(User).filter(User.email == form.email.data).first()
        return render_template('user_added.html', title='Success', user=user, status=rus_statuses[status])
    return render_template('add_user.html', title='Регистрация', status=rus_statuses[status], form=form)


@app.route('/add_school', methods=['GET', 'POST'])
def add_school():
    if not current_user.is_authenticated:
        return redirect('/')
    if current_user.status not in [1, 2]:
        abort(403)
    form = SchoolRegistrationForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        exist1 = session.query(School).filter(School.title == form.title.data).first()
        exist2 = session.query(School).filter(School.email == form.email.data).first()
        if exist1 or exist2:
            message = 'Организация с таким наименованием уже существует'
            return render_template('add_school.html', form=form, message=message)
        school = School()
        school.email = form.email.data
        school.title = form.title.data
        school.director = form.director.data
        school.address = form.address.data
        school.phone = form.phone.data
        session.add(school), session.commit()
        school = session.query(School).filter(School.email == form.email.data).first()
        return render_template('school_added.html', title='Success', school=school)
    return render_template('add_school.html', title='Регистрация Школы', form=form)


@app.route('/school<int:school_id>')
def school_profile(school_id):
    session = db_session.create_session()
    school = session.query(School).filter(School.id == school_id).first()
    if not school:
        abort(404, message='Организации с таким ID не существует!')
    return render_template('school_profile.html', title=school.title, school=school)


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


if __name__ == '__main__':
    main()
