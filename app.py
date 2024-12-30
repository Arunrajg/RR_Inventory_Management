import logging
from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from flask_mail import Mail, Message
from db_utils import *
from encryption import encrypt_message, decrypt_message, generate_random_password
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "your_secret_key"
encryption_key = b'ES4FoQd6EwUUUY3v-_WwoyYsBEYkWUTOrQD1VEngBkI='

app.logger.setLevel(logging.DEBUG)
# Mail configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'arungraj23@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = 'wbusccstpfgmizcd'  # Replace with your Gmail app password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


# Send email function
def send_email(to_email, new_password):
    try:
        msg = Message(
            'Your New Password',
            sender='arungraj23@gmail.com',
            recipients=[to_email]
        )
        msg.body = f"Your new password is: {new_password}\nPlease log in and change it immediately."
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        existing_user = get_user_by_email(email)
        app.logger.debug(f"existing_user {existing_user}")
        if not existing_user:
            flash("User doesnot exist with this email. Please Sign Up and Create a new account.", "danger")
            return render_template("login.html")
        elif existing_user:
            decrypted_password = decrypt_message(existing_user["password"], encryption_key)
            existing_user.pop("password")
            if decrypted_password == password:
                session['user'] = existing_user
                return redirect("/index")
            else:
                flash("Invalid Email or Password", "danger")
            return render_template("login.html")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        # Check if the email is already registered

        existing_user = get_user_by_email(email)
        app.logger.debug(f"existing_user {existing_user}")

        if existing_user:
            # Email already exists
            flash("User already exists with this email. Please log in or use a different email.", "danger")
        else:
            password = encrypt_message(password, encryption_key)
            # Insert new user details
            insert_query = """
                INSERT INTO users (username, email, password, role)
                VALUES (%s, %s, %s, %s)
            """
            if execute_query(insert_query, (username, email, password, "user")):
                flash("Account created successfully! Click Sign In to login with your account.", "success")
            else:
                flash("Error: Unable to create account. Please try again later.", "danger")

        return redirect("/signup")
    return render_template("signup.html")


