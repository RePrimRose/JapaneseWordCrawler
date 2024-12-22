import json
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm


def get_furigana_from_kuroshiro(text):
    response = requests.post("http://localhost:3000/getFurigana", json={"text": text})
    return response.json()["result"]


def contains_kanji(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def process_sentence_with_ruby(sentence, divided_sentence):
    # 전체 문장의 루비 태그 포함 결과 가져오기
    ruby_sentence = get_furigana_from_kuroshiro(sentence)

    # BeautifulSoup으로 루비 태그를 파싱
    soup = BeautifulSoup(ruby_sentence, "html.parser")

    # 루비 태그 내 한자와 루비 태그를 매핑
    ruby_map = {}  # { "한자": "<ruby>한자<rt>읽기</rt></ruby>" }
    for ruby in soup.find_all("ruby"):
        kanji = ruby.get_text()  # 루비 태그 안의 한자 (한자만 추출)
        ruby_map[kanji] = str(ruby)  # 해당 한자의 루비 태그 전체 저장

    # 배열에서 한자를 포함한 요소를 루비 태그로 대체
    ruby_phrases = []
    for phrase in divided_sentence:
        # phrase에 포함된 한자를 루비 태그로 대체
        replaced_phrase = phrase
        for kanji, ruby_tag in ruby_map.items():
            if kanji in replaced_phrase:  # 한자가 포함되어 있다면
                # 한자를 루비 태그로 대체
                replaced_phrase = replaced_phrase.replace(kanji, ruby_tag)
        ruby_phrases.append(replaced_phrase)

    return ruby_phrases, ruby_sentence


def get_divided_sentence(sentence, client):
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": "다음 일본어 문장을 언어 학습 퀴즈에 적합하도록 적절한 크기로 나누어 주세요. 각 단위는 단어로 나누세요."
                                        "너무 작은 단위로 나누지 말고 의미를 알아볼수있는 정도의 단위로 나누세요. 무조건 key값으론 "
                                        "words라고 보내주세요. 주어진 문장 외에 다른 말을 추가하지 마세요."},
            {"role": "user", "content": sentence}
        ]
    )

    result = response.choices[0].message.content
    result = json.loads(result)
    print(result['words'])

    return result['words']


def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    df = pd.read_csv('./data/temp.csv')
    total_rows = df.shape[0]

    for index, row in tqdm(df.iterrows(), total=total_rows, desc="진행 상황"):
        sentence = row['sentence']
        divided_sentence = get_divided_sentence(sentence, client)
        ruby_phrases, ruby_sentence = process_sentence_with_ruby(sentence, divided_sentence)
        row['divided_sentence'] = json.dumps(divided_sentence, ensure_ascii=False)
        row['divided_sentence_with_ruby'] = json.dumps(ruby_phrases, ensure_ascii=False)
        row['sentence_with_ruby'] = ruby_sentence

        df.to_csv('temp2.csv', index=False)

        time.sleep(1)


if __name__ == "__main__":
    load_dotenv()
    main()
