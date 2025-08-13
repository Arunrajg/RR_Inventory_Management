import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from decimal import Decimal
import os
import pytz
from dotenv import load_dotenv
load_dotenv()

# Set up logger
logging.basicConfig(level=logging.DEBUG,  # You can change the log level to INFO, ERROR, etc.
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        # logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()          # Log to console
                    ])
logger = logging.getLogger()

DB_CONFIG = {
    # Default to 'db' if not set
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "root"),  # Default to 'root' if not set
    "password": os.getenv("DB_PASSWORD", "password"),  # Default to 'password' if not set
    "database": os.getenv("DB_DATABASE", "dharaniinvmgmt"),  # Default to 'dharaniinvmgmt' if not set
    "init_command": "SET time_zone = 'Asia/Kolkata'"
}


def get_current_date():

    # Get the IST timezone
    ist_timezone = pytz.timezone('Asia/Kolkata')

    # Get current time in IST
    current_time_ist = datetime.now(ist_timezone)

    # Format the date as "YYYY-MM-DD"
    formatted_date_ist = current_time_ist.strftime("%Y-%m-%d")
    return formatted_date_ist


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error: {e}")
        return None

# Generic function to execute INSERT/UPDATE/DELETE queries


def execute_query(query, params=None, bulk=False):
    connection = get_db_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        if bulk and params:
            cursor.executemany(query, params)
        elif params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Ensure all results are read before returning
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
            cursor.close()  # Close the cursor before returning
            return result

        connection.commit()
        return True  # Return True for non-SELECT queries

    except Exception as e:
        logger.error(f"Database Error: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()  # Close the connection to prevent locking


# Generic function to execute SELECT queries


def fetch_all(query, params=None):
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Database Error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def fetch_one(query, params=None):
    results = fetch_all(query, params)
    return results[0] if results else None


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_storageroom_by_name(storageroom_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM storagerooms WHERE storageroomname = %s', (storageroom_name,))
    storageroom_name = cursor.fetchone()
    cursor.close()
    conn.close()
    return storageroom_name


def get_kitchen_by_name(kitchen_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM kitchen WHERE kitchenname = %s', (kitchen_name,))
    kitchen = cursor.fetchone()
    cursor.close()
    conn.close()
    return kitchen


def get_restaurant_by_name(restaurant_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM restaurant WHERE restaurantname = %s', (restaurant_name,))
    restaurant = cursor.fetchone()
    cursor.close()
    conn.close()
    return restaurant


def get_all_storagerooms(only_active=False):
    query = 'SELECT * FROM storagerooms ORDER BY id ASC'
    if only_active:
        query = 'SELECT * FROM storagerooms WHERE status="active" ORDER BY id ASC'
    storagerooms = fetch_all(query)
    return storagerooms


def get_all_kitchens(only_active=False):
    query = 'SELECT * FROM kitchen ORDER BY id ASC'
    if only_active:
        query = 'SELECT * FROM kitchen WHERE status="active" ORDER BY id ASC'
    kitchens = fetch_all(query)
    return kitchens


def get_all_restaurants(only_active=False):
    query = 'SELECT * FROM restaurant ORDER BY id ASC'
    if only_active:
        query = 'SELECT * FROM restaurant WHERE status="active" ORDER BY id ASC'
    restaurants = fetch_all(query)
    return restaurants


def get_dish_details_from_category(category_name, dish_name):
    query = 'SELECT id FROM dishes WHERE category =%s and name=%s'
    dish_id = fetch_all(query, (category_name, dish_name))
    return dish_id


def get_sales_report_data(sales_date):
    query = """
    SELECT
        sr.id,
        sr.sales_date,
        d.id AS dish_id,
        d.category AS dish_category,
        d.name AS dish_name,
        sr.quantity
    FROM
        daily_sales sr
    JOIN
        dishes d ON sr.dish_id = d.id
    WHERE sales_date=%s;
        """
    sales_report_data = fetch_all(query, (sales_date,))
    return sales_report_data


def get_dish_recipe(dish_id):
    query = 'SELECT dish_id, raw_material_id, quantity, metric FROM dish_raw_materials WHERE dish_id =%s'
    recipe = fetch_all(query, (dish_id,))
    return recipe


def check_dish_transferred(dish_id, prepared_date, restaurant_id):
    result = None
    conn = get_db_connection()
    query = """SELECT source_kitchen_id FROM prepared_dish_transfer WHERE dish_id = %s AND transferred_date = %s and destination_restaurant_id=%s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id, prepared_date, restaurant_id))
    result = cursor.fetchone()
    cursor.close()
    return result


def check_prepared_dish(dish_id, prepared_date, restaurant_id):
    result = None
    conn = get_db_connection()
    query = """SELECT id FROM kitchen_prepared_dishes WHERE prepared_dish_id = %s AND prepared_on = %s and prepared_in_kitchen=%s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id, prepared_date, restaurant_id))
    result = cursor.fetchone()
    cursor.close()
    return result


def get_restaurant_consumption_report(restaurant_id, report_date):
    query = """
    SELECT 
        r.restaurantname AS restaurant_name,
        rm.name AS raw_material_name,
        ris.metric AS metric,
        ROUND(SUM(CASE WHEN rmtd.destination_type = 'restaurant' THEN rmtd.quantity ELSE 0 END), 5) AS transferred_quantity,
        ROUND(SUM(c.quantity), 5) AS consumed_quantity,
        ROUND((SUM(CASE WHEN rmtd.destination_type = 'restaurant' THEN rmtd.quantity ELSE 0 END) - COALESCE(SUM(c.quantity), 0)), 5) AS remaining_quantity
    FROM 
        restaurant_inventory_stock ris
    JOIN 
        restaurant r ON ris.restaurant_id = r.id
    JOIN 
        raw_materials rm ON ris.raw_material_id = rm.id
    LEFT JOIN 
        raw_material_transfer_details rmtd ON rmtd.destination_id = ris.restaurant_id AND rmtd.raw_material_id = ris.raw_material_id AND DATE(rmtd.transferred_date) = %s AND rmtd.destination_type = 'restaurant'
    LEFT JOIN 
        consumption c ON c.location_id = ris.restaurant_id AND c.raw_material_id = ris.raw_material_id AND c.location_type = 'restaurant' AND DATE(c.consumption_date) = %s
    WHERE 
        ris.restaurant_id = %s AND DATE(ris.updated_at) = %s
    GROUP BY 
        r.restaurantname, rm.name, ris.metric
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (report_date, report_date, restaurant_id, report_date))
    result = cursor.fetchall()  # Fetch all results instead of just one
    cursor.close()
    return result


def get_kitchen_consumption_report(kitchen_id, report_date):
    query = """
    SELECT 
    k.kitchenname AS kitchen_name,
    rm.name AS raw_material_name,
    kis.metric AS metric,
    ROUND(SUM(CASE WHEN rmtd.destination_type = 'kitchen' THEN rmtd.quantity ELSE 0 END), 5) AS transferred_quantity,
    ROUND(SUM(c.quantity), 5) AS consumed_quantity,
    ROUND((SUM(CASE WHEN rmtd.destination_type = 'kitchen' THEN rmtd.quantity ELSE 0 END) - COALESCE(SUM(c.quantity), 0)), 5) AS remaining_quantity
FROM 
    kitchen_inventory_stock kis
JOIN 
    kitchen k ON kis.kitchen_id = k.id
JOIN 
    raw_materials rm ON kis.raw_material_id = rm.id
LEFT JOIN 
    raw_material_transfer_details rmtd ON rmtd.destination_id = kis.kitchen_id AND rmtd.raw_material_id = kis.raw_material_id AND DATE(rmtd.transferred_date) = %s AND rmtd.destination_type = 'kitchen'
LEFT JOIN 
    consumption c ON c.location_id = kis.kitchen_id AND c.raw_material_id = kis.raw_material_id AND c.location_type = 'kitchen' AND DATE(c.consumption_date) = %s
WHERE 
    kis.kitchen_id = %s AND DATE(kis.updated_at) = %s
GROUP BY 
    k.kitchenname, rm.name, kis.metric;
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (report_date, report_date, kitchen_id, report_date))
    result = cursor.fetchall()
    cursor.close()
    return result


def subtract_raw_materials(raw_materials, destination_type, type_id, report_date):
    conn = get_db_connection()
    for material in raw_materials:
        # if destination_type == "restaurant":
        query = """SELECT quantity FROM restaurant_inventory_stock WHERE raw_material_id = %s AND restaurant_id = %s"""
        update_query = """UPDATE restaurant_inventory_stock SET quantity = %s WHERE raw_material_id = %s AND restaurant_id = %s"""
        insert_consumption_query = """
        INSERT INTO consumption (raw_material_id, quantity, metric, consumption_date, location_type, location_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        quantity = quantity + %s;
        """
        # elif destination_type == "kitchen":
        #     query = """SELECT quantity FROM kitchen_inventory_stock WHERE raw_material_id = %s AND kitchen_id = %s"""
        #     update_query = """UPDATE kitchen_inventory_stock SET quantity = %s WHERE raw_material_id = %s AND kitchen_id = %s"""
        #     insert_consumption_query = """
        #         INSERT INTO consumption (report_date, raw_material_id, kitchen_id, quantity)
        #         VALUES (%s, %s, %s, %s)
        #         ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        #     """

        cursor = conn.cursor()
        cursor.execute(query, (material['raw_material_id'], type_id))
        stock = cursor.fetchone()

        if stock:
            metric = material["metric"]
            quantity = material["quantity"]
            # Metric conversion
            if metric == 'grams':
                quantity = float(quantity) / 1000  # Convert to kg
                metric = 'kg'
            elif metric == 'ml':
                quantity = float(quantity) / 1000  # Convert to liters
                metric = 'liter'
            new_quantity = float(stock[0]) - quantity

            cursor.execute(update_query, (new_quantity, material['raw_material_id'], type_id))
            cursor.execute(insert_consumption_query, (material['raw_material_id'], material["quantity"],
                           material["metric"], report_date, destination_type, type_id, material["quantity"]))
            conn.commit()

        cursor.close()


def get_purchase_years():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT YEAR(purchase_date) AS year FROM purchase_history ORDER BY year DESC;")
    years = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()
    return {"years": years}


def get_dish_recipe_raw_materials(dish_id):
    query = """
        SELECT 
            raw_materials.id as rid,
            raw_materials.name AS name,
            dish_raw_materials.quantity AS quantity,
            COALESCE(dish_raw_materials.metric, raw_materials.metric) AS metric
        FROM 
            dish_raw_materials
        JOIN 
            raw_materials ON dish_raw_materials.raw_material_id = raw_materials.id
        WHERE 
            dish_raw_materials.dish_id = %s;
        """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (dish_id,))
    materials = cursor.fetchall()
    cursor.close()
    return materials


