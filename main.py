from flask import Flask, render_template, redirect, abort, url_for, request, make_response
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from forms import LoginForm, UserRegistrationForm, CreateIndependentGroupForm
from forms import ChatForm, WriteMessageForm, CreatePostForm

from data import db_session
from data.__all_models import User, Notification, Chat, Message, Post, Group

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
    return """"""


@app.route('/add-to-friends', methods=['POST'])
@login_required
def add_to_friends():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if not request.args:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    user_id = request.args.get('user_id', type=int)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    curr_user = session.query(User).get(current_user.id)
    if user and user.id != curr_user.id:
        notification = user.friendship_notification_exists(curr_user.id)
        if notification is not None:
            notification = session.query(Notification).get(notification.id)
            if curr_user.add_friend(user_id):
                user.add_friend(curr_user.id)
                user.delete_notification(notification.id)
                curr_user.delete_notification(notification.id)
                session.delete(notification)
                session.commit()
    return make_response("Success", 200)


@app.route('/chat-<int:chat_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def chat_view(chat_id):
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    session = db_session.create_session()
    chat_obj = session.query(Chat).get(chat_id)
    if chat_obj is None:
        return make_response(f"CHAT ID:{chat_id} NOT FOUND", 404)
    if current_user.id not in chat_obj.get_users(only_id=True):
        return make_response("FORBIDDEN", 403)

    if request.method == 'GET':
        only_number = request.args.get('only_number', type=int)
        if only_number:
            return f"{len(chat_obj.messages)}"
        text = ''
        for message in chat_obj.messages:
            data = message.get_json()
            if current_user.id == message.author:
                text += render_template("message_own.html", **data)
            elif chat_obj.check_admin(current_user.id):
                text += render_template("message_own.html", **data)
            elif chat_obj.check_moderator(current_user.id):
                text += render_template("message_own.html", **data)
            else:
                text += render_template("message_someone.html", **data)
        return text

    if request.method == 'POST':
        if not request.json:
            return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
        text = request.json.get("message")
        if not text:
            return make_response("EMPTY MESSAGE", 400)
        message = Message()
        message.text = text
        message.chat = chat_obj
        message.author = current_user.id
        message.date = datetime.datetime.utcnow()
        session.add(message)
        session.commit()
        return make_response("Success", 200)
    return make_response("Error", 404)


@app.route('/courses')
@login_required
def courses():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    if selector == 'popular':
        params = {"current_user": current_user}
        return render_template('courses $ popular.html', **params)
    if selector == 'search':
        params = {"current_user": current_user}
        return render_template('courses $ search.html', **params)

    params = {"current_user": current_user}
    return render_template('courses $ my_courses.html', **params)


@app.route('/create-group', methods=['POST'])
@login_required
def create_group():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    dependency = request.args.get('dependency')
    if dependency == 'independent':
        form = CreateIndependentGroupForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            group_obj = Group()
            group_obj.set_admin(current_user.id)
            group_obj.title = form.title.data
            group_obj.set_type(form.group_type.data)
            if form.description.data:
                group_obj.description = form.description.data
            session.add(group_obj)
            session.commit()
            curr_user = session.query(User).get(current_user.id)
            curr_user.add_group(group_obj.id)
            group_obj.add_user(current_user.id)
            session.commit()
            return redirect(url_for('group_profile', group_id=group_obj.id))
        return make_response('Error', 400)
    return make_response('Error', 400)


@app.route('/create-group-chat', methods=['POST'])
@login_required
def create_group_chat():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if request.json is None:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    chat_title = str(request.json.get('chat_title'))
    if not chat_title:
        return make_response("CHAT TITLE NOT FOUND", 400)
    users_list = str(request.json.get('users_list'))
    session = db_session.create_session()

    users_list = [int(x) for x in users_list.split(';') if x.isdigit()]
    curr_user_friends = current_user.get_friends(only_id=True)

    users_list = list(filter(lambda x: x in curr_user_friends, users_list))
    users_list.append(current_user.id)
    users_list = list(set(users_list))
    for i in range(len(users_list)):
        users_list[i] = session.query(User).get(users_list[i])
    users_list = [item for item in users_list if item]

    if not users_list:
        return make_response("CHAT CAN NOT BE WITHOUT USERS", 400)
    chat = Chat()
    chat.set_type("GROUP")
    chat.title = chat_title
    chat.set_admin(current_user.id)
    for user in users_list:
        chat.add_user(user.id)
    session.add(chat)
    session.commit()
    for user in users_list:
        user.add_chat(chat.id)
    session.commit()
    return f"""{chat.id}"""


@app.route('/create-notification', methods=['POST'])
@login_required
def create_notification():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if not request.args:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    selector = request.args.get('selector')
    if not selector:
        return make_response("SELECTOR NOT EXISTS", 400)
    if selector == 'friendship':
        user_id = request.args.get('to_user', type=int)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        curr_user = session.query(User).get(current_user.id)
        if user is None:
            return make_response("USER NOT FOUND", 404)

        notification = Notification()
        if user.id in curr_user.get_friends(only_id=True):
            return make_response("USER ALREADY IS FRIEND", 404)
        if curr_user.friendship_notification_exists(user.id):
            return make_response("Error", 404)
        if user.friendship_notification_exists(curr_user.id):
            return make_response("Error", 404)
        notification.set_type(selector)
        notification.sender = curr_user.id
        session.add(notification)
        session.commit()
        notification.add_recipient(user.id)
        notification.send()
        curr_user.add_notification(notification.id)
        session.commit()
        return make_response("Success", 200)
    return make_response("Error", 404)


@app.route('/create-post', methods=['POST'])
@login_required
def create_post():
    return make_response("Error", 404)


@app.route('/delete-from-friends', methods=['DELETE'])
@login_required
def delete_from_friends():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if not request.args:
        return make_response("ARGS NOT FOUND", 400)
    user_id = request.args.get('user_id', type=int)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    curr_user = session.query(User).get(current_user.id)
    if user.id in curr_user.get_friends(only_id=True):
        user.delete_friend(curr_user.id)
        curr_user.delete_friend(user.id)
        session.commit()
        return make_response('Success', 200)
    return make_response('Error', 404)


@app.route('/delete-notification', methods=['DELETE'])
@login_required
def delete_notification():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if not request.args:
        return make_response("ARGS NOT FOUND", 400)
    item = request.args.get('id', type=int)
    session = db_session.create_session()
    item = session.query(Notification).get(item)
    if item is None:
        return make_response("NOTIFICATION NOT FOUND", 404)
    if item.is_friendship():
        curr_user = session.query(User).get(current_user.id)
        if curr_user.id == item.sender:
            curr_user.delete_notification(item.id)
            item.cancel()
            session.delete(item)
            session.commit()
            return make_response("Success", 200)
        if curr_user.id in item.get_recipients(only_id=True):
            sender = session.query(User).get(item.sender)
            sender.delete_notification(item.id)
            item.cancel()
            session.delete(item)
            session.commit()
            return make_response("Success", 200)
    return make_response("Error", 404)


@app.route('/friends')
@login_required
def friends():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    if selector == 'notifications':
        inbox, outbox = [], []
        for item in current_user.get_notifications():
            if item.is_friendship():
                if item.sender != current_user.id:
                    inbox += [item]
                else:
                    outbox += [item]
        params = {"current_user": current_user, 'outbox': outbox, 'inbox': inbox}
        return render_template('friends $ notifications.html', **params)
    if selector == 'search':
        params = {"current_user": current_user}
        return render_template('friends $ search.html', **params)

    params = {"current_user": current_user}
    return render_template('friends $ my_friends.html', **params)


@app.route('/group-<int:group_id>')
@login_required
def group_profile(group_id):
    if current_user.is_blocked():
        abort(423)
    session = db_session.create_session()
    group_obj = session.query(Group).get(group_id)
    if group_obj is None:
        abort(404)
    params = {"current_user": current_user, "group": group_obj}
    return render_template('group_profile.html', **params)


@app.route('/groups')
@login_required
def groups():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    if selector == 'popular':
        params = {"current_user": current_user}
        return render_template('groups $ popular.html', **params)
    if selector == 'search':
        params = {"current_user": current_user}
        return render_template('groups $ search.html', **params)

    form = CreateIndependentGroupForm()
    params = {"current_user": current_user, "create_group_form": form}
    return render_template('groups $ my_groups.html', **params)


@app.route('/id-<int:user_id>', methods=['GET'])
@login_required
def user_profile(user_id):
    if current_user.is_blocked():
        abort(423)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404)
    write_message_form = WriteMessageForm()
    create_post_form = CreatePostForm()
    params = {'user': user, 'current_user': current_user,
              "write_message_form": write_message_form,
              "create_post_form": create_post_form}
    return render_template('user_profile.html', **params)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('profile'))


