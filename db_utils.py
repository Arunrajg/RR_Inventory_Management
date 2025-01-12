import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from decimal import Decimal
import os
import pytz

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


def get_dish_details_from_category(category_name, dish_name):
    query = 'SELECT id FROM dishes WHERE category =%s and name=%s'
    dish_id = fetch_all(query, (category_name, dish_name))
    logger.debug(f"dish_id -- {dish_id}")
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
    logger.debug(f"sales_report_data -- {sales_report_data}")
    return sales_report_data


def get_dish_recipe(dish_id):
    query = 'SELECT dish_id, raw_material_id, quantity, metric FROM dish_raw_materials WHERE dish_id =%s'
    recipe = fetch_all(query, (dish_id,))
    logger.debug(f"recipe -- {recipe}")
    return recipe


def check_dish_transferred(dish_id, prepared_date, restaurant_id):
    result = None
    conn = get_db_connection()
    query = """SELECT source_kitchen_id FROM prepared_dish_transfer WHERE dish_id = %s AND transferred_date = %s and destination_restaurant_id=%s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id, prepared_date, restaurant_id))
    result = cursor.fetchone()
    logger.debug(f"transfer result {result}")
    cursor.close()
    return result


def check_prepared_dish(dish_id, prepared_date, restaurant_id):
    result = None
    conn = get_db_connection()
    logger.debug(f"check preapred {dish_id} {prepared_date} {restaurant_id}")
    query = """SELECT id FROM kitchen_prepared_dishes WHERE prepared_dish_id = %s AND prepared_on = %s and prepared_in_kitchen=%s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id, prepared_date, restaurant_id))
    result = cursor.fetchone()
    logger.debug(f"check_prepared_dish result {result}")
    cursor.close()
    return result


def get_restaurant_consumption_report(restaurant_id, report_date):
    query = """
    SELECT 
        r.restaurantname AS restaurant_name,
        rm.name AS raw_material_name,
        ris.metric AS metric,
        SUM(rmtd.quantity) AS transferred_quantity,
        SUM(c.quantity) AS estimated_consumed_quantity,
        (SUM(rmtd.quantity) - COALESCE(SUM(c.quantity), 0)) AS remaining_quantity
    FROM 
        restaurant_inventory_stock ris
    JOIN 
        restaurant r ON ris.restaurant_id = r.id
    JOIN 
        raw_materials rm ON ris.raw_material_id = rm.id
    LEFT JOIN 
        raw_material_transfer_details rmtd ON rmtd.destination_id = ris.restaurant_id AND rmtd.raw_material_id = ris.raw_material_id AND DATE(rmtd.transferred_date) = %s
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
    logger.debug(f"restaurant consumption result {result}")
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
    logger.debug(f"kitchen consumption result {result}")
    cursor.close()
    return result


def subtract_raw_materials(raw_materials, destination_type, type_id, report_date):
    conn = get_db_connection()
    logger.debug(f"raw_materials {raw_materials} destination_type {destination_type} type_id {type_id}")
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

        logger.debug(f"query {query}")
        cursor = conn.cursor()
        cursor.execute(query, (material['raw_material_id'], type_id))
        stock = cursor.fetchone()
        logger.debug(f"stock {stock}")
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
            logger.debug(f"new_quantity {new_quantity}")
            cursor.execute(update_query, (new_quantity, material['raw_material_id'], type_id))
            cursor.execute(insert_consumption_query, (material['raw_material_id'], material["quantity"],
                           material["metric"], report_date, destination_type, type_id, material["quantity"]))
            conn.commit()

        cursor.close()


def get_raw_materials(dish_id):
    conn = get_db_connection()
    query = """SELECT raw_material_id, quantity, metric FROM dish_raw_materials WHERE dish_id = %s"""
    cursor = conn.cursor()
    cursor.execute(query, (dish_id,))
    materials = cursor.fetchall()
    cursor.close()
    logger.debug(f"materialsss {materials}")
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


def get_prepared_dishes_transfer_history():
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
        dishes d ON pdt.dish_id = d.id;
    """
    prepared_dishes_transfer = fetch_all(query)
    logger.debug(f"prepared_dishes_transfer -- {prepared_dishes_transfer}")
    return prepared_dishes_transfer


