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
