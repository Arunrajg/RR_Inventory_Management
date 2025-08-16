CREATE DATABASE IF NOT EXISTS dharaniinvmgmt;

USE dharaniinvmgmt;

CREATE TABLE IF NOT EXISTS `contact_details` (
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `contact_number` varchar(100) NOT NULL,
  `address` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `raw_materials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `metric` enum('kg','liter','ml','grams','unit') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `category` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `restaurant` (
  `id` int NOT NULL AUTO_INCREMENT,
  `restaurantname` varchar(100) NOT NULL,
  `address` varchar(1000) NOT NULL,
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `storagerooms` (
  `id` int NOT NULL AUTO_INCREMENT,
  `storageroomname` varchar(100) NOT NULL,
  `address` varchar(1000) NOT NULL,
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `storageroomname` (`storageroomname`)
);

CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL DEFAULT 'user',
  `status` varchar(50) NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
);

CREATE TABLE IF NOT EXISTS `vendor_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_name` varchar(100) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address` varchar(255) NOT NULL,
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `kitchen` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kitchenname` varchar(100) NOT NULL,
  `address` varchar(1000) NOT NULL,
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `inventory_stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_type` enum('storageroom','kitchen','restaurant') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `destination_id` int NOT NULL,
  `raw_material_id` int NOT NULL,
  `metric` enum('kg','liter','unit') NOT NULL,
  `opening_stock` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `incoming_stock` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `outgoing_stock` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `currently_available` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `minimum_quantity` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `quantity_needed` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_inventory` (`destination_type`,`destination_id`,`raw_material_id`),
  KEY `raw_material_id` (`raw_material_id`),
  CONSTRAINT `inventory_stock_ibfk_1` FOREIGN KEY (`raw_material_id`) REFERENCES `raw_materials` (`id`)
);

CREATE TABLE IF NOT EXISTS `minimum_stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` enum('storageroom','kitchen','restaurant') NOT NULL,
  `destination_id` int NOT NULL,
  `raw_material_id` int NOT NULL,
  `min_quantity` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_min_stock` (`type`,`destination_id`,`raw_material_id`),
  KEY `raw_material_id` (`raw_material_id`),
  CONSTRAINT `minimum_stock_ibfk_1` FOREIGN KEY (`raw_material_id`) REFERENCES `raw_materials` (`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `miscellaneous_items` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_of_expense VARCHAR(255),
    sub_category VARCHAR(100),
    cost DECIMAL(10, 2) NOT NULL,
    notes TEXT,
    restaurant_id INT,
    branch_manager VARCHAR(100),
    status VARCHAR(10) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_restaurant_id (restaurant_id),
    CONSTRAINT fk_misc_restaurant FOREIGN KEY (restaurant_id)
        REFERENCES restaurant(id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE TABLE IF NOT EXISTS `payment_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_id` int NOT NULL,
  `invoice_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `purchase_date` date NOT NULL,
  `amount_paid` decimal(35,2) NOT NULL,
  `mode_of_payment` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `paid_on` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `vendor_id` (`vendor_id`),
  CONSTRAINT `payment_records_ibfk_1` FOREIGN KEY (`vendor_id`) REFERENCES `vendor_list` (`id`)
);

CREATE TABLE IF NOT EXISTS `purchase_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_id` int NOT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `raw_material_id` int NOT NULL,
  `raw_material_name` varchar(100) NOT NULL,
  `quantity` decimal(25,5) NOT NULL,
  `metric` enum('kg','liter','ml','grams','unit') NOT NULL,
  `total_cost` decimal(35,2) NOT NULL,
  `purchase_date` date NOT NULL,
  `storageroom_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_purchase_entry` (`vendor_id`,`invoice_number`,`raw_material_id`,`purchase_date`,`storageroom_id`),
  KEY `fk_raw_material_id` (`raw_material_id`),
  KEY `fk_storageroom_id` (`storageroom_id`),
  CONSTRAINT `fk_raw_material_id` FOREIGN KEY (`raw_material_id`) REFERENCES `raw_materials` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_storageroom_id` FOREIGN KEY (`storageroom_id`) REFERENCES `storagerooms` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE IF NOT EXISTS `raw_material_transfer_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `source_storage_room_id` int NOT NULL,
  `destination_type` enum('kitchen','restaurant') NOT NULL,
  `destination_id` int NOT NULL,
  `raw_material_id` int NOT NULL,
  `quantity` decimal(25,5) NOT NULL,
  `metric` enum('kg','grams','liter','ml','unit') NOT NULL,
  `transferred_date` date NOT NULL,
  `transfer_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `transfer_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `destination_id` (`destination_id`),
  KEY `raw_material_id` (`raw_material_id`),
  CONSTRAINT `raw_material_transfer_details_ibfk_3` FOREIGN KEY (`raw_material_id`) REFERENCES `raw_materials` (`id`)
);

CREATE TABLE IF NOT EXISTS `vendor_payment_tracker` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_id` int NOT NULL,
  `invoice_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `purchase_date` date DEFAULT NULL,
  `outstanding_cost` decimal(35,2) NOT NULL DEFAULT '0.00',
  `total_paid` decimal(35,2) NOT NULL DEFAULT '0.00',
  `total_due` decimal(35,2) GENERATED ALWAYS AS ((`outstanding_cost` - `total_paid`)) STORED,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_vendor_invoice` (`vendor_id`,`invoice_number`,`purchase_date`),
  CONSTRAINT `fk_vendor_id` FOREIGN KEY (`vendor_id`) REFERENCES `vendor_list` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
);
