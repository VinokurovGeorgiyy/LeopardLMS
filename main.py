from flask import Flask, render_template, redirect, abort, url_for, request
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from forms import LoginForm, UserRegistrationForm, UserProfileEditForm
from forms import ChangePasswordForm, ChatForm, WriteMessageForm

from data import db_session
from data.__all_models import User, Chat, Message

from lms_utils import *
import datetime


class Application(Flask):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        db_session.global_init("db/lms.sqlite")
        print('--------------------- INITIALISATION ---------------------')


app = Application(__name__, template_folder="templates")
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
    other_user = session.query(User).get(user_id)
    user = session.query(User).get(current_user.id)
    if other_user and other_user.id != user.id:
        if user.add_friend(user_id):
            other_user.add_friend(user.id)
            session.commit()
    return redirect(url_for('friends'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    session = db_session.create_session()
    form = ChangePasswordForm()
    params = {"current_user": current_user, "form": form, "message": ""}
    if form.validate_on_submit():
        new_password = form.new_password.data
        user = session.query(User).get(current_user.id)
        if user.check_password(form.old_password.data):
            is_correct = is_correct_password(new_password)
            if is_correct.get('error'):
                params['message'] = is_correct['error']
                return render_template("change_password.html", **params)
            new_password = user.make_hashed_password(new_password)
            user.hashed_password = new_password
            session.commit()
            return redirect(url_for('profile'))
        params['message'] = "Неверный старый пароль"
    return render_template("change_password.html", **params)


@app.route('/delete-message', methods=['DELETE'])
@login_required
def delete_message():
    session = db_session.create_session()
    message_id = request.args.get('message', type=int)
    if message_id is None:
        return """"""
    message = session.query(Message).get(message_id)
    if message is None:
        return """"""
    chat = session.query(Chat).get(message.chat_id)
    if chat is not None:
        if current_user.id not in chat.get_users(only_id=True):
            return """"""
        if current_user.id != message.author:
            return """"""
    session.delete(message)
    session.commit()
    return """"""



@app.route('/edit-user-profile', methods=['GET', 'POST'])
@login_required
def edit_user_profile():
    session = db_session.create_session()
    form = UserProfileEditForm()
    params = {"form": form, "user": current_user, "message": ""}
    user = session.query(User).get(current_user.id)
    if form.validate_on_submit():
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.patronymic = form.patronymic.data
        session.commit()
        return redirect(url_for('profile'))
    return render_template('edit_user_profile.html', **params)


@app.route('/get-messages')
@login_required
def get_messages():
    session = db_session.create_session()
    chat_id = request.args.get('chat', type=int)
    only_number = request.args.get('only_number', type=int)
    if chat_id is None:
        abort(404)
    chat = session.query(Chat).get(chat_id)
    if chat is None:
        abort(404)
    if current_user.id not in [item for item in chat.get_users(only_id=True)]:
        abort(403)
    if only_number:
        return f"{len(chat.messages)}"
    text = ''
    for message in chat.messages:
        data = message.json_for_messenger()
        if current_user.id == message.author:
            text += render_template("message_own.html", **data)
        else:
            text += render_template("message_someone.html", **data)
    return text


@app.route('/id-<int:user_id>', methods=['GET', 'POST'])
def user_profile(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404)
    form = WriteMessageForm()
    params = {'user': user, 'current_user': current_user, "form": form}
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
    session = db_session.create_session()
    chats = current_user.get_chats()
    chat_id = request.args.get('chat', type=int)
    params = {"current_user": current_user, "chats": chats}

    if chat_id is None:
        return render_template("messenger.html", **params)
    chat = session.query(Chat).get(chat_id)
    if chat is None:
        abort(404)
    chat_users = chat.get_users()
    if current_user.id not in [item.id for item in chat_users]:
        abort(403)
    chat_title = chat.get_title(current_user)

    form = ChatForm()
    params["chat"] = chat
    params["form"] = form
    params["chat_title"] = chat_title
    return render_template("messenger_with_chat.html", **params)


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

        correct_password = is_correct_password(form.password.data)
        if correct_password.get('error'):
            params['message'] = correct_password['error']
            return render_template('sign-up.html', **params)

        user.hashed_password = user.make_hashed_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=True)
        return redirect(url_for('user_profile', user_id=user.id))
    return render_template('sign-up.html', **params)


@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    if not request.json:
        return """"""
    session = db_session.create_session()
    text = request.json.get("message")
    chat_id = request.json.get("chat_id")
    if not str(chat_id).isdigit():
        return """"""

    chat = session.query(Chat).get(chat_id)
    if chat is None:
        abort(404)
    chat_users = chat.get_users()
    if current_user.id not in [item.id for item in chat_users]:
        abort(403)

    message = Message()
    message.text = text
    message.chat = chat
    message.author = current_user.id
    message.date = datetime.datetime.utcnow()
    session.add(message)
    session.commit()
    print(chat.messages)
    return """"""


@app.route('/write-message/user-<int:user_id>', methods=['POST'])
@login_required
def write_message(user_id):
    session = db_session.create_session()
    if not request.json:
        return """"""
    text = request.json.get('message')
    chat = current_user.find_personal_chat(user_id)
    curr_user = session.query(User).get(current_user.id)
    if chat is None:
        user = session.query(User).get(user_id)
        if user is None:
            abort(404)
        chat = Chat()
        chat.type = 'personal'
        chat.add_user(user_id)
        chat.add_user(current_user.id)
        session.add(chat)
        session.commit()
        user.add_chat(chat.id)
        curr_user.add_chat(chat.id)
    chat = session.query(Chat).get(chat.id)
    message = Message()
    message.text = text
    message.author = current_user.id
    message.date = datetime.datetime.utcnow()
    message.chat = chat
    session.add(message)
    session.commit()
    print(chat.messages)
    return """"""


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    app.run(host='127.0.0.1', port=8000)


if __name__ == "__main__":
    main()
