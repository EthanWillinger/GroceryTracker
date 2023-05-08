from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, SubmitField, HiddenField
from wtforms import PasswordField, validators, TextAreaField, IntegerField

class LoginForm(FlaskForm):
    email = StringField("Email",render_kw={"placeholder": "Email"}, validators=[validators.Email(message="Please enter a valid email address")])
    password = PasswordField("Password", render_kw={"placeholder": "Password"}, validators =[validators.DataRequired(message="Please Fill This Field")])

class RegisterForm(FlaskForm):
    username = StringField("Username", render_kw={"placeholder": "Username"}, validators=[validators.Length(min=3, max=25), validators.DataRequired(message="Please Fill This Field")])
    email = StringField("Email",render_kw={"placeholder": "Email"}, validators=[validators.Email(message="Please enter a valid email address"), validators.DataRequired(message="Please Fill This Field")])
    password = PasswordField("Password", render_kw={"placeholder": "Password"}, validators =[
        validators.DataRequired(message="Please Fill This Field"),
        validators.EqualTo(fieldname="confirm", message="Your Passwords Do Not Match")
        ])
    confirm = PasswordField("Confirm Password", render_kw={"placeholder": "Confirm Password"}, validators=[validators.DataRequired(message="Please Fill This Field")])

    submit = SubmitField("Create Account!")

# Flask Form for the search bar
class Search_Form(FlaskForm):
    search = StringField('Search')

class UpdateEmail(FlaskForm):
    email = StringField("Email",render_kw={"placeholder": "Email"}, validators=[validators.Email(message="Please enter a valid email address"), validators.DataRequired(message="Please Fill This Field")])
    update = SubmitField("Update")

class UpdatePwd(FlaskForm):
    oldpassword = PasswordField("Password", render_kw={"placeholder": "Old Password"}, validators = [
    validators.DataRequired(message="Please Fill This Field")])
    newpassword = PasswordField("Password", render_kw={"placeholder": "New Password"}, validators =[
    validators.DataRequired(message="Please Fill This Field"),
    validators.EqualTo(fieldname="confirm", message="Your Passwords Do Not Match")
    ])
    confirm = PasswordField("Confirm Password", render_kw={"placeholder": "Confirm Password"}, validators=[validators.DataRequired(message="Please Fill This Field")])

    setpwd = SubmitField("Set Password")


