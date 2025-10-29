from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sjacobo3:newpassword@localhost/sjacobo3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/")
def home():
    return render_template('home_page.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5028)
