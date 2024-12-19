import mysql.connector
from mysql.connector import Error
from encryption import encrypt_message, decrypt_message

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
        print(f"Error: {e}")
        return None

# Generic function to execute INSERT/UPDATE/DELETE queries


def execute_query(query, params=None):
    print(query)
    connection = get_db_connection()
    print(connection)
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return True
    except Error as e:
        print(f"Database Error: {e}")
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
        print(f"Database Error: {e}")
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
    print(f"user -- {user}")
    return user


def get_inventory_by_code(inventory_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM inventory WHERE inventorycode = %s', (inventory_code,))
    inventory = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"inventory -- {inventory}")
    return inventory


def get_kitchen_by_code(kitchen_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM kitchen WHERE kitchencode = %s', (kitchen_code,))
    kitchen = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"kitchen -- {kitchen}")
    return kitchen


def get_restaurant_by_code(restaurant_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM restaurant WHERE restaurantcode = %s', (restaurant_code,))
    restaurant = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"restaurant -- {restaurant}")
    return restaurant


def get_all_inventories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM inventory')
    inventories = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"inventories -- {inventories}")
    return inventories


def get_all_kitchens():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM kitchen')
    kitchens = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"kitchens -- {kitchens}")
    return kitchens


def get_all_restaurants():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM restaurant')
    restaurants = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"restaurants -- {restaurants}")
    return restaurants


def get_raw_material_by_name(material_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM raw_materials WHERE name = %s', (material_name,))
    material = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"material -- {material}")
    return material


def get_all_rawmaterials():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM raw_materials')
    raw_materials = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"raw_materials -- {raw_materials}")
    return raw_materials