@app.route('/messenger')
@login_required
def messenger():
    session = db_session.create_session()
    chats = current_user.get_chats()
    chat_id = request.args.get('chat', type=int)
    params = {"current_user": current_user, "chats": chats, "chat": None}

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
        return redirect(url_for('profile'))
    form = LoginForm()
    params = {'form': form, 'message': ''}
    if form.validate_on_submit():
        session = db_session.create_session()
        email = form.email.data
        user = session.query(User).filter(User.email == email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            return redirect(url_for('profile'))
        else:
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
        user.set_status("USER")

        correct_password = is_correct_password(form.password.data)
        if correct_password.get('error'):
            params['message'] = correct_password['error']
            return render_template('sign-up.html', **params)

        user.hashed_password = user.make_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=True)
        return redirect(url_for('user_profile', user_id=user.id))
    return render_template('sign-up.html', **params)


@app.route('/write-message', methods=['POST'])
@login_required
def write_message():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    form = WriteMessageForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user_id = form.user_id.data
        text = form.message.data
        chat = current_user.find_personal_chat(user_id)
        curr_user = session.query(User).get(current_user.id)
        if chat is None:
            user = session.query(User).get(user_id)
            if user is None:
                return make_response(f"USER ID:{user_id} NOT FOUND", 404)
            chat = Chat()
            chat.set_type("PERSONAL")
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
        return redirect(url_for("user_profile", user_id=user_id))
    return make_response("Error", 400)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    app.run(host='127.0.0.1', port=8000)


if __name__ == "__main__":
    main()
