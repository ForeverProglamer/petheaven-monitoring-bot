CREATE EVENT IF NOT EXISTS unused_products_deletion
ON SCHEDULE EVERY 1 DAY
DO
    DELETE FROM products
    WHERE id NOT IN (SELECT product_id FROM monitoring_list);