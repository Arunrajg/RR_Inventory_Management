import pandas as pd
from decimal import Decimal
import logging
from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from markupsafe import Markup
from flask_mail import Mail, Message
from db_utils import *
from encryption import encrypt_message, decrypt_message, generate_random_password
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os
import pytz
from dotenv import load_dotenv
load_dotenv()
# Get the current working directory
current_workspace = os.getcwd()

# Define the path for the uploads folder
UPLOAD_FOLDER = os.path.join(current_workspace, 'uploads')

# Create the uploads folder if it doesn't already exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx'}

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
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

mail = Mail(app)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
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


def get_current_date():

    # Get the IST timezone
    ist_timezone = pytz.timezone('Asia/Kolkata')

    # Get current time in IST
    current_time_ist = datetime.now(ist_timezone)

    # Format the date as "YYYY-MM-DD"
    formatted_date_ist = current_time_ist.strftime("%Y-%m-%d")
    return formatted_date_ist


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
            if existing_user["status"] == "inactive":
                flash("User Account has been made Inactive. Kindy contact the Admin to activate the account.", "danger")
            else:
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
    cost_details = get_total_cost_stats()[0]
    return render_template("index.html", user=session["user"], cost_details=cost_details)


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

    return render_template('changepassword.html', user=session["user"])


@app.route("/addstorageroom", methods=["GET", "POST"])
def addstorageroom():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        storageroom_name = request.form["storageroom_name"].strip()
        address = request.form["address"].strip()
        existing_storageroom = get_storageroom_by_name(storageroom_name)
        if existing_storageroom:
            flash("Storage Room with same name already exists. Please use a different Storage Room Name.", "danger")
        else:
            insert_query = """
                INSERT INTO storagerooms (storageroomname, address)
                VALUES (%s, %s)
            """
            if execute_query(insert_query, (storageroom_name, address)):
                flash("Storage Room added successfully!", "success")
            else:
                flash("Error: Unable to add a new Storage Room. Please try again later.", "danger")
        return redirect("/addstorageroom")
    return render_template("addstorageroom.html", user=session["user"])


@app.route("/storageroomlist", methods=["GET", "POST"])
def storageroomlist():
    if "user" not in session:
        return redirect("/login")
    storagerooms = get_all_storagerooms()
    print(storagerooms)
    return render_template("storageroomlist.html", user=session["user"], storagerooms=storagerooms)


@app.route('/editstorageroom', methods=['POST'])
def edit_storage_room():
    # Get data from the form
    room_id = request.form.get('id')
    room_status = request.form.get('status')
    room_address = request.form.get('address')

    # Validate inputs
    if not room_id or not room_address:
        flash("All fields are required.", "error")
        return redirect(url_for('storage_rooms_list'))

    # SQL query to update the storage room
    query = """
        UPDATE storagerooms
        SET address = %s, status= %s
        WHERE id = %s
    """
    params = (room_address, room_status, room_id)

    # Execute the query
    success = execute_query(query, params)

    if success:
        flash("Storage room details updated successfully.", "success")
    else:
        flash("Failed to update the storage room details. Please try again.", "danger")

    # Redirect back to the storage rooms list
    return redirect(url_for('storageroomlist'))


@app.route('/editkitchen', methods=['POST'])
def edit_kitchen():
    # Get data from the form
    kitchen_id = request.form.get('id')
    kitchen_status = request.form.get('status')
    kitchen_address = request.form.get('address')

    # Validate inputs
    if not kitchen_id or not kitchen_address:
        flash("All fields are required.", "error")
        return redirect(url_for('kitchenlist'))

    # SQL query to update the kitchen
    query = """
        UPDATE kitchen
        SET address = %s, status= %s
        WHERE id = %s
    """
    params = (kitchen_address, kitchen_status, kitchen_id)

    # Execute the query
    success = execute_query(query, params)

    if success:
        flash("Kitchen details updated successfully.", "success")
    else:
        flash("Failed to update the Kitchen details. Please try again.", "danger")

    # Redirect back to the kitchen list
    return redirect(url_for('kitchenlist'))


@app.route('/editrestaurant', methods=['POST'])
def edit_restaurant():
    # Get data from the form
    restaurant_id = request.form.get('id')
    restaurant_status = request.form.get('status')
    restaurant_address = request.form.get('address')

    # Validate inputs
    if not restaurant_id or not restaurant_address:
        flash("All fields are required.", "error")
        return redirect(url_for('restaurantlist'))

    # SQL query to update the restaurant
    query = """
        UPDATE restaurant
        SET address = %s, status= %s
        WHERE id = %s
    """
    params = (restaurant_address, restaurant_status, restaurant_id)

    # Execute the query
    success = execute_query(query, params)

    if success:
        flash("restaurant details updated successfully.", "success")
    else:
        flash("Failed to update the restaurant details. Please try again.", "danger")

    # Redirect back to the restaurant list
    return redirect(url_for('restaurantlist'))


@app.route('/editvendor', methods=['POST'])
def edit_vendor():
    # Get data from the form
    vendor_id = request.form.get('id')
    vendor_status = request.form.get('status')
    vendor_address = request.form.get('address')
    vendor_phone = request.form.get('phone')

    # Validate inputs
    if not vendor_id or not vendor_address or not vendor_phone:
        flash("All fields are required.", "error")
        return redirect(url_for('vendorlist'))

    # SQL query to update the vendor
    query = """
        UPDATE vendor_list
        SET address= %s, status= %s, phone=%s
        WHERE id = %s
    """
    params = (vendor_address, vendor_status, vendor_phone, vendor_id)

    # Execute the query
    success = execute_query(query, params)

    if success:
        flash("vendor details updated successfully.", "success")
    else:
        flash("Failed to update the vendor details. Please try again.", "danger")

    # Redirect back to the vendor list
    return redirect(url_for('list_vendors'))


@app.route("/addkitchen", methods=["GET", "POST"])
def addkitchen():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        kitchen_name = request.form["kitchen_name"].strip()
        address = request.form["address"].strip()
        existing_kitchen = get_kitchen_by_name(kitchen_name)
        if existing_kitchen:
            flash("Kitchen with same name already exists. Please use a different Kitchen name.", "danger")
        else:
            insert_query = """
                INSERT INTO kitchen (kitchenname, address)
                VALUES (%s, %s)
            """
            if execute_query(insert_query, (kitchen_name, address)):
                flash("Kitchen added successfully!", "success")
            else:
                flash("Error: Unable to add a new Kitchen. Please try again later.", "danger")
        return redirect("/addkitchen")
    return render_template("addkitchen.html", user=session["user"])


@app.route("/kitchenlist", methods=["GET", "POST"])
def kitchenlist():
    if "user" not in session:
        return redirect("/login")
    kitchens = get_all_kitchens()
    return render_template("kitchenlist.html", user=session["user"], kitchens=kitchens)


