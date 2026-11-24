-- Repair this runnable starter using the rules in DATA.md.
SELECT
    o.period,
    o.channel,
    p.category,
    COUNT(*) AS completed_orders,
    SUM(o.gross_pence) AS gross_pence,
    SUM(r.refund_pence) AS refund_pence,
    SUM(o.gross_pence - r.refund_pence) AS net_revenue_pence,
    SUM(p.unit_cost_pence) AS product_cost_pence,
    SUM(o.fulfilment_cost_pence) AS fulfilment_cost_pence,
    SUM(o.gross_pence - r.refund_pence - p.unit_cost_pence
        - o.fulfilment_cost_pence) AS contribution_pence,
    COUNT(*) AS refunded_orders
FROM orders AS o
JOIN products AS p ON p.product_id = o.product_id
JOIN refunds AS r ON r.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY o.period, o.channel, p.category
ORDER BY o.period, o.channel, p.category;
