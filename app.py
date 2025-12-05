from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func
from models import Drinks, Users, User_Details, app, db

@app.route("/")
def home():
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

@app.route('/view_profile')
def view_profile():
    return render_template('view_profile.html')

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to update profile.')
        return redirect(url_for('accounts'))

    if request.method == 'POST':
        user = Users.query.get(user_id)
        age = request.form['age']
        gender = request.form['gender']
        weight = request.form['weight']
        
        update_user = User_Details(user_id=user.id, age=age, gender=gender, weight=weight)

        # add and commit to database
        db.session.add(update_user)
        db.session.commit()

        flash("Profile Successfully Updated.")
        return redirect(url_for('accounts'))

    return render_template('update_profile.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5030)
