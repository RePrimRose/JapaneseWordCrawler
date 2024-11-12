import csv
import json
import re
import requests
import time
import pandas as pd
import deepl
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv


def get_options():
    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                'like Gecko) Chrome/92.0.4515.107 Safari/537.36')
    chrome_options.add_argument('--headless')  # 브라우저를 백그라운드 모드로 실행
    chrome_options.add_argument('--log-level=3')  # 로그 레벨을 최소화
    chrome_options.add_argument('--disable-logging')  # 로깅 비활성화
    chrome_options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    chrome_options.add_argument('--disable-dev-shm-usage')  # 메모리 공유 비활성화
    chrome_options.add_argument('--disable-gpu')  # GPU 가속 비활성화
    chrome_options.add_argument('--disable-software-rasterizer')  # 소프트웨어 래스터라이저 비활성화

    return chrome_options


def get_example(soup):
    texts = soup.select('div.sentence')
    if not texts:
        return ''

    lang = texts[0].select_one('img.language-icon').get('title')
    if lang != '일본어':
        return ''

    example_sentence = texts[0].select_one('div.text').get_text()

    return example_sentence


def contains_kanji(text):
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    return bool(kanji_pattern.search(text))


def get_furigana_from_kuroshiro(text):
    response = requests.post("http://localhost:3000/getFurigana", json={"text": text})
    return response.json()["result"]


def split_into_phrases(sentence):
    josa_pattern = re.compile(r'(を|が|は|も|に|と|から|まで|よ|ね|か|。|、)')
    phrases = []
    phrase = ""

    for char in sentence:
        phrase += char
        if josa_pattern.match(char):
            phrases.append(phrase.strip())
            phrase = ""

    # 마지막 남은 부분에 공백 제거하여 추가
    if phrase.strip():  # 공백이 아닌 경우에만 추가
        phrases.append(phrase.strip())

    return phrases


def process_sentence(sentence):
    # 조사와 구분자로 문장 나누기
    original_phrases = split_into_phrases(sentence)

    # 각 의미 단위에 대해 한자에만 루비 태그 적용
    ruby_phrases = []
    ruby_sentence = ""

    for phrase in original_phrases:
        if contains_kanji(phrase):
            # 한자 포함 구 단위만 루비 태그 적용
            ruby_phrase = get_furigana_from_kuroshiro(phrase)
        else:
            ruby_phrase = phrase

        ruby_phrases.append(ruby_phrase)
        ruby_sentence += ruby_phrase  # 전체 문장 조합용

    return original_phrases, ruby_phrases, ruby_sentence


def get_translate(sentence, key):
    translator = deepl.Translator(key)

    result = translator.translate_text(sentence, target_lang="KO")

    return result


def save_csv(data):
    with open('./data/example_sentences.csv', mode='w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)

        writer.writerow(
            ["sentence", "translate", "divided_sentence", "sentence_with_ruby", "divided_sentence_with_ruby"])

        for row in data:
            writer.writerow(row)


def main():
    driver = webdriver.Chrome(options=get_options())
    df = pd.read_csv('./data/completed_vocab_data.csv')
    total_rows = df.shape[0]
    load_dotenv()
    deepl_api_key = os.getenv("DEEPL_API_KEY")

    datas = []

    for index, row in tqdm(df.iterrows(), total=total_rows, desc="진행 상황"):
        kanji = row['Word']
        url = 'https://tatoeba.org/ko/sentences/search?from=jpn&query=' + kanji

        driver.get(url)

        time.sleep(2)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        example_sentence = get_example(soup)
        if example_sentence == '':
            continue

        original_phrases, ruby_phrases, ruby_sentence = process_sentence(example_sentence)
        translate_sentence = get_translate(example_sentence, deepl_api_key)

        json_original_phrases = json.dumps(original_phrases, ensure_ascii=False)
        json_ruby_phrases = json.dumps(ruby_phrases, ensure_ascii=False)
        json_ruby_sentence = json.dumps(ruby_sentence, ensure_ascii=False)

        datas.append(
            [example_sentence, translate_sentence, json_original_phrases, json_ruby_phrases, json_ruby_sentence])

        print(example_sentence, translate_sentence, json_original_phrases)

    driver.quit()

    save_csv(datas)


if __name__ == "__main__":
    main()
