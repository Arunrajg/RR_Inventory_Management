from flask import Flask, render_template, request, redirect, flash, session
from db_utils import *
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


@app.route("/addkitchen", methods=["GET", "POST"])
def addkitchen():
    if not session["email"]:
        return redirect("/login")
    if request.method == "POST":
        kitchen_name = request.form["kitchen_name"].strip()
        kitchen_code = request.form["kitchen_code"].strip()
        address = request.form["address"].strip()
        existing_kitchen = get_kitchen_by_code(kitchen_code)
        if existing_kitchen:
            flash("Kitchen with same code already exists. Please use a different Kitchen Code.", "danger")
        else:
            insert_query = """
                INSERT INTO kitchen (kitchenname, kitchencode, address)
                VALUES (%s, %s, %s)
            """
            if execute_query(insert_query, (kitchen_name, kitchen_code, address)):
                flash("Kitchen created successfully!", "success")
            else:
                flash("Error: Unable to create a new Kitchen. Please try again later.", "danger")
        return redirect("/addkitchen")
    return render_template("addkitchen.html", user=session)


@app.route("/kitchenlist", methods=["GET", "POST"])
def kitchenlist():
    if not session["email"]:
        return redirect("/login")
    print("kitchenlist")
    kitchens = get_all_kitchens()
    print(kitchens)
    return render_template("kitchenlist.html", user=session, kitchens=kitchens)


@app.route("/addrestaurant", methods=["GET", "POST"])
def addrestaurant():
    if not session["email"]:
        return redirect("/login")
    if request.method == "POST":
        restaurant_name = request.form["restaurant_name"].strip()
        restaurant_code = request.form["restaurant_code"].strip()
        address = request.form["address"].strip()
        existing_restaurant = get_restaurant_by_code(restaurant_code)
        if existing_restaurant:
            flash("Restaurant with same code already exists. Please use a different Restaurant Code.", "danger")
        else:
            insert_query = """
                INSERT INTO restaurant (restaurantname, restaurantcode, address)
                VALUES (%s, %s, %s)
            """
            if execute_query(insert_query, (restaurant_name, restaurant_code, address)):
                flash("Restaurant created successfully!", "success")
            else:
                flash("Error: Unable to create a new Restaurant. Please try again later.", "danger")
        return redirect("/addrestaurant")
    return render_template("addrestaurant.html", user=session)


@app.route("/restaurantlist", methods=["GET", "POST"])
def restaurantlist():
    if not session["email"]:
        return redirect("/login")
    print("restaurantlist")
    restaurants = get_all_restaurants()
    print(restaurants)
    return render_template("restaurantlist.html", user=session, restaurants=restaurants)


@app.route("/addrawmaterials", methods=["GET", "POST"])
def addrawmaterials():
    if not session["email"]:
        return redirect("/login")
    if request.method == "POST":
        raw_material = request.form["rawmaterial_name"].strip().lower()
        metric = request.form["metric"].strip()
        existing_material = get_raw_material_by_name(raw_material)
        if existing_material:
            flash("Raw material already exists.", "danger")
        else:
            insert_query = """
                INSERT INTO raw_materials (name, metric)
                VALUES (%s, %s)
            """
            if execute_query(insert_query, (raw_material, metric)):
                flash("Raw material added successfully!", "success")
            else:
                flash("Error: Unable to add the raw material. Please try again later.", "danger")
        return redirect("/addrawmaterials")
    return render_template("addrawmaterials.html", user=session)


@app.route("/rawmaterialslist", methods=["GET", "POST"])
def rawmaterialslist():
    if not session["email"]:
        return redirect("/login")
    print("rawmaterialslist")
    rawmaterials = get_all_rawmaterials()
    print(rawmaterials)
    return render_template("rawmaterialslist.html", user=session, rawmaterials=rawmaterials)


@app.route('/add_dish', methods=['GET', 'POST'])
def add_dish():
    if not session["email"]:
        return redirect("/login")
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        raw_materials = request.form.getlist('raw_materials[]')
        quantities = request.form.getlist('quantities[]')
        units = request.form.getlist('units[]')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insert into dishes table
            cursor.execute("INSERT INTO dishes (category, name) VALUES (%s, %s)", (category, name))
            dish_id = cursor.lastrowid

            # Insert into dish_raw_materials table
            for raw_material, quantity, unit in zip(raw_materials, quantities, units):
                cursor.execute(
                    "INSERT INTO dish_raw_materials (dish_id, raw_material_id, quantity, unit) VALUES (%s, %s, %s, %s)",
                    (dish_id, raw_material, quantity, unit)
                )

            conn.commit()
            flash('Dish added successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect('/add_dish')

    # Fetch raw materials from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM raw_materials")
    raw_materials = cursor.fetchall()  # Fetch all raw materials
    cursor.close()
    conn.close()
    print(raw_materials)

    return render_template('add_dish.html', user=session, raw_materials=raw_materials)


@app.route('/list_dishes')
def list_dishes():
    if not session["email"]:
        return redirect("/login")
    # Fetch dishes and their raw materials from the database
    query = """
        SELECT d.id, d.name AS dish_name, d.category, 
               rm.name AS raw_material_name, dr.quantity, dr.unit 
        FROM dishes d
        JOIN dish_raw_materials dr ON d.id = dr.dish_id
        JOIN raw_materials rm ON dr.raw_material_id = rm.id
        ORDER BY d.id, rm.name
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()

    # Organize data into a dictionary grouped by dishes
    dishes = {}
    for row in data:
        dish_id, dish_name, category, raw_material_name, quantity, unit = row
        if dish_id not in dishes:
            dishes[dish_id] = {
                "name": dish_name,
                "category": category,
                "raw_materials": []
            }
        dishes[dish_id]["raw_materials"].append({
            "name": raw_material_name,
            "quantity": quantity,
            "unit": unit
        })

    return render_template('list_dishes.html', user=session, dishes=dishes)


if __name__ == "__main__":
    app.run(debug=True)
