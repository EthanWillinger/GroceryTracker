import os
import secrets
import MySQLdb
import requests
from forms import *
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
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit



# Create a flask app for the website
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'thegrocerytrackerapp@gmail.com'
app.config['MAIL_PASSWORD'] = 'aptvhrhyfqbngmkp'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

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

from models import Users, grocery_index_items, pantry

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))


with app.app_context():
    db.create_all()

#Temporary import location due to the fact that pantry_modifiers.py depends on the database
#from this file to be initialized, this will be moved once the database models and initialization
#are relocated to their own /py file
from pantry_modifiers import *

#Function that determines what users notifications to
def expiration_notification():
    with app.app_context():
        users_to_notify = []
        items = []
        expired_items_string = ""
        users = db.session.query(Users).filter(Users.notifications == True).all()

        class food:
            def __init__(self,name,shelf_life, date_added):
                self.name = name
                self.shelf_life = shelf_life
                self.date_added = date_added

        
        #For each user, grab the email and append it to the users_to_notify
        for user in users:
            user = user.email
            users_to_notify.append(user)

        #Begin looking for expired food
        for user in users_to_notify:
            users_food_items = db.session.query(pantry).filter(pantry.user_id == user).all()
            #Check if each food item belonging to the user.email specified is expired or about to expire
            for item in users_food_items:
                item = food(item.item_name, item.expiration_date, item.date_added)
                days_left = calculate_expiration_date(item.shelf_life, item.date_added)
                days_left = days_left.split()

                if 'day(s)' in days_left:
                    print(days_left)
                    days_left = int(days_left[0])
                    if days_left <= 1:
                        expired_items_string = expired_items_string + item.name + "\n"


            print(expired_items_string)
            if expired_items_string != "":    
                #Begin generating email for user
                msg = Message("You have grocieres that are going bad!", sender = 'thegrocerytrackerapp@gmail.com', recipients = [user])
                msg.body = "The following groceries are either about to expire or are already rotten, check your grocery tracker for more information. \n" + expired_items_string
                mail.send(msg)
                expired_items_string = ""

#sanitizes user inputs to prevent injections
def sanitize(data):
    return bleach.clean(data)

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

    

scheduler = BackgroundScheduler()
scheduler.add_job(func = expiration_notification, trigger="interval", seconds=15)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


 
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
                return redirect(url_for('gpantry'))
            else:
                clearFormLogin(form)
                return render_template('login.html', current_page= url_for("login"), form=form, wel_display="block", acc_display="none", display="block", login=url_for("login"), logout=url_for("logout"))
        else:
            clearFormLogin(form)
            return render_template('login.html', current_page= url_for("login"), form=form, wel_display="block", acc_display="none", display="block", login=url_for("login"), logout=url_for("logout"))
    
    clearFormLogin(form)
    return render_template('login.html', current_page= url_for("login"), form=form, wel_display="block", acc_display="none", display="none", signup=url_for("signup"), logout=url_for("logout"))


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
            user = Users(username=username, email=email, password=password, notifications=False)

            #Add to database
            db.session.add(user)

            #finalize this action
            db.session.commit()

            #Clear all Registration form fields for future use
            clearForm(form)

            #Redirect user to the login page
            return render_template('login.html', current_page= url_for("signup"),form=form, wel_display="none", acc_display="block", display="none", signup=url_for("signup"), logout=url_for("logout"))

        #If the user email already has an account in the database, reload the page and only clear the email field.
        else:
            # print("An account with this email already exists")
            clearForm(form)
            return render_template('signup.html', current_page= url_for("signup"), form=form, display="block", login=url_for("login"), logout=url_for("logout"))
    
    clearForm(form)
    return render_template('signup.html', current_page= url_for("signup"), form=form, display="none", login=url_for("login"), logout=url_for("logout"))

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
                            account=url_for("account"), form=form, groceries=grocery_items, count = count_list, status = [], expiration = [], logout=url_for("logout"))
        elif Search_Term == " ":
            grocery_items = getIndex()
             # get the frequency of each item in the user's pantry
            count_list = get_quantity(grocery_items, user_id)
            return render_template('gindex.html', current_page= url_for("gindex"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_items, count = count_list, status = [], expiration = [], logout=url_for("logout"))

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
                        account=url_for("account"), form=form, groceries=grocery_items, count = count_list, status = [], expiration = [], logout=url_for("logout"))