def get_storageroom_rawmaterial_quantity(storageroom_id, rawmaterial_id):
    query = """
    SELECT
        storageroom_id, raw_material_id, quantity, metric
    FROM storageroom_stock
    WHERE storageroom_id=%s AND raw_material_id=%s"""
    data = fetch_all(query, (storageroom_id, rawmaterial_id))
    logger.debug(f"ddddaaata {data}")
    return data


def get_total_cost_stats():
    query = """
    SELECT
        IFNULL(SUM(outstanding_cost), 0) AS total_purchased_amount,
        IFNULL(SUM(total_paid), 0) AS total_paid,
        IFNULL(SUM(total_due), 0) AS total_due
    FROM `vendor_payment_tracker`;
    """
    data = fetch_all(query)
    logger.debug(f"total cost {data}")
    return data


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
            restaurant r ON ris.restaurant_id = r.id
        JOIN
            raw_materials rm ON ris.raw_material_id = rm.id;
        """
    restaurant_inventory_stock = fetch_all(query)
    logger.debug(f"restaurant_inventory_stock -- {restaurant_inventory_stock}")
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
    logger.debug(f"raw_materials for dish {dish_id} {raw_materials} qty {sold_quantity}")
    # Calculate the total quantity needed for the prepared dishes
    required_quantities = {}
    for material in raw_materials:
        logger.debug(f"mm {material}")
        total_quantity = material['quantity'] * float(sold_quantity)
        logger.debug(f"{material['quantity']} * {sold_quantity}, {total_quantity}")
        raw_material_id = material['raw_material_id']

        # Convert grams to kilograms and milliliters to liters
        if material['metric'] == 'grams':
            total_quantity /= 1000  # Convert to kg
            logger.debug("grams")
        elif material['metric'] == 'ml':
            total_quantity /= 1000  # Convert to liters
            logger.debug("liter")
        logger.debug(f"tq {total_quantity}")
        if raw_material_id in required_quantities:
            required_quantities[raw_material_id] += total_quantity
        else:
            required_quantities[raw_material_id] = total_quantity
    logger.debug(f"required quantities {required_quantities}")
    # Update the kitchen inventory stock
    for raw_material_id, required_quantity in required_quantities.items():
        cursor.execute("""
            SELECT quantity, metric
            FROM restaurant_inventory_stock
            WHERE restaurant_id = %s AND raw_material_id = %s
        """, (restaurant_id, raw_material_id))
        stock = cursor.fetchone()
        if not stock:
            logger.debug(f"Stock not found for raw_material_id: {raw_material_id} in restaurant_id: {restaurant_id}")
            continue
        logger.debug(f"stockkkkkkk {stock}")
        # Convert stock metric to match the required quantity
        available_quantity = stock['quantity']
        if stock['metric'] == 'grams':
            available_quantity /= 1000  # Convert to kg
            stock['metric'] = "kg"
        elif stock['metric'] == 'ml':
            available_quantity /= 1000  # Convert to liters
            stock['metric'] = "liter"
        logger.debug(f"stockkkkkkk after {stock} {available_quantity} {required_quantity}")
        # Calculate the new quantity after deduction
        new_quantity = available_quantity - required_quantity
        logger.debug(f"new new {new_quantity}")
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
    logger.debug(f"raw_materials for dish {dish_id} {raw_materials} qty {prepared_quantity}")
    # Calculate the total quantity needed for the prepared dishes
    required_quantities = {}
    for material in raw_materials:
        logger.debug(f"mm {material}")
        total_quantity = material['quantity'] * float(prepared_quantity)
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
    logger.debug(f"required quantities {required_quantities}")
    # Update the kitchen inventory stock
    for raw_material_id, required_quantity in required_quantities.items():
        cursor.execute("""
            SELECT quantity, metric
            FROM kitchen_inventory_stock
            WHERE kitchen_id = %s AND raw_material_id = %s
        """, (kitchen_id, raw_material_id))
        stock = cursor.fetchone()
        if not stock:
            logger.debug(f"Stock not found for raw_material_id: {raw_material_id} in kitchen_id: {kitchen_id}")

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
