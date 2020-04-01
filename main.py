from flask import Flask, render_template, redirect

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField, DateTimeField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Optional

from flask_login import LoginManager, login_user, current_user, logout_user

from data import db_session
from data.users import User
from data.user_statuses import UserStatus

app = Flask(__name__)
app.config['SECRET_KEY'] = 'One adventure will change to worlds'

login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = StringField('Адрес электронной почты', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Leopard LMS')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


def main():
    db_session.global_init("db/leopard_lms.sqlite")
    statuses = ['system-manager', 'admin', 'director', 'teacher', 'student']
    users = [{'first_name': 'Manager', 'last_name': 'System',
              'email': 'leopard.hq@yandex.ru',
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
