import os
import secrets
import MySQLdb
import requests
from forms import Search_Form, LoginForm, RegisterForm
from flask import session, request
from flask import Flask, render_template
from flask import url_for, flash, redirect
from flask_login import LoginManager, UserMixin, login_user
from flask_login import login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text, select


# Create a flask app for the website
app = Flask(__name__) 

#Add Databases, default initial database is defined in the first line below.
#Additional databases will be defined in 'SQLALCHEMY_BINDS'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_BINDS'] = {'grocery_index' : 'sqlite:///grocery_index.db'}

# Secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)
# Initialize The Database
db = SQLAlchemy(app)

# Create user accounts table model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    # Create A String
    def __repr__(self):
        return "<username %r>" % self.username

# Create user accounts table model
# This table will store all the items for all users, table will have a primary key for each record
# but will have a foreign key defining the user


# Create grocery index model
class grocery_index_items(db.Model):
    __bind_key__ = 'grocery_index'
    id = db.Column(db.Integer, primary_key=True)
    Name= db.Column(db.String(), unique=True, nullable=False)
    ExpirationDate = db.Column(db.String(), nullable = False)
    StorageType = db.Column(db.String())    

    # Create A String
    def __repr__(self):
        return "<Name %r>" % self.Name

# Create model for every user's groceries    
class user_pantry_items(db.Model):
    __bind_key__ = 'grocery_index'
    entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer)
    expiration_date = db.Column(db.Integer, nullable = False)
    item_name = db.Column(db.String, db.ForeignKey('grocery_index_items.Name'))

    # Create A String
    def __repr__(self):
        return "<entry_id %r>" % self.entry_id


with app.app_context():
    db.create_all()

#This will be filled with a value upon login, the program will use this to access items in the pantry database
#that are exclusive to this user
session_user_email = ''

def addToPantry(item):
    pass

def getIndex():
    #Build starting grocery_items list
    grocery_items = []
    item_quantity = str(db.session.query(db.session.query(grocery_index_items).count()))
    item_quantity = int(item_quantity.strip("SELECT "))

    for i in range(1, item_quantity + 1):
        item = db.session.query(grocery_index_items).filter(grocery_index_items.id == i).first()
        item = item.Name
        grocery_items.append(item)
    return grocery_items

def incrInPantry(user_email, grocery_item):
    item_exists = db.session.query(db.session.query(user_pantry_items).filter_by(user_id =user_email, item_name = grocery_item).exists()).scalar()
    if not item_exists:

            #Object that we will be placing in our add query
            item = user_pantry_items(user_id=user_email, quantity = 1, expiration_date = "test", item_name=grocery_item)

            #Add to database
            db.session.add(item)

            #finalize this action
            db.session.commit()
    else:
         
         item = db.session.query(grocery_index_items).filter(grocery_index_items.Name == grocery_item).first()
         food_shelf_life = item.expiration_date
         setattr(item, 'quantity', user_pantry_items.quantity+1)
         setattr(item, 'expiration_date', calculate_expiration_date(food_shelf_life))

def decrInPantry(item):
    # decr grocery count in pantry
    print(item)
    pass

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
            session_user_email = form.email.data
            print(session_user_email)
            clearFormLogin(form)
            # return render_template('gindex.html')
            return gindex()
        else:
            clearFormLogin(form)
            return render_template('login.html', form=form, wel_display="block", acc_display="none", display="block", login=url_for("login"))
    
    return render_template('login.html', form=form, wel_display="block", acc_display="none", display="none", signup=url_for("signup"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if request.method=="POST":

        #Check if the email exists in the database already
        email_exists = db.session.query(db.session.query(Users).filter_by(email=form.email.data).exists()).scalar()

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
            return render_template('login.html', form=form, wel_display="none", acc_display="block", display="none", signup=url_for("signup"))

        #If the user email already has an account in the database, reload the page and only clear the email field.
        else:
            # print("An account with this email already exists")
            clearForm(form)
            return render_template('signup.html', form=form, display="block", login=url_for("login"))
   
    return render_template('signup.html', form=form, display="none", login=url_for("login"))

# grocery index page function
@app.route('/gindex', methods=['GET', 'POST'])
def gindex():
    form = Search_Form()

    # get the contents of the grocery Index
    grocery_items = getIndex()
    # in place of the frequency of each item in the user's pantry
    count_list = [i for i in range(len(grocery_items))]

    # Search bar
    if request.method == "POST":
        Search_Term = request.form.get('search')
        if Search_Term != None:
            grocery_items = find_item(Search_Term, grocery_items)
            # in place of the frequency of each item in the user's pantry
            count_list = [i for i in range(len(grocery_items))]
            return render_template('gindex.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                            account=url_for("account"), form=form, groceries=grocery_items, count = count_list)
        elif Search_Term == " ":
            grocery_items = getIndex()
            # in place of the frequency of each item in the user's pantry
            count_list = [i for i in range(len(grocery_items))]
            return render_template('gindex.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_items, count = count_list)
        
        if "increment" in request.form:
            # increase the grocery count in the user's pantry
            incrInPantry(request.form.get("increment"))
        if "decrement" in request.form:
            # decrease the grocery count in the user's pantry
            decrInPantry(request.form.get("decrement"))


    return render_template('gindex.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                        account=url_for("account"), form=form, groceries=grocery_items, count = count_list)

# grocery pantry page function
@app.route('/gpantry', methods=['GET', 'POST'])
def gpantry():
    # Search bar functionality
    search_form = Search_Form()
    return render_template('gpantry.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=search_form)

# user account page function
@app.route('/account', methods=['GET', 'POST'])
def account():
    # Search bar functionality
    search_form = Search_Form()
    return render_template('account.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=search_form)

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


#This returns an array based on if search_term exists inside search_arr
def find_item(search_item, search_arr):
    results = []

    # search for all occurences of the search term within each grocery
    for item in search_arr:
        if search_item.lower() in item.lower() or item.lower() in search_item.lower():
            results.append(item)


    return results
        

#Calculate the days remaining on a selected food item, return the days_remaining
#UNDER CONSTRUCTION
def calculate_expiration_date(shelf_life):

    days_remaining = 0
    digit_in_shelf_life = int("".join(filter(str.isdigit, shelf_life)))

    if 'months' or 'month' in shelf_life:
        days_remaining = digit_in_shelf_life * 30

    elif 'weeks' or 'week' in shelf_life:
        days_remaining = digit_in_shelf_life * 7

    elif 'years' or 'year' in shelf_life:
        days_remaining = digit_in_shelf_life * 365

    else:
        days_remaining = digit_in_shelf_life

    return days_remaining

    

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")