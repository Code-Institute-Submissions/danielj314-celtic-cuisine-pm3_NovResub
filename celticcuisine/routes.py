from flask import render_template
from celticcuisine import app, db
from celticcuisine.models import Nations, Users


@app.route("/")
def home():
    return render_template("base.html")