@app.route("/addrestaurant", methods=["GET", "POST"])
def addrestaurant():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        restaurant_name = request.form["restaurant_name"].strip()
        address = request.form["address"].strip()
        existing_restaurant = get_restaurant_by_name(restaurant_name)
        if existing_restaurant:
            flash("Restaurant with same name already exists. Please use a different Restaurant name.", "danger")
        else:
            insert_query = """
                INSERT INTO restaurant (restaurantname, address)
                VALUES (%s, %s)
            """
            if execute_query(insert_query, (restaurant_name, address)):
                flash("Restaurant added successfully!", "success")
            else:
                flash("Error: Unable to add a new Restaurant. Please try again later.", "danger")
        return redirect("/addrestaurant")
    return render_template("addrestaurant.html", user=session["user"])


@app.route("/restaurantlist", methods=["GET", "POST"])
def restaurantlist():
    if "user" not in session:
        return redirect("/login")
    restaurants = get_all_restaurants()
    return render_template("restaurantlist.html", user=session["user"], restaurants=restaurants)


@app.route("/addrawmaterials", methods=["GET", "POST"])
def addrawmaterials():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        raw_materials = request.form.getlist("rawmaterial_name[]")
        metrics = request.form.getlist("metric[]")

        # Check for mismatched lengths (in case of any unexpected UI issues)
        if len(raw_materials) != len(metrics):
            flash("Error: Inconsistent data. Please try again.", "danger")
            return redirect("/addrawmaterials")

        # Fetch all existing raw materials in one query
        existing_materials = get_all_rawmaterials()
        existing_set = {(row["name"].lower(), row["metric"].lower()) for row in existing_materials}

        # Prepare data for bulk insert
        to_insert = []
        errors = []
        successes = []

        for raw_material, metric in zip(raw_materials, metrics):
            raw_material = raw_material.strip().lower()
            metric = metric.strip().lower()

            if not raw_material:
                errors.append("Raw material name cannot be empty.")
                continue

            if (raw_material, metric) in existing_set:
                errors.append(f"Raw material '{raw_material}' with metric '{metric}' already exists.")
                continue

            # Add to batch insert list
            to_insert.append((raw_material, metric))

        # Perform bulk insert if there are valid entries
        if to_insert:
            insert_query = "INSERT INTO raw_materials (name, metric) VALUES (%s, %s)"
            if execute_query(insert_query, to_insert, bulk=True):  # Pass `bulk=True` to handle batch inserts
                successes = [f"{raw_material}-{metric}" for raw_material, metric in to_insert]
            else:
                errors.append("Error: Unable to add some raw materials due to a database issue.")

        # Flash messages for successes and errors
        if successes:
            flash(f"Raw materials {' ,'.join(successes)} have been added successfully.", "success")
        if errors:
            flash(" ".join(errors), "danger")

        return redirect("/addrawmaterials")

    return render_template("addrawmaterials.html", user=session["user"])


@app.route("/rawmaterialslist", methods=["GET", "POST"])
def rawmaterialslist():
    if "user" not in session:
        return redirect("/login")
    rawmaterials = get_all_rawmaterials()
    return render_template("rawmaterialslist.html", user=session["user"], rawmaterials=rawmaterials)


@app.route('/add_dish_recipe', methods=['GET', 'POST'])
def add_dish_recipe():
    if "user" not in session:
        return redirect("/login")

    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        raw_materials = request.form.getlist('raw_materials[]')
        quantities = request.form.getlist('quantities[]')
        metrics = request.form.getlist('metric[]')

        if len(raw_materials) != len(quantities) or len(raw_materials) != len(metrics):
            flash("Error: Mismatched data for raw materials. Please check your input.", "danger")
            return redirect('/add_dish_recipe')

        # try:
        existing_dish = get_dish_details_from_category(category, name)
        if not existing_dish:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert into `dishes` table
                    cursor.execute("INSERT INTO dishes (category, name) VALUES (%s, %s)", (category, name))
                    dish_id = cursor.lastrowid

                    # Fetch all existing raw materials in one query
                    cursor.execute("SELECT id, name, metric FROM raw_materials")
                    existing_raw_materials = {row[1].lower(): (row[0], row[2])
                                              for row in cursor.fetchall()}

                    # Prepare data for batch inserts
                    new_raw_materials = []
                    dish_raw_materials = []

                    for raw_material, quantity, metric in zip(raw_materials, quantities, metrics):
                        raw_material = raw_material.strip().lower()
                        metric = metric.strip()

                        if raw_material in existing_raw_materials:
                            raw_material_id = existing_raw_materials[raw_material][0]
                        else:
                            # Add to new raw materials batch
                            new_raw_materials.append((raw_material, metric))

                    # Bulk insert new raw materials
                    if new_raw_materials:
                        cursor.executemany(
                            "INSERT INTO raw_materials (name, metric) VALUES (%s, %s)",
                            new_raw_materials
                        )
                        # Update existing_raw_materials with newly added materials
                        cursor.execute("SELECT id, name, metric FROM raw_materials WHERE name IN %s",
                                       ([rm[0] for rm in new_raw_materials],))
                        for row in cursor.fetchall():
                            existing_raw_materials[row['name'].lower()] = (row['id'], row['metric'])

                    # Build dish_raw_materials mapping
                    for raw_material, quantity, metric in zip(raw_materials, quantities, metrics):
                        raw_material_id = existing_raw_materials[raw_material][0]
                        dish_raw_materials.append((dish_id, raw_material_id, quantity, metric))

                    # Bulk insert into `dish_raw_materials`
                    cursor.executemany(
                        "INSERT INTO dish_raw_materials (dish_id, raw_material_id, quantity, metric) VALUES (%s, %s, %s, %s)",
                        dish_raw_materials
                    )

                conn.commit()
                flash('Dish added successfully!', 'success')
        else:
            flash('Dish already exists. Kindly check.', 'danger')

        # except Exception as e:
        #     flash(f'Error: {str(e)}', 'danger')

        return redirect('/add_dish_recipe')

    raw_materials = get_all_rawmaterials()
    dish_categories = get_all_dish_categories()

    return render_template('add_dish_recipe.html', user=session["user"], raw_materials=raw_materials, dish_categories=dish_categories)


@app.route('/list_dish_recipe', methods=['GET', 'POST'])
def list_dish_recipe():
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

    return render_template('list_dish_recipe.html', user=session["user"], dishes=dishes)


@app.route('/get_dish_raw_materials', methods=['GET'])
def get_dish_raw_materials():
    dish_id = int(request.args.get('dish_id'))
    materials_map = get_dish_recipe_raw_materials(dish_id)
    return jsonify({'raw_materials': materials_map})


