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

# Create a flask app for the website
app = Flask(__name__) 
proxied = FlaskBehindProxy(app)

# Assign the flask app an secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)

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
def login():
    form = LoginForm()
    return render_template('login.html', form=form, display="none", signup=url_for("signup"))

@app.route("/")
# signup page function
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
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
    app.run(debug=True, host="0.0.0.0")