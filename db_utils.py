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


def get_all_inventories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM inventory')
    inventories = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"inventories -- {inventories}")
    return inventories
# # Check if the provided password matches the stored encrypted password


# def check_password(stored_encrypted_password, provided_password):
#     decrypted_password = decrypt_message(stored_encrypted_password, ENCRYPTION_KEY)
#     return decrypted_password == provided_password

# # Encrypt password before saving it to the database


# def encrypt_password(password):
#     return encrypt_message(password, ENCRYPTION_KEY)