def get_raw_materials(dish_id):
    conn = get_db_connection()
    query = """SELECT raw_material_id, quantity, metric FROM dish_raw_materials WHERE dish_id = %s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id,))
    materials = cursor.fetchall()
    cursor.close()
    return materials


def get_prepared_dishes_today():
    query = """
    SELECT d.id, d.category as prepared_dish_category, d.name AS prepared_dish_name, k.kitchenname AS prepared_kitchen_name, kpd.prepared_quantity, kpd.available_quantity
    FROM kitchen_prepared_dishes kpd
    JOIN dishes d ON kpd.prepared_dish_id = d.id
    JOIN kitchen k ON kpd.prepared_in_kitchen = k.id
    WHERE prepared_on = %s
    """
    prepared_dishes = fetch_all(query, (get_current_date(),))
    return prepared_dishes


def get_all_prepared_dishes(prepared_date):
    query = """
    SELECT kpd.id, kpd.prepared_dish_id, kpd.prepared_quantity, kpd.available_quantity, kpd.prepared_in_kitchen, kpd.prepared_on,
        d.name AS dish_name, d.category AS dish_category, k.kitchenname AS kitchen_name
    FROM kitchen_prepared_dishes kpd
    JOIN dishes d ON kpd.prepared_dish_id = d.id
    JOIN kitchen k ON kpd.prepared_in_kitchen = k.id
    WHERE kpd.prepared_on=%s;
    """
    prepared_dishes = fetch_all(query, (prepared_date,))
    return prepared_dishes


# def update_stock_consumption(raw_material_id, stock_availability, estimated_stock_consumption, metric, source_type, source_id, date):
#     query = """
#         INSERT INTO raw_material_consumption (
#             raw_material_id, stock_availability, estimated_stock_consumption, metric, source_type, source_id, date
#         ) VALUES
#             (%s, %s, %s, %s, %s, %s, %s)
#         ON DUPLICATE KEY UPDATE
#             estimated_stock_consumption = estimated_stock_consumption + VALUES(estimated_stock_consumption),
#             stock_availability = VALUES(stock_availability);
#         """


