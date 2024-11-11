from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd


def make_set(file_path):
    df = pd.read_csv(file_path)

    kanji_set = set(df['Word'])
    furigana_set = set(df['Furigana'])

    return kanji_set, furigana_set


def set_options():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    chrome_options.add_argument('--headless')  # 브라우저를 백그라운드 모드로 실행
    chrome_options.add_argument('--log-level=3')  # 로그 레벨을 최소화
    chrome_options.add_argument('--disable-logging')  # 로깅 비활성화
    chrome_options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    chrome_options.add_argument('--disable-dev-shm-usage')  # 메모리 공유 비활성화
    chrome_options.add_argument('--disable-gpu')  # GPU 가속 비활성화
    chrome_options.add_argument('--disable-software-rasterizer')  # 소프트웨어 래스터라이저 비활성화

    return chrome_options


def main():
    file_path = './data/modified_vocab_data.csv'
    kanji_set, furigana_set = make_set(file_path)
    driver = webdriver.Chrome(options=set_options())


if __name__ == "__main__":
    main()
