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
import bleach
from datetime import datetime, date


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

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

# Create user accounts table model
class Users(db.Model, UserMixin):
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
class pantry(db.Model):
    __bind_key__ = 'grocery_index'
    entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer)
    expiration_date = db.Column(db.String, nullable = False)
    item_name = db.Column(db.String, nullable = False)
    date_added = db.Column(db.String, nullable = False)

    # Create A String
    def __repr__(self):
        return "<entry_id %r>" % self.entry_id


with app.app_context():
    db.create_all()

#sanitizes user inputs to prevent injections
def sanitize(data):
    return bleach.clean(data)


def addToPantry(user_email, grocery_item, expiration, date_added):
    #Object that we will be placing in our add query
    item =  pantry(user_id=user_email, quantity = 1, expiration_date = expiration, item_name=grocery_item, date_added=date_added)

    #Add to database
    db.session.add(item)

    #finalize this action
    db.session.commit()

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
    date_added = str(datetime.now()).split(' ')[0]
    item_exists = db.session.query(db.session.query(pantry).filter_by(user_id = user_email, item_name = grocery_item, date_added=date_added).exists()).scalar()
    index = db.session.query(grocery_index_items).filter(grocery_index_items.Name == grocery_item).first()
    expires = index.ExpirationDate

    if not item_exists:
        expiration = calculate_expiration_date(expires, date_added)
        addToPantry(user_email, grocery_item, expiration, date_added)
    
    else:
         item = db.session.query(pantry).filter(pantry.item_name == grocery_item, pantry.user_id == user_email).first()
         date_added = item.date_added
         item.quantity += 1
         db.session.commit()

def decrInPantry(user_email, grocery_item):
            date_added = str(datetime.now()).split(' ')[0]
            item_exists = db.session.query(db.session.query(pantry).filter_by(user_id = user_email, item_name = grocery_item, date_added=date_added).exists()).scalar()
            
            if item_exists:
                item = db.session.query(pantry).filter(pantry.item_name == grocery_item,pantry.user_id == user_email).first()
                if item.quantity > 0:
                    setattr(item, 'quantity', pantry.quantity-1)
                    db.session.commit()
            else:
                old_item_exists = db.session.query(db.session.query(pantry).filter_by(user_id = user_email, item_name = grocery_item).exists()).scalar()
                if old_item_exists:
                    item = db.session.query(pantry).filter(pantry.item_name == grocery_item,pantry.user_id == user_email).first()
                    if item.quantity > 0:
                        setattr(item, 'quantity', pantry.quantity-1)
                        db.session.commit()


