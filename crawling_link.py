from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv

# Step 1: Selenium을 이용한 웹페이지 요청
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 표시하지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# WebDriverManager를 사용해 ChromeDriver 설정 및 웹페이지 로드
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
url = 'https://nihongokanji.com/2285'
driver.get(url)

# 페이지 로딩 대기 (필요시 조정)
time.sleep(5)

# Step 2: BeautifulSoup을 이용한 파싱
html_content = driver.page_source
driver.quit()
soup = BeautifulSoup(html_content, 'html.parser')

# 원하는 데이터 추출하기 (특정 div 클래스 내 ul 구조의 리스트에서 모든 링크 추출)
data_list = []
for container in soup.find_all('div', class_='tt_article_useless_p_margin contents_style'):
    ul_tag = container.find('ul')
    if ul_tag:
        for li in ul_tag.find_all('li'):
            a_tag = li.find('a')
            if a_tag and 'href' in a_tag.attrs:
                link = a_tag['href']
                data_list.append(link)

# 추출된 링크 출력
print(f"Extracted links: {data_list}")

# Step 3: CSV 파일에 저장
csv_file_name = 'extracted_links.csv'
with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Link'])  # 헤더 작성
    for link in data_list:
        writer.writerow([link])  # 링크 작성

print(f"Links successfully saved to {csv_file_name}")
