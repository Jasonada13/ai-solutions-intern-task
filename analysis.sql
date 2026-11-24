-- Repair this starter to follow the channel summary rules in DATA.md.
SELECT
    o.channel,
    COUNT(*) AS completed_orders,
    SUM(o.gross_pence) AS gross_pence,
    SUM(r.refund_pence) AS refund_pence,
    SUM(o.gross_pence) - SUM(r.refund_pence) AS net_pence,
    COUNT(DISTINCT o.order_id) AS refunded_orders,
    COUNT(DISTINCT o.order_id) / COUNT(*) AS refund_rate
FROM orders AS o
JOIN refunds AS r ON r.order_id = o.order_id
WHERE o.status = 'completed'
  AND o.ordered_at >= :period_start
  AND o.ordered_at < :period_end
GROUP BY o.channel
ORDER BY o.channel;