def get_all_purchases():
    query = """
        SELECT
            ph.id,
            ph.vendor_id,
            v.vendor_name,
            ph.invoice_number,
            ph.raw_material_id,
            ph.raw_material_name,
            ph.quantity,
            ph.metric,
            ph.total_cost,
            ph.purchase_date,
            ph.storageroom_id,
            sr.storageroomname AS storageroom_name,
            ph.created_at
        FROM
            purchase_history ph
        JOIN
            vendor_list v ON ph.vendor_id = v.id
        JOIN
            storagerooms sr ON ph.storageroom_id = sr.id
        ORDER BY
            ph.created_at DESC
            """
    purchases = fetch_all(query)
    return purchases


def get_all_pending_payments():
    query = """
    SELECT
        vpt.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        vpt.invoice_number,
        vpt.outstanding_cost,
        vpt.total_paid,
        vpt.total_due,
        vpt.last_updated
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list AS vl ON vpt.vendor_id = vl.id
    WHERE
        vpt.total_due != 0;
    """
    payments = fetch_all(query)
    return payments


def get_all_pending_payments_vendor_cumulative():
    query = """
        SELECT
        vl.id AS vendor_id,
        vl.vendor_name,
        SUM(vpt.outstanding_cost) AS total_outstanding_cost,
        SUM(vpt.total_paid) AS total_paid,
        SUM(vpt.total_due) AS total_due,
        MAX(vpt.last_updated) AS last_updated
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list AS vl ON vpt.vendor_id = vl.id
    GROUP BY
        vl.id, vl.vendor_name
    HAVING
        total_due != 0;
    """
    payments = fetch_all(query)
    return payments


def get_payment_details_of_vendor_between_dates(vendor_id, from_date, to_date):
    query = """
    SELECT
        pr.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        pr.invoice_number,
        DATE_FORMAT(pr.purchase_date, '%Y-%m-%d') AS purchase_date,
        pr.mode_of_payment,
        pr.amount_paid,
        pr.paid_on
    FROM
        payment_records AS pr
    JOIN
        vendor_list AS vl ON pr.vendor_id = vl.id
    WHERE
        pr.vendor_id = %s
        AND pr.paid_on BETWEEN %s AND %s
    ORDER BY
    pr.paid_on ASC;
    """
    payments = fetch_all(query, (vendor_id, from_date, to_date))
    return payments


def get_payment_details_of_vendor(vendor_id):
    query = """
    SELECT
        vpt.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        vpt.invoice_number,
        vpt.outstanding_cost,
        vpt.total_paid,
        vpt.total_due,
        DATE_FORMAT(vpt.purchase_date, '%Y-%m-%d') AS purchase_date
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list AS vl ON vpt.vendor_id = vl.id
    WHERE
        vpt.total_due != 0 
        AND vpt.vendor_id = %s
    ORDER BY purchase_date;
    """
    payments = fetch_all(query, (vendor_id,))
    return payments


def get_storageroom_stock(destination_id=None, category=None):
    query = """
    SELECT
        sr.storageroomname,
        rm.name AS rawmaterial_name,
        rm.category AS category,
        srm.metric,
        srm.opening_stock,
        srm.incoming_stock,
        srm.outgoing_stock,
        srm.currently_available,
        COALESCE(ms.min_quantity, 0) AS minimum_required,
        GREATEST(0, COALESCE(ms.min_quantity, 0) - srm.currently_available) AS quantity_needed
    FROM
        inventory_stock AS srm
    JOIN
        storagerooms AS sr ON sr.id = srm.destination_id
        AND srm.destination_type = 'storageroom'
    JOIN
        raw_materials AS rm ON rm.id = srm.raw_material_id
    LEFT JOIN
        minimum_stock AS ms ON ms.destination_id = srm.destination_id 
        AND ms.raw_material_id = srm.raw_material_id
        AND ms.type = 'storageroom'
    WHERE rm.is_deleted=FALSE
    """

    params = []
    filters = []

    if destination_id:
        filters.append("srm.destination_id = %s")
        params.append(destination_id)

    if category and category.lower() != "all":
        filters.append("rm.category = %s")
        params.append(category)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY category ASC;"
    storage_stock = fetch_all(query, params)
    return storage_stock


