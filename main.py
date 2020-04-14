from flask import Flask, render_template, redirect, abort
from flask_login import LoginManager, login_user, current_user, logout_user

from forms import LoginForm, UserRegistrationForm, SchoolRegistrationForm
from functions import make_hashed_password

from data import db_session
from data.users import User
from data.user_statuses import UserStatus
from data.schools import School

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
        return redirect(f'/id{current_user.id}')
    form = LoginForm()
    if form.validate_on_submit():
        session, email = db_session.create_session(), form.email.data
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f'/id{current_user.id}')
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


@app.route('/id<int:user_id>')
def user_profile(user_id):
    if not current_user.is_authenticated:
        return redirect('/')
    user = db_session.create_session().query(User).get(user_id)
    if not user:
        abort(404)
    params = {'title': f'{user.last_name} {user.first_name}', 'user': user}
    return render_template('user.html', **params)


@app.route('/add_<string:status>', methods=['GET', 'POST'])
def add_user(status):
    if not current_user.is_authenticated:
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
        return redirect('/')
    return render_template('add_user.html', title='Регистрация',
                           status=rus_statuses[status], form=form)


@app.route('/add_school', methods=['GET', 'POST'])
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

        school.email = form.email.data
        school.title = form.title.data
        school.director = form.director.data
        school.teachers, school.groups, school.students = '', '', ''
        school.index = form.index.data
        school.region = form.region.data
        school.city = form.city.data
        school.street = form.street.data
        school.house = form.house.data
        school.phone = form.phone.data
        session.add(school), session.commit()
        return redirect('/')
    return render_template('add_school.html', title='Регистрация', form=form)


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
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404)


@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', code=403)


if __name__ == '__main__':
    main()
