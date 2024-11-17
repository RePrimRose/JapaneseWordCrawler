import pandas as pd

# CSV 파일 읽기
file_path = "./data/example_sentences.csv"
df = pd.read_csv(file_path)

# 중복 제거
df_cleaned = df.drop_duplicates(subset=['sentence'])

# 중복이 제거된 데이터 저장
output_path = "./data/example_sentences.csv"
df_cleaned.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"중복 제거 완료. 결과가 {output_path}에 저장되었습니다.")
