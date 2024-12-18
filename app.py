from flask import Flask, render_template, request, redirect, flash, session
from db_utils import execute_query, get_user_by_email, get_inventory_by_code, get_all_inventories
from encryption import encrypt_message, decrypt_message

app = Flask(__name__)
app.secret_key = "your_secret_key"
encryption_key = b'ES4FoQd6EwUUUY3v-_WwoyYsBEYkWUTOrQD1VEngBkI='


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        existing_user = get_user_by_email(email)
        if not existing_user:
            flash("User doesnot exist with this email. Please Sign Up and Create a new account.", "danger")
            return render_template("login.html")
        elif existing_user:
            decrypted_password = decrypt_message(existing_user["password"], encryption_key)
            if decrypted_password == password:
                session['username'] = existing_user["username"]
                session['email'] = email
                return redirect("/index")
            else:
                flash("Invalid Email or Password", "danger")
            return render_template("login.html")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    print(request.method)
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        # superuser = request.form.get("superuser", "no").lower()

        # Check if the email is already registered

        existing_user = get_user_by_email(email)
        print(f"existing_user {existing_user}")

        if existing_user:
            # Email already exists
            flash("User already exists with this email. Please log in or use a different email.", "danger")
        else:
            password = encrypt_message(password, encryption_key)
            # Insert new user details
            insert_query = """
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            """
            if execute_query(insert_query, (username, email, password)):
                flash("Account created successfully! Click Sign In to login with your account.", "success")
            else:
                flash("Error: Unable to create account. Please try again later.", "danger")

        return redirect("/signup")
    return render_template("signup.html")


@app.route("/index", methods=["GET", "POST"])
def index():
    if not session["email"]:
        return redirect("/login")
    return render_template("index.html", user=session)


@app.route("/addinventory", methods=["GET", "POST"])
def addinventory():
    if not session["email"]:
        return redirect("/login")
    if request.method == "POST":
        inventory_name = request.form["inventory_name"].strip()
        inventory_code = request.form["inventory_code"].strip()
        address = request.form["address"].strip()
        existing_inventory = get_inventory_by_code(inventory_code)
        if existing_inventory:
            flash("Inventory with same code already exists. Please use a different Inventory Code.", "danger")
        else:
            insert_query = """
                INSERT INTO inventory (inventoryname, inventorycode, address)
                VALUES (%s, %s, %s)
            """
            if execute_query(insert_query, (inventory_name, inventory_code, address)):
                flash("Inventory created successfully!", "success")
            else:
                flash("Error: Unable to create a new Inventory. Please try again later.", "danger")
        return redirect("/addinventory")
    return render_template("addinventory.html", user=session)


@app.route("/inventorylist", methods=["GET", "POST"])
def inventorylist():
    if not session["email"]:
        return redirect("/login")
    print("inventorylist")
    inventories = get_all_inventories()
    print(inventories)
    return render_template("inventorylist.html", user=session, inventories=inventories)


if __name__ == "__main__":
    app.run(debug=True)
