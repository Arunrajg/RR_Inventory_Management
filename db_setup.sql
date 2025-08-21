CREATE DATABASE rrinventorymanagement;

USE rrinventorymanagement;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    superuser BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventoryname VARCHAR(100) NOT NULL,
    inventorycode VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(1000) NOT NULL
);

CREATE TABLE kitchen (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kitchenname VARCHAR(100) NOT NULL,
    kitchencode VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(1000) NOT NULL
);

CREATE TABLE restaurant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurantname VARCHAR(100) NOT NULL,
    restaurantcode VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(1000) NOT NULL
);

CREATE TABLE raw_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    metric ENUM('kg', 'liters') NOT NULL
);

CREATE TABLE dishes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE dish_raw_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dish_id INT NOT NULL,
    raw_material_id INT NOT NULL,
    quantity FLOAT(5, 2) NOT NULL,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id) ON DELETE CASCADE,
    UNIQUE KEY (dish_id, raw_material_id)
);

CREATE TABLE raw_material_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_material_id INT NOT NULL,
    date DATE NOT NULL,
    quantity FLOAT(5, 2) NOT NULL,
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id) ON DELETE CASCADE
);

CREATE TABLE raw_material_allocation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dish_id INT NOT NULL,
    raw_material_id INT NOT NULL,
    date DATE NOT NULL,
    quantity FLOAT(5, 2) NOT NULL,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id) ON DELETE CASCADE
);

CREATE TABLE sales_report (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dish_id INT NOT NULL,
    date DATE NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE
);