@app.route('/submit_raw_materials', methods=['POST'])
def submit_raw_materials():
    data = request.get_json()
    app.logger.debug(f"Received data: {data}")

    dish_id = data["dish_id"]
    incoming_materials = data["materials"]

    # Fetch current materials from the database
    current_materials = get_dish_recipe_raw_materials(dish_id)
    app.logger.debug(f"Current materials: {current_materials}")

    # Map current materials for easy comparison
    current_map = {mat[1].lower(): (mat[2], mat[3]) for mat in current_materials}  # {name: (quantity, metric)}
    incoming_map = {mat["name"].lower(): (float(mat["quantity"]), mat["metric"]) for mat in incoming_materials}

    to_update = []
    to_insert = []
    to_delete = []

    # Identify materials to update or insert
    for name, (quantity, metric) in incoming_map.items():
        if name in current_map:
            # Check if there is a difference
            if current_map[name] != (quantity, metric):
                to_update.append((dish_id, name, quantity, metric))
        else:
            # New material to insert
            to_insert.append((dish_id, name, quantity, metric))

    # Identify materials to delete
    for name in current_map:
        if name not in incoming_map:
            to_delete.append(name)

    # Perform batch updates, inserts, and deletions
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update materials
        for dish_id, name, quantity, metric in to_update:
            cursor.execute("""
                UPDATE dish_raw_materials AS drm
                JOIN raw_materials AS rm ON drm.raw_material_id = rm.id
                SET drm.quantity = %s, drm.metric = %s
                WHERE drm.dish_id = %s AND rm.name = %s
            """, (quantity, metric, dish_id, name))

        # Insert new materials
        for dish_id, name, quantity, metric in to_insert:
            # Check if the raw material already exists
            cursor.execute("SELECT id FROM raw_materials WHERE name = %s", (name,))
            raw_material = cursor.fetchone()

            if raw_material:
                raw_material_id = raw_material[0]
            else:
                # Insert raw material if not exists
                cursor.execute("INSERT INTO raw_materials (name, metric) VALUES (%s, %s)", (name, metric))
                raw_material_id = cursor.lastrowid

            # Insert into dish_raw_materials
            cursor.execute("""
                INSERT INTO dish_raw_materials (dish_id, raw_material_id, quantity, metric)
                VALUES (%s, %s, %s, %s)
            """, (dish_id, raw_material_id, quantity, metric))

        # Delete removed materials
        for name in to_delete:
            cursor.execute("""
                DELETE drm FROM dish_raw_materials AS drm
                JOIN raw_materials AS rm ON drm.raw_material_id = rm.id
                WHERE drm.dish_id = %s AND rm.name = %s
            """, (dish_id, name))

        conn.commit()
        flash('Raw materials updated successfully', "success")
        return jsonify({
            'message': 'Raw materials updated successfully.',
            'redirect_url': url_for("edit_dish_recipe")  # Include the redirect URL
        }), 200
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error updating raw materials: {e}")
        flash(f"Error updating raw materials: {e}", "danger")
        return redirect(url_for("edit_dish_recipe"))
    finally:
        cursor.close()
        conn.close()


@app.route("/edit_dish_recipe", methods=['GET', 'POST'])
def edit_dish_recipe():
    if "user" not in session:
        return redirect("/login")
    dish_categories = get_unique_dish_categories()
    app.logger.debug(dish_categories)
    dishes = get_all_dishes()
    app.logger.debug(dishes)
    return render_template('edit_dish_recipe.html', user=session["user"], dish_categories=dish_categories, dishes=dishes)


@app.route('/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        vendor_names = request.form.getlist("vendor_name[]")
        phone_numbers = request.form.getlist("phone_number[]")
        addresses = request.form.getlist("address[]")
        app.logger.debug(f"vendor_names {vendor_names}")
        app.logger.debug(f"phone_numbers {phone_numbers}")
        app.logger.debug(f"addresses {addresses}")
        if vendor_names and phone_numbers and addresses:
            app.logger.debug("if")
            try:
                db_connection = get_db_connection()
                cursor = db_connection.cursor()

                # Insert each vendor's data into the database
                for name, phone, address in zip(vendor_names, phone_numbers, addresses):
                    cursor.execute(
                        "INSERT INTO vendor_list (vendor_name, phone, address) VALUES (%s, %s, %s)",
                        (name, phone, address)
                    )

                db_connection.commit()
                cursor.close()
                db_connection.close()
                flash('Vendor added successfully!', 'success')
            except Exception as e:
                app.logger.error(f"Error: {e}")
                flash("An error occurred while adding vendor details.", 'danger')
            return redirect("/add_vendor")
    return render_template('add_vendor.html', user=session["user"])


@app.route("/list_vendors", methods=["GET", "POST"])
def list_vendors():
    if "user" not in session:
        return redirect("/login")
    vendors = get_all_vendors()
    return render_template("list_vendors.html", user=session["user"], vendors=vendors)


@app.route('/add_purchase', methods=['GET', 'POST'])
def add_purchase():
    if "user" not in session:
        return redirect("/login")
    connection = get_db_connection()
    raw_materials = get_all_rawmaterials()
    storage_rooms = get_all_storagerooms()
    vendors = get_all_vendors()

    if request.method == 'POST':
        app.logger.debug(f"request {request.form}")
        vendor_name = request.form.get('vendor')
        storageroom_name = request.form.get('storage_room')
        raw_material_names = request.form.getlist('raw_material[]')  # List of raw materials
        quantities = request.form.getlist('quantity[]')             # List of quantities
        metrics = request.form.getlist('metric[]')                  # List of metrics
        total_costs = request.form.getlist('total_cost[]')          # List of total costs
        purchase_date = request.form.get("purchase_date")
        invoice_number = request.form.get("invoice_number")

        app.logger.debug(f"vendors {vendors}")
        app.logger.debug(f"raw_materials {raw_materials}")
        app.logger.debug(f"storage_rooms {storage_rooms}")
        app.logger.debug(f"vendor_name {vendor_name}")
        app.logger.debug(f"storageroom_name {storageroom_name}")
        app.logger.debug(f"raw_material_names {raw_material_names}")
        app.logger.debug(f"quantities {quantities}")
        app.logger.debug(f"metrics {metrics}")
        app.logger.debug(f"total_costs {total_costs}")
        app.logger.debug(f"invoice_number {invoice_number}")

        # Check for valid vendor
        vendor = next((v for v in vendors if v['vendor_name'] == vendor_name), None)
        if not vendor:
            flash('Vendor does not exist. Please add the vendor first.', 'danger')
            return redirect('/add_purchase')

        # Check for valid storageroom
        storageroom = next((s for s in storage_rooms if s['storageroomname'] == storageroom_name), None)
        if not storageroom:
            flash('Storage room does not exist. Please add the storage room first.', 'danger')
            return redirect('/add_purchase')

        # Iterate over the multiple raw materials
        for raw_material_name, quantity, metric, cost in zip(raw_material_names, quantities, metrics, total_costs):
            # Check and add raw material if not exists
            raw_material = next((rm for rm in raw_materials if rm['name'] == raw_material_name), None)
            if not raw_material:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO raw_materials (name, metric) VALUES (%s, %s)",
                    (raw_material_name, metric)
                )
                connection.commit()
                raw_material_id = cursor.lastrowid
            else:
                raw_material_id = raw_material['id']

            # Metric conversion
            if metric == 'grams':
                quantity = float(quantity) / 1000  # Convert to kg
                metric = 'kg'
            elif metric == 'ml':
                quantity = float(quantity) / 1000  # Convert to liters
                metric = 'liter'

            # Insert into purchase_history
            cursor = connection.cursor()
            cursor.execute(
                """
            INSERT INTO purchase_history 
            (vendor_id, invoice_number, raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, storageroom_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                quantity = quantity + VALUES(quantity),
                total_cost = total_cost + VALUES(total_cost);
            """,
                (vendor["id"], invoice_number, raw_material_id, raw_material_name,
                 quantity, metric, cost, purchase_date, storageroom['id'])
            )

            connection.commit()

            # Update vendor_payment_tracker
            cursor.execute(
                """
                INSERT INTO vendor_payment_tracker (vendor_id, invoice_number, outstanding_cost) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE outstanding_cost = outstanding_cost + VALUES(outstanding_cost);
                """,
                (vendor['id'], invoice_number, cost)
            )
            connection.commit()

            # Update storageroom_stock
            cursor.execute(
                """
                INSERT INTO storageroom_stock (storageroom_id, raw_material_id, quantity, metric) 
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    quantity = quantity + VALUES(quantity),
                    metric = VALUES(metric)
                """,
                (storageroom['id'], raw_material_id, quantity, metric)
            )
            connection.commit()

        flash('Purchases added successfully!', 'success')
        cursor.close()
        connection.close()
        return redirect('/add_purchase')

    return render_template('add_purchase.html', vendors=vendors, raw_materials=raw_materials, storage_rooms=storage_rooms, user=session["user"], today_date=get_current_date())


