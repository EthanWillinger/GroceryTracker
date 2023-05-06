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

with app.app_context():
    db.create_all()

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
                return gpantry()
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
                            account=url_for("account"), form=form, groceries=grocery_items, count = count_list, expiration = [], logout=url_for("logout"))
        elif Search_Term == " ":
            grocery_items = getIndex()
             # get the frequency of each item in the user's pantry
            count_list = get_quantity(grocery_items, user_id)
            return render_template('gindex.html', current_page= url_for("gindex"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_items, count = count_list, expiration = [], logout=url_for("logout"))

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
                        account=url_for("account"), form=form, groceries=grocery_items, count = count_list, expiration = [], logout=url_for("logout"))

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
    expiration = [i.shelf_life for i in groceries]
    date_added = [i.date for i in groceries]

    if request.method == "POST":
         # Search bar
        Search_Term = request.form.get('search')
        if Search_Term != None:
            grocery_items = find_item(Search_Term, grocery_names)
            #if there are no results for the search, returns -1
            if grocery_items != -1:
                # get the frequency and shelf life of each item in the user's pantry
                # temporary format
                count_list = [i.quantity for i in groceries if i.name == grocery_names]
                expiration = [i.shelf_life for i in groceries if i.name == grocery_names]


            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                            account=url_for("account"), form=form, groceries=grocery_names, count = count_list, expiration = expiration, logout=url_for("logout"))
        elif Search_Term == " ":
            # get the frequency of each item in the user's pantry
            #temporary format
            grocery_names = [i.name for i in groceries]
            count_list = [i.quantity for i in groceries]
            expiration = [i.shelf_life for i in groceries]
            return render_template('gpantry.html', current_page= url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), 
                                account=url_for("account"), form=form, groceries=grocery_names, count = count_list, expiration = expiration, logout=url_for("logout"))

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
        
        if "autofill" in request.form:
            print("auto")
            name = request.form.get("autofill")
            date_ = date_added[grocery_names[name.index()]]
            toggleAutofill(name, user_id, date_)
        

    
    return render_template('gpantry.html', current_page=url_for("gpantry"), gindex=url_for("gindex"), gpantry=url_for("gpantry"), account=url_for("account"), form=form, count = count_list, groceries=grocery_names, expiration=expiration, logout=url_for("logout"))

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


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
