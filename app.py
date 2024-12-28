import logging
from flask import Flask, render_template, request, redirect, flash, session
from db_utils import *
from encryption import encrypt_message, decrypt_message
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
encryption_key = b'ES4FoQd6EwUUUY3v-_WwoyYsBEYkWUTOrQD1VEngBkI='

app.logger.setLevel(logging.DEBUG)


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


@app.route('/list_dishes', methods=['GET', 'POST'])
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


@app.route('/add_purchase', methods=['GET', 'POST'])
def add_purchase():
    connection = get_db_connection()
    raw_materials = []
    inventories = []

    try:
        with connection.cursor() as cursor:
            # Fetch raw materials
            cursor.execute("SELECT id, name FROM raw_materials")
            raw_materials = cursor.fetchall()

            # Fetch inventory
            cursor.execute("SELECT id, inventoryname, inventorycode FROM inventory")
            inventories = cursor.fetchall()
    finally:
        connection.close()
    app.logger.debug(f"raw_materialsraw_materials {raw_materials}")
    app.logger.debug(inventories)

    if request.method == 'POST':
        # Handle form submission
        raw_material_id = request.form.get('raw_material_id')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        total_cost = request.form.get('total_cost')
        purchase_date = request.form.get('purchase_date')
        inventory_id = request.form.get('inventory_id')
        inventory_name = get_inventory_by_id(inventory_id)["inventoryname"]
        app.logger.debug(raw_materials)
        app.logger.debug(raw_material_id)
        app.logger.debug(f"inventory_name {inventory_name}")

        connection = get_db_connection()
        try:
            raw_material_name = [m[1] for m in raw_materials if m[0] == int(raw_material_id)][0]
            app.logger.debug(raw_material_name)
            with connection.cursor() as cursor:
                # Insert into purchase_history
                cursor.execute("""
                    INSERT INTO purchase_history
                    (raw_material_id, raw_material_name, quantity, unit, total_cost, purchase_date, inventory_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (raw_material_id, raw_material_name, quantity, unit, total_cost, purchase_date, inventory_id))
                connection.commit()
                cursor.execute("""
                    INSERT INTO inventory_stock
                    (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, unit)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, unit))
                connection.commit()
            flash("Purchase added successfully!", "success")

        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            connection.close()
        return redirect('/add_purchase')

    return render_template('add_purchase.html', raw_materials=raw_materials, inventories=inventories, user=session)


