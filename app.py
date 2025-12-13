from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
from models import Drinks, Users, User_Details, GenderEnum, app, db
from sqlalchemy import func, desc 
from datetime import datetime, timezone
from functools import wraps
import random


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

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    user_id = session['user_id'] if 'user_id' in session else None

    #get user inputs for search 
    userinput_query = request.args.get('name', None)
    userinput_category = request.args.get('category', 'name')

    #get all drink data 
    drinks = Drinks.query

    if userinput_query: 
        if userinput_category == 'name':
            drinks = drinks.filter(func.lower(Drinks.name).contains(userinput_query.lower()))
        elif userinput_category == 'calories': 
            if userinput_query.isdigit():
                drinks = drinks.filter(Drinks.calories == int(userinput_query))
            else: 
                drinks = drinks.filter(False)
        elif userinput_category == 'caffeine_amt': 
            if userinput_query.isdigit(): 
                drinks = drinks.filter(Drinks.caffeine_amt == int(userinput_query))
            else: 
                drinks = drinks.filter(False)
        else:
            drinks = drinks.filter(False)

    # pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = drinks.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    # get user favorites if logged in
    user_favorites = Drink_Favorites.query.filter_by(user_id=user_id).all() if user_id else []
    user_favorite_ids = {fav.drink_id for fav in user_favorites}

    return render_template('home_page.html', drinks=items, active_tab='home', pagination=pagination, query=userinput_query, category=userinput_category, user_favorites=user_favorite_ids)

@app.post("/add_favorite")
@login_required
def add_favorite():
    user_id = session['user_id']
    drink_id = request.form.get('drink_id', type=int)

    exists = Drink_Favorites.query.filter_by(user_id=user_id, drink_id=drink_id).first()
    if exists:
        flash("Drink is already in your favorites.")
        return redirect(url_for('home'))

    new_favorite = Drink_Favorites(user_id=user_id, drink_id=drink_id)
    db.session.add(new_favorite)
    db.session.commit()
    flash("Added to favorites!", 'success')
    return redirect(url_for('home'))

@app.post("/remove_favorite")
@login_required
def remove_favorite():
    user_id = session['user_id']
    drink_id = request.form.get('drink_id', type=int)

    exists = Drink_Favorites.query.filter_by(user_id=user_id, drink_id=drink_id).first()
    if exists:
        db.session.delete(exists)
        db.session.commit()
        flash("Removed from favorites!", 'success')
        return redirect(url_for('home'))

    flash("Drink is not in your favorites.")
    return redirect(url_for('home'))

@app.route("/log_drink", methods=["POST"])
@login_required
def log_drink():
    user_id = session['user_id']
    drink_id = request.form.get('drink_id')
    drink_ml = request.form.get('drink_ml')

    drink = Drinks.query.get(drink_id)

    # calculate caffeine consumed based on volume
    caffeine_consumed = (drink.caffeine_amt / drink.volume) * int(drink_ml)

    new_log = Caffeine_Log(user_id=user_id, drink_id=drink_id, drink_ml=drink_ml, caffeine_consumed=caffeine_consumed)
    db.session.add(new_log)
    db.session.commit()
    flash("Drink logged!", 'success')
    return redirect(url_for('home'))

