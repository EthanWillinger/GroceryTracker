from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask import current_app as app




def initDB():
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
        
        

        
    return db