from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import re
import threading
import csv
from selenium import webdriver
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Lock oluştur
lock = threading.Lock()
data_list = []  
# Fonksiyonu oluştur



def get_data(url, page_index):
    driver = webdriver.Chrome()
    driver.get(url)
    html_doc = driver.page_source
    soup = BeautifulSoup(html_doc, 'html.parser')
    with lock:
        with open("link-ıd.csv", "a", newline='', encoding="utf-8") as file:
            url_list = []
            product_cards = soup.find_all('div', class_='product-card product-card--one-of-4')
            for product_card in product_cards:
                a_tags = product_card.find_all('a', attrs={'data-optionid': True})
                for a_tag in a_tags:
                    data_optionid = a_tag['data-optionid']
                    data_title = a_tag.get('title', '')
                    href = a_tag['href']
                    url_list.append(href)
                       
                    csv_writer = csv.writer(file)
                    csv_writer.writerow([data_optionid, href])
    
    driver.quit()
    return url_list



# Ana işlem
if __name__ == "__main__":
    url = "https://www.lcwaikiki.com/tr-TR/TR/kadin/giyim"
    driver = webdriver.Chrome()
    driver.get(url)
    html_doc = driver.page_source
    soup = BeautifulSoup(html_doc, 'html.parser')
    product_grid_div = soup.find('div', class_='product-grid')
    paginator_span = product_grid_div.find('span', class_='paginator__button-page-indicator')

    if paginator_span:
        text = paginator_span.text
        string_deger = text
        sonuc = re.search(r'\((.*?)\/(.*?)\)', string_deger)
        if sonuc:
            after_slash = int(sonuc.group(2))  
            print("Sonraki kısım:", after_slash)
    driver.quit()

    number_of_workers = 1
    threads = []

    for i in range(1, after_slash):
        thread = threading.Thread(target=get_data, args=(f"{url}?PageIndex={i}", i))
        threads.append(thread)
        thread.start()

        if i % number_of_workers == 0 or i == after_slash - 1:
            for thread in threads:
                thread.join()
            threads = []
