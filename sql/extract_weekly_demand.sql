-- =============================================================================
-- Demand Forecasting: Weekly Order Extraction Query
-- Database: NeonDB (PostgreSQL)
-- Schema: ecom
-- Description: Aggregates order item transactions into weekly demand by category
--              and product, computing units demanded, gross revenue, order frequency,
--              and average realized selling prices.
-- =============================================================================

SELECT 
    DATE_TRUNC('week', o.created_at)::date AS week_start,
    c.category_id,
    c.category_name,
    p.product_id,
    p.product_name,
    SUM(oi.qty) AS units_demanded,
    ROUND(SUM(oi.line_total)::numeric, 2) AS total_revenue,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(AVG(oi.unit_price)::numeric, 2) AS avg_unit_price
FROM ecom.orders o
JOIN ecom.order_items oi ON o.order_id = oi.order_id
JOIN ecom.product_variants pv ON oi.variant_id = pv.variant_id
JOIN ecom.products p ON pv.product_id = p.product_id
JOIN ecom.categories c ON p.category_id = c.category_id
WHERE o.status IN ('paid', 'delivered', 'shipped')
GROUP BY 1, 2, 3, 4, 5
ORDER BY week_start ASC, c.category_name ASC, units_demanded DESC;