#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabMaster - 現代化桌面版 GUI
參考現代 Dashboard 設計，提供優雅的學習體驗
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
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
            self.cursor.execute("""
                SELECT id FROM words WHERE folder = ? AND english = ?
            """, (folder.lower(), english.lower()))
            
            if self.cursor.fetchone():
                return False
            
            self.cursor.execute("""
                INSERT INTO words (english, chinese, folder, error_count)
                VALUES (?, ?, ?, 0)
            """, (english.lower(), chinese, folder.lower()))
            
            self.connection.commit()
            return True
        except sqlite3.Error:
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
                FROM words WHERE english LIKE ? OR chinese LIKE ?
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


class ModernVocabApp:
    """現代化單字背誦應用程式"""
    
    # 配色方案（參考提供的設計）
    PRIMARY_BLUE = "#3B9DF2"
    BG_LIGHT = "#F8FAFC"
    WHITE = "#FFFFFF"
    TEXT_DARK = "#1E293B"
    SIDEBAR_TEXT = "#64748B"
    BORDER = "#E2E8F0"
    HOVER_BG = "#EEF6FF"
    
    def __init__(self, root):
        self.root = root
        self.root.title("VocabMaster - Dashboard")
        
        # 設定視窗大小和位置
        window_width = 1200
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 設定背景色
        self.root.configure(bg=self.BG_LIGHT)
        
        # 初始化資料庫
        self.db = VocabularyDatabase()
        
        # 測驗相關變數
        self.test_words = []
        self.current_test_index = 0
        self.test_score = 0
        
        # 單字卡相關變數
        self.flashcard_words = []
        self.current_flashcard_index = 0
        self.flashcard_flipped = False
        
        # 設定字型
        self.setup_fonts()
        
        # 建立介面
        self.create_interface()
        
        # 載入統計資訊
        self.load_statistics()
    
    def setup_fonts(self):
        """設定字型"""
        self.font_title = font.Font(family="Arial", size=24, weight="bold")
        self.font_heading = font.Font(family="Arial", size=16, weight="bold")
        self.font_normal = font.Font(family="Arial", size=10)
        self.font_large = font.Font(family="Arial", size=14)
    
    def create_interface(self):
        """建立主介面"""
        # 側邊欄
        self.create_sidebar()
        
        # 主內容區
        self.create_main_content()
        
        # 預設顯示 Dashboard
        self.show_dashboard()
    
    def create_sidebar(self):
        """建立側邊欄"""
        sidebar = tk.Frame(self.root, bg=self.WHITE, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = tk.Frame(sidebar, bg=self.WHITE)
        logo_frame.pack(pady=24, padx=24)
        
        tk.Label(
            logo_frame,
            text="📚 VocabMaster",
            font=("Arial", 14, "bold"),
            bg=self.WHITE,
            fg=self.PRIMARY_BLUE
        ).pack()
        
        # 選單項目
        menu_items = [
            ("📊 Dashboard", "dashboard"),
            ("➕ New Word", "add"),
            ("📖 Flashcards", "flashcard"),
            ("❓ Test", "test"),
            ("⚠️ Wrong Answers", "errors"),
            ("📈 Statistics", "stats"),
            ("⚙️ Management", "manage"),
        ]
        
        self.menu_buttons = {}
        for text, page in menu_items:
            btn = tk.Button(
                sidebar,
                text=text,
                font=self.font_normal,
                bg=self.WHITE,
                fg=self.SIDEBAR_TEXT,
                relief="flat",
                anchor="w",
                padx=24,
                pady=12,
                cursor="hand2",
                command=lambda p=page: self.navigate_to(p)
            )
            btn.pack(fill="x")
            self.menu_buttons[page] = btn
            
            # 懸停效果
            btn.bind("<Enter>", lambda e, b=btn: self.on_menu_hover(b, True))
            btn.bind("<Leave>", lambda e, b=btn: self.on_menu_hover(b, False))
        
        # 用戶資訊
        user_frame = tk.Frame(sidebar, bg=self.WHITE)
        user_frame.pack(side="bottom", fill="x", pady=20, padx=24)
        
        # 頭像
        avatar = tk.Label(
            user_frame,
            text="JD",
            font=("Arial", 10, "bold"),
            bg="#DBEAFE",
            fg=self.PRIMARY_BLUE,
            width=3,
            height=1
        )
        avatar.pack(side="left", padx=(0, 12))
        
        # 用戶名稱
        user_info = tk.Frame(user_frame, bg=self.WHITE)
        user_info.pack(side="left")
        
        tk.Label(
            user_info,
            text="John Doe",
            font=("Arial", 9, "bold"),
            bg=self.WHITE,
            fg=self.TEXT_DARK
        ).pack(anchor="w")
        
        tk.Label(
            user_info,
            text="Free Account",
            font=("Arial", 8),
            bg=self.WHITE,
            fg=self.SIDEBAR_TEXT
        ).pack(anchor="w")
    
    def on_menu_hover(self, button, is_hover):
        """選單懸停效果"""
        if button.cget("bg") != self.HOVER_BG:  # 不是活動狀態
            if is_hover:
                button.configure(bg=self.HOVER_BG, fg=self.PRIMARY_BLUE)
            else:
                button.configure(bg=self.WHITE, fg=self.SIDEBAR_TEXT)
    
    def create_main_content(self):
        """建立主內容區"""
        self.main_frame = tk.Frame(self.root, bg=self.BG_LIGHT)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=40, pady=20)
        
        # 頂部導航
        self.create_top_nav()
        
        # 內容容器
        self.content_container = tk.Frame(self.main_frame, bg=self.BG_LIGHT)
        self.content_container.pack(fill="both", expand=True)
    
    def create_top_nav(self):
        """建立頂部導航"""
        top_nav = tk.Frame(self.main_frame, bg=self.BG_LIGHT)
        top_nav.pack(fill="x", pady=(0, 20))
        
        # 搜尋框
        search_frame = tk.Frame(top_nav, bg="#F1F5F9")
        search_frame.pack(side="left")
        
        tk.Label(
            search_frame,
            text="🔍",
            bg="#F1F5F9",
            fg=self.SIDEBAR_TEXT
        ).pack(side="left", padx=(8, 4))
        
        self.search_entry = tk.Entry(
            search_frame,
            font=self.font_normal,
            bg="#F1F5F9",
            relief="flat",
            width=25
        )
        self.search_entry.pack(side="left", padx=(0, 8), pady=8)
        self.search_entry.insert(0, "Search words...")
        
        # 右側按鈕
        btn_frame = tk.Frame(top_nav, bg=self.BG_LIGHT)
        btn_frame.pack(side="right")
        
        add_btn = tk.Button(
            btn_frame,
            text="+ Add New",
            font=("Arial", 9, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=lambda: self.navigate_to("add")
        )
        add_btn.pack()
    
    def clear_content(self):
        """清空內容區"""
        for widget in self.content_container.winfo_children():
            widget.destroy()
    
    def navigate_to(self, page):
        """導航到指定頁面"""
        # 重置所有選單按鈕
        for btn in self.menu_buttons.values():
            btn.configure(bg=self.WHITE, fg=self.SIDEBAR_TEXT)
        
        # 設定當前按鈕為活動狀態
        if page in self.menu_buttons:
            self.menu_buttons[page].configure(bg=self.HOVER_BG, fg=self.PRIMARY_BLUE)
        
        # 顯示對應頁面
        if page == "dashboard":
            self.show_dashboard()
        elif page == "add":
            self.show_add_word()
        elif page == "flashcard":
            self.show_flashcard_setup()
        elif page == "test":
            self.show_test_setup()
        elif page == "errors":
            self.show_errors()
        elif page == "stats":
            self.show_statistics()
        elif page == "manage":
            self.show_manage()
    
    def show_dashboard(self):
        """顯示 Dashboard"""
        self.clear_content()
        
        # Hero Banner
        hero = tk.Frame(self.content_container, bg=self.PRIMARY_BLUE)
        hero.pack(fill="x", pady=(0, 24))
        
        hero_content = tk.Frame(hero, bg=self.PRIMARY_BLUE)
        hero_content.pack(padx=40, pady=40)
        
        tk.Label(
            hero_content,
            text="Welcome back, Learner!",
            font=("Arial", 22, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white"
        ).pack(anchor="w")
        
        tk.Label(
            hero_content,
            text="Ready to master some new English words today?\nYou've already made great progress this week. Keep up the momentum!",
            font=("Arial", 10),
            bg=self.PRIMARY_BLUE,
            fg="white",
            justify="left"
        ).pack(anchor="w", pady=(12, 24))
        
        # Hero 按鈕
        btn_frame = tk.Frame(hero_content, bg=self.PRIMARY_BLUE)
        btn_frame.pack(anchor="w")
        
        tk.Button(
            btn_frame,
            text="Continue Lesson",
            font=("Arial", 10, "bold"),
            bg="white",
            fg=self.PRIMARY_BLUE,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=lambda: self.navigate_to("flashcard")
        ).pack(side="left", padx=(0, 12))
        
        tk.Button(
            btn_frame,
            text="View Goals",
            font=("Arial", 10, "bold"),
            bg="#5BA8F5",  # 稍淺的藍色代替半透明效果
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=lambda: self.navigate_to("stats")
        ).pack(side="left")
        
        # 統計卡片
        self.create_stat_cards()
        
        # 快速動作
        tk.Label(
            self.content_container,
            text="⚡ Quick Actions",
            font=("Arial", 14, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(32, 20))
        
        self.create_action_cards()
    
    def create_stat_cards(self):
        """建立統計卡片"""
        stats_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        stats_frame.pack(fill="x", pady=(0, 32))
        
        stats = self.db.get_statistics()
        
        cards_data = [
            ("📄", "TOTAL WORDS", stats.get('total_words', 0), "#E0F2FE", "#0EA5E9"),
            ("📁", "FOLDERS", stats.get('total_folders', 0), "#FFEDD5", "#F97316"),
            ("🔄", "WRONG RECORDS", stats.get('words_with_errors', 0), "#FEE2E2", "#EF4444"),
        ]
        
        for i, (icon, label, value, bg, fg) in enumerate(cards_data):
            card = tk.Frame(stats_frame, bg=self.WHITE)
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 10, 0))
            
            inner = tk.Frame(card, bg=self.WHITE)
            inner.pack(padx=20, pady=20)
            
            # Icon
            icon_label = tk.Label(
                inner,
                text=icon,
                font=("Arial", 20),
                bg=bg,
                fg=fg,
                width=2,
                height=1
            )
            icon_label.pack(side="left", padx=(0, 16))
            
            # 文字
            text_frame = tk.Frame(inner, bg=self.WHITE)
            text_frame.pack(side="left")
            
            tk.Label(
                text_frame,
                text=label,
                font=("Arial", 8),
                bg=self.WHITE,
                fg=self.SIDEBAR_TEXT
            ).pack(anchor="w")
            
            tk.Label(
                text_frame,
                text=str(value),
                font=("Arial", 20, "bold"),
                bg=self.WHITE,
                fg=self.TEXT_DARK
            ).pack(anchor="w")
    
    def create_action_cards(self):
        """建立動作卡片"""
        actions_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        actions_frame.pack(fill="both", expand=True)
        
        actions = [
            ("➕", "New Word", "Expand your dictionary by adding new vocabulary.", self.WHITE, self.TEXT_DARK, "add"),
            ("📖", "Flashcards", "Review your words using spaced repetition.", self.WHITE, self.TEXT_DARK, "flashcard"),
            ("❓", "Start Test", "Challenge yourself with a quiz.", self.PRIMARY_BLUE, "white", "test"),
        ]
        
        for i, (icon, title, desc, bg, fg, page) in enumerate(actions):
            card = tk.Frame(actions_frame, bg=bg, cursor="hand2")
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 20, 0))
            card.bind("<Button-1>", lambda e, p=page: self.navigate_to(p))
            
            inner = tk.Frame(card, bg=bg)
            inner.pack(padx=24, pady=30)
            
            # Icon
            icon_bg = "#5BA8F5" if bg == self.PRIMARY_BLUE else "#F1F5F9"
            icon_fg = "white" if bg == self.PRIMARY_BLUE else self.TEXT_DARK
            
            tk.Label(
                inner,
                text=icon,
                font=("Arial", 16),
                bg=bg,
                fg=icon_fg,
                width=2
            ).pack(anchor="w", pady=(0, 12))
            
            tk.Label(
                inner,
                text=title,
                font=("Arial", 12, "bold"),
                bg=bg,
                fg=fg
            ).pack(anchor="w", pady=(0, 8))
            
            desc_fg = "#E0F2FE" if bg == self.PRIMARY_BLUE else self.SIDEBAR_TEXT
            tk.Label(
                inner,
                text=desc,
                font=("Arial", 9),
                bg=bg,
                fg=desc_fg,
                wraplength=200,
                justify="left"
            ).pack(anchor="w")
    
    def show_add_word(self):
        """顯示新增單字頁面"""
        self.clear_content()
        
        # 標題
        tk.Label(
            self.content_container,
            text="➕ Add New Word",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 8))
        
        tk.Label(
            self.content_container,
            text="Expand your vocabulary library",
            font=("Arial", 10),
            bg=self.BG_LIGHT,
            fg=self.SIDEBAR_TEXT
        ).pack(anchor="w", pady=(0, 32))
        
        # 表單卡片
        form_card = tk.Frame(self.content_container, bg=self.WHITE)
        form_card.pack(fill="both", expand=True, pady=(0, 20))
        
        form_inner = tk.Frame(form_card, bg=self.WHITE)
        form_inner.pack(padx=40, pady=40, fill="both", expand=True)
        
        # 表單欄位
        fields = [
            ("Folder", "folder"),
            ("English Word", "english"),
            ("Chinese Meaning", "chinese"),
        ]
        
        entries = {}
        for label_text, field_name in fields:
            field_frame = tk.Frame(form_inner, bg=self.WHITE)
            field_frame.pack(fill="x", pady=(0, 20))
            
            tk.Label(
                field_frame,
                text=label_text,
                font=("Arial", 10, "bold"),
                bg=self.WHITE,
                fg=self.TEXT_DARK
            ).pack(anchor="w", pady=(0, 8))
            
            entry = tk.Entry(
                field_frame,
                font=("Arial", 11),
                relief="solid",
                borderwidth=1
            )
            entry.pack(fill="x", ipady=8)
            entries[field_name] = entry
        
        # 結果訊息
        self.add_result_label = tk.Label(
            form_inner,
            text="",
            font=("Arial", 10),
            bg=self.WHITE
        )
        self.add_result_label.pack(pady=(0, 20))
        
        # 提交按鈕
        def submit():
            folder = entries["folder"].get().strip()
            english = entries["english"].get().strip()
            chinese = entries["chinese"].get().strip()
            
            if not folder or not english or not chinese:
                self.add_result_label.config(
                    text="❌ All fields are required!",
                    fg="#EF4444"
                )
                return
            
            if self.db.add_word(english, chinese, folder):
                self.add_result_label.config(
                    text=f"✅ Successfully added: {english}",
                    fg="#10B981"
                )
                entries["english"].delete(0, tk.END)
                entries["chinese"].delete(0, tk.END)
                entries["english"].focus()
                self.load_statistics()
            else:
                self.add_result_label.config(
                    text="⚠️ Word already exists!",
                    fg="#F97316"
                )
        
        tk.Button(
            form_inner,
            text="Add Word",
            font=("Arial", 11, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=submit,
            pady=12
        ).pack(fill="x")
        
        entries["chinese"].bind("<Return>", lambda e: submit())
    
    def show_flashcard_setup(self):
        """顯示單字卡設定頁面"""
        self.clear_content()
        
        tk.Label(
            self.content_container,
            text="📖 Flashcard Learning",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 32))
        
        # 選擇框
        select_card = tk.Frame(self.content_container, bg=self.WHITE)
        select_card.pack(fill="x", pady=(0, 20))
        
        inner = tk.Frame(select_card, bg=self.WHITE)
        inner.pack(padx=40, pady=40)
        
        tk.Label(
            inner,
            text="Select Folder",
            font=("Arial", 10, "bold"),
            bg=self.WHITE,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 12))
        
        self.flashcard_folder_var = tk.StringVar()
        folders = ["All Words"] + self.db.get_all_folders()
        
        folder_menu = ttk.Combobox(
            inner,
            textvariable=self.flashcard_folder_var,
            values=folders,
            font=("Arial", 11),
            state="readonly"
        )
        folder_menu.pack(fill="x", pady=(0, 20))
        if folders:
            folder_menu.current(0)
        
        tk.Button(
            inner,
            text="Start Learning",
            font=("Arial", 11, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self.start_flashcard,
            pady=12
        ).pack(fill="x")
    
    def start_flashcard(self):
        """開始單字卡學習"""
        folder = self.flashcard_folder_var.get()
        
        if folder == "All Words":
            self.flashcard_words = self.db.get_all_words()
        else:
            self.flashcard_words = self.db.get_words_by_folder(folder)
        
        if not self.flashcard_words:
            messagebox.showwarning("Warning", "No words available for learning")
            return
        
        random.shuffle(self.flashcard_words)
        self.current_flashcard_index = 0
        self.flashcard_flipped = False
        
        self.show_flashcard()
    
    def show_flashcard(self):
        """顯示單字卡"""
        self.clear_content()
        
        if self.current_flashcard_index >= len(self.flashcard_words):
            self.show_flashcard_complete()
            return
        
        word = self.flashcard_words[self.current_flashcard_index]
        
        # 進度
        progress = (self.current_flashcard_index + 1) / len(self.flashcard_words)
        
        tk.Label(
            self.content_container,
            text=f"Card {self.current_flashcard_index + 1} / {len(self.flashcard_words)}",
            font=("Arial", 10),
            bg=self.BG_LIGHT,
            fg=self.SIDEBAR_TEXT
        ).pack(anchor="w", pady=(0, 20))
        
        # 卡片
        card = tk.Frame(self.content_container, bg=self.PRIMARY_BLUE)
        card.pack(fill="both", expand=True, pady=(0, 20))
        
        self.card_label = tk.Label(
            card,
            text=word.english.upper(),
            font=("Arial", 36, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white"
        )
        self.card_label.pack(expand=True)
        
        # 按鈕
        btn_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        btn_frame.pack()
        
        def flip_card():
            if self.flashcard_flipped:
                self.card_label.config(text=word.english.upper())
            else:
                self.card_label.config(text=word.chinese)
            self.flashcard_flipped = not self.flashcard_flipped
        
        def next_card():
            self.current_flashcard_index += 1
            self.flashcard_flipped = False
            self.show_flashcard()
        
        tk.Button(
            btn_frame,
            text="Flip Card",
            font=("Arial", 11, "bold"),
            bg="#F97316",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=flip_card,
            padx=30,
            pady=12
        ).pack(side="left", padx=(0, 12))
        
        tk.Button(
            btn_frame,
            text="Next →",
            font=("Arial", 11, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=next_card,
            padx=30,
            pady=12
        ).pack(side="left")
    
    def show_flashcard_complete(self):
        """顯示學習完成"""
        self.clear_content()
        
        complete_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        complete_frame.pack(expand=True)
        
        tk.Label(
            complete_frame,
            text="🎉",
            font=("Arial", 60),
            bg=self.BG_LIGHT
        ).pack()
        
        tk.Label(
            complete_frame,
            text="Learning Complete!",
            font=("Arial", 24, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(pady=20)
        
        tk.Button(
            complete_frame,
            text="Back to Dashboard",
            font=("Arial", 11, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.navigate_to("dashboard"),
            padx=30,
            pady=12
        ).pack()
    
    def show_test_setup(self):
        """顯示測驗設定"""
        self.clear_content()
        
        tk.Label(
            self.content_container,
            text="❓ Start Test",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 32))
        
        select_card = tk.Frame(self.content_container, bg=self.WHITE)
        select_card.pack(fill="x")
        
        inner = tk.Frame(select_card, bg=self.WHITE)
        inner.pack(padx=40, pady=40)
        
        tk.Label(
            inner,
            text="Select Folder",
            font=("Arial", 10, "bold"),
            bg=self.WHITE,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 12))
        
        self.test_folder_var = tk.StringVar()
        folders = ["All Words"] + self.db.get_all_folders()
        
        folder_menu = ttk.Combobox(
            inner,
            textvariable=self.test_folder_var,
            values=folders,
            font=("Arial", 11),
            state="readonly"
        )
        folder_menu.pack(fill="x", pady=(0, 20))
        if folders:
            folder_menu.current(0)
        
        tk.Button(
            inner,
            text="Start Test",
            font=("Arial", 11, "bold"),
            bg="#10B981",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self.start_test,
            pady=12
        ).pack(fill="x")
    
    def start_test(self):
        """開始測驗"""
        folder = self.test_folder_var.get()
        
        if folder == "All Words":
            self.test_words = self.db.get_all_words()
        else:
            self.test_words = self.db.get_words_by_folder(folder)
        
        if not self.test_words:
            messagebox.showwarning("Warning", "No words available for testing")
            return
        
        random.shuffle(self.test_words)
        self.current_test_index = 0
        self.test_score = 0
        
        self.show_test_question()
    
    def show_test_question(self):
        """顯示測驗題目"""
        self.clear_content()
        
        if self.current_test_index >= len(self.test_words):
            self.show_test_complete()
            return
        
        word = self.test_words[self.current_test_index]
        
        # 進度和得分
        header = tk.Frame(self.content_container, bg=self.WHITE)
        header.pack(fill="x", pady=(0, 20))
        
        inner = tk.Frame(header, bg=self.WHITE)
        inner.pack(padx=20, pady=20)
        
        tk.Label(
            inner,
            text=f"Question {self.current_test_index + 1} / {len(self.test_words)}",
            font=("Arial", 10),
            bg=self.WHITE,
            fg=self.SIDEBAR_TEXT
        ).pack(side="left")
        
        tk.Label(
            inner,
            text=f"Score: {self.test_score}",
            font=("Arial", 12, "bold"),
            bg=self.WHITE,
            fg=self.PRIMARY_BLUE
        ).pack(side="right")
        
        # 題目卡片
        question_card = tk.Frame(self.content_container, bg=self.WHITE)
        question_card.pack(fill="both", expand=True, pady=(0, 20))
        
        q_inner = tk.Frame(question_card, bg=self.WHITE)
        q_inner.pack(padx=40, pady=60)
        
        tk.Label(
            q_inner,
            text=word.chinese,
            font=("Arial", 28, "bold"),
            bg=self.WHITE,
            fg=self.TEXT_DARK
        ).pack(pady=(0, 30))
        
        self.answer_entry = tk.Entry(
            q_inner,
            font=("Arial", 14),
            justify="center",
            relief="solid",
            borderwidth=2
        )
        self.answer_entry.pack(fill="x", ipady=10, pady=(0, 20))
        self.answer_entry.focus()
        
        self.test_result_label = tk.Label(
            q_inner,
            text="",
            font=("Arial", 12, "bold"),
            bg=self.WHITE
        )
        self.test_result_label.pack(pady=(0, 20))
        
        def check():
            answer = self.answer_entry.get().strip().lower()
            
            if not answer:
                return
            
            if answer == word.english:
                self.test_score += 1
                self.test_result_label.config(text="✅ Correct!", fg="#10B981")
            else:
                word.error_count += 1
                self.db.update_error_count(word.id, word.error_count)
                self.test_result_label.config(
                    text=f"❌ Wrong! Answer: {word.english}",
                    fg="#EF4444"
                )
            
            self.root.after(1500, self.next_question)
        
        tk.Button(
            q_inner,
            text="Submit Answer",
            font=("Arial", 11, "bold"),
            bg="#10B981",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=check,
            pady=12
        ).pack(fill="x")
        
        self.answer_entry.bind("<Return>", lambda e: check())
    
    def next_question(self):
        """下一題"""
        self.current_test_index += 1
        self.show_test_question()
    
    def show_test_complete(self):
        """顯示測驗完成"""
        self.clear_content()
        
        percentage = (self.test_score / len(self.test_words)) * 100
        
        complete_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        complete_frame.pack(expand=True)
        
        tk.Label(
            complete_frame,
            text="🎉",
            font=("Arial", 60),
            bg=self.BG_LIGHT
        ).pack()
        
        tk.Label(
            complete_frame,
            text="Test Complete!",
            font=("Arial", 24, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(pady=20)
        
        tk.Label(
            complete_frame,
            text=f"{self.test_score} / {len(self.test_words)} ({percentage:.1f}%)",
            font=("Arial", 32, "bold"),
            bg=self.BG_LIGHT,
            fg=self.PRIMARY_BLUE if percentage >= 80 else "#EF4444"
        ).pack(pady=20)
        
        tk.Button(
            complete_frame,
            text="Back to Dashboard",
            font=("Arial", 11, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.navigate_to("dashboard"),
            padx=30,
            pady=12
        ).pack()
        
        self.load_statistics()
    
    def show_errors(self):
        """顯示錯題本"""
        self.clear_content()
        
        tk.Label(
            self.content_container,
            text="⚠️ Wrong Answers",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 32))
        
        errors = self.db.get_error_words()
        
        if not errors:
            complete_frame = tk.Frame(self.content_container, bg=self.BG_LIGHT)
            complete_frame.pack(expand=True)
            
            tk.Label(
                complete_frame,
                text="🎉",
                font=("Arial", 60),
                bg=self.BG_LIGHT
            ).pack()
            
            tk.Label(
                complete_frame,
                text="No wrong records!",
                font=("Arial", 20, "bold"),
                bg=self.BG_LIGHT,
                fg="#10B981"
            ).pack(pady=20)
            return
        
        # 錯題列表
        list_card = tk.Frame(self.content_container, bg=self.WHITE)
        list_card.pack(fill="both", expand=True)
        
        # 建立 Treeview
        tree_frame = tk.Frame(list_card, bg=self.WHITE)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        columns = ("Rank", "English", "Chinese", "Folder", "Errors")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center" if col in ["Rank", "Errors"] else "w")
        
        for i, word in enumerate(errors, 1):
            tree.insert("", "end", values=(
                i, word.english, word.chinese, word.folder, word.error_count
            ))
        
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
    
    def show_statistics(self):
        """顯示統計資訊"""
        self.clear_content()
        
        tk.Label(
            self.content_container,
            text="📈 Statistics",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 32))
        
        stats = self.db.get_statistics()
        
        # 使用與 dashboard 相同的統計卡片
        self.create_stat_cards()
    
    def show_manage(self):
        """顯示管理頁面"""
        self.clear_content()
        
        tk.Label(
            self.content_container,
            text="⚙️ Management",
            font=("Arial", 20, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(anchor="w", pady=(0, 32))
        
        # 搜尋框
        search_card = tk.Frame(self.content_container, bg=self.WHITE)
        search_card.pack(fill="x", pady=(0, 20))
        
        inner = tk.Frame(search_card, bg=self.WHITE)
        inner.pack(padx=20, pady=20)
        
        search_entry = tk.Entry(
            inner,
            font=("Arial", 11),
            relief="solid",
            borderwidth=1
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        
        def do_search():
            keyword = search_entry.get().strip()
            if not keyword:
                return
            
            results = self.db.search_words(keyword)
            
            # 清空結果區
            for widget in result_container.winfo_children():
                widget.destroy()
            
            if not results:
                tk.Label(
                    result_container,
                    text="No results found",
                    font=("Arial", 12),
                    bg=self.BG_LIGHT,
                    fg=self.SIDEBAR_TEXT
                ).pack(pady=40)
                return
            
            for word in results:
                item = tk.Frame(result_container, bg=self.WHITE)
                item.pack(fill="x", pady=5)
                
                tk.Label(
                    item,
                    text=f"{word.english} - {word.chinese} ({word.folder})",
                    font=("Arial", 10),
                    bg=self.WHITE,
                    fg=self.TEXT_DARK
                ).pack(side="left", padx=20, pady=10)
                
                def delete_word(wid=word.id):
                    if messagebox.askyesno("Confirm", "Delete this word?"):
                        if self.db.delete_word(wid):
                            do_search()
                            self.load_statistics()
                
                tk.Button(
                    item,
                    text="Delete",
                    font=("Arial", 9),
                    bg="#EF4444",
                    fg="white",
                    relief="flat",
                    cursor="hand2",
                    command=delete_word,
                    padx=15,
                    pady=5
                ).pack(side="right", padx=20)
        
        tk.Button(
            inner,
            text="Search",
            font=("Arial", 10, "bold"),
            bg=self.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=do_search,
            padx=20,
            pady=8
        ).pack(side="left", padx=(12, 0))
        
        search_entry.bind("<Return>", lambda e: do_search())
        
        # 結果容器
        result_container = tk.Frame(self.content_container, bg=self.BG_LIGHT)
        result_container.pack(fill="both", expand=True)
    
    def load_statistics(self):
        """載入統計資訊（用於更新 dashboard）"""
        pass  # 已在 show_dashboard 中實現
    
    def run(self):
        """執行應用程式"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """關閉應用程式"""
        self.db.close()
        self.root.destroy()


def main():
    """主程式"""
    root = tk.Tk()
    app = ModernVocabApp(root)
    app.run()


if __name__ == "__main__":
    main()