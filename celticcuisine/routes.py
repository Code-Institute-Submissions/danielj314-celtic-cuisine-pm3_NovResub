from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from celticcuisine import app, db, mongo
from celticcuisine.models import Nations, Users


@app.route("/")
@app.route("/home")
def home():
    """
    Finds all categories in the Nations collection
    in Postgres Database.
    """
    categories = list(Nations.query.order_by(Nations.category_name).all())
    return render_template("home.html", categories=categories)


@app.route("/my_recipes/<username>", methods=["GET", "POST"])
def my_recipes(username):
    """
    Finds all recipes in MongoDB recipes collection
    that were created by the user currently logged in to the site.
    """
    if "user" not in session:
        flash("You need to be logged in to view your recipes")
        return redirect("home")

    recipes = list(mongo.db.recipes.find({"created_by": str(username)}))
    return render_template(
        "my_recipes.html", username=session["user"], recipes=recipes)


@app.route("/recipes/<int:category_id>", methods=["GET"])
def recipes(category_id):
    """
    Finds all recipes in the MongoDB recipes collection
    with the category id that correlates with the selected
    Nations category in the Postgres database.
    """
    category = Nations.query.get_or_404(category_id)
    recipes = list(mongo.db.recipes.find({"category_id": str(category_id)}))
    return render_template("recipes.html", category=category, recipes=recipes)


@app.route("/full_recipe/<recipe_id>")
def full_recipe(recipe_id):
    """
    View full recipe by searching for the relevant recipe._id in MongoDB.
    """
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return render_template("full_recipe.html", recipe=recipe)


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    """
    Adds recipe to MongoDB recipes collection. Only logged in
    user may access this page.
    """
    if "user" not in session:
        flash("You need to be logged in to add a recipe")
        return redirect(url_for("home"))

    if request.method == "POST":
        recipe = {
            "category_id": request.form.get("category_id"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_image": request.form.get("recipe_image"),
            "recipe_description": request.form.get("recipe_description"),
            "ingredients": request.form.get("ingredients"),
            "method": request.form.get("method"),
            "prep_time": request.form.get("prep_time"),
            "servings": request.form.get("servings"),
            "created_by": session["user"]
        }

        mongo.db.recipes.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("home"))

    categories = list(Nations.query.order_by(Nations.category_name).all())
    return render_template("add_recipe.html", categories=categories)


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    """ 
    Only the user who created the recipe may edit a recipe.
    Finds selected recipe based on current recipe_id in url
    for editing in MongoDB recipes collection.
    """
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    if "user" not in session or session["user"] != recipe["created_by"]:
        flash("You can only edit your own recipes!")
        return redirect(url_for("home"))

    if request.method == "POST":
        submit = {
            "category_id": request.form.get("category_id"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_image": request.form.get("recipe_image"),
            "recipe_description": request.form.get("recipe_description"),
            "ingredients": request.form.get("ingredients"),
            "method": request.form.get("method"),
            "prep_time": request.form.get("prep_time"),
            "servings": request.form.get("servings"),
            "created_by": session["user"]
        }
        mongo.db.recipes.update_one(
            {"_id": ObjectId(recipe_id)}, {"$set": submit})
        flash("Recipe Successfully Updated")
        return redirect(url_for("my_recipes", username=session["user"]))

    categories = list(Nations.query.order_by(Nations.category_name).all())
    return render_template("edit_recipe.html", recipe=recipe,
                           categories=categories)


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    """
    Allows the user who created the recipe or admin to delete a recipe
    Finds recipe in recipes collection in MongoDB via current
    recipe_id in url
    """
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    if "user" not in session or session["user"] != recipe["created_by"]:
        if session["user"] != "admin":
            flash("You can only delete your own recipes!")
            return redirect(url_for("home"))

    mongo.db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("my_recipes", username=session["user"]))


@app.route("/add_nation", methods=["GET", "POST"])
def add_nation():
    """
    Only Admin may add a nation category.
    Creates new nation category in Postgres db.
    """
    if session["user"] != "admin":
        flash("Only Admin can add a nation category")
        return redirect(url_for("home"))

    if request.method == "POST":
        category = Nations(category_name=request.form.get("category_name"))
        db.session.add(category)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_nation.html")


@app.route("/edit_nation/<int:category_id>", methods=["GET", "POST"])
def edit_nation(category_id):
    """
    Only Admin may edit a nation category.
    Finds Nation using category_id in url.
    Change the name of nation category in Postgres db.
    """

    if session["user"] != "admin":
        flash("Only Admin can edit a nation category")
        return redirect(url_for("home"))

    category = Nations.query.get_or_404(category_id)
    if request.method == "POST":
        category.category_name = request.form.get("category_name")
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit_nation.html", category=category)


@app.route("/delete_nation/<int:category_id>")
def delete_nation(category_id):
    """
    Only Admin may delete a nation category.
    Deletes a nation category from Postgres db using category_id........................
    """
    if session["user"] != "admin":
        flash("Only Admin can delete a nation category")
        return redirect(url_for("home"))

    category = Nations.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    mongo.db.tasks.delete_many({"category_id": str(category_id)})
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Adds a user to Users table in Postgres afte checking to confirm
    user does not already exist and that password and confirm-password
    fields match. Adds this user to a session cookie.
    """
    if request.method == "POST":
        # checks if username already exists in Postgres - Users table
        existing_user = Users.query.filter(
            Users.user_name == request.form.get("username").lower()).all()

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        # check password field against confirm password field:
        if request.form.get("password") != request.form.get(
                "cpassword"):
            flash("Passwords do not match. Please try again.")
            return redirect(url_for("register"))

        user = Users(
            user_name=request.form.get("username").lower(),
            password=generate_password_hash(request.form.get("password"))
        )

        db.session.add(user)
        db.session.commit()

        # insert new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("my_recipes", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Searches Users db table for user, checks that hashed password is correct
    Adds user to session.
    """
    if request.method == "POST":
        # check if username exists in db
        existing_user = Users.query.filter(
            Users.user_name == request.form.get("username").lower()).all()

        if existing_user:
            print(request.form.get("username"))
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user[0].password, request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "my_recipes", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# Error handling
@app.errorhandler(400)
def bad_request(error):
    """
    Returns 400.html error page if this error is found
    """
    return render_template('400.html'), 400


@app.errorhandler(401)
def unauthorized(error):
    """
    Returns 401.html error page if this error is found
    """
    return render_template('401.html'), 401


@app.errorhandler(404)
def page_not_found(error):
    """
    Returns 404.html error page if this error is found
    """
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """
    Returns 405.html error page if this error is found
    """
    return render_template('405.html'), 405


@app.errorhandler(500)
def internal_server_error(error):
    """
    Returns 500.html error page if this error is found
    """
    return render_template('500.html'), 500