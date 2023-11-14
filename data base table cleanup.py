import psycopg2

# Veritabanına bağlan
conn = psycopg2.connect(database="dbtest", user="postgres", password="muharrem628fb", host="localhost", port="5432")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS image_data_medium;")
cursor.execute("DROP TABLE IF EXISTS image_data_large;")
cursor.execute("DROP TABLE IF EXISTS feature_data;")
conn.commit()

# Bağlantıyı kapat
cursor.close()
conn.close()



    #options = Options()
    #options.headless = True
    #driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    #driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    #driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    #driver = webdriver.Chrome(options=options)
    #driver = webdriver.Chrome(ChromeDriverManager().install())
    #driver = webdriver.Chrome(service=service(ChromeDriverManager().install()),options=options)
