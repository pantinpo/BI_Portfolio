-- Raw sales export, one row per order line. Cleaning is done in clean_data.py.
-- sqlite3 -header -csv data/source/ecommerce.db < extract_sales.sql > data/raw/sales_raw.csv

WITH customer_orders AS (
    SELECT
        order_id,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_id) AS order_number
    FROM orders
)

SELECT
    o.order_id AS "Order ID",
    oi.line_item AS "Line Item",
    o.order_date AS "Order Date",
    o.customer_id AS "Customer ID",
    CASE WHEN co.order_number = 1 THEN 'New' ELSE 'Returning' END AS "Customer Type",
    c.country AS "Country",
    c.region AS "Region",
    o.ship_state AS "State",
    o.ship_city AS "City",
    o.channel AS "Channel",
    o.traffic_source AS "Traffic Source",
    o.payment_method AS "Payment Method",
    p.category AS "Category",
    p.sub_category AS "Sub-Category",
    p.product_name AS "Product",
    oi.sku AS "SKU",
    oi.unit_price AS "Unit Price",
    oi.quantity AS "Quantity",
    COALESCE(pr.discount, '0') AS "Discount %",
    COALESCE(pr.promotion_name, 'None') AS "Promotion",
    oi.gross_sales AS "Gross Sales",
    oi.discount_amount AS "Discount Amount",
    oi.net_sales AS "Net Sales",
    oi.cost AS "Cost",
    oi.profit AS "Profit",
    CASE WHEN r.order_id IS NOT NULL THEN 'Returned' ELSE o.status END AS "Order Status"
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN customer_orders co ON co.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN products p ON p.sku = oi.sku
LEFT JOIN promotions pr ON pr.promotion_id = o.promotion_id
LEFT JOIN returns r ON r.order_id = oi.order_id AND r.line_item = oi.line_item
ORDER BY o.order_id, oi.line_item;
