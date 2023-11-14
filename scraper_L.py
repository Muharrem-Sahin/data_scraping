from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
from queue import Queue
import concurrent.futures
import pandas as pd
import threading
import requests
import psycopg2
import json
import time
import csv
import os

# Setup Selenium WebDriver
def setup_driver():

    options = Options()
    options.headless = True
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    #time.sleep(1)
    return driver
    

# Teardown Selenium WebDriver
def teardown_driver(driver):
    driver.quit()

# Fetch Page Source
def fetch_page_source(driver, product_url):
    full_url = "https://www.lcwaikiki.com" + product_url
    driver.get(full_url)
    driver.implicitly_wait(2)
    return driver.page_source

# Parse HTML
def parse_html(html_doc):
    return BeautifulSoup(html_doc, 'html.parser')

# Scrape Gender Details
def scrape_gender_details(soup):
    gender_div = soup.find_all('span', itemprop='name')
    return [' '.join(element.text.split()) for element in gender_div] if gender_div else []

# Scrape Product Option ID
def scrape_product_optionid(soup):
    div_tag = soup.find('div', {'id': 'productSliderPhotos', 'optionid': True})
    return div_tag['optionid'] if div_tag else "No optionid found."

# Scrape Product Info
def scrape_product_info(soup):
    product_code_div = soup.find('div', class_='product-code')
    if product_code_div:
        product_code_text = product_code_div.text.strip().replace('Ürün Kodu:', '').strip()
        words = product_code_text.split()
        if len(words) >= 2 and words[-2] != '-':
            last_two_words = " ".join(words[-2:])
            return last_two_words
        elif len(words) >= 1:
            last_word = words[-1]
            return last_word
        else:
            return "Product color not found."
    else:
        return "Product code information not found."

# Download Image
def download_image(image_url, folder_path, cursor, conn, relation):
    os.makedirs(folder_path, exist_ok=True)
    headers_param = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }
    response = requests.get(image_url, headers=headers_param)
    if response.status_code == 200:
        image_path = os.path.join(folder_path, image_url.split('/')[-1])
        with open(image_path, 'wb') as file:
            file.write(response.content)

        with open(image_path, 'rb') as file:
            blob_data = file.read()
            table_name = "image_data_large"
            cursor.execute(f"""
                INSERT INTO {table_name} (blob, path, relation)
                VALUES (%s, %s, %s)
            """, (psycopg2.Binary(blob_data), image_path, relation))
            conn.commit()

        return image_path
    else:
        print(f"Failed to download {image_url}")
        return None

# Download Images into a structured directory
def download_images(image_details, gender, product_info, option_id, cursor, conn, relation, base_folder_path='downloaded_images'):
    folder_structure = os.path.join(base_folder_path, *gender, product_info, option_id)
    large_folder_path = os.path.join(folder_structure, 'large')
    
    for large_image_url in image_details:
        path_L = download_image(large_image_url, large_folder_path, cursor, conn, relation)

# Scrape Image Details
def scrape_image_details(soup):
    product_images_div = soup.find('div', class_='product-images-desktop hidden-xs')
    image_details = []
    if product_images_div:
        img_tags = product_images_div.find_all('img', attrs={'onclick': True})
        image_details = [img['data-large-img-url'] for img in img_tags]
    return image_details

# Scrape Product Option Info
def scrape_product_option_info(soup):
    option_info_div = soup.find('div', class_='col-md-6 option-info nopadding')
    if option_info_div:
        option_features = option_info_div.find_all('p')
        return [feature.text.strip() for feature in option_features]
    return ["Option information not found."]

# Scrape Product Details
def scrape_product_details(product_url, cursor, conn, relation, download_images_flag=True, base_folder_path='downloaded_images'):
    driver = setup_driver()
    html_doc = fetch_page_source(driver, product_url)
    soup = parse_html(html_doc)
    
    gender_details = scrape_gender_details(soup)
    product_info = scrape_product_info(soup)
    option_id = scrape_product_optionid(soup)
    product_option_info = scrape_product_option_info(soup)
    
    if download_images_flag:
        image_details = scrape_image_details(soup)
        download_images(image_details, gender_details, product_info, option_id, cursor, conn, relation, base_folder_path)

    teardown_driver(driver)

    return gender_details, product_info, option_id, product_option_info, product_url

# Write Header to CSV
def write_header_to_csv(filename, header):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)

# Append Data to CSV
def append_to_csv(filename, data):
    
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

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

# Veritabanına veri kaydetme fonksiyonu
def save_to_database(conn, cursor, data):
    cursor.execute("""
        INSERT INTO feature_data (p_key, json_type, color, free_text)
        VALUES (%s, %s, %s, %s)
    """, (data[2], json.dumps(data[0]), data[1], json.dumps(data[3])))
    conn.commit()

# Scrape ve CSV'ye kaydetme fonksiyonunu güncelle
def scrape_and_save(product_url, conn, cursor, last_p_key, current_relation, base_folder_path='downloaded_images'):
    # İndirme işlemini burada yapacak şekilde ayarlayın.
    details = scrape_product_details(product_url, cursor, conn, current_relation, download_images_flag=True, base_folder_path=base_folder_path)
    append_to_csv("output.csv", details)
    
    # p_key değiştiyse relation değerini artır
    if last_p_key != details[2]:  # details[2] ürünün option ID'sidir, p_key olarak varsayıyorum.
        current_relation += 1
    last_p_key = details[2]  # Sonraki karşılaştırma için mevcut p_key'i sakla
    
    save_to_database(conn, cursor, details)

    return last_p_key, current_relation

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
    number_of_workers = 5
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
    main()
