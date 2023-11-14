import psycopg2
from PIL import Image
from io import BytesIO

# Veritabanına bağlan
conn = psycopg2.connect(database="dbtest", user="postgres", password="muharrem628fb", host="localhost", port="5432")
cursor = conn.cursor()

# Gerçek tablo adı ve koşulu kullanarak SQL sorgusunu güncelleyin
cursor.execute("SELECT blob FROM image WHERE id = 1")
bytea_data = cursor.fetchone()[0]

# Bytea verisini bir bayt akışına dönüştürün
bytea_stream = BytesIO(bytea_data)

# Bayt akışını bir PIL Image nesnesine dönüştürün
image = Image.open(bytea_stream)

# Kaydedilecek dosya yolunu belirtin ve JPEG formatı kullanın
output_path = "C:/Users/mhr62/OneDrive/Masaüstü/LCW/asdfgh/output.jpg"

# Image nesnesini belirtilen yol ile bir JPEG dosyasına kaydedin
image.save(output_path, "JPEG")

# Veritabanı bağlantısını kapat
conn.close()

