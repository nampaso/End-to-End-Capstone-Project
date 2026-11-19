-- 1. Branch revenue, gross profit, margin %, and AOV (completed orders)
SELECT
    branch,
    COUNT(DISTINCT transaction_id) AS completed_orders,
    ROUND(SUM(gross_revenue_kes), 2) AS net_revenue_kes,
    ROUND(SUM(gross_profit_kes), 2) AS gross_profit_kes,
    ROUND(SUM(gross_profit_kes) * 100.0 / SUM(gross_revenue_kes), 2) AS gross_margin_pct,
    ROUND(AVG(gross_revenue_kes), 2) AS avg_order_value_kes
FROM transactions
WHERE order_status = 'Completed'
GROUP BY branch
ORDER BY net_revenue_kes DESC;

-- 2. Product category performance using JOIN
SELECT
    p.category,
    COUNT(DISTINCT t.transaction_id) AS completed_orders,
    SUM(t.quantity) AS units_sold,
    ROUND(SUM(t.gross_revenue_kes), 2) AS net_revenue_kes,
    ROUND(SUM(t.gross_profit_kes), 2) AS gross_profit_kes,
    ROUND(SUM(t.gross_profit_kes) * 100.0 / SUM(t.gross_revenue_kes), 2) AS gross_margin_pct
FROM transactions t
JOIN products p ON t.product_id = p.product_id
WHERE t.order_status = 'Completed'
GROUP BY p.category
ORDER BY net_revenue_kes DESC;

-- 3. Repeat high-value customers using GROUP BY and HAVING
SELECT
    c.customer_id,
    c.city,
    c.loyalty_tier,
    COUNT(t.transaction_id) AS completed_orders,
    ROUND(SUM(t.gross_revenue_kes), 2) AS total_spend_kes,
    ROUND(AVG(t.gross_revenue_kes), 2) AS avg_order_value_kes
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.order_status = 'Completed'
GROUP BY c.customer_id, c.city, c.loyalty_tier
HAVING COUNT(t.transaction_id) >= 4
   AND SUM(t.gross_revenue_kes) >= 150000
ORDER BY total_spend_kes DESC;

-- 4. Quarter-over-quarter branch revenue growth using LAG window function
WITH quarterly_sales AS (
    SELECT
        branch,
        quarter,
        COUNT(DISTINCT transaction_id) AS completed_orders,
        ROUND(SUM(gross_revenue_kes), 2) AS net_revenue_kes
    FROM transactions
    WHERE order_status = 'Completed'
    GROUP BY branch, quarter
)
SELECT
    branch,
    quarter,
    completed_orders,
    net_revenue_kes,
    LAG(net_revenue_kes) OVER (PARTITION BY branch ORDER BY quarter) AS prev_quarter_revenue_kes,
    ROUND(
        (net_revenue_kes - LAG(net_revenue_kes) OVER (PARTITION BY branch ORDER BY quarter)) * 100.0
        / LAG(net_revenue_kes) OVER (PARTITION BY branch ORDER BY quarter),
        2
    ) AS qoq_growth_pct
FROM quarterly_sales
ORDER BY branch, quarter;

-- 5. Top 2 products per category by revenue using RANK window function
WITH ranked_products AS (
    SELECT
        p.category,
        p.product_name,
        SUM(t.quantity) AS units_sold,
        ROUND(SUM(t.gross_revenue_kes), 2) AS net_revenue_kes,
        RANK() OVER (PARTITION BY p.category ORDER BY SUM(t.gross_revenue_kes) DESC) AS revenue_rank
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    WHERE t.order_status = 'Completed'
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    revenue_rank,
    product_name,
    units_sold,
    net_revenue_kes
FROM ranked_products
WHERE revenue_rank <= 2
ORDER BY category, revenue_rank;

-- 6. Monthly net revenue and return rate by payment method
SELECT
    order_month,
    payment_method,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders,
    ROUND(SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS return_rate_pct,
    ROUND(SUM(CASE WHEN order_status = 'Completed' THEN gross_revenue_kes ELSE 0 END), 2) AS net_revenue_kes
FROM transactions
GROUP BY order_month, payment_method
ORDER BY order_month, net_revenue_kes DESC;
