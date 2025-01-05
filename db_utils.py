import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import os

# Set up logger
logging.basicConfig(level=logging.DEBUG,  # You can change the log level to INFO, ERROR, etc.
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        # logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()          # Log to console
                    ])
logger = logging.getLogger()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),  # Default to 'db' if not set
    "user": os.getenv("DB_USER", "root"),  # Default to 'root' if not set
    "password": os.getenv("DB_PASSWORD", "password"),  # Default to 'password' if not set
    "database": os.getenv("DB_DATABASE", "rrinventorymanagement")  # Default to 'rrinventorymanagement' if not set
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.debug(f"Error: {e}")
        return None

# Generic function to execute INSERT/UPDATE/DELETE queries


def execute_query(query, params=None):
    logger.debug(query)
    connection = get_db_connection()
    logger.debug(connection)
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return True
    except Error as e:
        logger.debug(f"Database Error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

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
        logger.debug(f"Database Error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"user -- {user}")
    return user


def get_storageroom_by_name(storageroom_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM storagerooms WHERE storageroomname = %s', (storageroom_name,))
    storageroom_name = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"storageroom_name -- {storageroom_name}")
    return storageroom_name


def get_kitchen_by_name(kitchen_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM kitchen WHERE kitchenname = %s', (kitchen_name,))
    kitchen = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"kitchen -- {kitchen}")
    return kitchen


def get_restaurant_by_name(restaurant_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM restaurant WHERE restaurantname = %s', (restaurant_name,))
    restaurant = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"restaurant -- {restaurant}")
    return restaurant


def get_all_storagerooms():
    query = 'SELECT * FROM storagerooms ORDER BY id ASC'
    storagerooms = fetch_all(query)
    logger.debug(f"storagerooms -- {storagerooms}")
    return storagerooms


def get_all_kitchens():
    query = 'SELECT * FROM kitchen ORDER BY id ASC'
    kitchens = fetch_all(query)
    logger.debug(f"kitchens -- {kitchens}")
    return kitchens


def get_all_restaurants():
    query = 'SELECT * FROM restaurant ORDER BY id ASC'
    restaurants = fetch_all(query)
    logger.debug(f"restaurants -- {restaurants}")
    return restaurants


def get_prepared_dishes_today():
    query = """
    SELECT d.id, d.category as prepared_dish_category, d.name AS prepared_dish_name, k.kitchenname AS prepared_kitchen_name, kpd.prepared_quantity
    FROM kitchen_prepared_dishes kpd
    JOIN dishes d ON kpd.prepared_dish_id = d.id
    JOIN kitchen k ON kpd.prepared_in_kitchen = k.id
    WHERE prepared_on = %s
    """
    prepared_dishes = fetch_all(query, (datetime.now().strftime("%Y-%m-%d"),))
    logger.debug(f"prepared_dishes -- {prepared_dishes}")
    return prepared_dishes


def get_all_prepared_dishes():
    query = """
    SELECT kpd.id, kpd.prepared_dish_id, kpd.prepared_quantity, kpd.prepared_in_kitchen, kpd.prepared_on,
        d.name AS dish_name, d.category AS dish_category, k.kitchenname AS kitchen_name
    FROM kitchen_prepared_dishes kpd
    JOIN dishes d ON kpd.prepared_dish_id = d.id
    JOIN kitchen k ON kpd.prepared_in_kitchen = k.id;

    """
    prepared_dishes = fetch_all(query)
    logger.debug(f"prepared_dishes -- {prepared_dishes}")
    return prepared_dishes


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
    logger.debug(f"purchases -- {purchases}")
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
    logger.debug(f"payments -- {payments}")
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
    logger.debug(f"payments cumulative -- {payments}")
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
        vpt.last_updated
    FROM 
        vendor_payment_tracker AS vpt
    JOIN 
        vendor_list AS vl ON vpt.vendor_id = vl.id
    WHERE 
        vpt.total_due != 0 AND vpt.vendor_id=%s
    """
    payments = fetch_all(query, (vendor_id,))
    logger.debug(f"vendor due payments -- {payments}")
    return payments


def get_storageroom_stock():
    query = """
    SELECT 
        sr.id as storageroom_id, 
        sr.storageroomname, 
        rm.id as rawmaterial_id, 
        rm.name as rawmaterial_name, 
        srm.quantity, 
        srm.metric
    FROM 
        storageroom_stock AS srm
    JOIN 
        storagerooms AS sr ON sr.id = srm.storageroom_id
    JOIN 
        raw_materials AS rm ON rm.id = srm.raw_material_id;
    """
    storage_stock = fetch_all(query)
    logger.debug(f"storage_stock -- {storage_stock}")
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
    logger.debug(f"vendor due payments -- {payments}")
    return payments


def get_payment_record():
    query = """
    SELECT 
        pr.id AS payment_id,
        vl.id AS vendor_id,
        vl.vendor_name,
        pr.invoice_number,
        pr.amount_paid,
        pr.paid_on
    FROM 
        payment_records AS pr
    JOIN 
        vendor_list AS vl ON pr.vendor_id = vl.id
        """
    payments = fetch_all(query)
    logger.debug(f"vendor due payments -- {payments}")
    return payments


def get_rawmaterial_transfer_history():
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
        restaurant r ON rmt.destination_type = 'restaurant' AND rmt.destination_id = r.id;
    """
    rawmaterial_transfer = fetch_all(query)
    logger.debug(f"rawmaterial_transfer -- {rawmaterial_transfer}")
    return rawmaterial_transfer


def get_all_dishes():
    query = 'SELECT * FROM dishes ORDER BY id ASC'
    dishes = fetch_all(query)
    logger.debug(f"dishes -- {dishes}")
    return dishes


def get_unique_dish_categories():
    query = 'SELECT DISTINCT(category) FROM dishes'
    dish_categories = fetch_all(query)
    logger.debug(f"dish_categories -- {dish_categories}")
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
            rm.id, 
            rm.name as rawmaterial_name, 
            kis.quantity, 
            kis.metric
        FROM 
            kitchen_inventory_stock AS kis
        JOIN 
            kitchen AS k ON k.id = kis.kitchen_id
        JOIN 
            raw_materials AS rm ON rm.id = kis.raw_material_id;
        """
    kitchen_inventory_stock = fetch_all(query)
    logger.debug(f"kitchen_inventory_stock -- {kitchen_inventory_stock}")
    return kitchen_inventory_stock


def get_restaurant_inventory_stock():
    query = """
        SELECT r.id AS restaurant_id,
            r.restaurantname AS restaurant_name,
            rm.id AS raw_material_id,
            rm.name AS raw_material_name,
            ris.quantity,
            ris.metric
        FROM 
            restaurant_inventory_stock as ris
        JOIN 
            restaurant r ON ris.id = r.id
        JOIN 
            raw_materials rm ON ris.raw_material_id = rm.id;
        """
    restaurant_inventory_stock = fetch_all(query)
    logger.debug(f"restaurant_inventory_stock -- {restaurant_inventory_stock}")
    return restaurant_inventory_stock


def get_raw_material_by_name(material_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM raw_materials WHERE name = %s', (material_name,))
    material = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"material -- {material}")
    return material


def get_all_rawmaterials():
    query = 'SELECT * FROM raw_materials ORDER BY id ASC'
    raw_materials = fetch_all(query)
    logger.debug(f"raw_materials -- {raw_materials}")
    return raw_materials


def get_all_dish_categories():
    query = 'SELECT DISTINCT category from dishes'
    dish_categories = fetch_all(query)
    logger.debug(f"dish_categories -- {dish_categories}")
    return dish_categories


def get_all_vendors():
    query = 'SELECT * from vendor_list'
    vendors = fetch_all(query)
    logger.debug(f"vendors -- {vendors}")
    return vendors


def update_user_password(new_encrypted_password, email):
    status = False
    try:
        conn = get_db_connection()
        logger.debug(f"conn {conn}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute('UPDATE users SET password = %s WHERE email = %s', (new_encrypted_password, email))
        conn.commit()
        rows_affected = cursor.rowcount
        logger.debug(f"Rows affected: {rows_affected}")
        cursor.close()
        conn.close()
        status = True
    except Exception as e:
        status = e
        logger.debug(f"ERROR: {e}")
    return status