@app.route('/purchase_list')
def purchase_list():
    connection = get_db_connection()
    purchases = []

    try:
        with connection.cursor() as cursor:
            # Query the purchase history to retrieve required fields
            cursor.execute("""
                SELECT ph.id, rm.name AS raw_material_name, ph.quantity, ph.unit, ph.total_cost, ph.purchase_date, i.inventoryname AS inventory_name
                FROM purchase_history ph
                JOIN raw_materials rm ON ph.raw_material_id = rm.id
                JOIN inventory i ON ph.inventory_id = i.id
            """)
            purchases = cursor.fetchall()

            app.logger.debug(f"purchases {purchases}")
    except Exception as e:
        app.logger.debug(f"purchases {purchases}")
        app.logger.error(f"Error retrieving purchase data: {e}")
        flash(f"Error retrieving purchase data: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('purchase_list.html', purchases=purchases, user=session)


@app.route('/inventory_stock')
def inventory_stock():
    connection = get_db_connection()
    purchases = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT inventory_name, raw_material_name, quantity, unit FROM inventory_stock")
            inventory_stock = cursor.fetchall()
            purchases = cursor.fetchall()

            app.logger.debug(f"inventory_stock {inventory_stock}")
    except Exception as e:
        app.logger.debug(f"inventory_stock {inventory_stock}")
        app.logger.error(f"Error retrieving inventory_stock data: {e}")
        flash(f"Error retrieving inventory_stock data: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('inventory_stock.html', inventory_stock=inventory_stock, user=session)


@app.route('/kitchen_stock')
def kitchen_stock():
    connection = get_db_connection()
    purchases = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT kitchen_id, raw_material_name, quantity, unit FROM kitchen_stock")
            kitchen_stock = cursor.fetchall()
            purchases = cursor.fetchall()

            app.logger.debug(f"kitchen_stock {kitchen_stock}")
    except Exception as e:
        app.logger.debug(f"kitchen_stock {kitchen_stock}")
        app.logger.error(f"Error retrieving kitchen_stock data: {e}")
        flash(f"Error retrieving kitchen_stock data: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('kitchen_stock.html', kitchen_stock=kitchen_stock, user=session)


@app.route('/transfer_raw_material', methods=['GET', 'POST'])
def transfer_raw_material():
    if request.method == 'POST':
        raw_material_id = request.form['raw_material_id']
        quantity = request.form['quantity']
        destination_type = request.form['destination_type']  # restaurant or kitchen
        destination_id = request.form['destination_id']
        dish_id = request.form['dish_id']

        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get raw material and dish names
        cursor.execute('SELECT name, metric FROM raw_materials WHERE id = %s', (raw_material_id,))
        raw_material = cursor.fetchone()

        cursor.execute('SELECT name FROM dishes WHERE id = %s', (dish_id,))
        dish = cursor.fetchone()

        if not raw_material or not dish:
            flash('Invalid raw material or dish ID.')
            return redirect('/transfer_raw_material')

        # Calculate the new stock after transfer
        if destination_type == 'restaurant':
            cursor.execute('SELECT * FROM restaurant_stock WHERE restaurant_id = %s AND raw_material_id = %s',
                           (destination_id, raw_material_id))
            stock = cursor.fetchone()

            if stock:
                # Update the existing stock record
                new_quantity = float(stock['quantity']) + float(quantity)
                cursor.execute('UPDATE restaurant_stock SET quantity = %s WHERE id = %s', (new_quantity, stock['id']))
            else:
                # Insert new record into restaurant_stock
                cursor.execute('INSERT INTO restaurant_stock (restaurant_id, raw_material_id, raw_material_name, quantity, unit, dish_id, dish_name) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (destination_id, raw_material_id, raw_material['name'], quantity, raw_material['metric'], dish_id, dish['name']))

        elif destination_type == 'kitchen':
            cursor.execute('SELECT * FROM kitchen_stock WHERE kitchen_id = %s AND raw_material_id = %s',
                           (destination_id, raw_material_id))
            stock = cursor.fetchone()

            if stock:
                # Update the existing stock record
                new_quantity = float(stock['quantity']) + float(quantity)
                cursor.execute('UPDATE kitchen_stock SET quantity = %s WHERE id = %s', (new_quantity, stock['id']))
            else:
                # Insert new record into kitchen_stock
                cursor.execute('INSERT INTO kitchen_stock (kitchen_id, raw_material_id, raw_material_name, quantity, unit, dish_id, dish_name) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (destination_id, raw_material_id, raw_material['name'], quantity, raw_material['metric'], dish_id, dish['name']))

        # Create a new transfer record in raw_material_transfer
        cursor.execute('INSERT INTO raw_material_transfer (raw_material_id, raw_material_name, quantity, unit, dish_id, dish_name, destination_type, destination_id, transaction_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (raw_material_id, raw_material['name'], quantity, raw_material['metric'], dish_id, dish['name'], destination_type, destination_id, datetime.now()))

        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        flash('Raw material transferred successfully!')
        return redirect('/transfer_raw_material')

    # Fetch raw materials, dishes, and restaurant/kitchen data to populate in the form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM raw_materials')
    raw_materials = cursor.fetchall()

    cursor.execute('SELECT * FROM dishes')
    dishes = cursor.fetchall()

    cursor.execute('SELECT * FROM restaurant')
    restaurants = cursor.fetchall()

    cursor.execute('SELECT * FROM kitchen')
    kitchens = cursor.fetchall()

    cursor.execute('SELECT * FROM inventory')
    inventories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('transfer_raw_material.html', inventories=inventories, raw_materials=raw_materials, dishes=dishes, restaurants=restaurants, kitchens=kitchens, user=session)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session["email"]:
        return redirect("/login")
    user = get_user_by_email(session["email"])
    return render_template('profile.html', user=user)


if __name__ == "__main__":
    app.run(debug=True)
