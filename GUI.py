#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文單字背誦系統 - 電腦版 GUI (Tkinter)
提供圖形化介面，讓操作更直覺、更美觀
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import random
from typing import List, Optional


class Word:
    """單字類別"""
    def __init__(self, word_id: int, english: str, chinese: str, 
                 folder: str, error_count: int = 0):
        self.id = word_id
        self.english = english.lower().strip()
        self.chinese = chinese.strip()
        self.folder = folder.lower().strip()
        self.error_count = error_count


class VocabularyDatabase:
    """資料庫管理類別"""
    
    def __init__(self, db_name: str = "vocabulary.db"):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """連接到資料庫"""
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"資料庫連線錯誤: {e}")
    
    def create_tables(self):
        """建立資料表"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    english TEXT NOT NULL,
                    chinese TEXT NOT NULL,
                    folder TEXT NOT NULL,
                    error_count INTEGER DEFAULT 0
                )
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder ON words(folder)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_english ON words(english)
            """)
            
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"建立資料表錯誤: {e}")
    
    def add_word(self, english: str, chinese: str, folder: str) -> bool:
        """新增單字"""
        try:
            # 檢查是否已存在
            self.cursor.execute("""
                SELECT id FROM words WHERE folder = ? AND english = ?
            """, (folder.lower(), english.lower()))
            
            if self.cursor.fetchone():
                return False
            
            # 插入新單字
            self.cursor.execute("""
                INSERT INTO words (english, chinese, folder, error_count)
                VALUES (?, ?, ?, 0)
            """, (english.lower(), chinese, folder.lower()))
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"新增單字錯誤: {e}")
            return False
    
    def get_all_words(self) -> List[Word]:
        """取得所有單字"""
        try:
            self.cursor.execute("""
                SELECT id, english, chinese, folder, error_count
                FROM words ORDER BY folder, english
            """)
            
            return [Word(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_words_by_folder(self, folder: str) -> List[Word]:
        """取得指定資料夾的單字"""
        try:
            self.cursor.execute("""
                SELECT id, english, chinese, folder, error_count
                FROM words WHERE folder = ? ORDER BY english
            """, (folder.lower(),))
            
            return [Word(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def search_words(self, keyword: str) -> List[Word]:
        """搜尋單字"""
        try:
            search_pattern = f"%{keyword}%"
            self.cursor.execute("""
                SELECT id, english, chinese, folder, error_count
                FROM words
                WHERE english LIKE ? OR chinese LIKE ?
                ORDER BY folder, english
            """, (search_pattern, search_pattern))
            
            return [Word(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def update_error_count(self, word_id: int, error_count: int) -> bool:
        """更新錯誤次數"""
        try:
            self.cursor.execute("""
                UPDATE words SET error_count = ? WHERE id = ?
            """, (error_count, word_id))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def delete_word(self, word_id: int) -> bool:
        """刪除單字"""
        try:
            self.cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def get_all_folders(self) -> List[str]:
        """取得所有資料夾"""
        try:
            self.cursor.execute("""
                SELECT DISTINCT folder FROM words ORDER BY folder
            """)
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_error_words(self) -> List[Word]:
        """取得錯題"""
        try:
            self.cursor.execute("""
                SELECT id, english, chinese, folder, error_count
                FROM words WHERE error_count > 0
                ORDER BY error_count DESC, english
            """)
            return [Word(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_statistics(self) -> dict:
        """取得統計資訊"""
        stats = {}
        try:
            self.cursor.execute("SELECT COUNT(*) FROM words")
            stats['total_words'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT folder) FROM words")
            stats['total_folders'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM words WHERE error_count > 0")
            stats['words_with_errors'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT SUM(error_count) FROM words")
            result = self.cursor.fetchone()[0]
            stats['total_errors'] = result if result else 0
            
            return stats
        except sqlite3.Error:
            return stats
    
    def close(self):
        """關閉連線"""
        if self.connection:
            self.connection.close()


class VocabularyApp:
    """主應用程式類別"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("英文單字背誦系統 v2.0")
        self.root.geometry("900x650")
        
        # 設定樣式
        self.setup_style()
        
        # 初始化資料庫
        self.db = VocabularyDatabase()
        
        # 建立主介面
        self.create_main_interface()
        
        # 測驗相關變數
        self.test_words = []
        self.current_test_index = 0
        self.test_score = 0
        
        # 單字卡相關變數
        self.flashcard_words = []
        self.current_flashcard_index = 0
        
    def setup_style(self):
        """設定視覺樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配色方案
        bg_color = "#f5f5f5"
        primary_color = "#4a90e2"
        success_color = "#52c41a"
        error_color = "#ff4d4f"
        
        # 設定按鈕樣式
        style.configure('Primary.TButton',
                       background=primary_color,
                       foreground='white',
                       padding=10,
                       font=('Arial', 10, 'bold'))
        
        style.map('Primary.TButton',
                 background=[('active', '#3a7bc8')])
        
        self.root.configure(bg=bg_color)
    
    def create_main_interface(self):
        """建立主介面"""
        # 標題
        title_frame = tk.Frame(self.root, bg="#4a90e2", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="📚 英文單字背誦系統",
            font=("Arial", 24, "bold"),
            bg="#4a90e2",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # 主內容區
        content_frame = tk.Frame(self.root, bg="#f5f5f5")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 左側選單
        menu_frame = tk.Frame(content_frame, bg="white", width=200)
        menu_frame.pack(side="left", fill="y", padx=(0, 20))
        menu_frame.pack_propagate(False)
        
        # 選單標題
        menu_title = tk.Label(
            menu_frame,
            text="功能選單",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#333"
        )
        menu_title.pack(pady=20)
        
        # 選單按鈕
        buttons = [
            ("➕ 新增單字", self.show_add_word),
            ("📖 單字卡學習", self.show_flashcard),
            ("✏️ 開始測驗", self.show_test),
            ("❌ 錯題本", self.show_error_list),
            ("🔍 查詢單字", self.show_search),
            ("📊 統計資訊", self.show_statistics),
            ("🗑️ 管理單字", self.show_manage),
        ]
        
        for text, command in buttons:
            btn = tk.Button(
                menu_frame,
                text=text,
                command=command,
                width=18,
                bg="#4a90e2",
                fg="white",
                font=("Arial", 10),
                relief="flat",
                cursor="hand2",
                pady=10
            )
            btn.pack(pady=5, padx=10)
            
            # 懸停效果
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#3a7bc8"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#4a90e2"))
        
        # 右側內容區
        self.content_area = tk.Frame(content_frame, bg="white")
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # 顯示歡迎畫面
        self.show_welcome()
    
    def clear_content(self):
        """清空內容區"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def show_welcome(self):
        """顯示歡迎畫面"""
        self.clear_content()
        
        # 取得統計資訊
        stats = self.db.get_statistics()
        
        welcome_text = f"""
        
        歡迎使用英文單字背誦系統！
        
        📚 目前共有 {stats.get('total_words', 0)} 個單字
        📁 分布在 {stats.get('total_folders', 0)} 個資料夾
        ❌ {stats.get('words_with_errors', 0)} 個單字有錯誤記錄
        
        請從左側選單選擇功能開始使用
        """
        
        label = tk.Label(
            self.content_area,
            text=welcome_text,
            font=("Arial", 14),
            bg="white",
            fg="#666",
            justify="left"
        )
        label.pack(pady=100)
    
    def show_add_word(self):
        """顯示新增單字介面"""
        self.clear_content()
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="➕ 新增單字",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 表單框架
        form_frame = tk.Frame(self.content_area, bg="white")
        form_frame.pack(pady=20)
        
        # 資料夾
        tk.Label(form_frame, text="資料夾：", font=("Arial", 12), bg="white").grid(
            row=0, column=0, sticky="w", pady=10, padx=10
        )
        folder_entry = tk.Entry(form_frame, font=("Arial", 12), width=30)
        folder_entry.grid(row=0, column=1, pady=10, padx=10)
        
        # 英文單字
        tk.Label(form_frame, text="英文單字：", font=("Arial", 12), bg="white").grid(
            row=1, column=0, sticky="w", pady=10, padx=10
        )
        english_entry = tk.Entry(form_frame, font=("Arial", 12), width=30)
        english_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # 中文意思
        tk.Label(form_frame, text="中文意思：", font=("Arial", 12), bg="white").grid(
            row=2, column=0, sticky="w", pady=10, padx=10
        )
        chinese_entry = tk.Entry(form_frame, font=("Arial", 12), width=30)
        chinese_entry.grid(row=2, column=1, pady=10, padx=10)
        
        # 結果顯示
        result_label = tk.Label(
            self.content_area,
            text="",
            font=("Arial", 11),
            bg="white",
            fg="#52c41a"
        )
        result_label.pack(pady=10)
        
        def add_word():
            folder = folder_entry.get().strip()
            english = english_entry.get().strip()
            chinese = chinese_entry.get().strip()
            
            if not folder or not english or not chinese:
                result_label.config(text="❌ 所有欄位都必須填寫！", fg="#ff4d4f")
                return
            
            if self.db.add_word(english, chinese, folder):
                result_label.config(
                    text=f"✅ 成功新增：{english} - {chinese}",
                    fg="#52c41a"
                )
                # 清空輸入框
                english_entry.delete(0, tk.END)
                chinese_entry.delete(0, tk.END)
                english_entry.focus()
            else:
                result_label.config(
                    text=f"⚠️ 單字已存在或新增失敗",
                    fg="#ff4d4f"
                )
        
        # 新增按鈕
        add_btn = tk.Button(
            self.content_area,
            text="新增單字",
            command=add_word,
            bg="#52c41a",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        )
        add_btn.pack(pady=20)
        
        # 按 Enter 也可以新增
        chinese_entry.bind("<Return>", lambda e: add_word())
    
    def show_flashcard(self):
        """顯示單字卡學習介面"""
        self.clear_content()
        
        # 選擇資料夾
        folders = self.db.get_all_folders()
        
        if not folders:
            tk.Label(
                self.content_area,
                text="❌ 目前沒有任何單字\n請先新增單字",
                font=("Arial", 14),
                bg="white",
                fg="#ff4d4f"
            ).pack(pady=100)
            return
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="📖 單字卡學習",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 選擇資料夾
        select_frame = tk.Frame(self.content_area, bg="white")
        select_frame.pack(pady=20)
        
        tk.Label(
            select_frame,
            text="選擇資料夾：",
            font=("Arial", 12),
            bg="white"
        ).pack(side="left", padx=10)
        
        folder_var = tk.StringVar()
        folder_combo = ttk.Combobox(
            select_frame,
            textvariable=folder_var,
            values=["全部單字"] + folders,
            font=("Arial", 12),
            state="readonly",
            width=20
        )
        folder_combo.current(0)
        folder_combo.pack(side="left", padx=10)
        
        def start_flashcard():
            selected = folder_var.get()
            
            if selected == "全部單字":
                self.flashcard_words = self.db.get_all_words()
            else:
                self.flashcard_words = self.db.get_words_by_folder(selected)
            
            if not self.flashcard_words:
                messagebox.showwarning("警告", "沒有可學習的單字")
                return
            
            random.shuffle(self.flashcard_words)
            self.current_flashcard_index = 0
            self.display_flashcard()
        
        start_btn = tk.Button(
            select_frame,
            text="開始學習",
            command=start_flashcard,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        start_btn.pack(side="left", padx=10)
    
    def display_flashcard(self):
        """顯示單字卡內容"""
        self.clear_content()
        
        if self.current_flashcard_index >= len(self.flashcard_words):
            # 學習完成
            tk.Label(
                self.content_area,
                text="🎉 恭喜！\n\n已完成所有單字學習",
                font=("Arial", 16, "bold"),
                bg="white",
                fg="#52c41a"
            ).pack(pady=100)
            
            tk.Button(
                self.content_area,
                text="返回",
                command=self.show_flashcard,
                bg="#4a90e2",
                fg="white",
                font=("Arial", 12),
                relief="flat",
                cursor="hand2",
                padx=30,
                pady=10
            ).pack()
            return
        
        word = self.flashcard_words[self.current_flashcard_index]
        
        # 進度
        progress_text = f"📊 進度：{self.current_flashcard_index + 1} / {len(self.flashcard_words)}"
        tk.Label(
            self.content_area,
            text=progress_text,
            font=("Arial", 12),
            bg="white",
            fg="#666"
        ).pack(pady=20)
        
        # 單字卡片
        card_frame = tk.Frame(
            self.content_area,
            bg="#f0f8ff",
            relief="raised",
            borderwidth=2
        )
        card_frame.pack(pady=30, padx=50, fill="both", expand=True)
        
        # 英文
        english_label = tk.Label(
            card_frame,
            text=word.english,
            font=("Arial", 36, "bold"),
            bg="#f0f8ff",
            fg="#333"
        )
        english_label.pack(pady=40)
        
        # 中文（初始隱藏）
        chinese_label = tk.Label(
            card_frame,
            text="",
            font=("Arial", 24),
            bg="#f0f8ff",
            fg="#666"
        )
        chinese_label.pack(pady=20)
        
        # 顯示/隱藏中文的函數
        shown = [False]
        
        def toggle_chinese():
            if not shown[0]:
                chinese_label.config(text=word.chinese)
                show_btn.config(text="隱藏中文")
                shown[0] = True
            else:
                chinese_label.config(text="")
                show_btn.config(text="顯示中文")
                shown[0] = False
        
        # 顯示中文按鈕
        show_btn = tk.Button(
            self.content_area,
            text="顯示中文",
            command=toggle_chinese,
            bg="#ffa500",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        )
        show_btn.pack(pady=10)
        
        # 下一張按鈕
        def next_card():
            self.current_flashcard_index += 1
            self.display_flashcard()
        
        next_btn = tk.Button(
            self.content_area,
            text="下一張 →",
            command=next_card,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        )
        next_btn.pack(pady=10)
    
    def show_test(self):
        """顯示測驗介面"""
        self.clear_content()
        
        folders = self.db.get_all_folders()
        
        if not folders:
            tk.Label(
                self.content_area,
                text="❌ 目前沒有任何單字\n請先新增單字",
                font=("Arial", 14),
                bg="white",
                fg="#ff4d4f"
            ).pack(pady=100)
            return
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="✏️ 開始測驗",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 選擇資料夾
        select_frame = tk.Frame(self.content_area, bg="white")
        select_frame.pack(pady=20)
        
        tk.Label(
            select_frame,
            text="選擇資料夾：",
            font=("Arial", 12),
            bg="white"
        ).pack(side="left", padx=10)
        
        folder_var = tk.StringVar()
        folder_combo = ttk.Combobox(
            select_frame,
            textvariable=folder_var,
            values=["全部單字"] + folders,
            font=("Arial", 12),
            state="readonly",
            width=20
        )
        folder_combo.current(0)
        folder_combo.pack(side="left", padx=10)
        
        def start_test():
            selected = folder_var.get()
            
            if selected == "全部單字":
                self.test_words = self.db.get_all_words()
            else:
                self.test_words = self.db.get_words_by_folder(selected)
            
            if not self.test_words:
                messagebox.showwarning("警告", "沒有可測驗的單字")
                return
            
            random.shuffle(self.test_words)
            self.current_test_index = 0
            self.test_score = 0
            self.display_test_question()
        
        start_btn = tk.Button(
            select_frame,
            text="開始測驗",
            command=start_test,
            bg="#52c41a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        start_btn.pack(side="left", padx=10)
    
    def display_test_question(self):
        """顯示測驗題目"""
        self.clear_content()
        
        if self.current_test_index >= len(self.test_words):
            # 測驗完成
            percentage = (self.test_score / len(self.test_words)) * 100
            
            result_text = f"測驗完成！\n\n得分：{self.test_score} / {len(self.test_words)}\n正確率：{percentage:.1f}%"
            
            tk.Label(
                self.content_area,
                text=result_text,
                font=("Arial", 16, "bold"),
                bg="white",
                fg="#52c41a" if percentage >= 80 else "#ff4d4f"
            ).pack(pady=100)
            
            tk.Button(
                self.content_area,
                text="返回",
                command=self.show_test,
                bg="#4a90e2",
                fg="white",
                font=("Arial", 12),
                relief="flat",
                cursor="hand2",
                padx=30,
                pady=10
            ).pack()
            return
        
        word = self.test_words[self.current_test_index]
        
        # 進度
        progress_text = f"📝 題目：{self.current_test_index + 1} / {len(self.test_words)}　　得分：{self.test_score}"
        tk.Label(
            self.content_area,
            text=progress_text,
            font=("Arial", 12),
            bg="white",
            fg="#666"
        ).pack(pady=20)
        
        # 題目
        question_frame = tk.Frame(self.content_area, bg="white")
        question_frame.pack(pady=30)
        
        tk.Label(
            question_frame,
            text=word.chinese,
            font=("Arial", 28, "bold"),
            bg="white",
            fg="#333"
        ).pack()
        
        # 答案輸入
        answer_entry = tk.Entry(
            self.content_area,
            font=("Arial", 18),
            width=25,
            justify="center"
        )
        answer_entry.pack(pady=20)
        answer_entry.focus()
        
        # 結果顯示
        result_label = tk.Label(
            self.content_area,
            text="",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        result_label.pack(pady=10)
        
        def check_answer():
            answer = answer_entry.get().strip().lower()
            
            if answer == word.english:
                self.test_score += 1
                result_label.config(text=f"✅ 正確！", fg="#52c41a")
            else:
                word.error_count += 1
                self.db.update_error_count(word.id, word.error_count)
                result_label.config(
                    text=f"❌ 錯誤！正確答案：{word.english}",
                    fg="#ff4d4f"
                )
            
            # 1秒後自動下一題
            self.root.after(1500, next_question)
        
        def next_question():
            self.current_test_index += 1
            self.display_test_question()
        
        # 提交按鈕
        submit_btn = tk.Button(
            self.content_area,
            text="提交答案",
            command=check_answer,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        )
        submit_btn.pack(pady=10)
        
        # 按 Enter 提交
        answer_entry.bind("<Return>", lambda e: check_answer())
    
    def show_error_list(self):
        """顯示錯題本"""
        self.clear_content()
        
        error_words = self.db.get_error_words()
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="❌ 錯題本",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        if not error_words:
            tk.Label(
                self.content_area,
                text="🎉 太棒了！\n\n目前沒有錯誤記錄",
                font=("Arial", 14),
                bg="white",
                fg="#52c41a"
            ).pack(pady=100)
            return
        
        # 建立表格
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 建立Treeview
        columns = ("排名", "英文", "中文", "錯誤次數")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 設定欄位
        tree.heading("排名", text="排名")
        tree.heading("英文", text="英文")
        tree.heading("中文", text="中文")
        tree.heading("錯誤次數", text="錯誤次數")
        
        tree.column("排名", width=60, anchor="center")
        tree.column("英文", width=150, anchor="w")
        tree.column("中文", width=200, anchor="w")
        tree.column("錯誤次數", width=100, anchor="center")
        
        # 加入資料
        for i, word in enumerate(error_words, 1):
            tree.insert("", "end", values=(i, word.english, word.chinese, word.error_count))
        
        tree.pack(side="left", fill="both", expand=True)
        
        # 捲軸
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
    
    def show_search(self):
        """顯示查詢介面"""
        self.clear_content()
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="🔍 查詢單字",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 搜尋框
        search_frame = tk.Frame(self.content_area, bg="white")
        search_frame.pack(pady=20)
        
        search_entry = tk.Entry(search_frame, font=("Arial", 14), width=30)
        search_entry.pack(side="left", padx=10)
        search_entry.focus()
        
        # 結果顯示區
        result_frame = tk.Frame(self.content_area, bg="white")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def do_search():
            keyword = search_entry.get().strip()
            
            if not keyword:
                return
            
            # 清空結果區
            for widget in result_frame.winfo_children():
                widget.destroy()
            
            results = self.db.search_words(keyword)
            
            if not results:
                tk.Label(
                    result_frame,
                    text="❌ 查無結果",
                    font=("Arial", 12),
                    bg="white",
                    fg="#ff4d4f"
                ).pack(pady=20)
                return
            
            # 建立表格
            columns = ("英文", "中文", "資料夾", "錯誤次數")
            tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)
            
            tree.heading("英文", text="英文")
            tree.heading("中文", text="中文")
            tree.heading("資料夾", text="資料夾")
            tree.heading("錯誤次數", text="錯誤次數")
            
            tree.column("英文", width=150, anchor="w")
            tree.column("中文", width=200, anchor="w")
            tree.column("資料夾", width=120, anchor="w")
            tree.column("錯誤次數", width=100, anchor="center")
            
            for word in results:
                tree.insert("", "end", values=(
                    word.english, word.chinese, word.folder, word.error_count
                ))
            
            tree.pack(fill="both", expand=True)
            
            # 結果數量
            tk.Label(
                result_frame,
                text=f"找到 {len(results)} 筆結果",
                font=("Arial", 11),
                bg="white",
                fg="#666"
            ).pack(pady=10)
        
        search_btn = tk.Button(
            search_frame,
            text="搜尋",
            command=do_search,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        search_btn.pack(side="left", padx=10)
        
        search_entry.bind("<Return>", lambda e: do_search())
    
    def show_statistics(self):
        """顯示統計資訊"""
        self.clear_content()
        
        stats = self.db.get_statistics()
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="📊 統計資訊",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 統計卡片
        stats_frame = tk.Frame(self.content_area, bg="white")
        stats_frame.pack(pady=20)
        
        def create_stat_card(parent, title, value, icon, color):
            card = tk.Frame(parent, bg=color, relief="raised", borderwidth=2)
            card.pack(side="left", padx=20, pady=10)
            
            tk.Label(
                card,
                text=icon,
                font=("Arial", 30),
                bg=color,
                fg="white"
            ).pack(pady=10)
            
            tk.Label(
                card,
                text=str(value),
                font=("Arial", 24, "bold"),
                bg=color,
                fg="white"
            ).pack()
            
            tk.Label(
                card,
                text=title,
                font=("Arial", 12),
                bg=color,
                fg="white"
            ).pack(pady=10, padx=30)
        
        create_stat_card(stats_frame, "總單字數", stats.get('total_words', 0), "📚", "#4a90e2")
        create_stat_card(stats_frame, "資料夾數", stats.get('total_folders', 0), "📁", "#52c41a")
        create_stat_card(stats_frame, "錯誤單字", stats.get('words_with_errors', 0), "❌", "#ff4d4f")
    
    def show_manage(self):
        """顯示管理介面"""
        self.clear_content()
        
        # 標題
        title = tk.Label(
            self.content_area,
            text="🗑️ 管理單字",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333"
        )
        title.pack(pady=20)
        
        # 搜尋框
        search_frame = tk.Frame(self.content_area, bg="white")
        search_frame.pack(pady=20)
        
        search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
        search_entry.pack(side="left", padx=10)
        
        # 結果顯示
        result_frame = tk.Frame(self.content_area, bg="white")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def search_and_display():
            keyword = search_entry.get().strip()
            
            if not keyword:
                return
            
            for widget in result_frame.winfo_children():
                widget.destroy()
            
            results = self.db.search_words(keyword)
            
            if not results:
                tk.Label(
                    result_frame,
                    text="❌ 查無結果",
                    font=("Arial", 12),
                    bg="white",
                    fg="#ff4d4f"
                ).pack(pady=20)
                return
            
            # 顯示結果
            for word in results:
                word_frame = tk.Frame(result_frame, bg="#f5f5f5", relief="raised", borderwidth=1)
                word_frame.pack(fill="x", pady=5, padx=10)
                
                info_text = f"{word.english} - {word.chinese} ({word.folder})"
                tk.Label(
                    word_frame,
                    text=info_text,
                    font=("Arial", 11),
                    bg="#f5f5f5",
                    anchor="w"
                ).pack(side="left", padx=10, pady=5)
                
                def delete_word(w=word):
                    if messagebox.askyesno("確認", f"確定要刪除 '{w.english}' 嗎？"):
                        if self.db.delete_word(w.id):
                            messagebox.showinfo("成功", "已刪除單字")
                            search_and_display()
                        else:
                            messagebox.showerror("錯誤", "刪除失敗")
                
                delete_btn = tk.Button(
                    word_frame,
                    text="刪除",
                    command=delete_word,
                    bg="#ff4d4f",
                    fg="white",
                    font=("Arial", 9),
                    relief="flat",
                    cursor="hand2",
                    padx=15,
                    pady=3
                )
                delete_btn.pack(side="right", padx=10)
        
        search_btn = tk.Button(
            search_frame,
            text="搜尋",
            command=search_and_display,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        search_btn.pack(side="left")
        
        search_entry.bind("<Return>", lambda e: search_and_display())
    
    def run(self):
        """執行應用程式"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """關閉應用程式時的處理"""
        self.db.close()
        self.root.destroy()


def main():
    """主程式"""
    root = tk.Tk()
    app = VocabularyApp(root)
    app.run()


if __name__ == "__main__":
    main()