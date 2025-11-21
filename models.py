from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
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
class Drinks(db.Model):
    __tablename__ = 'drinks'
    name = db.Column(db.String(50), primary_key=True)
    volume = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    caffeine_amt = db.Column(db.Integer)
    caffeine_type = db.Column(db.String(15))

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

class GenderEnum(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class User_Details(db.Model):
    __tablename__ = 'user_details'
    user_id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum(GenderEnum))
    weight = db.Column(db.Numeric(5, 2))
    caffeine_max = db.Column(db.Integer)

class Drink_Ratings(db.Model):
    __tablename__ = 'drink_ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    drink_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    rating = db.Column(db.SmallInteger)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
