from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email


class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')


class UserRegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество', validators=[])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать')


class SchoolRegistrationForm(FlaskForm):
    title = StringField('Полное наименование организации', validators=[DataRequired()])
    short_title = StringField('Краткое наименование', validators=[DataRequired()])
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
    message = StringField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')