def get_invoice_payment_details():
    query = """
    SELECT
        vpt.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        vpt.invoice_number,
        vpt.outstanding_cost,
        vpt.total_paid,
        vpt.total_due
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list AS vl ON vpt.vendor_id = vl.id
    """
    payments = fetch_all(query)
    return payments


def get_payment_record():
    query = """
    SELECT
        pr.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        pr.invoice_number,
        pr.mode_of_payment,
        pr.amount_paid,
        pr.paid_on
    FROM
        payment_records AS pr
    JOIN
        vendor_list AS vl ON pr.vendor_id = vl.id
    WHERE pr.paid_on = %s
        """
    payments = fetch_all(query, (get_current_date(),))
    return payments


def get_rawmaterial_transfer_history(transferred_date):
    query = """
    SELECT
        rm.name AS raw_material_name,
        rmt.quantity,
        rmt.metric,
        sr.storageroomname AS transferred_from,
        rmt.destination_type,
        CASE
            WHEN rmt.destination_type = 'kitchen' THEN k.kitchenname
            WHEN rmt.destination_type = 'restaurant' THEN r.restaurantname
            ELSE 'Unknown'
        END AS transferred_to,
        rmt.transferred_date
    FROM
        raw_material_transfer_details rmt
    JOIN
        raw_materials rm ON rmt.raw_material_id = rm.id
    JOIN
        storagerooms sr ON rmt.source_storage_room_id = sr.id
    LEFT JOIN
        kitchen k ON rmt.destination_type = 'kitchen' AND rmt.destination_id = k.id
    LEFT JOIN
        restaurant r ON rmt.destination_type = 'restaurant' AND rmt.destination_id = r.id
    WHERE
        DATE(rmt.transferred_date) = %s;
    """
    rawmaterial_transfer = fetch_all(query, (transferred_date,))
    return rawmaterial_transfer


def get_prepared_dishes_transfer_history(transferred_date):
    query = """
    SELECT
        k.kitchenname AS kitchen_name,
        r.restaurantname AS restaurant_name,
        d.category AS dish_category,
        d.name AS dish_name,
        pdt.quantity AS transferred_quantity,
        pdt.transferred_date AS transferred_on
    FROM
        prepared_dish_transfer pdt
    JOIN
        kitchen k ON pdt.source_kitchen_id = k.id
    JOIN
        restaurant r ON pdt.destination_restaurant_id = r.id
    JOIN
        dishes d ON pdt.dish_id = d.id
    WHERE
        DATE(pdt.transferred_date) = %s;
    """
    prepared_dishes_transfer = fetch_all(query, (transferred_date,))
    return prepared_dishes_transfer


# def get_storageroom_rawmaterial_quantity(storageroom_id, rawmaterial_id):
#     query = """
#     SELECT
#         storageroom_id, raw_material_id, quantity, metric
#     FROM storageroom_stock
#     WHERE storageroom_id=%s AND raw_material_id=%s"""
#     data = fetch_all(query, (storageroom_id, rawmaterial_id))
#     return data

def get_storageroom_rawmaterial_quantity(storageroom_id, rawmaterial_id):
    query = """
    SELECT
        destination_id as storageroom_id, raw_material_id, currently_available as quantity, metric
    FROM inventory_stock
    WHERE destination_type='storageroom' AND destination_id=%s AND raw_material_id=%s"""
    data = fetch_all(query, (storageroom_id, rawmaterial_id))
    return data


def get_total_cost_stats():
    data = [{'total_purchased_amount': 0, 'total_paid': 0, 'total_due': 0}]
    query = """
    SELECT
        IFNULL(SUM(outstanding_cost), 0) AS total_purchased_amount,
        IFNULL(SUM(total_paid), 0) AS total_paid,
        IFNULL(SUM(total_due), 0) AS total_due
    FROM `vendor_payment_tracker`;
    """
    cost_data = fetch_all(query)
    if cost_data:
        data = cost_data
    return data


def get_all_dishes():
    query = 'SELECT * FROM dishes ORDER BY id ASC'
    dishes = fetch_all(query)
    return dishes


def get_unique_dish_categories():
    query = 'SELECT DISTINCT(category) FROM dishes'
    dish_categories = fetch_all(query)
    return dish_categories


# Helper function to execute SELECT queries


def get_data(query, params=None):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        return result
    finally:
        connection.close()


def get_kitchen_inventory_stock():
    query = """
    SELECT
    k.kitchenname,
    rm.name AS rawmaterial_name,
    rm.category AS category,
    srm.metric,
    srm.opening_stock,
    srm.incoming_stock,
    srm.outgoing_stock,
    srm.currently_available,
    COALESCE(ms.min_quantity, 0) AS minimum_required,
    GREATEST(0, COALESCE(ms.min_quantity, 0) - srm.currently_available) AS quantity_needed
FROM
    inventory_stock AS srm
JOIN
    kitchen AS k ON k.id = srm.destination_id
    AND srm.destination_type = 'kitchen'  -- Ensure only kitchen stocks are fetched
JOIN
    raw_materials AS rm ON rm.id = srm.raw_material_id
LEFT JOIN
    minimum_stock AS ms ON ms.destination_id = srm.destination_id 
    AND ms.raw_material_id = srm.raw_material_id
    AND ms.type = 'kitchen'
ORDER BY 
    k.kitchenname, rm.name;
"""
    kitchen_inventory_stock = fetch_all(query)
    return kitchen_inventory_stock


