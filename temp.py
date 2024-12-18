import tkinter as tk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup
import pandas as pd
import json
import pyperclip
import requests
import re

# 루비 태그를 가져오는 함수
def get_furigana_from_kuroshiro(text):
    response = requests.post("http://localhost:3000/getFurigana", json={"text": text})
    return response.json()["result"]

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

    # 최종 문장 조합
    ruby_sentence_combined = "".join(ruby_phrases)
    return ruby_phrases, ruby_sentence_combined

# 한자 포함 여부 확인 함수
def contains_kanji(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


class SentenceEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentence Divider Editor")
        self.data = None
        self.current_index = 0

        # GUI 구성
        self.status_label = tk.Label(root, text="Status: 0/0", font=("Arial", 12))
        self.status_label.pack(anchor="w")

        sentence_frame = tk.Frame(self.root)
        sentence_frame.pack(fill="x")
        self.sentence_label = tk.Label(sentence_frame, text="Sentence:", font=("Arial", 14))
        self.sentence_label.pack(side="left", anchor="w")

        self.sentence_text = self.create_scrollable_text(parent=sentence_frame, height=2)
        self.copy_sentence_button = tk.Button(
            sentence_frame, text="Copy", command=self.copy_sentence_to_clipboard, font=("Arial", 10)
        )
        self.copy_sentence_button.pack(side="right", padx=5)

        self.translate_label = tk.Label(root, text="Translate:", font=("Arial", 14))
        self.translate_label.pack(anchor="w")
        self.translate_text = self.create_scrollable_text(height=2)

        self.divided_label = tk.Label(root, text="Divided Sentence (Editable):", font=("Arial", 14))
        self.divided_label.pack(anchor="w")
        self.divided_text = self.create_scrollable_text(height=4)

        self.divided_ruby_label = tk.Label(root, text="Divided Sentence with Ruby:", font=("Arial", 14))
        self.divided_ruby_label.pack(anchor="w")
        self.divided_ruby_text = self.create_scrollable_text(height=4, state=tk.DISABLED)

        self.sentence_with_ruby_label = tk.Label(root, text="Sentence with Ruby:", font=("Arial", 14))
        self.sentence_with_ruby_label.pack(anchor="w")
        self.sentence_with_ruby_text = self.create_scrollable_text(height=2, state=tk.DISABLED)

        # Navigation Buttons
        self.prev_button = tk.Button(root, text="Previous", command=self.prev_sentence)
        self.prev_button.pack(side="left", padx=5)
        self.next_button = tk.Button(root, text="Next", command=self.next_sentence)
        self.next_button.pack(side="left", padx=5)

        # Delete Button
        self.delete_button = tk.Button(root, text="Delete", command=self.delete_sentence)
        self.delete_button.pack(side="left", padx=5)

        # Jump to Entry
        self.jump_label = tk.Label(root, text="Go to:", font=("Arial", 12))
        self.jump_label.pack(side="left", padx=5)
        self.jump_entry = tk.Entry(root, width=5, font=("Arial", 12))
        self.jump_entry.pack(side="left", padx=5)
        self.jump_button = tk.Button(root, text="Go", command=self.jump_to_sentence)
        self.jump_button.pack(side="left", padx=5)

        # File Buttons
        self.open_button = tk.Button(root, text="Open CSV", command=self.load_csv)
        self.open_button.pack(side="left", padx=5)
        self.save_button = tk.Button(root, text="Save CSV", command=self.save_csv)
        self.save_button.pack(side="left", padx=5)
        self.ruby_button = tk.Button(root, text="Generate Ruby", command=self.generate_ruby)
        self.ruby_button.pack(side="left", padx=5)

    def create_scrollable_text(self, parent=None, height=4, state=tk.NORMAL):
        if parent is None:
            parent = self.root

        frame = tk.Frame(parent)
        frame.pack(fill="x")

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame, height=height, wrap=tk.WORD, font=("Arial", 12), yscrollcommand=scrollbar.set, state=state)
        text.pack(side="left", fill="x", expand=True)
        scrollbar.config(command=text.yview)

        return text

    def copy_sentence_to_clipboard(self):
        sentence = self.sentence_text.get(1.0, tk.END).strip()
        pyperclip.copy(sentence)

    def load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                self.data = pd.read_csv(filepath)
                self.current_index = 0
                self.update_gui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_csv(self):
        if self.data is not None:
            self.save_current_edit()  # 마지막 수정 내용 반영
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if filepath:
                try:
                    self.data.to_csv(filepath, index=False)
                    messagebox.showinfo("Success", "File saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            messagebox.showwarning("Warning", "No data to save!")

    def update_gui(self):
        if self.data is not None and not self.data.empty:
            # Get current data
            sentence = self.data.loc[self.current_index, 'sentence']
            translate = self.data.loc[self.current_index, 'translate']
            divided_sentence = self.data.loc[self.current_index, 'divided_sentence']
            divided_sentence_with_ruby = self.data.loc[self.current_index, 'divided_sentence_with_ruby']
            sentence_with_ruby = self.data.loc[self.current_index, 'sentence_with_ruby']

            # Update fields
            self.status_label.config(text=f"Status: {self.current_index + 1}/{len(self.data)}")
            self.sentence_text.delete(1.0, tk.END)
            self.sentence_text.insert(tk.END, sentence)
            self.translate_text.delete(1.0, tk.END)
            self.translate_text.insert(tk.END, translate)

            # Load divided_sentence as a list for easier editing
            divided_list = json.loads(divided_sentence)
            self.divided_text.delete(1.0, tk.END)
            self.divided_text.insert(tk.END, "\n".join(divided_list))  # Show as plain text

            self.divided_ruby_text.config(state=tk.NORMAL)
            self.divided_ruby_text.delete(1.0, tk.END)
            self.divided_ruby_text.insert(tk.END, divided_sentence_with_ruby)
            self.divided_ruby_text.config(state=tk.DISABLED)

            self.sentence_with_ruby_text.config(state=tk.NORMAL)
            self.sentence_with_ruby_text.delete(1.0, tk.END)
            self.sentence_with_ruby_text.insert(tk.END, sentence_with_ruby)
            self.sentence_with_ruby_text.config(state=tk.DISABLED)

    def save_current_edit(self):
        if self.data is not None:
            # Save divided_sentence
            divided_list = self.divided_text.get(1.0, tk.END).strip().split("\n")
            self.data.loc[self.current_index, 'divided_sentence'] = json.dumps(divided_list, ensure_ascii=False)

            # Save divided_sentence_with_ruby
            divided_ruby_text = self.divided_ruby_text.get(1.0, tk.END).strip()
            self.data.loc[self.current_index, 'divided_sentence_with_ruby'] = divided_ruby_text

            # Save sentence_with_ruby
            sentence_with_ruby_text = self.sentence_with_ruby_text.get(1.0, tk.END).strip()
            self.data.loc[self.current_index, 'sentence_with_ruby'] = sentence_with_ruby_text

            # Save translate
            translate_text = self.translate_text.get(1.0, tk.END).strip()
            self.data.loc[self.current_index, 'translate'] = translate_text

    def generate_ruby(self):
        if self.data is not None:
            sentence = self.sentence_text.get(1.0, tk.END).strip()
            divided_list = self.divided_text.get(1.0, tk.END).strip().split("\n")
            try:
                # Generate ruby based on full sentence and divided sentence structure
                ruby_phrases, ruby_sentence = process_sentence_with_ruby(sentence, divided_list)

                # Save to data
                divided_sentence_with_ruby = json.dumps(ruby_phrases, ensure_ascii=False)
                self.data.loc[self.current_index, 'divided_sentence_with_ruby'] = divided_sentence_with_ruby
                self.data.loc[self.current_index, 'sentence_with_ruby'] = ruby_sentence

                # Update GUI fields
                self.divided_ruby_text.config(state=tk.NORMAL)
                self.divided_ruby_text.delete(1.0, tk.END)
                self.divided_ruby_text.insert(tk.END, divided_sentence_with_ruby)
                self.divided_ruby_text.config(state=tk.DISABLED)

                self.sentence_with_ruby_text.config(state=tk.NORMAL)
                self.sentence_with_ruby_text.delete(1.0, tk.END)
                self.sentence_with_ruby_text.insert(tk.END, ruby_sentence)
                self.sentence_with_ruby_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate ruby: {e}")

    def delete_sentence(self):
        if self.data is not None and not self.data.empty:
            confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this sentence?")
            if confirm:
                self.data = self.data.drop(self.current_index).reset_index(drop=True)
                if self.current_index >= len(self.data):  # 마지막 문장을 삭제했을 경우
                    self.current_index = len(self.data) - 1
                self.update_gui()
                messagebox.showinfo("Success", "Sentence deleted successfully.")

    def next_sentence(self):
        if self.data is not None and self.current_index < len(self.data) - 1:
            self.save_current_edit()
            self.current_index += 1
            self.update_gui()

    def prev_sentence(self):
        if self.data is not None and self.current_index > 0:
            self.save_current_edit()
            self.current_index -= 1
            self.update_gui()

    def jump_to_sentence(self):
        if self.data is not None:
            try:
                target_index = int(self.jump_entry.get()) - 1
                if 0 <= target_index < len(self.data):
                    self.save_current_edit()
                    self.current_index = target_index
                    self.update_gui()
                else:
                    messagebox.showwarning("Warning", "Index out of range!")
            except ValueError:
                messagebox.showerror("Error", "Invalid input! Please enter a number.")


# 프로그램 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = SentenceEditor(root)
    root.mainloop()
