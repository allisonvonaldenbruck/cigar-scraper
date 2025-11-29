CREATE TABLE join_data AS
SELECT s.sku as s_sku,
	s.title as s_title,
	s.size as s_size,
	s.qty as s_qty,
	s.price as s_price,
	s.msrp as s_msrp,
	s.url as s_url,
	i.sku as i_sku,
	i.title as i_title,
	i.size as i_size,
	i.name as i_name,
	i.qty as i_qty,
	i.price as i_price,
	i.msrp as i_msrp,
	i.url as i_url
FROM smoke_inn_data as s
	JOIN equivalent_skus as e
	ON e.smoke_sku=s.sku
		JOIN international_data as i
	 	ON e.inter_sku=i.sku;
