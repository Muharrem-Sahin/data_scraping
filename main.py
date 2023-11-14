from scraper import Scraper
from scrape_website import scrape_website
import csv
import pandas as pd
import psycopg2
from queue import Queue
import threading
import csv
import pandas as pd


def write_header_to_csv(filename, header):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)

def append_to_csv(filename, data):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def scrape_and_save(product_url):
    scraper = Scraper()
    details = scraper.scrape_product_details(product_url)
    append_to_csv("output.csv", details)

    

# PostgreSQL veritabanı tablosu oluşturma fonksiyonu
def create_database_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_data (
            id SERIAL PRIMARY KEY,
            p_key VARCHAR,
            json_type JSON,
            color VARCHAR,
            free_text JSON
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_data_large (
            id SERIAL PRIMARY KEY,
            blob BYTEA,
            path VARCHAR,
            relation INTEGER   
        );
    """)


def main():
    header = ["Gender Details", "Product Info", "Option ID", "Product Option Info", "Full URL"]
    write_header_to_csv("output.csv", header)

    # Veritabanı bağlantısını kur
    conn = psycopg2.connect(database="dbtest", user="postgres", password="muharrem628fb", host="localhost", port="5432")
    cursor = conn.cursor()

    # Veritabanı tablolarını oluştur
    create_database_tables(cursor)

    # Ürün URL'lerini oku
    file_path = 'link-ıd.csv'
    df = pd.read_csv(file_path, encoding='utf-8')
    data_list = df.iloc[:, 1].tolist()

    last_p_key = None  # İlk p_key değeri için None olarak başlat
    current_relation = 1
    # İş parçacıkları arasında paylaşılan veri yapısı (Queue)
    shared_data_queue = Queue()

    # İş parçacıklarının çalışacağı fonksiyon
    def worker():
        nonlocal last_p_key, current_relation
        while True:
            url = shared_data_queue.get()
            if url is None:
                break

            last_p_key, current_relation = scrape_and_save(url, conn, cursor, last_p_key, current_relation)
            shared_data_queue.task_done()

    # İş parçacıkları oluştur
    number_of_workers = 10
    threads = []
    for _ in range(number_of_workers):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    # İş parçacıklarına işleri dağıt
    for url in data_list:
        shared_data_queue.put(url)

    # Tüm işleri bitir
    shared_data_queue.join()

    # İş parçacıklarını durdur
    for _ in range(number_of_workers):
        shared_data_queue.put(None)
    for thread in threads:
        thread.join()

    # Bağlantıyı kapat
    cursor.close()
    conn.close()

 
if __name__ == '__main__':
    #Create an instance of the scrape_website class
    scraper_instance = scrape_website()

    # Call the method on the instance
    data_list = scraper_instance.scrape_website("https://www.lcwaikiki.com/tr-TR/TR/kadin/giyim")

    main()
