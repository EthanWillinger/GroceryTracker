import os
import secrets
import requests
from forms import Search_Form, LoginForm, RegisterForm
from flask import session, request
from flask import Flask, render_template
from flask import url_for, flash, redirect
from flask_login import LoginManager, UserMixin, login_user
from flask_login import login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text


# Create a flask app for the website
app = Flask(__name__) 

#Add Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
# Secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)
# Initialize The Database
db = SQLAlchemy(app)

# Create Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    # Create A String
    def __repr__(self):
        return "<username %r>" % self.username
    
with app.app_context():
    db.create_all()

 

# The intro page
@app.route("/intro", methods=['GET', 'POST'])
def intro():
    return render_template('intro.html', login=url_for('login'), signup=url_for('signup'))

# Home webpage function
@app.route("/home", methods=['GET', 'POST'])
def home(user):
    print("home page")

@app.route("/")
# login page function. The code below until the next comment allows the user to interact with forms.py
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method=="POST":

        email_exists = db.session.query(db.session.query(Users).filter_by(email=form.email.data).exists()).scalar()
        password_exists = db.session.query(db.session.query(Users).filter_by(password=form.password.data).exists()).scalar()

        if email_exists and password_exists:
            clearFormLogin(form)
            #Page will change this is for testing purposes
            return render_template('intro.html')
        else:
            clearFormLogin(form)
            return render_template('Login.html', form=form, display="block", login=url_for("login"))
    else:
        return render_template('Login.html', form=form, display="block", signup=url_for("signup"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    return render_template('signup.html', form=form, display="none", login=url_for("login"))

@app.route('/register_success', methods=['GET', 'POST'])
def success():
    form = RegisterForm()
    if request.method=="POST":

        #Check if the email exists in the database already
        email_exists = db.session.query(db.session.query(Users).filter_by(email=form.email.data).exists()).scalar()
        #Debug Code on next line
        #print(email_exists)

        #If the email is not in the database, process the form and add it to users.db
        if not email_exists:

            #Object that we will be placing in our add query
            user = Users(username=form.username.data, email=form.email.data, password=form.password.data)

            #Add to database
            db.session.add(user)

            #finalize this action
            db.session.commit()

            #Clear all Registration form fields for future use
            clearForm(form)

            #Redirect user to the login page
            return render_template('login.html', form=form, display="none", signup=url_for("signup"))

        #If the user email already has an account in the database, reload the page and only clear the email field.
        else:
            print("An account with this email already exists")
            form.email.data = ''
            return render_template('signup.html', form=form, display="none", login=url_for("login"))
			
# grocery index page function
@app.route('/gindex', methods=['GET', 'POST'])
def gindex():
    return render_template('gindex.html')

# grocery pantry page function
@app.route('/gpantry', methods=['GET', 'POST'])
def gpantry():
    return render_template('gpantry.html')

# user account page function
@app.route('/account', methods=['GET', 'POST'])
def account():
    return render_template('account.html')

# logout function
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('intro'))

def clearForm(form):
    form.username.data = ''
    form.email.data = ''
    form.password.data = ''
    return form

def clearFormLogin(form):
    form.email.data = ''
    form.password.data = ''
    return form

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")