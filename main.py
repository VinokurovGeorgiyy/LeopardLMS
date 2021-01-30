from flask import Flask, render_template, redirect, abort, url_for, request, make_response
from flask import jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from data import db_session
from data.__all_models import User, Alert, Chat, Message, Post, Group, Course, Lesson

from lms_utils import *
from forms import *
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


@app.route("/alerts")
@login_required
def alerts():
    return """"""


@app.route('/chat-<int:chat_id>/messages', methods=['GET', 'POST', 'DELETE'])
@login_required
def chat_messages(chat_id):
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    session = db_session.create_session()
    chat_obj = session.query(Chat).get(chat_id)
    if chat_obj is None:
        return make_response(f"CHAT ID:{chat_id} NOT FOUND", 404)
    if current_user.id not in chat_obj.get_users(only_id=True):
        return make_response("FORBIDDEN", 403)

    if request.method == 'GET':
        data, items = [], chat_obj.messages
        for item in items:
            data += [item.to_json()]
        return make_response(jsonify({"data": data}), 200)


@app.route('/chat-<int:chat_id>/users', methods=['GET', 'POST', 'DELETE'])
@login_required
def chat_users(chat_id):
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    session = db_session.create_session()
    chat_obj = session.query(Chat).get(chat_id)
    if chat_obj is None:
        return make_response(f"CHAT ID:{chat_id} NOT FOUND", 404)
    if not chat_obj.check_user(current_user.id):
        return make_response("FORBIDDEN", 403)

    if request.method == 'GET':
        data, items = [], chat_obj.get_users()
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('user_profile', user_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)


@app.route('/course-<int:course_id>')
@login_required
def course_profile(course_id):
    if current_user.is_blocked():
        abort(423)
    session = db_session.create_session()
    course_obj = session.query(Course).get(course_id)
    if course_obj is None:
        abort(404)
    params = {"current_user": current_user, "course": course_obj}
    return render_template('course_profile.html', **params)


@app.route('/course-<int:course_id>/alerts', methods=['GET', 'POST', 'DELETE'])
@login_required
def course_alerts(course_id):
    return


@app.route('/course-<int:course_id>/lessons', methods=['GET', 'POST', 'DELETE'])
@login_required
def course_lessons(course_id):
    return


@app.route('/course-<int:course_id>/posts', methods=['GET', 'POST', 'DELETE'])
@login_required
def course_posts(course_id):
    return


@app.route('/course-<int:course_id>/users', methods=['GET', 'POST', 'DELETE'])
@login_required
def course_users(course_id):
    return


@app.route("/courses")
@login_required
def courses():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    params = {"current_user": current_user}
    if selector == 'popular':
        return render_template('courses $ popular.html', **params)
    if selector == 'search':
        params["simple_search_form"] = SearchForm()
        params["advanced_search_form"] = AdvancedSearchCourseForm()
        return render_template('courses $ search.html', **params)
    params["create_course_form"] = CreateCourseForm()
    return render_template('courses $ my_courses.html', **params)


@app.route("/friends")
@login_required
def friends():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    params = {"current_user": current_user}
    if selector == 'alerts':
        return render_template('friends $ applications.html', **params)
    if selector == 'search':
        params["simple_search_form"] = SearchForm()
        params["advanced_search_form"] = AdvancedSearchUserForm()
        return render_template('friends $ search.html', **params)
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


@app.route('/group-<int:group_id>/alerts', methods=['GET', 'POST', 'DELETE'])
@login_required
def group_alerts(group_id):
    return


