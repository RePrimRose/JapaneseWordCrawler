from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import csv
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import requests
import random

def configure_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36'
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def load_completed_links(csv_file_name):
    completed_links = set()
    if os.path.exists(csv_file_name):
        with open(csv_file_name, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header if present
            for row in reader:
                if len(row) > 0:
                    completed_links.add(row[0])
    return completed_links

def save_data_to_csv(file_name, data, headers=None):
    write_header = not os.path.exists(file_name)
    with open(file_name, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if write_header and headers:
            writer.writerow(headers)
        writer.writerow(data)

def extract_kanji_details(page_soup, level, kanji_title):
    h3_tag = page_soup.find('h3', text=lambda t: t and '1. 기본 정보' in t)
    if not h3_tag:
        return None
    
    details = {'kanji': kanji_title, 'meanings': [], 'on_yomi': [], 'kun_yomi': [], 'pronunciations': [], 'level': level}
    ul_tag = h3_tag.find_next_sibling('ul')
    if ul_tag:
        for li in ul_tag.find_all('li'):
            b_tags = li.find_all('b')
            if b_tags:
                category = b_tags[0].get_text(strip=True).replace('"', '').strip()
                if len(b_tags) > 1:
                    values = [b_tag.get_text(strip=True).replace('"', '').strip() for b_tag in b_tags[1:]]
                else:
                    values = re.split(r'[.,]', b_tags[0].get_text(strip=True).replace('"', '').replace('의미', '').replace('음독', '').replace('훈독', '').strip())
                values = [v.strip() for v in values if v.strip()]

                if '의미' in category:
                    if values:
                        pronunciation = re.sub(r'[".]', '', values[0]).strip()  # Extract the first value as pronunciation
                        details['pronunciations'].append(pronunciation)
                        if len(values) > 1:
                            meanings = [re.sub(r'[".]', '', v).strip() for v in values[1:]]  # Remaining values are meanings
                            details['meanings'].extend(meanings)
                elif '음독' in category:
                    details['on_yomi'].extend(values)
                elif '훈독' in category:
                    details['kun_yomi'].extend(values)
    return details

def download_image(page_soup, kanji_title, image_save_path):
    img_tag = page_soup.find('img')
    if img_tag and 'src' in img_tag.attrs:
        img_url = img_tag['src']
        try:
            img_data = requests.get(img_url).content
            img_filename = f"{kanji_title}.jpg"
            img_filepath = os.path.join(image_save_path, img_filename)
            with open(img_filepath, 'wb') as img_file:
                img_file.write(img_data)
            print(f"Image saved for {kanji_title} at {img_filepath}")
        except requests.RequestException as e:
            print(f"Failed to download image for {kanji_title}: {e}")

def extract_vocab_details(page_soup, level):
    vocab_details = []
    ul_tags = page_soup.find_all('ul')
    for ul_tag in ul_tags:
        for ruby in ul_tag.find_all('ruby'):
            word = ruby.text.strip()
            furigana = ruby.rt.text.strip() if ruby.rt else ''
            meaning = ruby.next_sibling
            if meaning and isinstance(meaning, str):
                meaning = meaning.strip().strip(',')
            else:
                meaning = ''
            vocab_details.append({'word': word, 'furigana': furigana, 'meaning': meaning, 'level': level})
    return vocab_details

def scrape_links(csv_files, driver, completed_links_kanji, completed_links_vocab, kanji_csv_file_name, vocab_csv_file_name, image_save_path):
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            print(f"CSV file {csv_file} not found. Skipping.")
            continue

        level = csv_file.split('.')[0]
        with open(csv_file, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header if present
            for row in reader:
                link = row[0]
                if not link:
                    print("Empty link found. Skipping.")
                    continue
                if link in completed_links_kanji and link in completed_links_vocab:
                    continue

                try:
                    start_time = time.time()
                    driver.get(link)
                    time.sleep(random.uniform(5, 10))  # Reduced sleep time for better efficiency
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'title')))

                    page_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    kanji_title = re.sub(r'[0-9]+\.', '', page_soup.find('title').get_text(strip=True)).replace('「', '').replace('」', '').replace(':: 일본어 한자 공부방', '').strip()
                    details = extract_kanji_details(page_soup, level, kanji_title)
                    
                    if details:
                        download_image(page_soup, kanji_title, image_save_path)
                        save_data_to_csv(kanji_csv_file_name, [
                            link,
                            details['kanji'],
                            json.dumps(details['meanings'], ensure_ascii=False),
                            json.dumps(details['on_yomi'], ensure_ascii=False),
                            json.dumps(details['kun_yomi'], ensure_ascii=False),
                            json.dumps(details['pronunciations'], ensure_ascii=False),
                            details['level']
                        ], headers=['Link', 'Kanji', 'Meanings', 'On Yomi', 'Kun Yomi', 'Pronunciations', 'Level'])

                    # Extract vocabulary data
                    vocab_data_list = extract_vocab_details(page_soup, level)

                    # Save vocabulary data to CSV immediately
                    for vocab in vocab_data_list:
                        save_data_to_csv(vocab_csv_file_name, [
                            link,
                            vocab['word'],
                            vocab['furigana'],
                            vocab['meaning'],
                            vocab['level']
                        ], headers=['Link', 'Word', 'Furigana', 'Meaning', 'Level'])

                    elapsed_time = time.time() - start_time
                    print(f"Processed link from {level}: {link} | Time taken: {elapsed_time:.2f} seconds")
                except Exception as e:
                    print(f"Error processing link {link}: {e}")

