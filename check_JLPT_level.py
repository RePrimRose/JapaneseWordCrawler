from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import csv
import pandas as pd
from tqdm import tqdm

def get_jlpt_level(target_hiragana, target_kanji, soup):
    rows = soup.select('.row')  # 모든 .row 요소 선택
    for row in rows:
        # 각 row에서 히라가나와 한자 부분을 찾음
        hiragana_element = row.select_one('.origin a.link')
        hiragana = hiragana_element.text.strip() if hiragana_element else ""

        kanji_container = row.select_one('.origin ._kanji strong.highlight')
        if kanji_container:
            kanji = ''.join([el.text for el in kanji_container.find_all('em', class_='letter _letterTooltip')])
            kanji = re.sub(r'[()]', '', kanji)  # `(`와 `)` 제거
        else:
            kanji = ""

        # 사용자 제공 한자에서 히라가나 제거
        target_kanji_only = re.sub(r'[\u3040-\u309F]', '', target_kanji)

        # 히라가나와 한자 비교
        if hiragana == target_hiragana and kanji == target_kanji_only:
            # JLPT 레벨 찾기
            jlpt_level_tag = row.select_one('.unit_tooltip .btn_toggle_square')
            jlpt_level = jlpt_level_tag.text.strip() if jlpt_level_tag else ''
            return jlpt_level  # 일치하는 요소가 있으면 해당 레벨 반환

    # 모든 row를 확인해도 일치하는 항목이 없는 경우
    return ''  # 공백 반환


def main():
    # ChromeOptions 객체 생성 및 필요한 옵션 추가
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    chrome_options.add_argument('--headless')  # 브라우저를 백그라운드 모드로 실행
    chrome_options.add_argument('--log-level=3')  # 로그 레벨을 최소화
    chrome_options.add_argument('--disable-logging')  # 로깅 비활성화
    chrome_options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    chrome_options.add_argument('--disable-dev-shm-usage')  # 메모리 공유 비활성화
    chrome_options.add_argument('--disable-gpu')  # GPU 가속 비활성화
    chrome_options.add_argument('--disable-software-rasterizer')  # 소프트웨어 래스터라이저 비활성화

    # Chrome 드라이버에 옵션 추가 및 드라이버 실행
    driver = webdriver.Chrome(options=chrome_options)

    df = pd.read_csv('./JapaneseWordCrawler/data/modified_vocab_data.csv')
    
    total_rows = df.shape[0]
    
    for index, row in tqdm(df.iterrows(), total=total_rows, desc="진행 상황"):
        target_hiragana = row['Furigana']
        target_kanji = row['Word']
        
        url = "https://ja.dict.naver.com/#/search?query=" + target_kanji
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(2)

        # 페이지 소스 가져오기
        page_source = driver.page_source

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        jlpt_level = get_jlpt_level(target_hiragana, target_kanji, soup)
        print(f"타겟 히라가나: {target_hiragana}, 타겟 한자: {target_kanji}, JLPT 레벨: {jlpt_level if jlpt_level else '없음'}")
        
        if(jlpt_level == 'JLPT 1'):
            df.at[index, 'Level'] = 'N1'
        elif(jlpt_level == 'JLPT 2'):
            df.at[index, 'Level'] = 'N2'
        elif(jlpt_level == 'JLPT 3'):
            df.at[index, 'Level'] = 'N3'
        elif(jlpt_level == 'JLPT 4'):
            df.at[index, 'Level'] = 'N4'
        elif(jlpt_level == 'JLPT 5'):
            df.at[index, 'Level'] = 'N5'
        else:
            df.at[index, 'Level'] = 'etc'
        
        if index % 100 == 0:
            driver.quit()
            driver = webdriver.Chrome(options=chrome_options)
    
    driver.quit()
    
    df.to_csv('./JapaneseWordCrawler/data/completed_vocab_data.csv', index=False, encoding='utf-8-sig')
    print("파일이 'completed_vocab_data.csv'로 저장되었습니다.")

if __name__ == "__main__":
    main()