@app.route('/purchase_list')
def purchase_list():
    if "user" not in session:
        return redirect("/login")
    purchases = get_all_purchases()
    return render_template('purchase_list.html', purchases=purchases, user=session["user"])


@app.route("/pending_payments", methods=["GET", "POST"])
def pending_payments():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        # Handle form submission
        vendor_id = request.json.get("vendorId")
        vendor_name = request.json.get("vendorName")
        amount_paid = float(request.json.get("amountPaid"))
        app.logger.debug(f"vendor_id {vendor_id}")
        app.logger.debug(f"vendor_name {vendor_name}")
        app.logger.debug(f"amount_paid {amount_paid}")
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
                INSERT INTO vendor_payment_tracker (vendor_id, total_paid) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE total_paid = total_paid + %s
                """,
            (vendor_id, amount_paid, amount_paid)
        )
        connection.commit()
        cursor.close()
        connection.close()
        flash('Payment done successfully!', "success")
        return redirect(url_for("pending_payments"))
    # pending_payments = get_all_pending_payments()
    pending_payments_vendor_cumulative = get_all_pending_payments_vendor_cumulative()
    return render_template("pending_payments.html", user=session["user"], pending_payments_vendor_cumulative=pending_payments_vendor_cumulative, todays_date=get_current_date())


@app.route("/process_payments", methods=["POST"])
def process_payments():
    # try:
    if request.method == "POST":
        app.logger.debug(f"process_payments {request.json}")
        vendor_id = request.json.get("vendor_id")
        paid_values = []
        for payment in request.json.get("payments", []):
            if payment["pay_amount"] > 0:
                paid_values.append(payment)
        app.logger.debug(f"vendor id {vendor_id}")
        app.logger.debug(f"paid values {paid_values}")
        connection = get_db_connection()
        cursor = connection.cursor()
        for payment_detail in paid_values:
            app.logger.debug(payment_detail)
            cursor.execute(
                """
                    INSERT INTO vendor_payment_tracker (vendor_id, invoice_number, total_paid) 
                    VALUES (%s, %s, %s) 
                    ON DUPLICATE KEY UPDATE total_paid = total_paid + %s
                    """,
                (vendor_id, payment_detail["invoice_number"],
                    payment_detail["pay_amount"], payment_detail["pay_amount"])
            )
            cursor.execute(
                """
                    INSERT INTO payment_records (vendor_id, invoice_number, amount_paid, mode_of_payment, paid_on) 
                    VALUES (%s, %s, %s, %s, %s) 
                    """,
                (vendor_id, payment_detail["invoice_number"],
                    payment_detail["pay_amount"], payment_detail["mode_of_payment"], payment_detail["date_of_payment"])
            )
        connection.commit()
        cursor.close()
        connection.close()
        flash('Payment processed successfully!', 'success')
        return jsonify({'message': 'Payment processed successfully'}), 200
    # except Exception as e:
    #     flash(f'An error occurred while processing the payment. Please try again. {str(e)}', 'error')
    #     return jsonify({'error': str(e)}), 400


@app.route('/storageroom_stock')
def storageroom_stock():
    if "user" not in session:
        return redirect("/login")
    storage_stock = get_storageroom_stock()

    return render_template('storageroom_stock.html', storage_stock=storage_stock, user=session["user"])


@app.route('/kitchen_inventory_stock')
def kitchen_inventory_stock():
    if "user" not in session:
        return redirect("/login")
    kitcheninv_stock = get_kitchen_inventory_stock()

    return render_template('kitchen_inventory_stock.html', kitcheninv_stock=kitcheninv_stock, user=session["user"])


@app.route("/get_payment_details")
def get_payment_details():
    vendor_id = request.args.get('vendor_id')
    app.logger.debug(f"modal vendor_id {vendor_id}")
    payments_per_vendor = get_payment_details_of_vendor(vendor_id)

    def serialize(payment):
        return {
            'payment_id': payment['payment_id'],
            'invoice_number': payment['invoice_number'],
            'outstanding_cost': float(payment['outstanding_cost']),
            'total_paid': float(payment['total_paid']),
            'total_due': float(payment['total_due']),
            'last_updated': payment['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
        }

    return jsonify([serialize(p) for p in payments_per_vendor])


@app.route("/invoice_payment_details")
def invoice_payment_details():
    if "user" not in session:
        return redirect("/login")
    inv_payment_details = get_invoice_payment_details()

    return render_template('invoice_payment_details.html', inv_payment_details=inv_payment_details, user=session["user"])


@app.route("/payment_record")
def payment_record():
    if "user" not in session:
        return redirect("/login")
    payment_record = get_payment_record()

    return render_template('payment_record.html', payment_record=payment_record, user=session["user"])


@app.route('/restaurant_inventory_stock')
def restaurant_inventory_stock():
    if "user" not in session:
        return redirect("/login")
    restaurantinv_stock = get_restaurant_inventory_stock()

    return render_template('restaurant_inventory_stock.html', restaurantinv_stock=restaurantinv_stock, user=session["user"])


# Utility function for converting metric units

def convert_to_base_units(quantity, metric):
    if metric == "grams":
        return quantity / 1000  # Convert grams to kg
    elif metric == "ml":
        return quantity / 1000  # Convert ml to liters
    return quantity  # Return as is for kg, liters, and units


@app.route('/transfer_raw_material', methods=['GET', 'POST'])
def transfer_raw_material():
    if "user" not in session:
        return redirect("/login")

    if request.method == 'POST':
        # Get form data
        app.logger.debug(request.form)
        source_storageroom_id = request.form.get("storageroom")
        app.logger.debug(f"        source_storageroom_id  {source_storageroom_id}")
        destination_type = request.form.get("destination_type")
        app.logger.debug(f"        destination_type  {destination_type}")
        destination_id = request.form.get("destination_name")
        app.logger.debug(f"        destination_id  {destination_id}")
        transfer_date = request.form.get("transfer_date")
        app.logger.debug(f"        transfer_date  {transfer_date}")

        raw_materials = request.form.getlist("raw_material_id[]")
        app.logger.debug(f"        raw_materials  {raw_materials}")
        quantities = request.form.getlist("quantity[]")
        app.logger.debug(f"        quantities  {quantities}")
        metrics = request.form.getlist("metric[]")
        app.logger.debug(f"        metrics  {metrics}")
        # metrics = request.form.get("metric[]")
        # app.logger.debug(f"        metrics  {metrics}")

        # Convert quantities based on metric before processing
        transfer_details = []
        for raw_material, quantity, metric in zip(raw_materials, quantities, metrics):
            raw_material_data = get_raw_material_by_id(raw_material)
            app.logger.debug(f"raw_material_data {raw_material_data}")
            if not raw_material_data:
                flash(f"raw material {raw_material} is not available. Please add the raw material to continue", "danger")
                return redirect(url_for("transfer_raw_material"))
            quantity = quantity
            converted_quantity = convert_to_base_units(quantity, metric)
            transfer_details.append({
                "raw_material_id": raw_material,
                "raw_material_name": raw_material_data["name"],
                "quantity": converted_quantity,
                "metric": metric,
            })
        app.logger.debug(f"transfer_details {transfer_details}")

        try:
            # Process each transfer
            for detail in transfer_details:
                raw_material_id = detail["raw_material_id"]
                quantity = detail["quantity"]
                metric = detail["metric"]

                # # Step 1: Check if sufficient stock is available in the source storeroom
                # storageroom_check_query = """
                #     SELECT quantity FROM storageroom_stock
                #     WHERE storageroom_id = %s AND raw_material_id = %s
                # """
                # storageroom_stock = get_data(storageroom_check_query, (source_storageroom_id, raw_material_id))
                # app.logger.debug(f"storageroom_stock {storageroom_stock}")
                # if storageroom_stock and storageroom_stock[0][0] >= quantity:
                # Step 2: Update storageroom stock (decrease quantity)
                update_storageroom_query = """
                    UPDATE storageroom_stock
                    SET quantity = quantity - %s
                    WHERE storageroom_id = %s AND raw_material_id = %s
                """
                execute_query(update_storageroom_query, (quantity, source_storageroom_id, raw_material_id))

                # Step 3: Update or insert into the destination stock table (kitchen or restaurant)
                if destination_type == 'kitchen':
                    destination_table = 'kitchen_inventory_stock'
                elif destination_type == 'restaurant':
                    destination_table = 'restaurant_inventory_stock'
                else:
                    flash('Invalid destination type', 'danger')
                    return redirect('/transfer_raw_material')

                # Check if the raw material already exists in the destination table
                destination_check_query = f"""
                    SELECT quantity FROM {destination_table}
                    WHERE {destination_type}_id = %s AND raw_material_id = %s
                """
                destination_stock = get_data(destination_check_query, (destination_id, raw_material_id))
                app.logger.debug(f"destination_stock {destination_stock}")
                if destination_stock:
                    # Update existing entry in the destination table
                    update_destination_query = f"""
                        UPDATE {destination_table}
                        SET quantity = quantity + %s
                        WHERE {destination_type}_id = %s AND raw_material_id = %s
                    """
                    execute_query(update_destination_query, (quantity, destination_id, raw_material_id))
                else:
                    # Insert a new record if no entry exists for this raw material in the destination table
                    insert_destination_query = f"""
                        INSERT INTO {destination_table} ({destination_type}_id, raw_material_id, quantity, metric)
                        VALUES (%s, %s, %s, %s)
                    """
                    execute_query(insert_destination_query, (destination_id, raw_material_id, quantity, metric))

                # Step 4: Log the transfer details into raw_material_transfer_details table
                insert_transfer_query = """
                    INSERT INTO raw_material_transfer_details (
                        source_storage_room_id, destination_type, destination_id,
                        raw_material_id, quantity, metric, transferred_date
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        quantity = quantity + VALUES(quantity)
                """
                execute_query(insert_transfer_query, (source_storageroom_id, destination_type, destination_id,
                                                      raw_material_id, quantity, metric, transfer_date))

                # else:
                #     flash(f'Insufficient stock in storageroom for raw_material {detail["raw_material_name"]}', 'danger')
                #     return redirect('/transfer_raw_material')

            flash('Transfer successful', 'success')
            return redirect('/transfer_raw_material')

        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
            return redirect('/transfer_raw_material')

    # GET request - fetch necessary data to render form
    storagerooms = get_all_storagerooms()
    restaurants = get_all_restaurants()
    kitchens = get_all_kitchens()
    raw_materials = get_all_rawmaterials()
    storageroom_stock = get_storageroom_stock()
    return render_template('transfer_raw_material.html', raw_materials=raw_materials,
                           storage_rooms=storagerooms, restaurants=restaurants, kitchens=kitchens,
                           user=session["user"], today_date=get_current_date(),
                           storageroom_stock=storageroom_stock)


