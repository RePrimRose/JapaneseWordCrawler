import pandas as pd
import time

from tqdm import tqdm


def get_data(file_name):
    datas = pd.read_csv(file_name)
    
    return datas


def modify_sentence(datas, file_name):
    total_rows = datas.shape[0]
    
    for index, row in tqdm(datas.iterrows(), total=total_rows, desc="진행 상황"):
        sentence = row['sentence']
        translate = row['translate']
        ruby = row['sentence_with_ruby']
        sentence = sentence.replace('\n', '')
        translate = translate.replace('\n', '')
        ruby = ruby.replace('"', '')
        datas.at[index, 'sentence'] = sentence
        datas.at[index, 'translate'] = translate
        datas.at[index, 'sentence_with_ruby'] = ruby
        
    datas.to_csv(file_name, index=False, encoding='utf-8-sig')
    

def main():
    file_name = './data/example_sentences.csv'
    datas = get_data(file_name)
    
    modify_sentence(datas, file_name)

    

if __name__ == "__main__":
    main()