@app.route("/index", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html", user=session["user"])


@app.route("/forgotpassword", methods=["GET", "POST"])
def forgot_password():
    app.logger.debug(request.method)
    if request.method == 'POST':

        email = request.form['email']
        user = get_user_by_email(email)

        if user is None:
            flash('User with the entered email not found.', 'error')
            return redirect(url_for('forgot_password'))
        else:
            # Generate a new password
            new_password = generate_random_password()
            app.logger.debug(new_password)
            new_encrypted_password = encrypt_message(new_password, key=encryption_key)
            app.logger.debug(new_encrypted_password)
            # Update the password in the database
            status = update_user_password(new_encrypted_password, email)
            app.logger.debug(f"password update status {status}")
            # Send the email
            try:
                send_email(email, new_password)
                flash('An email has been sent with the new password. Please log in with the new password.', 'success')
            except Exception:
                flash('Failed to send email. Please contact support.', 'error')

            return redirect(url_for('forgot_password'))
    return render_template('forgotpassword.html')


@app.route("/changepassword", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")
    if request.method == 'POST':

        email = session["user"]['email']
        new_password = request.form["newpassword"]
        current_password = request.form["currentpassword"]
        user = get_user_by_email(email)
        if current_password != decrypt_message(user["password"], encryption_key):
            flash("Current password is wrong. kindly provide the correct password")
            return redirect(url_for("change_password"))
        else:
            app.logger.debug(new_password)
            new_encrypted_password = encrypt_message(new_password, key=encryption_key)
            app.logger.debug(new_encrypted_password)
            # Update the password in the database
            status = update_user_password(new_encrypted_password, email)
            app.logger.debug(f"password update status {status}")
            if status:
                flash('Password has been changed successfully.', 'success')
            else:
                flash('Failed to change the password. Please contact support.', 'error')
            return redirect(url_for("change_password"))

    return render_template('changepassword.html', user=session["user"]["user"])


@app.route("/addinventory", methods=["GET", "POST"])
def addinventory():
    if "user" not in session:
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
    return render_template("addinventory.html", user=session["user"])


@app.route("/inventorylist", methods=["GET", "POST"])
def inventorylist():
    if "user" not in session:
        return redirect("/login")
    print("inventorylist")
    inventories = get_all_inventories()
    print(inventories)
    return render_template("inventorylist.html", user=session["user"], inventories=inventories)


@app.route("/addkitchen", methods=["GET", "POST"])
def addkitchen():
    if "user" not in session:
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
    return render_template("addkitchen.html", user=session["user"])


@app.route("/kitchenlist", methods=["GET", "POST"])
def kitchenlist():
    if "user" not in session:
        return redirect("/login")
    print("kitchenlist")
    kitchens = get_all_kitchens()
    print(kitchens)
    return render_template("kitchenlist.html", user=session["user"], kitchens=kitchens)


@app.route("/addrestaurant", methods=["GET", "POST"])
def addrestaurant():
    if "user" not in session:
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
    return render_template("addrestaurant.html", user=session["user"])


@app.route("/restaurantlist", methods=["GET", "POST"])
def restaurantlist():
    if "user" not in session:
        return redirect("/login")
    print("restaurantlist")
    restaurants = get_all_restaurants()
    print(restaurants)
    return render_template("restaurantlist.html", user=session["user"], restaurants=restaurants)


@app.route("/addrawmaterials", methods=["GET", "POST"])
def addrawmaterials():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        raw_material = request.form["rawmaterial_name"].strip().lower()
        metric = request.form["metric"].strip()
        existing_material = get_raw_material_by_name(raw_material)
        if existing_material and existing_material.get("name", "") == raw_material and existing_material.get("metric", "") == metric:
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
    return render_template("addrawmaterials.html", user=session["user"])


@app.route("/rawmaterialslist", methods=["GET", "POST"])
def rawmaterialslist():
    if "user" not in session:
        return redirect("/login")
    print("rawmaterialslist")
    rawmaterials = get_all_rawmaterials()
    print(rawmaterials)
    return render_template("rawmaterialslist.html", user=session["user"], rawmaterials=rawmaterials)


@app.route('/add_dish', methods=['GET', 'POST'])
def add_dish():
    if "user" not in session:
        return redirect("/login")
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        raw_materials = request.form.getlist('raw_materials[]')
        quantities = request.form.getlist('quantities[]')
        metric = request.form.getlist('metric[]')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insert into dishes table
            cursor.execute("INSERT INTO dishes (category, name) VALUES (%s, %s)", (category, name))
            dish_id = cursor.lastrowid

            # Insert into dish_raw_materials table
            for raw_material, quantity, metric in zip(raw_materials, quantities, metric):
                cursor.execute(
                    "INSERT INTO dish_raw_materials (dish_id, raw_material_id, quantity, metric) VALUES (%s, %s, %s, %s)",
                    (dish_id, raw_material, quantity, metric)
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

    return render_template('add_dish.html', user=session["user"], raw_materials=raw_materials)


@app.route('/list_dishes', methods=['GET', 'POST'])
def list_dishes():
    if "user" not in session:
        return redirect("/login")
    # Fetch dishes and their raw materials from the database
    query = """
        SELECT d.id, d.name AS dish_name, d.category,
               rm.name AS raw_material_name, dr.quantity, dr.metric
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
        dish_id, dish_name, category, raw_material_name, quantity, metric = row
        if dish_id not in dishes:
            dishes[dish_id] = {
                "name": dish_name,
                "category": category,
                "raw_materials": []
            }
        dishes[dish_id]["raw_materials"].append({
            "name": raw_material_name,
            "quantity": quantity,
            "metric": metric
        })

    return render_template('list_dishes.html', user=session["user"], dishes=dishes)


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
        metric = request.form.get('metric')
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
                    (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id))
                connection.commit()
                cursor.execute("""
                    INSERT INTO inventory_stock
                    (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    quantity = quantity + VALUES(quantity),
                    metric = VALUES(metric),
                    inventory_name = VALUES(inventory_name),
                    raw_material_name = VALUES(raw_material_name)
                """, (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric))

                connection.commit()
            flash("Purchase added successfully!", "success")

        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            connection.close()
        return redirect('/add_purchase')

    return render_template('add_purchase.html', raw_materials=raw_materials, inventories=inventories, user=session["user"])


@app.route('/purchase_list')
def purchase_list():
    connection = get_db_connection()
    purchases = []

    try:
        with connection.cursor() as cursor:
            # Query the purchase history to retrieve required fields
            cursor.execute("""
                SELECT ph.id, rm.name AS raw_material_name, ph.quantity, ph.metric, ph.total_cost, ph.purchase_date, i.inventoryname AS inventory_name
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

    return render_template('purchase_list.html', purchases=purchases, user=session["user"])


@app.route('/inventory_stock')
def inventory_stock():
    connection = get_db_connection()
    inventory_stock = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT inventory_name, raw_material_name, quantity, metric FROM inventory_stock")
            inventory_stock = cursor.fetchall()

            app.logger.debug(f"inventory_stock {inventory_stock}")
    except Exception as e:
        app.logger.debug(f"inventory_stock {inventory_stock}")
        app.logger.error(f"Error retrieving inventory_stock data: {e}")
        flash(f"Error retrieving inventory_stock data: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('inventory_stock.html', inventory_stock=inventory_stock, user=session["user"])


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

    return render_template('kitchen_stock.html', kitchen_stock=kitchen_stock, user=session["user"])


@app.route('/transfer_raw_material', methods=['GET', 'POST'])
def transfer_raw_material():
    if request.method == 'POST':
        source_inventory_id = request.form['source_inventory_id'].split("_")[0]
        source_inventory_code = request.form['source_inventory_id'].split("_")[1]
        raw_material_id = request.form['raw_material_id']
        quantity = request.form['quantity']
        metric = request.form['metric']
        destination_type = request.form['destination_type']  # restaurant or kitchen
        destination_id, destination_code = request.form['destination_id'].split("_")
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
            flash('Invalid raw material or dish ID.', "danger")
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
                cursor.execute('INSERT INTO restaurant_stock (restaurant_id, raw_material_id, raw_material_name, quantity, metric, dish_id, dish_name) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (destination_id, raw_material_id, raw_material['name'], quantity, metric, dish_id, dish['name']))

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
                cursor.execute('INSERT INTO kitchen_stock (kitchen_id, raw_material_id, raw_material_name, quantity, metric, dish_id, dish_name) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (destination_id, raw_material_id, raw_material['name'], quantity, metric, dish_id, dish['name']))

        # Create a new transfer record in raw_material_transfer
        cursor.execute('INSERT INTO raw_material_transfer (raw_material_id, raw_material_name, quantity, metric, dish_id, dish_name, source_inventory_id, destination_type, destination_id, destination_code, transaction_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (raw_material_id, raw_material['name'], quantity, metric, dish_id, dish['name'], source_inventory_id, destination_type, destination_id, destination_code, datetime.now()))

        # Update the inventory stock by subtracting the transferred quantity
        cursor.execute("""
            UPDATE inventory_stock
            SET quantity = quantity - %s
            WHERE raw_material_id = %s AND inventory_id = %s
        """, (quantity, raw_material_id, source_inventory_id))

        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        flash('Raw material transferred successfully!', "success")
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

    cursor.execute('SELECT * FROM inventory_stock')
    inventory_stock_result = cursor.fetchall()
    inventory_stock = [dict(row) for row in inventory_stock_result]

    cursor.close()
    conn.close()

    return render_template('transfer_raw_material.html', inventory_stock=inventory_stock, inventories=inventories, raw_materials=raw_materials, dishes=dishes, restaurants=restaurants, kitchens=kitchens, user=session["user"])


@app.route('/list_transfers')
def list_transfers():
    connection = get_db_connection()
    transfers = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT raw_material_name, quantity, metric , dish_name, source_inventory_id, destination_type, destination_id, transaction_date FROM raw_material_transfer")
            transfers = cursor.fetchall()

            app.logger.debug(f"transfers {transfers}")
    except Exception as e:
        app.logger.debug(f"transfers {transfers}")
        app.logger.error(f"Error retrieving transfers data: {e}")
        flash(f"Error retrieving transfers data: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('list_transfers.html', transfers=transfers, user=session["user"])


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user" not in session:
        return redirect("/login")
    user = get_user_by_email(session["user"]["email"])
    app.logger.debug(user)
    return render_template('profile.html', user=user)


@app.route('/logout')
def logout():
    if "user" not in session:
        return redirect("/login")
    session.pop("user")
    return redirect("/login")


@app.route('/bulk_add_purchases', methods=['GET', 'POST'])
def bulk_add_purchases():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Fetch inventory
            cursor.execute("SELECT id, inventoryname, inventorycode FROM inventory")
            inventories = cursor.fetchall()

        if request.method == 'POST':
            app.logger.debug(f"Request data: {request.data}")
            app.logger.debug(f"Form keys: {list(request.form.keys())}")

            inventory_id = request.form.get('inventory_id')
            if not inventory_id:
                flash('Inventory selection is required.', 'danger')
                return redirect(url_for('bulk_add_purchases'))

            inventory_name = get_inventory_by_id(inventory_id).get("inventoryname", "Unknown Inventory")
            raw_material_data = []

            for key, value in request.form.items():
                if key.startswith('material_'):
                    raw_material_id = key.split('_')[1]
                    raw_material_name = value
                    try:
                        quantity = float(request.form[f'quantity_{raw_material_id}'])
                        metric = request.form[f'metric_{raw_material_id}']
                        total_cost = float(request.form[f'total_cost_{raw_material_id}'])
                        purchase_date = request.form[f'purchase_date_{raw_material_id}']
                        raw_material_data.append((raw_material_id, raw_material_name,
                                                 quantity, metric, total_cost, purchase_date))
                    except KeyError as e:
                        flash(f'Missing data for raw material {raw_material_name}: {str(e)}', 'danger')
                        return redirect(url_for('bulk_add_purchases'))

            with conn.cursor() as cursor:
                for raw_material in raw_material_data:
                    raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date = raw_material
                    # Insert or update purchase history
                    cursor.execute("""
                        INSERT INTO purchase_history
                        (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id))

                    # Update inventory stock
                    cursor.execute("""
                        INSERT INTO inventory_stock
                        (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        quantity = quantity + VALUES(quantity),
                        metric = VALUES(metric),
                        inventory_name = VALUES(inventory_name),
                        raw_material_name = VALUES(raw_material_name)
                    """, (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric))
                conn.commit()

            flash('Bulk purchase data submitted successfully!', 'success')
            return redirect(url_for('bulk_add_purchases'))

        # Fetch raw materials and last purchase details
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.name, r.metric, 
                       COALESCE(p.quantity, NULL) AS last_quantity,
                       COALESCE(p.metric, NULL) AS last_metric,
                       COALESCE(p.total_cost, NULL) AS last_cost,
                       COALESCE(p.purchase_date, NULL) AS last_date
                FROM raw_materials r
                LEFT JOIN (
                    SELECT raw_material_id, quantity, metric, total_cost, purchase_date
                    FROM purchase_history
                    WHERE purchase_date = (SELECT MAX(purchase_date) 
                                           FROM purchase_history 
                                           WHERE raw_material_id = purchase_history.raw_material_id)
                ) p ON r.id = p.raw_material_id
            """)
            raw_materials = cursor.fetchall()

        # Deduplicate raw materials
        columns = ['id', 'name', 'metric', 'last_quantity', 'last_metric', 'last_cost', 'last_date']
        raw_materials = [dict(zip(columns, row)) for row in raw_materials]
        unique_raw_materials = {material['id']: material for material in raw_materials}
        raw_materials = list(unique_raw_materials.values())

        return render_template('bulk_add_purchases.html', user=session["user"], raw_materials=raw_materials, current_date=date.today(), inventories=inventories)

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        return redirect(url_for('bulk_add_purchases'))


def convert_to_base_unit(quantity, metric):
    """Converts the given quantity to its base unit (grams or ml)."""
    conversions = {
        'kg': 1000,
        'grams': 1,
        'liter': 1000,
        'ml': 1,
        'unit': 1
    }
    return quantity * conversions.get(metric, 1)


def convert_to_original_unit(quantity, metric):
    """Converts the given quantity to its original unit (grams or ml)."""
    conversions = {
        'kg': 1000,
        'grams': 1,
        'liter': 1000,
        'ml': 1,
        'unit': 1
    }
    return quantity // conversions.get(metric, 1)


@app.route('/estimate_dishes', methods=['GET', 'POST'])
def estimate_dishes():
    estimates_data = []
    if request.method == "POST":
        selected_date = request.form.get('date')
        # selected_date = '2024-12-29'

        if not selected_date:
            return jsonify({"error": "Please provide a valid date."}), 400

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Query transferred raw materials on the selected date
                transfer_query = """
                    SELECT raw_material_id, raw_material_name, SUM(quantity) as total_quantity, metric
                    FROM raw_material_transfer
                    WHERE transaction_date = %s
                    GROUP BY raw_material_id, raw_material_name, metric
                """
                cursor.execute(transfer_query, (selected_date,))
                transferred_materials = cursor.fetchall()
                app.logger.debug(f"transferred_materials {transferred_materials}")

                if not transferred_materials:
                    return jsonify({"message": "No data available for the selected date."})

                # Convert transferred materials to a dictionary
                material_map = {}
                for material in transferred_materials:
                    material_map[material[0]] = {
                        'name': material[1],
                        'quantity': convert_to_base_unit(material[2], material[3]),
                        'metric': material[3]
                    }
                app.logger.debug(f"material_map {material_map}")

                # Query all dishes and their required raw materials
                dishes_query = """
                    SELECT d.id AS dish_id, d.name AS dish_name, drm.raw_material_id, drm.quantity, drm.metric
                    FROM dishes d
                    JOIN dish_raw_materials drm ON d.id = drm.dish_id
                """
                cursor.execute(dishes_query)
                dish_data = cursor.fetchall()
                app.logger.debug(f"dish_data {dish_data}")
                # Calculate estimates for each dish
                dish_estimates = {}

                for dish in dish_data:
                    dish_id = dish[0]
                    dish_name = dish[1]
                    raw_material_id = dish[2]

                    # Skip if raw material is not available in the transferred data
                    if raw_material_id not in material_map:
                        continue

                    # Convert required raw material quantity to base unit
                    required_quantity = convert_to_base_unit(dish[3], dish[4])

                    # Calculate max dishes that can be prepared with available material
                    available_quantity = material_map[raw_material_id]['quantity']
                    max_dishes = float(available_quantity) // float(required_quantity)
                    app.logger.debug(f" dish {dish}, max_dishes {max_dishes}")

                    if dish_id not in dish_estimates:
                        dish_estimates[dish_id] = {
                            'name': dish_name,
                            'raw_materials': [],
                            'estimate': max_dishes
                        }
                    else:
                        dish_estimates[dish_id]['estimate'] = min(dish_estimates[dish_id]['estimate'], max_dishes)

                    # Add raw material details
                    dish_estimates[dish_id]['raw_materials'].append({
                        'name': material_map[raw_material_id]['name'],
                        'quantity_used': convert_to_original_unit(available_quantity, material_map[raw_material_id]['metric']),
                        'metric': material_map[raw_material_id]['metric']
                    })

                # Prepare the estimates_data
                estimates_data = []
                for dish_id, details in dish_estimates.items():
                    estimates_data.append({
                        'dish_name': details['name'],
                        'raw_materials': details['raw_materials'],
                        'estimate': details['estimate']
                    })

                return render_template("estimate_dishes.html", user=session["user"], estimates=estimates_data, selected_date=None)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            connection.close()
    return render_template("estimate_dishes.html", user=session["user"], estimates=estimates_data, selected_date=None)


@app.route('/bulk_transfer', methods=['GET', 'POST'])
def bulk_transfer():
    if request.method == 'GET':
        # Query the list of available dishes for selection (if applicable)
        dishes_query = "SELECT id, name FROM dishes"
        dishes = execute_query(dishes_query)

        return render_template('bulk_raw_material_transfer.html', dishes=dishes)

    elif request.method == 'POST':
        try:
            # Get form data
            inventory_id = request.form.get('inventory_id')
            dish_id = request.form.get('dish_id')
            transfer_data = {
                key: value
                for key, value in request.form.items()
                if key.startswith("transfer_quantity_")
            }

            # Process each raw material transfer
            for raw_material_id, transfer_quantity in transfer_data.items():
                raw_material_id = raw_material_id.replace("transfer_quantity_", "")
                transfer_quantity = float(transfer_quantity)

                # Validate available quantity
                query = """
                    SELECT quantity 
                    FROM inventory_stock 
                    WHERE raw_material_id = %s AND inventory_id = %s
                """
                available_quantity = execute_query(query, (raw_material_id, inventory_id))[0][0]

                if transfer_quantity > available_quantity:
                    flash(f"Transfer quantity for raw material {raw_material_id} exceeds available quantity.", "danger")
                    return redirect('/bulk_transfer')

                # Update inventory
                update_query = """
                    UPDATE inventory_stock
                    SET quantity = quantity - %s
                    WHERE raw_material_id = %s AND inventory_id = %s
                """
                execute_query(update_query, (transfer_quantity, raw_material_id, inventory_id))

            flash("Bulk transfer completed successfully.", "success")
            return redirect('/bulk_transfer')

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect('/bulk_transfer')


@app.route('/transfer_dish', methods=['GET', 'POST'])
def transfer_dish():
    pass


@app.route('/add_prepared_dishes', methods=['GET', 'POST'])
def add_prepared_dishes():
    # Fetch raw materials, dishes, and restaurant/kitchen data to populate in the form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # cursor.execute('SELECT * FROM raw_materials')
    # raw_materials = cursor.fetchall()

    cursor.execute('SELECT * FROM dishes')
    dishes = cursor.fetchall()

    cursor.execute('SELECT * FROM restaurant')
    restaurants = cursor.fetchall()

    cursor.execute('SELECT * FROM kitchen')
    kitchens = cursor.fetchall()

    # cursor.execute('SELECT * FROM inventory')
    # inventories = cursor.fetchall()

    # cursor.execute('SELECT * FROM inventory_stock')
    # inventory_stock_result = cursor.fetchall()
    # inventory_stock = [dict(row) for row in inventory_stock_result]

    cursor.close()
    conn.close()
    current_date = datetime.now().strftime("%Y-%m-%d")
    if request.method == "POST":
        try:
            # Parse form data
            location_type = request.form.get('location_type')
            location_code = request.form.get('location_code')

            # Multiple entries for dishes
            dish_categories = request.form.getlist('dish_category[]')
            dish_names = request.form.getlist('dish_name[]')
            quantities = request.form.getlist('quantity[]')
            prepared_on_dates = request.form.getlist('prepared_on[]')

            # Get location details (name and ID)
            if location_type == 'kitchen':
                location = next((k for k in kitchens if k['kitchencode'] == location_code), None)
            elif location_type == 'restaurant':
                location = next((r for r in restaurants if r['restaurantcode'] == location_code), None)
            else:
                flash("Invalid location type", "error")
                return redirect('/add_prepared_dishes')

            if not location:
                flash("Invalid location selected", "error")
                return redirect('/add_prepared_dishes')

            location_id = location['id']
            location_name = location['kitchenname'] if location_type == 'kitchen' else location['restaurantname']

            # Insert data into database
            conn = get_db_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO dishes_prepared_details 
                (location_type, location_id, location_name, location_code, dish_category, dish_id, dish_name, quantity, prepared_on) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for category, name, quantity, date in zip(dish_categories, dish_names, quantities, prepared_on_dates):
                dish_id = name.split("_")[0]
                dish_name = name.split("_")[1]
                app.logger.debug(dish_name)
                app.logger.debug(dish_id)
                cursor.execute(insert_query, (location_type, location_id, location_name,
                               location_code, category, dish_id, dish_name, quantity, date))

            conn.commit()
            cursor.close()
            conn.close()

            flash("Dish preparation details added successfully", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
        return redirect('/add_prepared_dishes')

    return render_template('add_prepared_dishes.html', current_date=current_date, dishes=dishes, restaurants=restaurants, kitchens=kitchens, user=session["user"])


@app.route('/list_prepared_dishes', methods=['GET', 'POST'])
def list_prepared_dishes():
    if "user" not in session:
        return redirect("/login")
    # Fetch dishes and their raw materials from the database
    query = """
        SELECT * from dishes_prepared_details ORDER BY prepared_on DESC
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    app.logger.debug(f"data {data}")

    return render_template('list_prepared_dishes.html', user=session["user"], data=data)


@app.route('/transfer_prepared_dishes', methods=['GET', 'POST'])
def transfer_prepared_dishes():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch dishes, restaurants, and kitchens to populate in the form
    cursor.execute('SELECT * FROM dishes')
    dishes = cursor.fetchall()

    cursor.execute('SELECT * FROM restaurant')
    restaurants = cursor.fetchall()

    cursor.execute('SELECT * FROM kitchen')
    kitchens = cursor.fetchall()

    cursor.close()
    conn.close()

    current_date = datetime.now().strftime("%Y-%m-%d")
    app.logger.debug(f"dishes {dishes}")
    app.logger.debug(f"restaurants {restaurants}")
    app.logger.debug(f"kitchens {kitchens}")

    # Handle form submission for dish transfer
    if request.method == 'POST':
        source_kitchen_id = request.form['source_kitchen_id']
        destination_restaurant_id = request.form['destination_restaurant_id']
        dish_id = request.form['dish_id']
        quantity = request.form['quantity']
        transferred_date = request.form['transferred_date']

        # Insert the transfer details into the database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO prepared_dish_transfer (
                    source_kitchen_id,
                    destination_restaurant_id,
                    dish_id,
                    quantity,
                    transferred_date
                ) VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (source_kitchen_id.split("_")[0], destination_restaurant_id.split("_")[0],
                           dish_id, quantity, transferred_date))
            conn.commit()

            flash("Dish transfer successful!", "success")

        except Exception as e:
            conn.rollback()  # Rollback in case of any error
            app.logger.error(f"Error during dish transfer: {e}")
            flash("Error occurred while transferring the dish.", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('transfer_prepared_dishes'))

    return render_template('transfer_prepared_dishes.html', current_date=current_date, dishes=dishes, restaurants=restaurants, kitchens=kitchens, user=session["user"])


@app.route('/check_dish_availability', methods=['GET', 'POST'])
def check_dish_availability():
    if request.method == 'POST':
        selected_date = request.form['selected_date']
        restaurant_id = request.form['restaurant_id']

        # Establish DB connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to get dish details for the selected restaurant and date
        query = """
        SELECT d.name, d.category, SUM(pdt.quantity) AS quantity_available
        FROM prepared_dish_transfer pdt
        JOIN dishes d ON pdt.dish_id = d.id
        WHERE pdt.destination_restaurant_id = %s
        AND pdt.transferred_date = %s
        GROUP BY pdt.dish_id
        """
        cursor.execute(query, (restaurant_id, selected_date))
        dishes = cursor.fetchall()

        cursor.close()
        conn.close()

        # Render the page with the fetched data
        return render_template('check_dish_availability.html', dishes=dishes, restaurants=get_restaurants(), user=session["user"])

    # Fetch restaurants to show in the dropdown
    return render_template('check_dish_availability.html', restaurants=get_restaurants(), user=session["user"])

# Function to fetch restaurant data for the dropdown


def get_restaurants():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, restaurantname, restaurantcode FROM restaurant")
    restaurants = cursor.fetchall()
    cursor.close()
    conn.close()
    return restaurants


if __name__ == "__main__":
    app.run(debug=True)