def get_restaurant_inventory_stock():
    query = """
        SELECT
    r.restaurantname,
    rm.name AS rawmaterial_name,
    rm.category AS category,
    srm.metric,
    srm.opening_stock,
    srm.incoming_stock,
    srm.outgoing_stock,
    srm.currently_available,
    COALESCE(ms.min_quantity, 0) AS minimum_required,
    GREATEST(0, COALESCE(ms.min_quantity, 0) - srm.currently_available) AS quantity_needed
FROM
    inventory_stock AS srm
JOIN
    restaurant AS r ON r.id = srm.destination_id
    AND srm.destination_type = 'restaurant'  -- Ensure only restaurant stocks are fetched
JOIN
    raw_materials AS rm ON rm.id = srm.raw_material_id
LEFT JOIN
    minimum_stock AS ms ON ms.destination_id = srm.destination_id 
    AND ms.raw_material_id = srm.raw_material_id
    AND ms.type = 'restaurant'
ORDER BY 
    r.restaurantname, rm.name;
        """
    restaurant_inventory_stock = fetch_all(query)
    return restaurant_inventory_stock


def update_restaurant_stock(restaurant_id, dish_id, sold_quantity, sold_on):
    # try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch raw materials required for the given dish
    cursor.execute("""
        SELECT raw_material_id, quantity, metric
        FROM dish_raw_materials
        WHERE dish_id = %s
    """, (dish_id,))
    raw_materials = cursor.fetchall()
    # Calculate the total quantity needed for the sold dishes
    required_quantities = {}
    for material in raw_materials:
        total_quantity = material['quantity'] * sold_quantity
        raw_material_id = material['raw_material_id']

        # Convert grams to kilograms and milliliters to liters
        if material['metric'] == 'grams':
            total_quantity /= 1000  # Convert to kg
        elif material['metric'] == 'ml':
            total_quantity /= 1000  # Convert to liters
        if raw_material_id in required_quantities:
            required_quantities[raw_material_id] += total_quantity
        else:
            required_quantities[raw_material_id] = total_quantity
    # Update the restaurant inventory stock
    for raw_material_id, required_quantity in required_quantities.items():
        cursor.execute("""
            SELECT quantity, metric
            FROM restaurant_inventory_stock
            WHERE restaurant_id = %s AND raw_material_id = %s
        """, (restaurant_id, raw_material_id))
        stock = cursor.fetchone()
        if not stock:
            continue
        # Convert stock metric to match the required quantity
        available_quantity = stock['quantity']
        if stock['metric'] == 'grams':
            available_quantity /= 1000  # Convert to kg
            stock['metric'] = "kg"
        elif stock['metric'] == 'ml':
            available_quantity /= 1000  # Convert to liters
            stock['metric'] = "liter"
        # Calculate the new quantity after deduction
        new_quantity = available_quantity - required_quantity
        # Update the stock quantity in the database
        cursor.execute("""
            UPDATE restaurant_inventory_stock
            SET quantity = %s
            WHERE restaurant_id = %s AND raw_material_id = %s
        """, (new_quantity, restaurant_id, raw_material_id))
        cursor.execute("""
        INSERT INTO consumption (raw_material_id, quantity, metric, consumption_date, location_type, location_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);
        """, (raw_material_id, required_quantity, stock['metric'], sold_on, "restaurant", restaurant_id))

    # Commit the transaction
    conn.commit()
    print("Kitchen stock updated successfully.")

    # except mysql.connector.Error as err:
    #     print(f"Error: {err}")
    # finally:
    #     if conn.is_connected():
    #         cursor.close()
    #         conn.close()


def update_kitchen_stock(kitchen_id, dish_id, prepared_quantity, prepared_on):
    # try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch raw materials required for the given dish
    cursor.execute("""
        SELECT raw_material_id, quantity, metric
        FROM dish_raw_materials
        WHERE dish_id = %s
    """, (dish_id,))
    raw_materials = cursor.fetchall()
    # Calculate the total quantity needed for the prepared dishes
    required_quantities = {}
    for material in raw_materials:
        total_quantity = material['quantity'] * prepared_quantity
        raw_material_id = material['raw_material_id']

        # Convert grams to kilograms and milliliters to liters
        if material['metric'] == 'grams':
            total_quantity /= 1000  # Convert to kg
        elif material['metric'] == 'ml':
            total_quantity /= 1000  # Convert to liters

        if raw_material_id in required_quantities:
            required_quantities[raw_material_id] += total_quantity
        else:
            required_quantities[raw_material_id] = total_quantity
    # Update the kitchen inventory stock
    for raw_material_id, required_quantity in required_quantities.items():
        cursor.execute("""
            SELECT quantity, metric
            FROM kitchen_inventory_stock
            WHERE kitchen_id = %s AND raw_material_id = %s
        """, (kitchen_id, raw_material_id))
        stock = cursor.fetchone()
        if not stock:
            continue
        # Convert stock metric to match the required quantity
        available_quantity = stock['quantity']
        if stock['metric'] == 'grams':
            available_quantity /= 1000  # Convert to kg
            stock['metric'] = "kg"
        elif stock['metric'] == 'ml':
            available_quantity /= 1000  # Convert to liters
            stock['metric'] = "liter"
        # Calculate the new quantity after deduction
        new_quantity = available_quantity - required_quantity

        # Update the stock quantity in the database
        cursor.execute("""
            UPDATE kitchen_inventory_stock
            SET quantity = %s
            WHERE kitchen_id = %s AND raw_material_id = %s
        """, (new_quantity, kitchen_id, raw_material_id))
        cursor.execute("""
        INSERT INTO consumption (raw_material_id, quantity, metric, consumption_date, location_type, location_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        quantity = quantity + VALUES(quantity);
        """, (raw_material_id, required_quantity, stock['metric'], prepared_on, "kitchen", kitchen_id))

    # Commit the transaction
    conn.commit()
    print("Kitchen stock updated successfully.")

    # except mysql.connector.Error as err:
    #     print(f"Error: {err}")
    # finally:
    #     if conn.is_connected():
    #         cursor.close()
    #         conn.close()


