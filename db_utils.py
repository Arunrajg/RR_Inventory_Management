import mysql.connector
from mysql.connector import Error
from encryption import encrypt_message, decrypt_message
import logging

# Set up logger
logging.basicConfig(level=logging.DEBUG,  # You can change the log level to INFO, ERROR, etc.
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()          # Log to console
                    ])
logger = logging.getLogger()

# Database Configuration
DB_CONFIG = {
    "host": "db",
    "user": "root",
    "password": "password",
    "database": "rrinventorymanagement"
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
