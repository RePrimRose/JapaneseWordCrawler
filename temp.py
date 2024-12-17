import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import json
import pyperclip
import requests


# 루비 태그를 가져오는 함수
def get_furigana_from_kuroshiro(text):
    response = requests.post("http://localhost:3000/getFurigana", json={"text": text})
    return response.json()["result"]


# divided_sentence를 처리하여 루비 태그를 적용하고 전체 문장도 생성하는 함수
def process_sentence_and_combine(divided_sentence):
    ruby_phrases = []
    ruby_sentence = ""  # 전체 문장 조합용
    for phrase in divided_sentence:
        if contains_kanji(phrase):
            ruby_phrase = get_furigana_from_kuroshiro(phrase)
        else:
            ruby_phrase = phrase
        ruby_phrases.append(ruby_phrase)
        ruby_sentence += ruby_phrase  # 전체 문장 조합
    return ruby_phrases, ruby_sentence


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

        # Status Label
        self.status_label = tk.Label(root, text="Status: 0/0", font=("Arial", 12))
        self.status_label.pack(anchor="w")

        # Sentence Frame
        sentence_frame = tk.Frame(self.root)
        sentence_frame.pack(fill="x", pady=5)
        self.sentence_label = tk.Label(sentence_frame, text="Sentence:", font=("Arial", 14))
        self.sentence_label.pack(side="left", padx=5)

        self.sentence_text = tk.Entry(sentence_frame, font=("Arial", 12), width=50)
        self.sentence_text.pack(side="left", fill="x", expand=True, padx=5)

        self.copy_button = tk.Button(sentence_frame, text="Copy", command=self.copy_sentence_to_clipboard)
        self.copy_button.pack(side="right", padx=5)

        # Translate Frame
        translate_frame = tk.Frame(self.root)
        translate_frame.pack(fill="x", pady=5)
        self.translate_label = tk.Label(translate_frame, text="Translate:", font=("Arial", 14))
        self.translate_label.pack(side="left", padx=5)

        self.translate_text = tk.Entry(translate_frame, font=("Arial", 12), width=50)
        self.translate_text.pack(side="left", fill="x", expand=True, padx=5)

        # Divided Sentence
        self.divided_label = tk.Label(root, text="Divided Sentence (Editable):", font=("Arial", 14))
        self.divided_label.pack(anchor="w")
        self.divided_text = self.create_scrollable_text(height=4)

        # Navigation Buttons
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(fill="x", pady=5)
        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_sentence)
        self.prev_button.pack(side="left", padx=5)

        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_sentence)
        self.next_button.pack(side="left", padx=5)

        self.save_button = tk.Button(nav_frame, text="Save CSV", command=self.save_csv)
        self.save_button.pack(side="right", padx=5)

        # File Open Button
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill="x", pady=5)
        self.open_button = tk.Button(file_frame, text="Open CSV", command=self.load_csv)
        self.open_button.pack(padx=5)

    def create_scrollable_text(self, height):
        frame = tk.Frame(self.root)
        frame.pack(fill="x")
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame, height=height, wrap=tk.WORD, font=("Arial", 12), yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="x", expand=True)
        scrollbar.config(command=text.yview)
        return text

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
            self.save_current_edit()
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if filepath:
                try:
                    self.data.to_csv(filepath, index=False)
                    messagebox.showinfo("Success", "File saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")

    def update_gui(self):
        if self.data is not None and not self.data.empty:
            # Get current data
            sentence = self.data.loc[self.current_index, 'sentence']
            translate = self.data.loc[self.current_index, 'translate']
            divided_sentence = self.data.loc[self.current_index, 'divided_sentence']

            # Update fields
            self.status_label.config(text=f"Status: {self.current_index + 1}/{len(self.data)}")
            self.sentence_text.delete(0, tk.END)
            self.sentence_text.insert(0, sentence)

            self.translate_text.delete(0, tk.END)
            self.translate_text.insert(0, translate)

            self.divided_text.delete(1.0, tk.END)
            self.divided_text.insert(tk.END, divided_sentence)

    def save_current_edit(self):
        if self.data is not None:
            self.data.loc[self.current_index, 'sentence'] = self.sentence_text.get().strip()
            self.data.loc[self.current_index, 'translate'] = self.translate_text.get().strip()
            divided_sentence = self.divided_text.get(1.0, tk.END).strip().split("\n")
            self.data.loc[self.current_index, 'divided_sentence'] = json.dumps(divided_sentence, ensure_ascii=False)

    def copy_sentence_to_clipboard(self):
        sentence = self.sentence_text.get().strip()
        pyperclip.copy(sentence)
        messagebox.showinfo("Copied", "Sentence copied to clipboard!")

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


if __name__ == "__main__":
    root = tk.Tk()
    app = SentenceEditor(root)
    root.mainloop()