#Calculate the days remaining on a selected food item, return the days_remaining
def calculate_expiration_date(shelf_life, date_added):

    #calculate the expiration relative to now
    current_date = str(datetime.now()).split(' ')[0]
    initial_date = date(int(date_added.split('-')[0]), int(date_added.split('-')[1]), int(date_added.split('-')[2]))
    current_date = date(int(current_date.split('-')[0]), int(current_date.split('-')[1]), int(current_date.split('-')[2]))
    days_used =  current_date - initial_date
    digit_in_shelf_life = int("".join(filter(str.isdigit, shelf_life)))

    if 'months' or 'month' in shelf_life:
        days_available = digit_in_shelf_life * 30

    elif 'weeks' or 'week' in shelf_life:
        days_available = digit_in_shelf_life * 7

    elif 'years' or 'year' in shelf_life:
        days_available = digit_in_shelf_life * 365

    else:
        days_available = digit_in_shelf_life
    
    days_left = days_available - days_used.days
    
    # Get the correct time frame for expiration
    if days_left < 7:
        time_left= str(days_left)+ " day(s)"
    elif days_left >= 7 and days_left < 30:
        time_left= str(days_left//7)+ " week(s)"
    elif days_left >= 30 and days_left < 365:
        time_left= str(days_left//30)+ " month(s)"
    else:
        time_left= str(days_left//365)+ " year(s)"  

    return time_left

def get_quantity(grocery_items, user_id):
    count_list = []
    quantity = 0
    for i in grocery_items:
        item_exits = db.session.query(db.session.query(pantry).filter_by(user_id = user_id, item_name = i).exists()).scalar()
        if item_exits:
            item = (db.session.query(pantry).filter(pantry.user_id == user_id, pantry.item_name == i).first())
            count_list.append(item.quantity)
        else:
            count_list.append(0)

    return count_list
    
# The intro page
@app.route("/intro", methods=['GET', 'POST'])
def intro():
    session['user_id'] = ""
    form=Search_Form() #will be removed later, needed only to make the page load
    return render_template('intro.html',gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), login=url_for('login'), signup=url_for('signup'), logout=url_for("logout"), form=form)


@app.route("/")
# login page function. The code below until the next comment allows the user to interact with forms.py
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method=="POST":
        #sanitize inputs
        email = sanitize(form.email.data)
        password = sanitize(form.password.data)

        email_exists = db.session.query(db.session.query(Users).filter_by(email=email).exists()).scalar()
        username_exists = db.session.query(db.session.query(Users).filter_by(username=email).exists()).scalar()

        if email_exists or username_exists:

            if email_exists:
                user = db.session.query(Users).filter_by(email=email).first()
            else:
                user = db.session.query(Users).filter_by(username=email).first()

            # check if password matches
            if check_password_hash(user.password, password):
                load_user(user.id)
                login_user(user)
                clearFormLogin(form)
                session['user_id'] = user.email
                return gindex()
            else:
                clearFormLogin(form)
                return render_template('login.html', form=form, wel_display="block", acc_display="none", display="block", login=url_for("login"), logout=url_for("logout"))
        else:
            clearFormLogin(form)
            return render_template('login.html', form=form, wel_display="block", acc_display="none", display="block", login=url_for("login"), logout=url_for("logout"))
    
    clearFormLogin(form)
    return render_template('login.html', form=form, wel_display="block", acc_display="none", display="none", signup=url_for("signup"), logout=url_for("logout"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if request.method=="POST":
        #sanitize inputs
        email = sanitize(form.email.data)
        password = generate_password_hash(sanitize(form.password.data))
        username = sanitize(form.username.data)

        #Check if the email exists in the database already
        email_exists = db.session.query(db.session.query(Users).filter_by(email=email).exists()).scalar()

        #If the email is not in the database, process the form and add it to users.db
        if not email_exists:

            #Object that we will be placing in our add query
            user = Users(username=username, email=email, password=password)

            #Add to database
            db.session.add(user)

            #finalize this action
            db.session.commit()

            #Clear all Registration form fields for future use
            clearForm(form)

            #Redirect user to the login page
            return render_template('login.html', form=form, wel_display="none", acc_display="block", display="none", signup=url_for("signup"), logout=url_for("logout"))

        #If the user email already has an account in the database, reload the page and only clear the email field.
        else:
            # print("An account with this email already exists")
            clearForm(form)
            return render_template('signup.html', form=form, display="block", login=url_for("login"), logout=url_for("logout"))
    
    clearForm(form)
    return render_template('signup.html', form=form, display="none", login=url_for("login"), logout=url_for("logout"))

# grocery index page function
@app.route('/gindex', methods=['GET', 'POST'])
def gindex():
    user_id = session.get('user_id')
    form = Search_Form()

    # get the contents of the grocery Index
    grocery_items = getIndex()
    count_list = get_quantity(grocery_items, user_id)

    if request.method == "POST":
         # Search bar
        Search_Term = request.form.get('search')
        if Search_Term != None:
            grocery_items = find_item(Search_Term, grocery_items)
            #if there are no results for the search, returns -1
            if grocery_items != -1:
                # get the frequency of each item in the user's pantry
                count_list = get_quantity(grocery_items, user_id)


            return render_template('gindex.html', current_page= url_for("gindex"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                            account=url_for("account"), form=form, groceries=grocery_items, count = count_list, logout=url_for("logout"))
        elif Search_Term == " ":
            grocery_items = getIndex()
             # get the frequency of each item in the user's pantry
            count_list = get_quantity(grocery_items, user_id)
            return render_template('gindex.html', current_page= url_for("gindex"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_items, count = count_list, logout=url_for("logout"))

        if "increment" in request.form:
            # increase the grocery count in the user's pantry
            
            if user_id != "":
                incrInPantry(user_id, request.form.get("increment"))
                count_list = get_quantity(grocery_items, user_id)
            else:
                return redirect(url_for('login'))

        if "decrement" in request.form:
            # decrease the grocery count in the user's pantry
            if user_id != "":
                decrInPantry(user_id, request.form.get("decrement"))
                count_list = get_quantity(grocery_items, user_id)
            else:
                return redirect(url_for('login'))


    return render_template('gindex.html', current_page= url_for("gindex"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                        account=url_for("account"), form=form, groceries=grocery_items, count = count_list, logout=url_for("logout"))

# grocery pantry page function
@app.route('/gpantry', methods=['GET', 'POST'])
@login_required
def gpantry():
    form = Search_Form()
    user_id = session.get('user_id')
    #temporary format
    groceries = load_user_pantry(user_id)
    grocery_names = [i.name for i in groceries]
    count_list = [i.quantity for i in groceries]

    if request.method == "POST":
         # Search bar
        Search_Term = request.form.get('search')
        if Search_Term != None:
            grocery_items = find_item(Search_Term, grocery_names)
            #if there are no results for the search, returns -1
            if grocery_items != -1:
                # get the frequency of each item in the user's pantry
                # temporary format
                count_list = [i.quantity for i in groceries if i.name == grocery_names]


            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                            account=url_for("account"), form=form, groceries=grocery_names, count = count_list, logout=url_for("logout"))
        elif Search_Term == " ":
            # get the frequency of each item in the user's pantry
            #temporary format
            grocery_names = [i.name for i in groceries]
            count_list = [i.quantity for i in groceries]
            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_names, count = count_list, logout=url_for("logout"))

        if "increment" in request.form:
            # increase the grocery count in the user's pantry
            print(user_id)
            
            if user_id != "":
                incrInPantry(user_id, request.form.get("increment"))
                count_list = get_quantity(grocery_names, user_id)
            else:
                return redirect(url_for('login'))

        if "decrement" in request.form:
            # decrease the grocery count in the user's pantry
            if user_id != "":
                decrInPantry(user_id, request.form.get("decrement"))
                count_list = get_quantity(grocery_names, user_id)
            else:
                return redirect(url_for('login'))

    
    return render_template('gpantry.html', current_page=url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=form, count = count_list, groceries=grocery_names, logout=url_for("logout"))

# user account page function
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # Search bar functionality
    search_form = Search_Form()
    return render_template('account.html', gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=search_form, logout=url_for("logout"))

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

    if results == []:
        return -1


    return results
        

#This function will do the following

#1. Perform a query on the user_pantry table that only selects entries
#   with the user_id matching the "users_email" argument. Save this to a variable

#2. Create a class that will store the name, shelf life, and quantity of a given pantry record

#3. For each record in the collection of records (items), create an instance of "food" and provide
#   it with the records item_name, expiration_date, and quantity save it to variable called food_item

#4. Add "food_item" to the user_items array
#
#5. Return user_items. This array of food objects will be used to display the name, quantity and to calculate
#   the days remaining on the item
def load_user_pantry(users_email):
    if users_email == "":
        return []
    user_items = []
    
    items = db.session.query(pantry).filter(pantry.user_id == users_email).all()

    class food:
        def __init__(self,name,shelf_life, quantity):
            self.name = name
            self.shelf_life = shelf_life
            self.quantity = quantity

    for item in items:
        food_item = food(item.item_name, item.expiration_date, item.quantity)
        if food_item.quantity != 0:
            user_items.append(food_item)

    return user_items

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")