@app.route('/list_rawmaterial_transfers')
def list_rawmaterial_transfers():
    if "user" not in session:
        return redirect("/login")
    transfers = get_rawmaterial_transfer_history()
    return render_template('list_rawmaterial_transfers.html', transfers=transfers, user=session["user"])


@app.route('/list_prepared_dishes_transfers')
def list_prepared_dishes_transfers():
    if "user" not in session:
        return redirect("/login")
    transfers = get_prepared_dishes_transfer_history()
    return render_template('list_prepared_dishes_transfers.html', transfers=transfers, user=session["user"])


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


# @app.route('/bulk_add_purchases', methods=['GET', 'POST'])
# def bulk_add_purchases():
#     try:
#         conn = get_db_connection()
#         with conn.cursor() as cursor:
#             # Fetch inventory
#             cursor.execute("SELECT id, inventoryname, inventorycode FROM inventory")
#             inventories = cursor.fetchall()

#         if request.method == 'POST':
#             app.logger.debug(f"Request data: {request.data}")
#             app.logger.debug(f"Form keys: {list(request.form.keys())}")

#             inventory_id = request.form.get('inventory_id')
#             if not inventory_id:
#                 flash('Inventory selection is required.', 'danger')
#                 return redirect(url_for('bulk_add_purchases'))

#             inventory_name = get_inventory_by_id(inventory_id).get("inventoryname", "Unknown Inventory")
#             raw_material_data = []

