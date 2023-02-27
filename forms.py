from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


# Flask Form for the search bar
class Search_Form(FlaskForm):
    search = StringField('Search')
