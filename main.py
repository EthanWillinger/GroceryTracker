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
import MySQLdb


# Create a flask app for the website
app = Flask(__name__) 
proxied = FlaskBehindProxy(app)

#Add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
# Assign the flask app an secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)


app.app_context().push()

#Initialize the database
db = SQLAlchemy(app)

db.create_all()
db.session.commit()


#Create User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique = True)
    email = db.Column(db.String(50), unique = True)
    password = db.Column(db.String(256), unique=True)

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name
    



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
    form = LoginForm(request.form)
    
    return render_template('login.html', form=form, display="none", signup=url_for("signup"))

# signup page function
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    username = None
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        new_user = User(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data
        )

        db.session.add(new_user)
        try:
            db.session.commit()
        except:
            return render_template('signup.html', form=form, login=url_for("login"), display = "block")

        flash('You have successfully registered', 'success')

        return redirect(url_for('login'))
    else:
        return render_template('signup.html', form = form)



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