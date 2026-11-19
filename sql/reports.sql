-- InsightBoard — Reference SQL Queries
-- Run each block independently in MySQL Workbench to validate results.
-- These are the exact queries used by the Flask application (parameterized in Python).

USE insightboard;

-- ============================================================
-- Query 1: Executive KPIs (completed orders only)
-- ============================================================
SELECT
    COALESCE(SUM(oi.quantity * oi.unit_price), 0)  AS total_revenue,
    COUNT(DISTINCT o.order_id)                      AS total_orders,
    COUNT(DISTINCT o.customer_id)                   AS unique_customers,
    COALESCE(SUM(oi.quantity), 0)                   AS units_sold,
    COALESCE(
        SUM(oi.quantity * oi.unit_price)
        / NULLIF(COUNT(DISTINCT o.order_id), 0), 0) AS avg_order_value
FROM Orders o
JOIN OrderItems oi ON oi.order_id = o.order_id
WHERE o.status = 'Completed';

-- ============================================================
-- Query 2: Monthly revenue trend
-- ============================================================
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m')  AS month,
    SUM(oi.quantity * oi.unit_price)    AS revenue
FROM Orders o
JOIN OrderItems oi ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month;

-- ============================================================
-- Query 3: Top 10 products by revenue
-- ============================================================
SELECT
    p.product_name,
    p.category,
    SUM(oi.quantity)                 AS units_sold,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM OrderItems oi
JOIN Orders   o ON o.order_id   = oi.order_id
JOIN Products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- ============================================================
-- Query 4: Regional performance
-- ============================================================
SELECT
    o.region,
    COUNT(DISTINCT o.order_id)       AS completed_orders,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM Orders o
JOIN OrderItems oi ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY o.region
ORDER BY revenue DESC;

-- ============================================================
-- Query 5: Repeat customers (more than 1 completed order)
-- ============================================================
SELECT
    c.customer_id,
    c.customer_name,
    c.region,
    COUNT(DISTINCT o.order_id)       AS order_count,
    SUM(oi.quantity * oi.unit_price) AS total_spend
FROM Customers c
JOIN Orders    o  ON o.customer_id = c.customer_id
JOIN OrderItems oi ON oi.order_id  = o.order_id
WHERE o.status = 'Completed'
GROUP BY c.customer_id, c.customer_name, c.region
HAVING COUNT(DISTINCT o.order_id) > 1
ORDER BY total_spend DESC;

-- ============================================================
-- Query 6: Month-over-month growth (CTE + window function)
-- ============================================================
WITH monthly_sales AS (
    SELECT
        DATE_FORMAT(o.order_date, '%Y-%m') AS month,
        SUM(oi.quantity * oi.unit_price)   AS revenue
    FROM Orders o
    JOIN OrderItems oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
),
sales_with_previous AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS previous_revenue
    FROM monthly_sales
)
SELECT
    month,
    revenue,
    previous_revenue,
    ROUND(
        100.0 * (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0),
    2) AS growth_percentage
FROM sales_with_previous
ORDER BY month;

-- ============================================================
-- Query 7: Revenue by category
-- ============================================================
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    SUM(oi.quantity)                 AS units_sold,
    COUNT(DISTINCT o.order_id)       AS order_count
FROM OrderItems oi
JOIN Orders   o ON o.order_id   = oi.order_id
JOIN Products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY revenue DESC;