# grocery pantry page function
@app.route('/gpantry', methods=['GET', 'POST'])
@login_required
def gpantry():
    form = Search_Form()
    user_id = session.get('user_id')

    groceries = load_user_pantry(user_id)
    grocery_names = [i.name for i in groceries]
    count_list = [i.quantity for i in groceries]
    expiration = [i.shelf_life for i in groceries]
    date_added = [i.date for i in groceries]
    auto_fill = [i.auto_fill for i in groceries]

    if request.method == "POST":
         # Search bar
        Search_Term = request.form.get('search')
        if Search_Term != None:
            grocery_items = find_item(Search_Term, grocery_names)
            #if there are no results for the search, returns -1
            if grocery_items != -1:
                # get the frequency and shelf life of each item in the user's pantry
                # temporary format
                count_list = [i.quantity for i in groceries if i.name in grocery_items]
                expiration = [i.shelf_life for i in groceries if i.name in grocery_items]
                auto_fill = [i.auto_fill for i in groceries if i.name in grocery_items]


            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                            account=url_for("account"), form=form, groceries=grocery_names, count = count_list, status=auto_fill, expiration = expiration, logout=url_for("logout"))
        elif Search_Term == " ":
            # get the frequency of each item in the user's pantry
            #temporary format
            grocery_names = [i.name for i in groceries]
            count_list = [i.quantity for i in groceries]
            expiration = [i.shelf_life for i in groceries]
            auto_fill = [i.auto_fill for i in groceries]
            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_names, count = count_list, status=auto_fill, expiration = expiration, logout=url_for("logout"))

        elif "increment" in request.form:
            # increase the grocery count in the user's pantry
            print(user_id)
            
            if user_id != "":
                incrInPantry(user_id, request.form.get("increment"))
                count_list = get_quantity(grocery_names, user_id)
            else:
                return redirect(url_for('login'))

        elif "decrement" in request.form:
            # decrease the grocery count in the user's pantry
            if user_id != "":
                decrInPantry(user_id, request.form.get("decrement"))
                count_list = get_quantity(grocery_names, user_id)
            else:
                return redirect(url_for('login'))
        
        elif "delete" in request.form:
            name = request.form.get("delete")
            date_ = date_added[grocery_names.index(name)]
            deleteItem(name, user_id, date_)

            groceries = load_user_pantry(user_id)
            grocery_names = [i.name for i in groceries]
            count_list = [i.quantity for i in groceries]
            expiration = [i.shelf_life for i in groceries]
            date_added = [i.date for i in groceries]
            auto_fill = [i.auto_fill for i in groceries]  

        elif "autofill" in request.form:
            name = request.form.get("autofill-selected")
            date_ = date_added[grocery_names.index(name)]
            toggleAutofill(name, user_id, date_)
            
            groceries = load_user_pantry(user_id)
            grocery_names = [i.name for i in groceries]
            count_list = [i.quantity for i in groceries]
            expiration = [i.shelf_life for i in groceries]
            date_added = [i.date for i in groceries]
            auto_fill = [i.auto_fill for i in groceries]      

    
    return render_template('gpantry.html', current_page=url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=form, count = count_list, groceries=grocery_names, expiration=expiration, status=auto_fill, logout=url_for("logout"))

# user account page function
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    user_id = session.get('user_id')
    this_user = db.session.query(Users).filter_by(email=user_id).first()

    if request.method == "POST":
        if "expiry" in request.form:
            this_user.notifications = not this_user.notifications
            db.session.commit()
            
    emailForm = UpdateEmail()
    pwdForm = UpdatePwd()
    notifs = this_user.notifications

    return render_template('account.html', current_page= url_for("account"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), emailUpdate=emailForm, pwdUpdate=pwdForm, expiryStatus=notifs, logout=url_for("logout"))

# logout functionn
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
        def __init__(self,name,shelf_life, quantity, date_added, auto_fill):
            self.name = name
            self.shelf_life = shelf_life
            self.quantity = quantity
            self.date = date_added
            self.auto_fill = auto_fill

    for item in items:
        food_item = food(item.item_name, item.expiration_date, item.quantity, item.date_added, item.auto_fill)
        if food_item.quantity != 0:
            user_items.append(food_item)

    return user_items

def toggle_notification():
    user_id = session.get('user_id')
    user = db.session.query(Users).filter(user.id == user_id).first()
    user.notifiactions = not user.notifications
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
