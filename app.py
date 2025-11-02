from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)


# DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sjacobo3:newpassword@localhost/sjacobo3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize SQLAlechemy
db = SQLAlchemy(app)

# MODELS
class Drink(db.Model):
    __tablename__ = 'drink'
    name = db.Column(db.String(50), primary_key=True)
    volume = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    caffeine_amt = db.Column(db.Integer)
    caffeine_type = db.Column(db.String(15))

    def __repr__(self):
        return f"<Drink {self.name}>"


@app.route("/")
def home():
    # pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = Drink.query.paginate(page=page, per_page=per_page, error_out=False)

    items = pagination.items

    return render_template('home_page.html', drinks=items, active_tab='home', pagination=pagination)

@app.route("/leaderboard")
def leaderboard():
    return render_template('leaderboard.html', active_tab='leaderboard')

@app.route("/recommendation")
def recommendation():
    return render_template('recommend.html', active_tab='recommendation')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5029)
