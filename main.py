from flask import Flask, render_template, redirect, abort, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from forms import LoginForm, UserRegistrationForm

from data import db_session
from data.users import User
from data.chats import Chat
from data.messages import Message


class Application(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        db_session.global_init("db/leopard_lms.sqlite")
        print('--------------------- INITIALISATION ---------------------')


app = Application(__name__)
app.config['SECRET_KEY'] = 'We`ll always stay together, You and I...'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'sign_in'


@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route('/add-to-friends/user-<int:user_id>')
@login_required
def add_to_friends(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if user and user.id != current_user.id:
        if current_user.add_friend(user_id):
            user.add_friend(current_user.id)
            session.add(current_user)
            session.add(user)
            session.commit()
    return redirect(url_for('friends'))


@app.route('/id-<int:user_id>')
def user_profile(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404)
    params = {'user': user, 'current_user': current_user}
    return render_template('profile.html', **params)


@app.route('/friends')
@login_required
def friends():
    friends = current_user.get_friends()
    params = {"friends": friends, "current_user": current_user}
    return render_template("friends.html", **params)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('homepage'))


@app.route('/messenger')
@login_required
def messenger():
    chats = current_user.chats
    params = {"chats": chats, "current_user": current_user}
    return render_template("messenger.html", **params)


@app.route('/profile')
@login_required
def profile():
    return redirect(url_for('user_profile', user_id=current_user.id))


@app.route("/sign-in", methods=['GET', 'POST'])
def sign_in():
    if current_user.is_authenticated:
        return redirect(url_for('user_profile', user_id=current_user.id))
    form = LoginForm()
    params = {'form': form, 'message': ''}
    if form.validate_on_submit():
        session = db_session.create_session()
        email = form.email.data
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            return redirect(url_for('user_profile', user_id=current_user.id))
        params['message'] = "Неправильный логин или пароль"
    return render_template('sign-in.html', **params)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    form = UserRegistrationForm()
    params = {'form': form, 'message': ''}
    if form.validate_on_submit():
        session = db_session.create_session()
        email = form.email.data
        exist = session.query(User).filter(User.email == email).first()
        if exist:
            params['message'] = 'Пользователь с таким логином уже существует'
            return render_template('sign-up.html', **params)
        user = User()
        user.email = form.email.data
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.patronymic = form.patronymic.data

        correct_password = user.check_correct_password(form.password.data)
        if correct_password.get('error'):
            params['message'] = correct_password['error']
            return render_template('sign-up.html', **params)

        user.hashed_password = user.make_hashed_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=True)
        return redirect(url_for('user_profile', user_id=user.id))
    return render_template('sign-up.html', **params)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    app.run(host='127.0.0.1', port=8000)


if __name__ == "__main__":
    main()