@app.route("/leaderboard")
def leaderboard():
    #get selected category (default overall)
    category = request.args.get('leadertype', 'overall')
          
    if category == 'overall':
        top_drinks= db.session.query(
            Drink_Ratings.drink_id,
            func.avg(Drink_Ratings.rating).label('avg_rating')
        ).join(
            Drinks, Drinks.drink_id == Drink_Ratings.drink_id 
        ).group_by(
            Drink_Ratings.drink_id
        ).order_by(
            desc('avg_rating')
        ).limit(10).all()

    elif category == 'coffee':
        top_drinks = db.session.query(
            Drink_Ratings.drink_id,
            func.avg(Drink_Ratings.rating).label('avg_rating')
        ).join(
            Drinks, Drinks.drink_id == Drink_Ratings.drink_id 
        ).filter(
            Drinks.category == 'Coffee'
        ).group_by(
            Drink_Ratings.drink_id
        ).order_by(
            desc('avg_rating')
        ).limit(10).all()
       
    elif category == 'tea':
        top_drinks= db.session.query(
            Drink_Ratings.drink_id,
            func.avg(Drink_Ratings.rating).label('avg_rating')
        ).join(
          Drinks, Drinks.drink_id == Drink_Ratings.drink_id
        ).filter(
            Drinks.category == 'Tea'
        ).group_by(
            Drink_Ratings.drink_id
        ).order_by(
            desc('avg_rating')
        ).limit(10).all()
       
    elif category == 'energy':
        top_drinks = db.session.query(
            Drink_Ratings.drink_id,
            func.avg(Drink_Ratings.rating).label('avg_rating')
        ).join(
          Drinks, Drinks.drink_id == Drink_Ratings.drink_id
        ).filter(
            Drinks.category == 'Energy'
        ).group_by(
            Drink_Ratings.drink_id
        ).order_by(
            desc('avg_rating')
        ).limit(10).all()

    elif category == 'water':
        top_drinks = db.session.query(
            Drink_Ratings.drink_id,
            func.avg(Drink_Ratings.rating).label('avg_rating')
        ).join(
            Drinks, Drinks.drink_id == Drink_Ratings.drink_id 
        ).filter(
            Drinks.category == 'Water'
        ).group_by(
            Drink_Ratings.drink_id
        ).order_by(
            desc('avg_rating')
        ).limit(10).all()

    elif category == 'brands':
            top_drinks = db.session.query(
                Drinks.brand,
                func.avg(Drink_Ratings.rating).label('avg_rating')
            ).join(
                Drinks, Drinks.drink_id == Drink_Ratings.drink_id 
            ).group_by(
                Drinks.brand
            ).order_by(
                desc('avg_rating')
            ).limit(10).all()

    else:
        top_drinks = []
   
    leaderboard_data = []
    if category != "brands":
        for rank, (drink_id, avg_rating) in enumerate(top_drinks, start=1):
            drink = Drinks.query.get(drink_id)
            if drink:
                leaderboard_data.append({
                    'rank': rank,
                    'drink': drink, 
                    'avg_rating': round(avg_rating, 2)
                })
    else: 
        for rank, (brand, avg_rating) in enumerate(top_drinks, start = 1):
            leaderboard_data.append({
                'rank': rank, 
                'brand' : brand,
                'avg_rating': round(avg_rating, 2)
            })

   
    return render_template('leaderboard.html',
                         active_tab='leaderboard',
                         leaderboard_data=leaderboard_data,
                         leadertype=category)


