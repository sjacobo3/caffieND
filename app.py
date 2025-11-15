from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func
from models import Drink, Users, app, db

@app.route("/")
def home():
    #get user inputs for search 
    userinput_query = request.args.get('name', None)
    userinput_category = request.args.get('category', 'name')

    #get all drink data 
    drinks = Drink.query

    if userinput_query: 
        if userinput_category == 'name':
            drinks = drinks.filter(func.lower(Drink.name).contains(userinput_query.lower()))
        elif userinput_category == 'calories': 
            if userinput_query.isdigit():
                drinks = drinks.filter(Drink.calories == int(userinput_query))
            else: 
                drinks = drinks.filter(False)
        elif userinput_category == 'caffeine_amt': 
            if userinput_query.isdigit(): 
                drinks = drinks.filter(Drink.caffeine_amt == int(userinput_query))
            else: 
                drinks = drinks.filter(False)
        else:
            drinks = drinks.filter(False)

    # pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = drinks.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    return render_template('home_page.html', drinks=items, active_tab='home', pagination=pagination, query=userinput_query, category=userinput_category)

@app.route("/leaderboard")
def leaderboard():
    return render_template('leaderboard.html', active_tab='leaderboard')

@app.route("/recommendation")
def recommendation():
    return render_template('recommend.html', active_tab='recommendation')

@app.route("/accounts")
def accounts():
    return render_template('accounts.html', active_tab='accounts')

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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5031)
