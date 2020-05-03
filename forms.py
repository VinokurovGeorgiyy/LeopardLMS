from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField, TextAreaField, FileField
from wtforms.validators import DataRequired, EqualTo, Email


class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Вход')


class UserRegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество', validators=[])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(),
                                                   EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать')


class SchoolRegistrationForm(FlaskForm):
    title = StringField('Полное наименование организации',
                        validators=[DataRequired()])
    short_title = StringField('Краткое наименование',
                              validators=[DataRequired()])
    director = IntegerField('ID директора', validators=[DataRequired()])
    index = IntegerField('Почтовый индекс', validators=[DataRequired()])
    region = StringField('Регион', validators=[DataRequired()])
    city = StringField('Город/район', validators=[DataRequired()])
    street = StringField('Улица/проспект и пр.', validators=[DataRequired()])
    house = StringField('Дом', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Тел.', validators=[DataRequired()])
    submit = SubmitField('Добавить школу')


class GroupRegistrationForm(FlaskForm):
    title = StringField('Название, литера', validators=[DataRequired()])
    leader = IntegerField('ID руководителя', validators=[DataRequired()])
    submit = SubmitField('Добавить класс')


class ChatForm(FlaskForm):
    message = StringField('Сообщение', validators=[])
    submit = SubmitField('Отправить')


class CourseRegistrationForm(FlaskForm):
    title = StringField('Название курса', validators=[DataRequired()])
    teacher = IntegerField('ID преподавателя курса',
                           validators=[DataRequired()])
    group = IntegerField('ID группы/класса', validators=[DataRequired()])
    submit = SubmitField('Добавить курс')


class UserProfileEditForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество', validators=[])
    photo = FileField('Загрузить фото', validators=[])
    url = StringField('Ссылка на фото', validators=[])
    submit = SubmitField('Сохранить')


class ChangePasswordForm(FlaskForm):
    old = PasswordField('Старый пароль', validators=[DataRequired()])
    password = PasswordField('Новый пароль',
                             validators=[DataRequired(), EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить пароль')


class SchoolProfileEditForm(FlaskForm):
    short_title = StringField('Краткое наименование',
                              validators=[DataRequired()])
    director = IntegerField('ID директора', validators=[DataRequired()])
    index = IntegerField('Почтовый индекс', validators=[DataRequired()])
    region = StringField('Регион', validators=[DataRequired()])
    city = StringField('Город/район', validators=[DataRequired()])
    street = StringField('Улица/проспект и пр.', validators=[DataRequired()])
    house = StringField('Дом', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Тел.', validators=[DataRequired()])
    photo = FileField('Загрузить фото', validators=[])
    submit = SubmitField('Сохранить')


class LessonRegistrationForm(FlaskForm):
    lesson_number = StringField('Номер урока', validators=[DataRequired()])
    title = StringField('Тема урока', validators=[DataRequired()])
    submit = SubmitField('Добавить урок в курс')


class EditLessonForm(FlaskForm):
    text = TextAreaField('Абзац', validators=[])
    link = StringField('Ссылка', validators=[])
    img_url = StringField('Изображние (ссылка)', validators=[])
    code = TextAreaField('Код', validators=[])
    submit = SubmitField('Сохранить')


class LoadSolution(FlaskForm):
    doc = FileField('Загрузить документ', validators=[])
    message = StringField('', validators=[])
    submit = SubmitField('Добавить')


class DeleteForm(FlaskForm):
    submit = SubmitField('Удалить')


class EditGroupForm(FlaskForm):
    title = StringField('Название, литера', validators=[DataRequired()])
    leader = IntegerField('ID руководителя', validators=[DataRequired()])
    submit = SubmitField('Изменить')