@app.route("/recommendation", methods=["GET", "POST"])
@login_required
def recommendation():
    user = session['user_id']
    
    if request.method == "POST":
        # get user inputs from form
        mood = request.form.get("mood")
        flavor = request.form.get("flavor")
        calorie_pref = request.form.get("calorie_pref")
        sugar_pref = request.form.get("sugar_pref")
        similarity = request.form.get("similarity")
        
        # base query
        query = Drinks.query

        # filter based on mood (Caffeine in mg) 
        if mood == "night":
            query = query.filter(Drinks.caffeine_amt.between(80, 200))
        elif mood == "morning":
            query = query.filter(Drinks.caffeine_amt.between(30, 100))
        elif mood == "gym":
            query = query.filter(Drinks.caffeine_amt.between(150, 300))
        elif mood == "refresh":
            query = query.filter(Drinks.caffeine_amt == 0)
        
        # filter based on flavor
        if flavor and flavor != "no-pref":
            query = query.filter(Drinks.flavor.ilike(f"%{flavor}%"))

        # filter based on calorie preference
        if calorie_pref == "low-cal":
            query = query.filter(Drinks.calories < 50)
        elif calorie_pref == "med-cal":
            query = query.filter(Drinks.calories.between(50, 150))
        elif calorie_pref == "high-cal":
            query = query.filter(Drinks.calories > 150)

        # filter based on sugar preference (Sugar in grams, ranges to match button labels: <50, 50-150, >150)
        # High Sugar: Over 11.25g per 100ml
        # Medium Sugar (Amber): 5g to 22.5g per 100g/ml.
        # Low Sugar (Green): 5g or less per 100g/ml.
        if sugar_pref == "low-sugar":
            query = query.filter(Drinks.sugar_g < 50)
        elif sugar_pref == "med-sugar":
            query = query.filter(Drinks.sugar_g.between(50, 150))
        elif sugar_pref == "high-sugar":
            query = query.filter(Drinks.sugar_g > 150)

        # filter based on similarity preference
        if similarity == "favorites":
            # get user's top rated drinks
            top_rated = db.session.query(
                Drink_Ratings.drink_id
                ).filter(
                    Drink_Ratings.user_id == user
                    ).order_by(
                        desc(Drink_Ratings.rating)
                        ).limit(5).all()
        
            top_rated_ids = [drink_id for (drink_id,) in top_rated]
            
            if top_rated_ids:
                # get flavors of top rated drinks
                favored_flavors = db.session.query(
                    Drinks.flavor
                    ).filter(
                        Drinks.drink_id.in_(top_rated_ids)
                        ).all()
            # Extract the first flavor from potentially comma-separated string
            favored_flavor_list = [flavor.split(',')[0].strip() for (flavor,) in favored_flavors if flavor]
            
            if favored_flavor_list:
                # filter drinks to match favored flavors
                query = query.filter(Drinks.flavor.in_(favored_flavor_list))
            
        drinks = query.all()
        
        return render_template('recommend.html', active_tab='recommendation', recommendation=drinks)

    return render_template('recommend.html', active_tab='recommendation')

@app.route("/accounts")
@login_required
def accounts():
    user_id = session.get('user_id')
    user_details = User_Details.query.filter_by(user_id=user_id).first()

    # fetch caffeine logs
    logs = Caffeine_Log.query.filter_by(user_id=user_id).order_by(Caffeine_Log.consumed_at.desc()).all()
    
    # fetch favorite drinks
    favorites = Drink_Favorites.query.filter_by(user_id=user_id).join(Drinks).all()

    return render_template('accounts.html', active_tab='accounts', user_details=user_details, caffeine_logs=logs, favorites=favorites)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # check if username or email already exists
        existing_user = Users.query.filter((Users.username==username) | (Users.email==email)).first() 
        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for('register'))
        
        # hash each new password so it is unique and save
        hashed_pw = generate_password_hash(password, method='sha256')
        new_user = Users(username=username, email=email, password=hashed_pw)

        # add and commit to database
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome, {user.username}")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    # clear session data to log the user out
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('accounts'))

@app.route('/password', methods=['GET', 'POST'])
def password():
    if request.method == 'POST':
        user = Users.query.get(session['user_id'])

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # verify if current password is correct
        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for('password'))
        
        # verify if new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for('password'))

        # hash new password so it is unique and update
        hashed_pw = generate_password_hash(new_password, method='sha256')
        user.password = hashed_pw
        db.session.commit()

        flash("Your password has been changed successfully!")
        return redirect(url_for('home'))

    return render_template('password.html')

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to update profile.')
        return redirect(url_for('login'))

    # fetch data if exists
    user_details = User_Details.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        age = request.form['age'].strip()
        gender_input = request.form['gender']
        weight = request.form.get("weight", "").strip()

        weight_digits = weight.lstrip('0')
        if len(weight_digits) > 8:
            flash("Invalid entry: weight cannot exceed 8 digits")
            return redirect(url_for('update_profile'))

        weight = float(weight)

        if user_details:
            user_details.age = age
            user_details.gender = GenderEnum(gender_input).value
            user_details.weight = weight
        else:
            user_details = User_Details(
                user_id=user_id,
                age=age,
                gender=GenderEnum(gender_input).value,
                weight=weight
            )
            db.session.add(user_details)

        db.session.commit()

        flash("Profile Successfully Updated.")
        return redirect(url_for('accounts'))

    return render_template('update_profile.html', user_details=user_details)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5030)
