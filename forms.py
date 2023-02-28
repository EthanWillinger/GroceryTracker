from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField, IntegerField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    pass

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[validators.Length(min=3, max=25), validators.DataRequired(message="Please Fill This Field")])
    email = StringField("Email", validators=[validators.Email(message="Please enter a valid email address")])
    password = PasswordField("Password", validators =[
        validators.DataRequired(message="Please Fill This Field"),
        validators.EqualTo(fieldname="confirm", message="Your Passwords Do Not Match")
        ])
    confirm = PasswordField("Confirm Password", validators=[validators.DataRequired(message="Please Fill This Field")])

# Flask Form for the search bar
class Search_Form(FlaskForm):
    search = StringField('Search')