#             for key, value in request.form.items():
#                 if key.startswith('material_'):
#                     raw_material_id = key.split('_')[1]
#                     raw_material_name = value
#                     try:
#                         quantity = float(request.form[f'quantity_{raw_material_id}'])
#                         metric = request.form[f'metric_{raw_material_id}']
#                         total_cost = float(request.form[f'total_cost_{raw_material_id}'])
#                         purchase_date = request.form[f'purchase_date_{raw_material_id}']
#                         raw_material_data.append((raw_material_id, raw_material_name,
#                                                  quantity, metric, total_cost, purchase_date))
#                     except KeyError as e:
#                         flash(f'Missing data for raw material {raw_material_name}: {str(e)}', 'danger')
#                         return redirect(url_for('bulk_add_purchases'))

#             with conn.cursor() as cursor:
#                 for raw_material in raw_material_data:
#                     raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date = raw_material
#                     # Insert or update purchase history
#                     cursor.execute("""
#                         INSERT INTO purchase_history
#                         (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s)
#                     """, (raw_material_id, raw_material_name, quantity, metric, total_cost, purchase_date, inventory_id))

#                     # Update inventory stock
#                     cursor.execute("""
#                         INSERT INTO inventory_stock
#                         (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric)
#                         VALUES (%s, %s, %s, %s, %s, %s)
#                         ON DUPLICATE KEY UPDATE
#                         quantity = quantity + VALUES(quantity),
#                         metric = VALUES(metric),
#                         inventory_name = VALUES(inventory_name),
#                         raw_material_name = VALUES(raw_material_name)
#                     """, (inventory_id, inventory_name, raw_material_id, raw_material_name, quantity, metric))
#                 conn.commit()

#             flash('Bulk purchase data submitted successfully!', 'success')
#             return redirect(url_for('bulk_add_purchases'))

#         # Fetch raw materials and last purchase details
#         with conn.cursor() as cursor:
#             cursor.execute("""
#                 SELECT r.id, r.name, r.metric,
#                        COALESCE(p.quantity, NULL) AS last_quantity,
#                        COALESCE(p.metric, NULL) AS last_metric,
#                        COALESCE(p.total_cost, NULL) AS last_cost,
#                        COALESCE(p.purchase_date, NULL) AS last_date
#                 FROM raw_materials r
#                 LEFT JOIN (
#                     SELECT raw_material_id, quantity, metric, total_cost, purchase_date
#                     FROM purchase_history
#                     WHERE purchase_date = (SELECT MAX(purchase_date)
#                                            FROM purchase_history
#                                            WHERE raw_material_id = purchase_history.raw_material_id)
#                 ) p ON r.id = p.raw_material_id
#             """)
#             raw_materials = cursor.fetchall()

#         # Deduplicate raw materials
#         columns = ['id', 'name', 'metric', 'last_quantity', 'last_metric', 'last_cost', 'last_date']
#         raw_materials = [dict(zip(columns, row)) for row in raw_materials]
#         unique_raw_materials = {material['id']: material for material in raw_materials}
#         raw_materials = list(unique_raw_materials.values())

#         return render_template('bulk_add_purchases.html', user=session["user"], raw_materials=raw_materials, current_date=get_current_date(), inventories=inventories)

#     except Exception as e:
#         app.logger.error(f"An error occurred: {e}")
#         flash('An unexpected error occurred. Please try again.', 'danger')
#         return redirect(url_for('bulk_add_purchases'))


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


# @app.route('/bulk_transfer', methods=['GET', 'POST'])
# def bulk_transfer():
#     if request.method == 'GET':
#         # Query the list of available dishes for selection (if applicable)
#         dishes_query = "SELECT id, name FROM dishes"
#         dishes = execute_query(dishes_query)

#         return render_template('bulk_raw_material_transfer.html', dishes=dishes)

#     elif request.method == 'POST':
#         try:
#             # Get form data
#             inventory_id = request.form.get('inventory_id')
#             dish_id = request.form.get('dish_id')
#             transfer_data = {
#                 key: value
#                 for key, value in request.form.items()
#                 if key.startswith("transfer_quantity_")
#             }

#             # Process each raw material transfer
#             for raw_material_id, transfer_quantity in transfer_data.items():
#                 raw_material_id = raw_material_id.replace("transfer_quantity_", "")
#                 transfer_quantity = float(transfer_quantity)

#                 # Validate available quantity
#                 query = """
#                     SELECT quantity
#                     FROM inventory_stock
#                     WHERE raw_material_id = %s AND inventory_id = %s
#                 """
#                 available_quantity = execute_query(query, (raw_material_id, inventory_id))[0][0]

#                 if transfer_quantity > available_quantity:
#                     flash(f"Transfer quantity for raw material {raw_material_id} exceeds available quantity.", "danger")
#                     return redirect('/bulk_transfer')

#                 # Update inventory
#                 update_query = """
#                     UPDATE inventory_stock
#                     SET quantity = quantity - %s
#                     WHERE raw_material_id = %s AND inventory_id = %s
#                 """
#                 execute_query(update_query, (transfer_quantity, raw_material_id, inventory_id))

#             flash("Bulk transfer completed successfully.", "success")
#             return redirect('/bulk_transfer')

#         except Exception as e:
#             flash(f"An error occurred: {e}", "danger")
#             return redirect('/bulk_transfer')