@app.route('/group-<int:group_id>/courses', methods=['GET', 'POST', 'DELETE'])
@login_required
def group_courses(group_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    group = session.query(Group).get(group_id)
    if not group:
        return make_response("GROUP NOT FOUND", 404)

    if request.method == "GET":
        data, items = [], group.get_courses()
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('course_profile', course_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)


@app.route('/group-<int:group_id>/groups', methods=['GET', 'POST', 'DELETE'])
@login_required
def group_groups(group_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    group = session.query(Group).get(group_id)
    if not group:
        return make_response("GROUP NOT FOUND", 404)

    if request.method == 'GET':
        data, items = [], group.get_groups()
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('group_profile', group_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)


@app.route('/group-<int:group_id>/posts', methods=['GET', 'POST', 'DELETE'])
@login_required
def group_posts(group_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    group = session.query(Group).get(group_id)
    if not group:
        return make_response("GROUP NOT FOUND", 404)
    if group.is_closed() and not group.check_user(current_user.id):
        return make_response("FORBIDDEN", 403)

    if request.method == 'GET':
        data, items = [], group.get_posts()
        for item in items:
            data += [item.to_json()]
        return make_response(jsonify({"data": data}), 200)


@app.route('/group-<int:group_id>/users', methods=['GET', 'POST', 'DELETE'])
@login_required
def group_users(group_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    group = session.query(Group).get(group_id)
    if not group:
        return make_response("GROUP NOT FOUND", 404)

    if request.method == 'GET':
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        category = request.args.get('category')

        data = []
        if category == "admins":
            items = [session.query(User).get(group.admin)]
        elif category == "moderators":
            items = group.get_moderators()
        else:
            items = group.get_users()
        for item in items:
            i_data = item.to_json()
            i_data["title"] = i_data.pop("name")
            i_data["profile_url"] = url_for('user_profile', user_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)


@app.route("/groups")
@login_required
def groups():
    if current_user.is_blocked():
        abort(423)
    selector = request.args.get('selector')

    params = {"current_user": current_user}
    if selector == 'popular':
        return render_template('groups $ popular.html', **params)
    if selector == 'search':
        params["simple_search_form"] = SearchForm()
        params["advanced_search_form"] = AdvancedSearchGroupForm()
        return render_template('groups $ search.html', **params)
    params["create_group_form"] = CreateGroupForm()
    return render_template('groups $ my_groups.html', **params)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('profile'))


@app.route("/messenger")
@login_required
def messenger():
    return """"""


@app.route("/profile")
@login_required
def profile():
    return redirect(url_for('user_profile', user_id=current_user.id))


@app.route('/search-course', methods=['POST'])
@login_required
def search_course():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if request.json is None:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    type_of_search = request.json.get('type_of_search')
    simple_request = request.json.get('request')
    title = request.json.get('title')
    course_id = request.json.get('course_id')
    session = db_session.create_session()
    query = session.query(Course)

    if type_of_search == 'simple':
        if not simple_request:
            return make_response("EMPTY REQUEST", 400)
        points = map(lambda x: x.lower(), str(simple_request).split())
        for point in points:
            search_data = f"%{point}%"
            f_search_data = f"%{point[0].upper() + point[1:]}%"
            query = query.filter((Course.title.like(search_data)) |
                                 (Course.title.like(f_search_data)))
    elif type_of_search == 'advanced':
        if not title and not course_id:
            return make_response("EMPTY REQUEST", 400)
        if title:
            query = query.filter(Course.title == title)
        if course_id and str(course_id).isdigit():
            course_id = int(course_id)
            query = query.filter(Course.id == course_id)
    else:
        return make_response("SEARCH_TYPE_ERR", 400)

    data, result = [], query.all()
    for item in result:
        i_data = item.to_json()
        i_data["profile_url"] = url_for('course_profile', course_id=item.id)
        data += [i_data]
    return make_response(jsonify({"data": data}), 200)


@app.route('/search-group', methods=['POST'])
@login_required
def search_group():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if request.json is None:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    type_of_search = request.json.get('type_of_search')
    simple_request = request.json.get('request')
    title = request.json.get('title')
    group_id = request.json.get('group_id')
    session = db_session.create_session()
    query = session.query(Group)

    if type_of_search == 'simple':
        if not simple_request:
            return make_response("EMPTY REQUEST", 400)
        points = map(lambda x: x.lower(), str(simple_request).split())
        for point in points:
            search_data = f"%{point}%"
            f_search_data = f"%{point[0].upper() + point[1:]}%"
            query = query.filter((Group.title.like(search_data)) |
                                 (Group.title.like(f_search_data)))
    elif type_of_search == 'advanced':
        if not title and not group_id:
            return make_response("EMPTY REQUEST", 400)
        if title:
            query = query.filter(Group.title == title)
        if group_id and str(group_id).isdigit():
            group_id = int(group_id)
            query = query.filter(Group.id == group_id)
    else:
        return make_response("SEARCH_TYPE_ERR", 400)

    data, result = [], query.all()
    for item in result:
        i_data = item.to_json()
        i_data["profile_url"] = url_for('group_profile', group_id=item.id)
        data += [i_data]
    return make_response(jsonify({"data": data}), 200)


@app.route('/search-user', methods=['POST'])
@login_required
def search_user():
    if current_user.is_blocked():
        return make_response("LOCKED", 423)
    if request.json is None:
        return make_response("BAD REQUEST: ARGS NOT FOUND", 400)
    type_of_search = request.json.get('type_of_search')
    simple_request = request.json.get('request')
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    user_id = request.json.get('user_id')
    session = db_session.create_session()
    query = session.query(User)

    if type_of_search == 'simple':
        if not simple_request:
            return make_response("EMPTY REQUEST", 400)
        points = map(lambda x: x.lower(), str(simple_request).split())
        for point in points:
            search_data = f"%{point}%"
            f_search_data = f"%{point[0].upper() + point[1:]}%"
            query = query.filter((User.first_name.like(search_data)) |
                                 (User.last_name.like(search_data)) |
                                 (User.first_name.like(f_search_data)) |
                                 (User.last_name.like(f_search_data)))
    elif type_of_search == 'advanced':
        if not first_name and not last_name and not user_id:
            return make_response("EMPTY REQUEST", 400)
        if first_name:
            query = query.filter(User.first_name == first_name)
        if last_name:
            query = query.filter(User.last_name == last_name)
        if user_id and str(user_id).isdigit():
            user_id = int(user_id)
            query = query.filter(User.id == user_id)
    else:
        return make_response("SEARCH_TYPE_ERR", 400)

    data, result = [], query.all()
    for item in result:
        i_data = item.to_json()
        i_data["profile_url"] = url_for('user_profile', user_id=item.id)
        data += [i_data]
    return make_response(jsonify({"data": data}), 200)


@app.route("/settings")
@login_required
def settings():
    return """"""


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
            params['message'] = "Wrong login or password"
    return render_template("sign-in.html", **params)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    form = UserRegistrationForm()
    params = {'form': form, 'message': ''}
    if form.validate_on_submit():
        session = db_session.create_session()
        email = form.email.data
        exist = session.query(User).filter(User.email == email).first()
        if exist:
            params['message'] = 'User already exists'
            return render_template('sign-up.html', **params)
        user = User()
        user.email = form.email.data
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.set_type("USER")

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


@app.route('/user-<int:user_id>', methods=['GET'])
@login_required
def user_profile(user_id):
    if current_user.is_blocked():
        abort(423)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404)
    params = {'user': user, 'current_user': current_user,
              "write_message_form": WriteMessageForm(),
              "create_post_form": CreatePostForm()}
    return render_template('user_profile.html', **params)


@app.route('/user-<int:user_id>/alerts', methods=['GET', 'POST', 'DELETE'])
@login_required
def user_alerts(user_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    if current_user.id != user_id:
        return make_response("FORBIDDEN", 403)
    session = db_session.create_session()
    curr_user = session.query(User).get(current_user.id)

    if request.method == "GET":
        data, items = [], curr_user.get_alerts()
        if request.args:
            alert_type = str(request.args.get('alert_type')).upper()
            role = str(request.args.get('role'))
            if alert_type:
                items = filter(lambda x: x.get_type() == alert_type, items)
            if role == "creator":
                items = filter(lambda x: x.check_creator(curr_user.id), items)
                items = filter(lambda x: x.get_creator_class() == User, items)
            if role == "recipient":
                items = filter(lambda x: x.check_recipient(curr_user.id), items)
                items = filter(lambda x: x.get_recipient_class() == User, items)
        for item in items:
            item_data = item.to_json()
            creator_id = item_data["creator"]["id"]
            recipient_id = item_data["recipient"]["id"]
            if item.is_application_friendship():
                creator_url = url_for("user_profile", user_id=creator_id)
                recipient_url = url_for("user_profile", user_id=recipient_id)
                item_data["creator"]["profile_url"] = creator_url
                item_data["recipient"]["profile_url"] = recipient_url
            data += [item_data]
        return make_response(jsonify({"data": data}), 200)

    if request.method == "POST":
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        alert_type = str(request.args.get('alert_type')).upper()
        alert_obj = Alert()
        alert_obj.set_type(alert_type)

        if alert_obj.is_application_friendship():
            friend_id = request.args.get('friend_id', type=int)
            if not friend_id:
                return make_response("FRIEND ID NOT FOUND", 400)
            friend_obj = session.query(User).get(friend_id)
            if friend_obj is None:
                return make_response(f"USER ID {friend_id} NOT FOUND", 404)
            if curr_user.check_friend(friend_id):
                return make_response("USER IS FRIEND", 400)
            if curr_user.friendship_alert_exists(friend_id):
                return make_response("ALERT EXISTS", 400)
            if friend_obj.friendship_alert_exists(curr_user.id):
                return make_response("ALERT EXISTS", 400)
            alert_obj.set_recipient_type("USER")
            alert_obj.set_creator_type("USER")
            alert_obj.creator_id = curr_user.id
            alert_obj.add_recipient(friend_id)
            session.add(alert_obj)
            session.commit()
            friend_obj.add_alert(alert_obj.id)
            curr_user.add_alert(alert_obj.id)
            session.commit()
            return make_response("SUCCESS", 200)

        if alert_obj.is_application_group_membership():
            group_id = request.args.get('group_id', type=int)
            if not group_id:
                return make_response("GROUP ID NOT FOUND", 400)
            group_obj = session.query(Group).get(group_id)
            if group_obj is None:
                return make_response(f"GROUP ID {group_id} NOT FOUND", 404)
            if group_obj.is_opened():
                return make_response("GROUP IS OPENED", 400)
            if group_obj.check_user(curr_user.id):
                return make_response("USER IS IN GROUP", 400)
            if group_obj.membership_alert_exists(curr_user.id):
                return make_response("ALERT EXISTS", 400)
            alert_obj.set_creator_type("USER")
            alert_obj.set_recipient_type("GROUP")
            alert_obj.creator_id = curr_user.id
            alert_obj.add_recipient(group_id)
            session.add(alert_obj)
            session.commit()
            group_obj.add_alert(alert_obj.id)
            curr_user.add_alert(alert_obj.id)
            session.commit()
            return make_response("SUCCESS", 200)


@app.route('/user-<int:user_id>/courses', methods=['GET', 'POST', 'DELETE'])
@login_required
def user_courses(user_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        return make_response("USER NOT FOUND", 404)

    if request.method == "GET":
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        role = request.args.get('role')

        data, items = [], user.get_courses()
        if role == "user":
            items = filter(lambda x: x.check_user(user.id), items)
        if role == "admin|moderator":
            items = filter(lambda x: x.check_admin(user.id) or x.check_moderator(user.id), items)
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('course_profile', course_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)

    if request.method == "POST":
        if current_user.id != user.id:
            abort(403)
        form = CreateCourseForm()
        if form.validate_on_submit():
            course_obj = Course()
            course_obj.title = form.title.data
            if form.description.data:
                course_obj.description = form.description.data
            course_obj.set_admin(user.id)
            course_obj.set_type(form.course_type.data)
            session.add(course_obj)
            session.commit()
            user.add_course(course_obj.id)
            session.commit()
            return redirect(url_for('course_profile', course_id=course_obj.id))


@app.route('/user-<int:user_id>/friends', methods=['GET', 'POST', 'DELETE'])
@login_required
def user_friends(user_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        return make_response("USER NOT FOUND", 404)

    if request.method == "GET":
        data, items = [], user.get_friends()
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('user_profile', user_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)

    if request.method == "POST":
        if current_user.id != user.id:
            return make_response("FORBIDDEN", 403)
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        friend_id = request.args.get('friend_id', type=int)
        if not friend_id:
            return make_response("FRIEND ID NOT FOUND", 400)
        if friend_id == current_user.id:
            return make_response("USER IS CURRENT USER", 400)
        if current_user.check_friend(friend_id):
            return make_response("USER IS FRIEND", 400)
        friend_obj = session.query(User).get(friend_id)
        if friend_obj is None:
            return make_response(f"USER ID {friend_id} NOT FOUND", 404)
        curr_user = session.query(User).get(current_user.id)
        friendship_alert = friend_obj.friendship_alert_exists(curr_user.id)
        if friendship_alert is None:
            return make_response("APPLICATION FOR FRIENDSHIP NOT FOUND", 404)
        friendship_alert = session.query(Alert).get(friendship_alert.id)
        curr_user.add_friend(friend_obj.id)
        friend_obj.add_friend(curr_user.id)
        curr_user.delete_alert(friendship_alert.id)
        friend_obj.delete_alert(friendship_alert.id)
        session.delete(friendship_alert)
        session.commit()
        return make_response("SUCCESS", 200)

    if request.method == "DELETE":
        if current_user.id != user.id:
            return make_response("FORBIDDEN", 403)
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        friend_id = request.args.get('friend_id', type=int)
        if not friend_id:
            return make_response("FRIEND ID NOT FOUND", 400)
        friend_obj = session.query(User).get(friend_id)
        user.delete_friend(friend_id)
        if friend_obj is not None:
            friend_obj.delete_friend(user.id)
        session.commit()
        return make_response("SUCCESS", 200)


@app.route('/user-<int:user_id>/groups', methods=['GET', 'POST', 'DELETE'])
@login_required
def user_groups(user_id):
    if current_user.is_blocked():
        return make_response("CURRENT USER IS BLOCKED", 423)
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        return make_response("USER NOT FOUND", 404)

    if request.method == "GET":
        if not request.args:
            return make_response("ARGS NOT FOUND", 400)
        role = request.args.get('role')

        data, items = [], user.get_groups()
        if role == "admin":
            items = filter(lambda x: x.check_admin(user.id), items)
        for item in items:
            i_data = item.to_json()
            i_data["profile_url"] = url_for('group_profile', group_id=item.id)
            data += [i_data]
        return make_response(jsonify({"data": data}), 200)

    if request.method == "POST":
        if current_user.id != user.id:
            abort(403)
        form = CreateGroupForm()
        if form.validate_on_submit():
            group_obj = Group()
            group_obj.title = form.title.data
            if form.description.data:
                group_obj.description = form.description.data
            group_obj.set_admin(user.id)
            group_obj.add_user(user.id)
            group_obj.set_type(form.group_type.data)
            session.add(group_obj)
            session.commit()
            user.add_group(group_obj.id)
            session.commit()
            return redirect(url_for('group_profile', group_id=group_obj.id))


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    app.run(host='127.0.0.1', port=8000)


if __name__ == "__main__":
    main()
