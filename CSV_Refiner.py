import csv

vocab_data = []

with open('final_vocab_data.csv', mode='r', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    next(reader)
    
    vocab = ''
    
    for row in reader:
        if(row[2] == ''):
            if(vocab):
                vocab = [a + b for a, b in zip(vocab, row[:-1])]
                vocab.append(row[3])
            else:
                vocab = row[:-1]
        else:
            if(vocab):
                vocab = [a + b for a, b in zip(vocab, row[:-1])]
                vocab.append(row[3])
                vocab_data.append(vocab)
                vocab = ''
            else:
                vocab_data.append(row)

with open('modified_vocab_data.csv', mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    writer.writerow(['Word', 'Furigana', 'Meaning', 'Level'])
    for vocab in vocab_data:
        writer.writerow(vocab)