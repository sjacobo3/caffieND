from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home_page.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5028)