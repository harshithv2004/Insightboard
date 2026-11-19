-- InsightBoard Database Schema
-- Run this file once in MySQL Workbench or CLI:
--   mysql -u root -p < sql/schema.sql

CREATE DATABASE IF NOT EXISTS insightboard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE insightboard;

-- --------------------------------------------------------
-- Customers
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS Customers (
    customer_id   INT           PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  UNIQUE,
    region        VARCHAR(50)   NOT NULL,
    signup_date   DATE          NOT NULL
);

-- --------------------------------------------------------
-- Products
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS Products (
    product_id   INT            PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100)   NOT NULL,
    category     VARCHAR(60)    NOT NULL,
    unit_price   DECIMAL(12,2)  NOT NULL,
    CHECK (unit_price >= 0)
);

-- --------------------------------------------------------
-- Orders
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS Orders (
    order_id    INT   PRIMARY KEY AUTO_INCREMENT,
    customer_id INT   NOT NULL,
    order_date  DATE  NOT NULL,
    region      VARCHAR(50) NOT NULL,
    status      ENUM('Completed','Pending','Cancelled') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- --------------------------------------------------------
-- OrderItems
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderItems (
    order_item_id INT            PRIMARY KEY AUTO_INCREMENT,
    order_id      INT            NOT NULL,
    product_id    INT            NOT NULL,
    quantity      INT            NOT NULL,
    unit_price    DECIMAL(12,2)  NOT NULL,
    CHECK (quantity > 0),
    CHECK (unit_price >= 0),
    FOREIGN KEY (order_id)   REFERENCES Orders(order_id)
        ON DELETE CASCADE  ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- --------------------------------------------------------
-- Indexes for reporting performance
-- --------------------------------------------------------
CREATE INDEX idx_orders_date     ON Orders(order_date);
CREATE INDEX idx_orders_region   ON Orders(region);
CREATE INDEX idx_orders_status   ON Orders(status);
CREATE INDEX idx_orders_customer ON Orders(customer_id);
CREATE INDEX idx_oi_product      ON OrderItems(product_id);
CREATE INDEX idx_oi_order        ON OrderItems(order_id);
