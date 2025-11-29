SELECT inter_sku, COUNT(inter_sku)
FROM joined_clean_data
GROUP BY inter_sku
HAVING COUNT(inter_sku) > 1
ORDER BY COUNT(inter_sku) DESC