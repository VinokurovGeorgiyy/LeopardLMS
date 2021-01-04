from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms import TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email


class ChatForm(FlaskForm):
    message = StringField('Сообщение', validators=[])
    submit = SubmitField('Отправить')


class CreateIndependentGroupForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[])
    group_type = SelectField('Тип', choices=[('OPENED', 'Открытая'), ('CLOSED', 'Закрытая')])
    submit = SubmitField('Создать')


class CreatePostForm(FlaskForm):
    text = TextAreaField('Текст', validators=[])
    code = TextAreaField('Код', validators=[DataRequired()])
    submit = SubmitField('Создать')


class LoginForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Вход')


class UserRegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество', validators=[])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), EqualTo('repeat')])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class WriteMessageForm(FlaskForm):
    message = TextAreaField('Сообщение', validators=[DataRequired()])
    user_id = IntegerField('ID получателя', validators=[DataRequired()])
    submit = SubmitField('Отправить')
