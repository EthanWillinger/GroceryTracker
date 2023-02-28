import os
import secrets
import requests
from forms import Search_Form, LoginForm, RegisterForm
from flask import session, request
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from flask import url_for, flash, redirect
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, UserMixin, login_user
from flask_login import login_required, logout_user, current_user

from werkzeug.security import generate_password_hash, check_password_hash

# Create a flask app for the website
app = Flask(__name__) 
proxied = FlaskBehindProxy(app)

# Assign the flask app an secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)

#Database configuration and creating sqlalchemy object
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/auth'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

#Create User Model

class User(db.Model):

    __tablename__ = 'usertable'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique = True)
    email = db.Column(db.String(50), unique = True)
    password = db.Column(db.String(256), unique=True)

# The intro page
@app.route("/intro", methods=['GET', 'POST'])
def intro():
    return render_template('intro.html', login=url_for('login'), signup=url_for('signup'))

# Home webpage function
@app.route("/home", methods=['GET', 'POST'])
def home(user):
    print("home page")

# login page function
@app.route('/login', methods=['GET', 'POST'])
#Umair code goes here
def login():
    form = LoginForm(request.form)
    
    return render_template('login.html', form=form, display="none", signup=url_for("signup"))

@app.route("/")
# signup page function
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm(request.form)

    # Checking that method is post and form is valid or not.
    if request.method == 'POST' and form.validate():
        print("Yay")
        #storing a users password in plain text is just... stupid.... encript it :)
        hashed_password = generate_password_hash(form.password.data, method='sha256')

        # create new user model object
        new_user = User(

            username = form.username.data,
            email = form.email.data,
            password = hashed_password
        )

        # saving user object into data base with hashed password
        db.session.add(new_user)

        db.session.commit()

        flash('Welcome to the cult', 'success')
        
        # if registration successful, then redirecting to login page
        return redirect(url_for('login'))
    
    else:
        # if method is Get, than render registration form
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

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host="0.0.0.0")