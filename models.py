from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from sqlalchemy import func
from datetime import datetime, timezone
import os

app = Flask(__name__)

# DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sjacobo3:newpassword@localhost/sjacobo3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24) # generate a random 24 byte string for the secret key for session cookies so it is not tampered with by client

# initialize SQLAlechemy
db = SQLAlchemy(app)


# MODELS
class GenderEnum(Enum):
    male = "male"
    female = "female"
    other = "other"

class Drinks(db.Model):
    __tablename__ = 'drinks'
    drink_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    brand = db.Column(db.String(50))
    name = db.Column(db.String(50))
    flavor = db.Column(db.String(50))
    volume = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    caffeine_amt = db.Column(db.Integer)
    category = db.Column(db.String(50))
    sugar_g = db.Column(db.Integer)

    def __repr__(self):
        return f"<Drink {self.name}>"


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username}" 

class Drink_Ratings(db.Model):
    __tablename__ = 'drink_ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    drink_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    rating = db.Column(db.SmallInteger)
    created_at = db.Column(db.DateTime, default=datetime.now())

class User_Details(db.Model):
    __tablename__ = 'user_details'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum(GenderEnum))
    weight = db.Column(db.Numeric(10, 2))
    caffeine_max = db.Column(db.Integer)

class Drink_Favorites(db.Model):
    __tablename__ = 'drink_favorites'
    fav_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.drink_id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())   

    user = db.relationship('Users', backref=db.backref('favorites'))
    drink = db.relationship('Drinks', backref=db.backref('favorited_by'))

class Caffeine_Log(db.Model):
    __tablename__ = 'caffeine_log'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.drink_id'))
    drink_ml = db.Column(db.Integer)
    caffeine_consumed = db.Column(db.Integer)
    consumed_at = db.Column(db.DateTime, default=datetime.now())

    user = db.relationship('Users', backref=db.backref('caffeine_logs'))
    drink = db.relationship('Drinks', backref=db.backref('caffeine_logs'))
