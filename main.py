import os
import secrets
import requests
from forms import Search_Form, LoginForm, RegisterForm
from flask import session, request
from flask import Flask, render_template
from flask import url_for, flash, redirect
from flask_behind_proxy import FlaskBehindProxy
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
# login page function
@app.route('/login', methods=['GET', 'POST'])
#Umair code goes here
def login():
    form = LoginForm()
    return render_template('login.html', form=form, display="none", signup=url_for("signup"))

# signup page function
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    return render_template('signup.html', form=form)

@app.route('/register_success', methods=['GET', 'POST'])
def success():
    form = RegisterForm()
    if request.method=="POST":
        email_exists = db.session.query(db.session.query(Users).filter_by(email=form.email.data).exists()).scalar()
        print(email_exists)
        if email_exists == False:
            user = Users(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            form.username.data = ''
            form.email.data = ''
            form.password.data = ''
            flash("User Added!")
            return render_template('login.html', form=form, display="none", signup=url_for("signup"))

        else:
            flash("An account with this email already exists")
            form.email.data = ''
            return render_template('signup.html', form=form)
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
    app.run(debug=True, host="0.0.0.0")