def save_final_csv(file_name, details_list, headers):
    headers_without_link = [header for header in headers if header != 'Link']
    details_list_without_link = [detail[1:] for detail in details_list]  # Remove the first element (Link)
    with open(file_name, mode='w', newline='', encoding='utf-8-sig') as final_file:
        writer = csv.writer(final_file)
        writer.writerow(headers_without_link)
        for details in details_list_without_link:
            writer.writerow(details)

def main():
    csv_files = ['N1.csv', 'N2.csv', 'N3.csv', 'N4.csv', 'N5.csv']
    kanji_csv_file_name = 'detailed_scraped_kanji_data.csv'
    vocab_csv_file_name = 'detailed_scraped_vocab_data.csv'
    image_save_path = 'japanese_kanji_pictures'
    os.makedirs(image_save_path, exist_ok=True)

    # Ensure CSV files are created if they don't exist
    if not os.path.exists(kanji_csv_file_name):
        save_data_to_csv(kanji_csv_file_name, [], headers=['Link', 'Kanji', 'Meanings', 'On Yomi', 'Kun Yomi', 'Pronunciations', 'Level'])
    if not os.path.exists(vocab_csv_file_name):
        save_data_to_csv(vocab_csv_file_name, [], headers=['Link', 'Word', 'Furigana', 'Meaning', 'Level'])

    completed_links_kanji = load_completed_links(kanji_csv_file_name)
    completed_links_vocab = load_completed_links(vocab_csv_file_name)
    driver = configure_webdriver()
    
    try:
        total_start_time = time.time()
        scrape_links(csv_files, driver, completed_links_kanji, completed_links_vocab, kanji_csv_file_name, vocab_csv_file_name, image_save_path)
        total_elapsed_time = time.time() - total_start_time
        print(f"All links processed successfully. Total time taken: {total_elapsed_time:.2f} seconds")

        # Save final kanji data to a separate CSV file without the Link column
        kanji_data = []
        with open(kanji_csv_file_name, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                kanji_data.append(row)
        save_final_csv('final_kanji_data.csv', kanji_data, ['Link', 'Kanji', 'Meanings', 'On Yomi', 'Kun Yomi', 'Pronunciations', 'Level'])

        # Save final vocabulary data to a separate CSV file without the Link column
        vocab_data = []
        with open(vocab_csv_file_name, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                vocab_data.append(row)
        save_final_csv('final_vocab_data.csv', vocab_data, ['Link', 'Word', 'Furigana', 'Meaning', 'Level'])
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