@app.route('/upload_sales_report', methods=['GET', 'POST'])
def upload_sales_report():
    if "user" not in session:
        return redirect("/login")

    if request.method == 'POST':
        app.logger.debug(f"request.files {request.files}")
        file = request.files.get('file')
        restaurant_id = request.form.get("restaurant_id")

        if 'file' not in request.files:
            flash('No file part found. Please try again.', "danger")
            return redirect(url_for('upload_sales_report'))

        if file.filename == '':
            flash('No selected file. Please upload a file', "danger")
            return redirect(url_for('upload_sales_report'))

        if file and file.filename.endswith('.xlsx'):
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Process the file
            missing_recipes = process_data(file_path)

            if missing_recipes:
                missing_recipes_table = """
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Missing Recipe</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for recipe in missing_recipes:
                    missing_recipes_table += f"<tr><td>{recipe}</td></tr>"
                missing_recipes_table += "</tbody></table>"

                flash(Markup(
                    f"Recipe not found for the following dishes. Kindly update recipe for all the dishes and continue:<br>{missing_recipes_table}"), "danger")
            else:
                # Process the data and update the daily_sales table
                df = pd.read_excel(file_path)
                # Extract sales date from filename format: Restaurant_item_tax_report_YYYY_MM_DD_HH_MM_SS.xlsx
                filename_parts = file.filename.split('_')
                sales_date_str = f"{filename_parts[4]}-{filename_parts[5]}-{filename_parts[6]}"
                sales_date = datetime.strptime(sales_date_str, '%Y-%m-%d').date()

                conn = get_db_connection()
                cursor = conn.cursor()

                for index, row in df.iterrows():
                    category = row['Category']
                    item_name = row['Item Name']
                    quantity = row['Qty']

                    cursor.execute(
                        "SELECT id FROM dishes WHERE category = %s AND name = %s", (category, item_name))
                    dish = cursor.fetchone()
                    app.logger.debug(f"dish fetchone one {dish}")
                    if dish:
                        dish_id = dish[0]
                        cursor.execute("""
                            INSERT INTO daily_sales (sales_date, dish_id, quantity)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
                        """, (sales_date, dish_id, quantity))
                    else:
                        missing_recipes.append(item_name)

                conn.commit()
                cursor.close()
                conn.close()

                # Delete the uploaded Excel file
                os.remove(file_path)
                adjust_stocks(sales_date, restaurant_id)
            flash("Sales report data has been processed succesfully and the inventory stocks have been adjusted accordingly. Please do not reupload the sales report as it will modify the inventory.", "success")
            return redirect(url_for('upload_sales_report'))

    restaurants = get_all_restaurants()
    return render_template('upload_sales_report.html', user=session["user"], restaurants=restaurants, current_date=get_current_date())


@app.route('/get_available_quantity', methods=['GET'])
def get_available_quantity():
    storageroom_id = int(request.args.get('storageroom_id'))
    raw_material_id = request.args.get('raw_material_id')
    app.logger.debug(f"ss {storageroom_id}")
    app.logger.debug(f"rm {raw_material_id}")
    available_quantity = get_storageroom_rawmaterial_quantity(storageroom_id, raw_material_id)
    storage_available_quantity = 0
    if available_quantity:
        storage_available_quantity = available_quantity[0]["quantity"]
    app.logger.debug(f"storage_available_quantity {storage_available_quantity}")
    # # Check if storage room and raw material exist
    # available_quantity = storage_available_quantity.get(raw_material_id, 0)
    data = {"available_quantity": float(storage_available_quantity)}
    app.logger.debug(f"jsonify data {data}")
    return jsonify(data)


@app.route('/add_prepared_dishes', methods=['GET', 'POST'])
def add_prepared_dishes():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        try:
            # Retrieve form data
            app.logger.debug(f"form {request.form}")
            dish_categories = request.form.getlist('dish_categories[]')
            app.logger.debug(f"dish_categories{dish_categories}")
            dish_names = request.form.getlist('dish_names[]')
            app.logger.debug(f"dish_names{dish_names}")
            prepared_quantities = request.form.getlist('prepared_quantities[]')
            app.logger.debug(f"prepared_quantities{prepared_quantities}")
            prepared_in_kitchen = request.form.get('kitchen_id')
            app.logger.debug(f"prepared_in_kitchen{prepared_in_kitchen}")
            prepared_on = request.form.get('prepared_on')
            app.logger.debug(f"prepared_on{prepared_on}")
            # kitchen_data = get_kitchen_by_name(prepared_in_kitchen)
            # app.logger.debug(f"kitchen_data{kitchen_data}")

            # Check and insert records
            for category, dish, quantity in zip(dish_categories, dish_names, prepared_quantities):
                # Check if dish exists in the category
                app.logger.debug(f"category{category}")
                app.logger.debug(f"dish{dish}")
                app.logger.debug(f"quantity{quantity}")
                query = f'SELECT * FROM dishes WHERE category ="{category}" AND name ="{dish}"'
                existing_dish = fetch_all(
                    query
                )
                app.logger.debug(f"existing_dish {existing_dish}")
                if not existing_dish:
                    flash(f"Dish '{dish}' under category '{category}' does not exist. Please add the dish.", "error")
                    return redirect(request.url)
                dish_id = existing_dish[0]['id']

                # Query to check if the dish for the given kitchen and date exists
                check_query = """
                    SELECT id, prepared_quantity FROM kitchen_prepared_dishes
                    WHERE prepared_dish_id = %s AND prepared_in_kitchen = %s AND prepared_on = %s
                """
                check_params = (dish_id, prepared_in_kitchen, prepared_on)

                # Execute the check query
                existing_record = fetch_all(check_query, check_params)
                app.logger.debug(f"existing dish record {existing_record}")

                if existing_record:
                    # If a record exists, update the quantity by adding the new value
                    update_query = """
                        UPDATE kitchen_prepared_dishes
                        SET prepared_quantity = prepared_quantity + %s,
                        available_quantity = available_quantity + %s
                        WHERE id = %s
                    """
                    update_params = (quantity, quantity, existing_record[0]['id'])
                    status = execute_query(update_query, update_params)
                else:
                    # If no record exists, insert a new one
                    insert_query = """
                        INSERT INTO kitchen_prepared_dishes (
                            prepared_dish_id, prepared_quantity, available_quantity, prepared_in_kitchen, prepared_on
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    insert_params = (dish_id, quantity, quantity,
                                     prepared_in_kitchen, prepared_on)
                    status = execute_query(insert_query, insert_params)
                update_kitchen_stock(prepared_in_kitchen, dish_id, quantity, prepared_on)
                if status:
                    flash(f"Prepared dish {dish} added successfully!", "success")
                else:
                    flash("Unable to add the prepared dish details", 'danger')
            return redirect('/add_prepared_dishes')

        except Exception as e:
            app.logger.error(f"Error while adding prepared dishes: {e}")
            flash(f"An error occurred while adding prepared dishes. {e}", "error")
            return redirect(request.url)

    # GET request: fetch data for rendering the page
    dish_categories = get_unique_dish_categories()
    dishes = get_all_dishes()
    kitchens = get_all_kitchens()
    app.logger.debug(f"dishes {dishes}")
    app.logger.debug(f"kitchens {kitchens}")
    dish_mapping = {}
    for dish in dishes:
        category = dish['category']
        if category not in dish_mapping:
            dish_mapping[category] = []
        dish_mapping[category].append(dish['name'])

    return render_template(
        'add_prepared_dishes.html',
        dish_categories=dish_categories,
        dishes=dishes,
        dish_mapping=dish_mapping,
        kitchens=kitchens,
        user=session["user"],
        todays_date=get_current_date()
    )


@app.route('/list_prepared_dishes', methods=['GET', 'POST'])
def list_prepared_dishes():
    if "user" not in session:
        return redirect("/login")
    prepared_dishes = get_all_prepared_dishes()

    return render_template('list_prepared_dishes.html', user=session["user"], prepared_dishes=prepared_dishes)


@app.route('/transfer_prepared_dishes', methods=['GET', 'POST'])
def transfer_prepared_dishes():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch dishes, restaurants, and kitchens to populate in the form
    prepared_dishes_today = get_prepared_dishes_today()
    dish_categories = list(set([dish["prepared_dish_category"] for dish in prepared_dishes_today]))
    kitchens = get_all_kitchens()
    restaurants = get_all_restaurants()

    current_date = get_current_date()
    app.logger.debug(f"dish_categories {dish_categories}")
    app.logger.debug(f"prepared_dishes_today {prepared_dishes_today}")
    app.logger.debug(f"restaurants {restaurants}")
    app.logger.debug(f"kitchens {kitchens}")

    # Handle form submission for dish transfer
    if request.method == 'POST':
        source_kitchen_id = request.form['kitchen']
        app.logger.debug(f"source_kitchen_id {source_kitchen_id}")
        destination_restaurant_id = request.form['destination_name']
        app.logger.debug(f"destination_restaurant_id {destination_restaurant_id}")
        dish_categories = request.form.getlist('dish_categories[]')
        app.logger.debug(f"dish_categories {dish_categories}")
        dish_names = request.form.getlist('dish_names[]')
        app.logger.debug(f"dish_names {dish_names}")
        transferred_quantities = request.form.getlist('transferred_quantities[]')
        app.logger.debug(f"transferred_quantities {transferred_quantities}")
        transfer_date = request.form['transfer_date']
        app.logger.debug(f"transfer_date {transfer_date }")

        # try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert the transfer details into the database
        for category, name, quantity in zip(dish_categories, dish_names, transferred_quantities):
            dish_id = get_dish_details_from_category(category, name)[0]["id"]
            cursor.execute(
                """
                SELECT available_quantity FROM kitchen_prepared_dishes
                WHERE prepared_dish_id=%s AND prepared_in_kitchen = %s AND prepared_on=%s
                """,
                (dish_id, source_kitchen_id, transfer_date)
            )
            dish = cursor.fetchone()
            app.logger.debug(f"dishhhh {dish}")
            if dish and dish[0] >= int(quantity):
                cursor.execute("""
                INSERT INTO prepared_dish_transfer (
                    source_kitchen_id,
                    destination_restaurant_id,
                    dish_id,
                    quantity,
                    transferred_date
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    quantity = quantity + VALUES(quantity);
                """, (source_kitchen_id, destination_restaurant_id, dish_id, quantity, transfer_date))

                # Update the available quantity in the source kitchen
                cursor.execute(
                    """
                    UPDATE kitchen_prepared_dishes
                    SET available_quantity = available_quantity - %s
                    WHERE prepared_dish_id=%s AND prepared_in_kitchen = %s AND prepared_on=%s
                    """,
                    (quantity, dish_id, source_kitchen_id, transfer_date)
                )
                conn.commit()
            else:
                flash(f"Insufficient quantity for dish: {name} in category: {category}", "danger")
                conn.rollback()
                cursor.close()
                conn.close()
                return redirect(url_for('transfer_prepared_dishes'))

        flash("Dish transfer successful!", "success")

        # except Exception as e:
        #     conn.rollback()  # Rollback in case of any error
        #     app.logger.error(f"Error during dish transfer: {e}")
        #     flash("Error occurred while transferring the dish.", "danger")
        # finally:
        #     cursor.close()
        #     conn.close()

        return redirect(url_for('transfer_prepared_dishes'))

    return render_template('transfer_prepared_dishes.html', dish_categories=dish_categories, current_date=current_date, prepared_dishes_today=prepared_dishes_today, restaurants=restaurants, kitchens=kitchens, user=session["user"])


# def upload_sales_report():

@app.route('/check_dish_availability', methods=['GET', 'POST'])
def check_dish_availability():
    if "user" not in session:
        return redirect("/login")
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


# Read the Excel file
def read_excel(file_path):
    return pd.read_excel(file_path)


def process_data(file_path):

    data = read_excel(file_path)
    missing_recipes = []

    for index, row in data.iterrows():
        category = row['Category']
        item_name = row['Item Name']
        # Find dish_id
        dish = get_dish_details_from_category(category, item_name)

        if dish:
            dish_id = dish[0]["id"]
            dish_recipe = get_dish_recipe(dish_id)
            if not dish_recipe:
                missing_recipes.append(f"{category} - {item_name}")
        else:
            missing_recipes.append(f"{category} - {item_name}")
    return missing_recipes


def adjust_stocks(report_date, restaurant_id):
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to the database.")
        return []
    app.logger.debug(report_date)
    data = get_sales_report_data(report_date)
    for dish_data in data:
        app.logger.debug(f"dish data for loop {dish_data}")
        dish_recipe = get_dish_recipe(dish_data["dish_id"])
        app.logger.debug(f"dish recipeee {dish_recipe}")
        transferred_dish = check_dish_transferred(dish_data["dish_id"], report_date, restaurant_id)
        if transferred_dish:
            app.logger.debug(f"{dish_data} is a prepared dish")
            pass
        else:
            update_restaurant_stock(restaurant_id, dish_data["dish_id"], dish_data["quantity"], report_date)
        #     materials = get_raw_materials(dish_data["dish_id"])
        #     raw_materials = []
        #     for material in materials:
        #         raw_materials.append({
        #             'raw_material_id': material[0],
        #             'quantity': material[1] * dish_data["quantity"],
        #             'metric': material[2]
        #         })
        #     app.logger.debug(f"raw raw {raw_materials}")
        #     subtract_raw_materials(raw_materials, "restaurant", restaurant_id, report_date)
        # # transferred_dish = check_dish_transferred(dish_data["id"], report_date, restaurant_id)
        # # if transferred_dish:
        # #     pass
        # #     # subtract_raw_materials(raw_materials, "kitchen", transferred_dish[0], report_date)

        # else:
        #     subtract_raw_materials(raw_materials, "restaurant", restaurant_id, report_date)


@app.route('/restaurant_consumption', methods=['GET', 'POST'])
def restaurant_consumption():
    if "user" not in session:
        return redirect("/login")
    restaurants = get_all_restaurants()
    if request.method == 'POST':
        selected_date = request.form['report_date']
        restaurant_id = request.form['restaurant_id']
        app.logger.debug(f"selected_date {selected_date}")
        app.logger.debug(f"restaurant_id {restaurant_id}")
        consumption_data = get_restaurant_consumption_report(restaurant_id, selected_date)
        return render_template("restaurant_consumption.html", user=session["user"], restaurants=restaurants, current_date=selected_date, query_result=consumption_data)
    return render_template("restaurant_consumption.html", user=session["user"], restaurants=restaurants, current_date=get_current_date())


@app.route('/kitchen_consumption', methods=['GET', 'POST'])
def kitchen_consumption():
    if "user" not in session:
        return redirect("/login")
    kitchens = get_all_kitchens()
    if request.method == 'POST':
        selected_date = request.form['report_date']
        kitchen_id = request.form['kitchen_id']
        app.logger.debug(f"selected_date {selected_date}")
        app.logger.debug(f"kitchen_id {kitchen_id}")
        consumption_data = get_kitchen_consumption_report(kitchen_id, selected_date)
        return render_template("kitchen_consumption.html", user=session["user"], kitchens=kitchens, current_date=selected_date, query_result=consumption_data)
    return render_template("kitchen_consumption.html", user=session["user"], kitchens=kitchens, current_date=get_current_date())


if __name__ == "__main__":
    app.run(debug=True)
