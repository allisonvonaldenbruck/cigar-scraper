CREATE TABLE joined_clean_data AS
SELECT *
FROM international_data_clean_2
JOIN equivalent_skus 
	ON equivalent_skus.inter_sku=international_data_clean_2.sku
	JOIN smokin_data_clean_2
	ON equivalent_skus.smokin_sku=smokin_data_clean_2.sku
