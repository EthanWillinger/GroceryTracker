from datetime import datetime, date
from models import grocery_index_items, pantry
from main import db


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
         item.quantity += 1
         db.session.commit()

def decrInPantry(user_email, grocery_item):
            date_added = str(datetime.now()).split(' ')[0]
            item_exists = db.session.query(db.session.query(pantry).filter_by(user_id = user_email, item_name = grocery_item, date_added=date_added).exists()).scalar()
            
            if item_exists:
                item = db.session.query(pantry).filter(pantry.item_name == grocery_item, pantry.user_id == user_email, pantry.date_added == date_added).first()
                quantity = item.quantity - 1
                if quantity > 0:
                    item.quantity -= 1
                else:
                    pantry.query.filter(pantry.item_name == grocery_item, pantry.user_id == user_email, pantry.date_added == date_added).delete()

            else:
                #if the item being deleted was not added today
                old_item_exists = db.session.query(db.session.query(pantry).filter_by(user_id = user_email, item_name = grocery_item).exists()).scalar()
                if old_item_exists:
                    item = db.session.query(pantry).filter(pantry.item_name == grocery_item, pantry.user_id == user_email).first()
                    quantity = item.quantity - 1
                    if quantity > 0:
                        item.quantity -= 1
                    else:
                        pantry.query.filter(pantry.item_name == grocery_item, pantry.user_id == user_email).delete()

            
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

def addToPantry(user_email, grocery_item, expiration, date_added):
    #Object that we will be placing in our add query
    item =  pantry(user_id=user_email, quantity = 1, expiration_date = expiration, item_name=grocery_item, date_added=date_added)

    #Add to database
    db.session.add(item)

    #finalize this action
    db.session.commit()

def toggleAutofill(grocery_item, user_email, date_added):
    item = db.session.query(pantry).filter(pantry.item_name == grocery_item, pantry.user_id == user_email, pantry.date_added == date_added).first()
    #toggle boolean value
    item.auto_fill = not item.auto_fill
    #finalize this action
    db.session.commit()

def deleteItem(grocery_item, user_email, date_added):
    pantry.query.filter(pantry.item_name == grocery_item, pantry.user_id == user_email, pantry.date_added == date_added).delete()
    #finalize this action
    db.session.commit()