def get_raw_material_by_id(rawmaterial_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM raw_materials WHERE id = %s', (rawmaterial_id,))
    material = cursor.fetchone()
    cursor.close()
    conn.close()
    return material


def get_raw_material_by_name(rawmaterial_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM raw_materials WHERE name = %s', (rawmaterial_name,))
    material = cursor.fetchone()
    cursor.close()
    conn.close()
    return material


def get_all_rawmaterials(only_not_deleted=True):
    query = 'SELECT * FROM raw_materials ORDER BY id ASC'
    if only_not_deleted:
        query = 'SELECT * FROM raw_materials WHERE is_deleted = FALSE ORDER BY id ASC'
    raw_materials = fetch_all(query)
    return raw_materials


def get_all_dish_categories():
    query = 'SELECT DISTINCT category from dishes'
    dish_categories = fetch_all(query)
    return dish_categories


def get_all_users():
    query = 'SELECT id, username, email, role, status from users'
    users = fetch_all(query)
    return users


def get_all_vendors(only_active=False):
    query = 'SELECT * from vendor_list ORDER BY id ASC'
    if only_active:
        query = 'SELECT * from vendor_list WHERE status="active" ORDER BY id ASC'
    vendors = fetch_all(query)
    return vendors


def update_user_password(new_encrypted_password, email):
    status = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('UPDATE users SET password = %s WHERE email = %s', (new_encrypted_password, email))
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        status = True
    except Exception as e:
        status = e
        logger.error(f"ERROR: {e}")
    return status


def get_purchase_record(date):
    query = """
    SELECT
        ph.id,
        v.vendor_name,
        ph.invoice_number,
        ph.raw_material_name,
        ph.quantity,
        ph.metric,
        ph.total_cost,
        sr.storageroomname AS storageroom_name,
        (SELECT SUM(total_cost) FROM purchase_history WHERE purchase_date = %s) AS total_purchase_amount
    FROM
        purchase_history ph
    JOIN
        vendor_list v ON ph.vendor_id = v.id
    JOIN
        storagerooms sr ON ph.storageroom_id = sr.id
    WHERE ph.purchase_date = %s
    ORDER BY
        ph.created_at DESC;
    """

    purchases = fetch_all(query, (date, date))
    total_purchase_amount = purchases[0]['total_purchase_amount'] if purchases else 0
    return purchases, total_purchase_amount


def get_purchase_records(vendor_id, from_date, to_date):
    purchase_query = """
    SELECT
        ph.invoice_number,
        v.vendor_name,
        SUM(ph.total_cost) AS total_cost,
        COUNT(ph.raw_material_name) AS item_count,
        sr.storageroomname AS storageroom_name,
        DATE_FORMAT(ph.purchase_date, '%Y-%m-%d') AS purchase_date
    FROM
        purchase_history ph
    JOIN
        vendor_list v ON ph.vendor_id = v.id
    JOIN
        storagerooms sr ON ph.storageroom_id = sr.id
    WHERE
        ph.purchase_date BETWEEN %s AND %s
        {vendor_filter}
    GROUP BY
        ph.invoice_number, v.vendor_name, sr.storageroomname, ph.purchase_date
    ORDER BY
        ph.purchase_date ASC;
    """

    vendor_total_query = """
    SELECT
        v.vendor_name,
        SUM(ph.total_cost) AS total_cost
    FROM
        purchase_history ph
    JOIN
        vendor_list v ON ph.vendor_id = v.id
    WHERE
        ph.purchase_date BETWEEN %s AND %s
        {vendor_filter}
    GROUP BY
        v.vendor_name
    ORDER BY
        total_cost DESC;
    """

    # Handling 'All' vendors by removing the vendor_id filter
    vendor_filter = "AND ph.vendor_id = %s" if vendor_id != "all" else ""

    purchase_query = purchase_query.format(vendor_filter=vendor_filter)
    vendor_total_query = vendor_total_query.format(vendor_filter=vendor_filter)

    # Define query parameters
    if vendor_id == "all":
        purchase_params = (from_date, to_date)
        vendor_total_params = (from_date, to_date)
    else:
        purchase_params = (from_date, to_date, vendor_id)
        vendor_total_params = (from_date, to_date, vendor_id)

    purchases = fetch_all(purchase_query, purchase_params)
    vendor_totals = fetch_all(vendor_total_query, vendor_total_params)

    return purchases, vendor_totals


def get_payment_records(vendor_id, from_date, to_date):
    payment_query = """
    SELECT
        ph.invoice_number,
        DATE_FORMAT(ph.purchase_date, '%Y-%m-%d') AS purchase_date,
        v.vendor_name,
        SUM(ph.amount_paid) AS amount_paid,
        DATE_FORMAT(ph.paid_on, '%Y-%m-%d') as paid_on
    FROM
        payment_records ph
    JOIN
        vendor_list v ON ph.vendor_id = v.id
    WHERE
        ph.paid_on BETWEEN %s AND %s
        {vendor_filter}
    GROUP BY
        ph.invoice_number, ph.purchase_date, v.vendor_name, ph.paid_on
    ORDER BY
        ph.paid_on ASC;
    """
    vendor_total_query = """
    SELECT
        v.vendor_name,
        SUM(pr.amount_paid) AS amount_paid
    FROM
        payment_records pr
    JOIN
        vendor_list v ON pr.vendor_id = v.id
    WHERE
        pr.paid_on BETWEEN %s AND %s
        {vendor_filter}
    GROUP BY
        v.vendor_name
    ORDER BY
        amount_paid DESC;
    """
    # Handling 'All' vendors by removing the vendor_id filter
    vendor_filter = "AND vendor_id = %s" if vendor_id != "all" else ""

    # Format the query dynamically
    payment_query = payment_query.format(vendor_filter=vendor_filter)
    vendor_total_query = vendor_total_query.format(vendor_filter=vendor_filter)

    # Define query parameters
    if vendor_id == "all":
        payment_params = (from_date, to_date)
        vendor_total_params = (from_date, to_date)
    else:
        payment_params = (from_date, to_date, vendor_id)
        vendor_total_params = (from_date, to_date, vendor_id)

    payments = fetch_all(payment_query, payment_params)
    vendor_totals = fetch_all(vendor_total_query, vendor_total_params)

    return payments, vendor_totals


def get_pending_payments_record(vendor_id):
    payment_query = """
    SELECT
        vpt.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        vpt.invoice_number,
        vpt.outstanding_cost,
        vpt.total_paid,
        vpt.total_due,
        DATE_FORMAT(vpt.purchase_date, '%Y-%m-%d') AS purchase_date
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list AS vl ON vpt.vendor_id = vl.id
    WHERE
        vpt.total_due != 0 
        {vendor_filter}
    ORDER BY
        purchase_date ASC;
    """
    vendor_total_query = """
    SELECT
        v.vendor_name,
        SUM(vpt.outstanding_cost) AS outstanding_cost,
        SUM(vpt.total_paid) AS total_paid,
        SUM(vpt.total_due) AS total_due
    FROM
        vendor_payment_tracker AS vpt
    JOIN
        vendor_list v ON vpt.vendor_id = v.id
    WHERE
        1=1 {vendor_filter}
    GROUP BY
        v.id
    ORDER BY
        total_due DESC;
    """
    # Handling 'All' vendors by removing the vendor_id filter
    vendor_filter = "AND vendor_id = %s" if vendor_id != "all" else ""

    # Format the query dynamically
    payment_query = payment_query.format(vendor_filter=vendor_filter)
    vendor_total_query = vendor_total_query.format(vendor_filter=vendor_filter)

    payment_params = None
    vendor_total_params = None
    # Define query parameters
    if vendor_id != "all":
        payment_params = (vendor_id,)
        vendor_total_params = (vendor_id,)
    pending_payments = fetch_all(payment_query, payment_params)
    vendor_totals = fetch_all(vendor_total_query, vendor_total_params)

    return pending_payments, vendor_totals


def get_payment_record_on_date(date):
    query = """
    SELECT
        pr.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        pr.invoice_number,
        pr.mode_of_payment,
        pr.amount_paid,
        (SELECT SUM(amount_paid) FROM payment_records WHERE paid_on = %s) AS total_paid_amount
    FROM
        payment_records AS pr
    JOIN
        vendor_list AS vl ON pr.vendor_id = vl.id
    WHERE pr.paid_on = %s
        """

    payments = fetch_all(query, (date, date))
    total_paid_amount = payments[0]['total_paid_amount'] if payments else 0

    return payments, total_paid_amount


def update_minimum_stock(destination_type, destination_id, min_stock_data):
    try:
        # Step 1: Fetch all existing records in one query
        existing_records_query = """
            SELECT raw_material_id, min_quantity 
            FROM minimum_stock 
            WHERE type = %s AND destination_id = %s
        """
        existing_records = execute_query(existing_records_query, (destination_type, destination_id))
        existing_records_dict = {row[0]: row[1] for row in existing_records} if existing_records else {}
        # Step 2: Prepare bulk UPDATE and INSERT data
        update_data = []
        insert_data = []

        for material_id, min_quantity in min_stock_data.items():
            material_id = int(material_id)
            min_quantity = max(round(min_quantity, 5), 0)  # Ensure 5 decimal points & no negatives
            if material_id in existing_records_dict:
                # If exists, prepare for UPDATE
                update_data.append((min_quantity, destination_type, destination_id, material_id))
            else:
                # If new, prepare for INSERT
                insert_data.append((destination_type, destination_id, material_id, min_quantity))

        # Step 3: Bulk UPDATE (if any)
        if update_data:
            update_query = """
                UPDATE minimum_stock 
                SET min_quantity = %s, updated_at = NOW()
                WHERE type = %s AND destination_id = %s AND raw_material_id = %s
            """
            execute_query(update_query, update_data, bulk=True)

            # Call `update_inventory_after_min_stock_change` for updated records
            for data in update_data:
                min_quantity, _, _, material_id = data  # Extract values
                update_inventory_after_min_stock_change(destination_type, destination_id, material_id, min_quantity)

        # Step 4: Bulk INSERT (if any)
        if insert_data:
            insert_query = """
                INSERT INTO minimum_stock (type, destination_id, raw_material_id, min_quantity) 
                VALUES (%s, %s, %s, %s)
            """
            execute_query(insert_query, insert_data, bulk=True)

            # Call `update_inventory_after_min_stock_change` for inserted records
            for data in insert_data:
                _, _, material_id, min_quantity = data  # Extract values
                update_inventory_after_min_stock_change(destination_type, destination_id, material_id, min_quantity)

        return True  # Success

    except Exception as e:
        logger.error(f"Error updating minimum stock: {str(e)}")
        return False  # Failure


def get_raw_materials_min_stock(destination_type, destination_id):
    query = """
        SELECT rm.id, rm.name, rm.category, rm.metric, COALESCE(ms.min_quantity, 0) AS min_quantity
        FROM raw_materials rm
        LEFT JOIN minimum_stock ms 
        ON rm.id = ms.raw_material_id AND ms.type = %s AND ms.destination_id = %s
        WHERE rm.is_deleted = FALSE
    """
    result = execute_query(query, (destination_type, destination_id))
    return [{"id": row[0], "name": row[1], "category": row[2], "metric": row[3], "min_quantity": float(row[4])} for row in result]


def get_raw_materials_stock_report(destination_type, destination_id, category):
    if destination_type == "storageroom":
        return get_storageroom_stock(destination_id, category)
    # You can add similar logic for kitchen and restaurant if needed
    return []


def update_inventory_after_min_stock_change(destination_type, destination_id, raw_material_id, new_min_quantity):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Update the minimum_quantity
    cursor.execute(
        """
        UPDATE inventory_stock 
        SET minimum_quantity = %s,
            quantity_needed = GREATEST(0, %s - currently_available)  -- Ensure non-negative quantity_needed
        WHERE destination_type = %s
          AND destination_id = %s
          AND raw_material_id = %s;
        """,
        (new_min_quantity, new_min_quantity, destination_type, destination_id, raw_material_id)
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_rawmaterial_category():
    conn = get_db_connection()
    query = """select distinct(category) as category from raw_materials order by category"""
    cursor = conn.cursor()
    cursor.execute(query)
    categories = cursor.fetchall()
    cursor.close()
    return categories


def get_transfer_raw_material_report(storageroom, destination_type, destination_id, transferred_date, transfer_id):
    if transfer_id == "total":
        base_query = """
            SELECT
                rm.name AS raw_material_name,
                rm.category,
                SUM(rmt.quantity) as quantity,
                rmt.metric,
                sr.storageroomname AS transferred_from,
                rmt.destination_type,
                CASE
                    WHEN rmt.destination_type = 'kitchen' THEN k.kitchenname
                    WHEN rmt.destination_type = 'restaurant' THEN r.restaurantname
                    ELSE 'Unknown'
                END AS transferred_to,
                DATE_FORMAT(rmt.transferred_date, '%Y-%m-%d') AS transferred_date
            FROM
                raw_material_transfer_details rmt
            JOIN
                raw_materials rm ON rmt.raw_material_id = rm.id
            JOIN
                storagerooms sr ON rmt.source_storage_room_id = sr.id
            LEFT JOIN
                kitchen k ON rmt.destination_type = 'kitchen' AND rmt.destination_id = k.id
            LEFT JOIN
                restaurant r ON rmt.destination_type = 'restaurant' AND rmt.destination_id = r.id
            WHERE
                sr.id = %s
                AND rmt.destination_type = %s
                AND rmt.destination_id = %s
                AND DATE(rmt.transferred_date) = %s
            GROUP BY
                rm.name, rm.category, rmt.metric, sr.storageroomname, rmt.destination_type, transferred_to, transferred_date;
            """
        params = [storageroom, destination_type, destination_id, transferred_date]
    else:
        base_query = """
        SELECT
            rm.name AS raw_material_name,
            rm.category,
            rmt.quantity,
            rmt.metric,
            sr.storageroomname AS transferred_from,
            rmt.destination_type,
            CASE
                WHEN rmt.destination_type = 'kitchen' THEN k.kitchenname
                WHEN rmt.destination_type = 'restaurant' THEN r.restaurantname
                ELSE 'Unknown'
            END AS transferred_to,
            DATE_FORMAT(rmt.transferred_date, '%Y-%m-%d') AS transferred_date,
            DATE_FORMAT(STR_TO_DATE(rmt.transfer_time, '%Y-%m-%d %H:%i:%S'), '%Y-%m-%d %I:%i:%S %p') AS transfer_time,
            rmt.transfer_id AS transfer_id
        FROM
            raw_material_transfer_details rmt
        JOIN
            raw_materials rm ON rmt.raw_material_id = rm.id
        JOIN
            storagerooms sr ON rmt.source_storage_room_id = sr.id
        LEFT JOIN
            kitchen k ON rmt.destination_type = 'kitchen' AND rmt.destination_id = k.id
        LEFT JOIN
            restaurant r ON rmt.destination_type = 'restaurant' AND rmt.destination_id = r.id
        WHERE
            sr.id = %s
            AND rmt.destination_type = %s
            AND rmt.destination_id = %s
            AND DATE(rmt.transferred_date) = %s
        """

        params = [storageroom, destination_type, destination_id, transferred_date]

        if transfer_id == "all":
            # No additional filtering for transfer_id
            pass
        else:
            # Filter for a specific transfer_id
            base_query += " AND rmt.transfer_id = %s"
            params.append(transfer_id)

    # Execute the query with dynamic parameters
    rawmaterial_transfer = fetch_all(base_query, tuple(params))
    logger.debug(f"rawmaterial_transfer {rawmaterial_transfer}")
    return rawmaterial_transfer


def get_contact_details():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT name, contact_number, address FROM contact_details')
    contact_details = cursor.fetchone() or {"name": "", "contact_number": "", "address": ""}
    cursor.close()
    conn.close()
    return contact_details


def delete_user_from_db(user_id):
    query = 'DELETE FROM users where id=%s'
    return execute_query(query, (user_id,))


def delete_rawmaterial_from_db(rawmaterial_id):
    query = 'UPDATE raw_materials SET is_deleted = TRUE WHERE id = %s'
    return execute_query(query, (rawmaterial_id,))


def get_cumulative_purchase_record_invoice_wise(date):
    query = """
    SELECT
        ph.invoice_number,
        ph.vendor_id,
        v.vendor_name,
        ph.storageroom_id,
        sr.storageroomname AS storageroom_name,
        SUM(ph.total_cost) AS total_purchase_amount,
        ph.purchase_date as purchase_date
    FROM
        purchase_history ph
    JOIN
        vendor_list v ON ph.vendor_id = v.id
    JOIN
        storagerooms sr ON ph.storageroom_id = sr.id
    WHERE
        ph.purchase_date = %s
    GROUP BY
        ph.invoice_number, ph.vendor_id, ph.storageroom_id
    ORDER BY
        MIN(ph.created_at) ASC;
    """

    cumulative_purchases = fetch_all(query, (date,))
    return cumulative_purchases
