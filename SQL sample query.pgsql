SELECT * FROM image_data_large;
SELECT * FROM image_data_medium;
SELECT * FROM feature_data;

SELECT * FROM image_data_medium WHERE relation = (SELECT id FROM feature_data WHERE p_key = CAST(3111827 AS VARCHAR));
SELECT * FROM image_data_medium WHERE relation = (SELECT id FROM feature_data WHERE id = 5);

SELECT relation FROM image_data_large;
SELECT path FROM image_data_medium;

SELECT json_type->1 FROM feature_data;

--NSERT into image_data_medium (blob,path,relation) VALUES ("\\xFFD8FFE000104" ,downloaded_images\Kadın\Plaj Kıyafeti\Optik Beyaz\3111827\medium\l_20231-s3eg98z8-ffb_u.jpg,5)
--FOREIGN KEY (relation) REFERENCES feature_data(id)