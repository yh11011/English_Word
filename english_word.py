#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文單字背誦系統 - SQLite 資料庫版本
"""

import random  # 用來產生隨機數字，讓測驗順序不固定
import sqlite3  # Python 內建的資料庫模組，不需要額外安裝
from typing import List, Optional, Tuple  # 用來標示變數類型，讓程式碼更清楚
from morphology_analyzer import MorphologyAnalyzer, MorphologyDatabase  # 構詞分析模組


class Word:
    """
    單字類別 - 用來表示一個英文單字的所有資訊
    
    什麼是「類別」(Class)？
    就像是一個模板，可以用來建立很多個單字物件
    每個單字物件都有：英文、中文、資料夾、錯誤次數等屬性
    """
    
    def __init__(self, word_id: int, english: str, chinese: str, 
                 folder: str, error_count: int = 0, part_of_speech: str = ''):
        """
        初始化函數 - 建立一個新的單字物件時會執行
        
        參數說明：
        word_id: 單字的編號（在資料庫中的唯一識別碼）
        english: 英文單字
        chinese: 中文意思
        folder: 所屬的資料夾名稱
        error_count: 錯誤次數（預設是 0）
        part_of_speech: 詞性（預設空字串）
        """
        self.id = word_id  # 儲存單字編號
        self.english = english.lower().strip()  # 轉小寫並去除前後空白
        self.chinese = chinese.strip()  # 去除前後空白
        self.folder = folder.strip()  # 去除前後空白（不轉小寫，保留中文級別名稱）
        self.error_count = error_count  # 儲存錯誤次數
        self.part_of_speech = part_of_speech.strip() if part_of_speech else ''  # 詞性
    
    def __str__(self):
        """
        當我們想要印出這個物件時，會顯示的內容
        例如：print(word) 時會顯示單字的所有資訊
        """
        return f"ID:{self.id} | {self.folder} | {self.english} ({self.part_of_speech}) - {self.chinese} (錯誤{self.error_count}次)"


class VocabularyDatabase:
    """
    單字資料庫管理類別
    負責所有與資料庫相關的操作：建立、新增、查詢、更新、刪除
    """
    
    def __init__(self, db_name: str = "vocabulary.db"):
        """
        初始化資料庫連線

        參數說明：
        db_name: 資料庫檔案名稱（預設是 vocabulary.db）

        SQLite 是什麼？
        - 是一種輕量級的資料庫，資料儲存在一個檔案裡
        - 不需要安裝資料庫伺服器，Python 就內建支援
        - 很適合個人使用的小型應用程式
        """
        self.db_name = db_name  # 儲存資料庫檔案名稱
        self.connection = None  # 資料庫連線物件（一開始是空的）
        self.cursor = None  # 資料庫游標物件（用來執行 SQL 指令）

        # 初始化構詞分析器
        self.morphology_db = MorphologyDatabase(db_name)

        # 連接到資料庫
        self.connect()

        # 建立資料表（如果還沒有的話）
        self.create_tables()

        # 建立構詞分析表（如果還沒有的話）
        self.morphology_db.create_morphology_tables()
    
    def connect(self):
        """
        連接到 SQLite 資料庫
        如果資料庫檔案不存在，會自動建立一個新的
        """
        try:
            # sqlite3.connect() 會建立連線，如果檔案不存在會自動建立
            self.connection = sqlite3.connect(self.db_name)
            
            # cursor（游標）就像是一個操作資料庫的「手」
            # 我們透過它來執行 SQL 指令
            self.cursor = self.connection.cursor()
            
            print(f"[成功] 已連接到資料庫: {self.db_name}")
        except sqlite3.Error as e:
            # 如果連線失敗，印出錯誤訊息
            print(f"[錯誤] 無法連接到資料庫: {e}")
    
    def create_tables(self):
        """
        建立資料表 - 如果資料表還不存在的話
        
        什麼是「資料表」(Table)？
        就像是 Excel 的一個工作表，有欄位（column）和資料列（row）
        
        我們的資料表結構：
        - id: 編號（主鍵，自動遞增）
        - english: 英文單字
        - chinese: 中文意思
        - folder: 資料夾名稱
        - error_count: 錯誤次數
        """
        try:
            # CREATE TABLE IF NOT EXISTS：如果資料表不存在才建立
            # INTEGER PRIMARY KEY AUTOINCREMENT：整數型態，主鍵，自動遞增
            # TEXT：文字型態
            # NOT NULL：不能是空值
            # DEFAULT 0：預設值是 0
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT NOT NULL,
                chinese TEXT NOT NULL,
                folder TEXT NOT NULL,
                part_of_speech TEXT DEFAULT '',
                error_count INTEGER DEFAULT 0,
                owner_id INTEGER,
                next_review INTEGER,
                interval INTEGER DEFAULT 0,
                efactor REAL DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Create a simple users table to support ownership/auth (CLI may ignore)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s','now'))
                )
            """)

            # Index to speed up owner-based queries
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_words_owner_id
                ON words(owner_id)
            """)
            
            # 執行 SQL 指令
            self.cursor.execute(create_table_sql)
            
            # 建立索引（讓查詢更快）
            # 索引就像是書的目錄，可以快速找到資料
            # 我們在 folder 和 english 欄位建立索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder 
                ON words(folder)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_english 
                ON words(english)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_count
                ON words(error_count)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder_english
                ON words(folder, english)
            """)
            
            # commit() 是「提交」的意思
            # 資料庫的修改要執行 commit() 才會真正儲存
            self.connection.commit()
            
            print("[成功] 資料表已就緒")
        except sqlite3.Error as e:
            print(f"[錯誤] 建立資料表失敗: {e}")
    
    def add_word(self, english: str, chinese: str, folder: str, part_of_speech: str = '') -> bool:
        """
        新增一個單字到資料庫
        
        參數說明：
        english: 英文單字（可以是片語，例如 "look at"）
        chinese: 中文意思
        folder: 資料夾名稱
        
        回傳值：
        True: 新增成功
        False: 新增失敗
        
        重複檢查邏輯：
        - 只檢查「同一資料夾 + 相同英文」
        - 允許同一個單字出現在不同資料夾（例如：重要單字可能在多個資料夾）
        - 不檢查中文，因為同一個英文可能有不同的翻譯或補充說明
        """
        try:
            # 先檢查是否已經存在相同的單字（在同一個資料夾）
            # ? 是「參數佔位符」，可以防止 SQL 注入攻擊
            # 後面的 (folder, english) 會依序填入兩個 ? 的位置
            check_sql = """
                SELECT id FROM words 
                WHERE folder = ? AND english = ?
            """
            self.cursor.execute(check_sql, (folder.strip(), english.lower()))
            
            # fetchone() 取得一筆資料，如果沒有資料會回傳 None
            existing = self.cursor.fetchone()
            
            if existing:
                # 如果已經存在，回傳 False
                print(f"[警告] 單字 '{english}' 在資料夾 '{folder}' 中已存在")
                return False
            
            # INSERT INTO：插入新資料
            # VALUES (?, ?, ?, ?)：四個問號代表四個參數
            insert_sql = """
                INSERT INTO words (english, chinese, folder, part_of_speech, error_count)
                VALUES (?, ?, ?, ?, 0)
            """
            
            # 執行插入指令，並傳入參數
            self.cursor.execute(insert_sql, (english.lower(), chinese, folder.strip(), part_of_speech))
            
            # 提交變更（儲存到資料庫）
            self.connection.commit()

            # 獲取新插入單字的 ID
            word_id = self.cursor.lastrowid

            # 進行構詞分析並儲存
            if word_id:
                self.morphology_db.analyze_and_store_word(word_id, english.lower())

            print(f"[成功] 已新增單字: {english} - {chinese}")
            return True
            
        except sqlite3.Error as e:
            print(f"[錯誤] 新增單字失敗: {e}")
            return False
    
    def get_all_words(self) -> List[Word]:
        """
        取得所有單字
        
        回傳值：
        單字物件的串列（List）
        
        什麼是「串列」(List)？
        就像是一個可以放很多東西的盒子，每個位置都有編號
        例如：[word1, word2, word3]
        """
        try:
            # SELECT * FROM：選取所有欄位
            # ORDER BY folder, english：按照資料夾和英文排序
            select_sql = """
                SELECT id, english, chinese, folder, error_count, part_of_speech
                FROM words
                ORDER BY folder, english
            """
            
            # 執行查詢
            self.cursor.execute(select_sql)
            
            # fetchall() 取得所有查詢結果
            # 每一筆資料是一個 tuple（元組），例如：(1, 'apple', '蘋果', 'unit1', 0)
            rows = self.cursor.fetchall()
            
            # 建立一個空串列來存放 Word 物件
            words = []
            
            # 遍歷每一筆資料
            for row in rows:
                # row[0] 是 id, row[1] 是 english, 依此類推
                word = Word(
                    word_id=row[0],
                    english=row[1],
                    chinese=row[2],
                    folder=row[3],
                    error_count=row[4],
                    part_of_speech=row[5]
                )
                # 把建立的 Word 物件加入串列
                words.append(word)
            
            return words
            
        except sqlite3.Error as e:
            print(f"[錯誤] 查詢單字失敗: {e}")
            return []
    
    def get_words_by_folder(self, folder: str) -> List[Word]:
        """
        取得指定資料夾的所有單字
        
        參數說明：
        folder: 資料夾名稱
        
        回傳值：
        該資料夾的所有單字物件串列
        """
        try:
            # WHERE folder = ?：只選取符合條件的資料
            select_sql = """
                SELECT id, english, chinese, folder, error_count, part_of_speech
                FROM words
                WHERE folder = ?
                ORDER BY english
            """
            
            self.cursor.execute(select_sql, (folder.strip(),))
            rows = self.cursor.fetchall()
            
            words = []
            for row in rows:
                word = Word(row[0], row[1], row[2], row[3], row[4], row[5])
                words.append(word)
            
            return words
            
        except sqlite3.Error as e:
            print(f"[錯誤] 查詢資料夾單字失敗: {e}")
            return []
    
    def search_words(self, keyword: str) -> List[Word]:
        """
        搜尋包含關鍵字的單字（可搜尋英文或中文）
        
        參數說明：
        keyword: 搜尋關鍵字
        
        回傳值：
        符合條件的單字物件串列
        """
        try:
            # LIKE '%keyword%'：模糊搜尋，% 代表任意字元
            # OR：或者（只要符合其中一個條件即可）
            select_sql = """
                SELECT id, english, chinese, folder, error_count, part_of_speech
                FROM words
                WHERE english LIKE ? OR chinese LIKE ?
                ORDER BY folder, english
            """
            
            # 在關鍵字前後加上 %，代表可以匹配任意字元
            # 例如：'%apple%' 可以匹配 'apple', 'pineapple', 'apple pie'
            search_pattern = f"%{keyword}%"
            
            self.cursor.execute(select_sql, (search_pattern, search_pattern))
            rows = self.cursor.fetchall()
            
            words = []
            for row in rows:
                word = Word(row[0], row[1], row[2], row[3], row[4], row[5])
                words.append(word)
            
            return words
            
        except sqlite3.Error as e:
            print(f"[錯誤] 搜尋單字失敗: {e}")
            return []
    
    def update_error_count(self, word_id: int, error_count: int) -> bool:
        """
        更新單字的錯誤次數
        
        參數說明：
        word_id: 單字編號
        error_count: 新的錯誤次數
        
        回傳值：
        True: 更新成功
        False: 更新失敗
        """
        try:
            # UPDATE：更新資料
            # SET error_count = ?：設定新的錯誤次數
            # WHERE id = ?：只更新指定編號的單字
            update_sql = """
                UPDATE words
                SET error_count = ?
                WHERE id = ?
            """
            
            self.cursor.execute(update_sql, (error_count, word_id))
            self.connection.commit()
            
            return True
            
        except sqlite3.Error as e:
            print(f"[錯誤] 更新錯誤次數失敗: {e}")
            return False
    
    def delete_word(self, word_id: int) -> bool:
        """
        刪除一個單字
        
        參數說明：
        word_id: 要刪除的單字編號
        
        回傳值：
        True: 刪除成功
        False: 刪除失敗
        """
        try:
            # DELETE FROM：刪除資料
            # WHERE id = ?：只刪除指定編號的單字
            delete_sql = """
                DELETE FROM words
                WHERE id = ?
            """
            
            self.cursor.execute(delete_sql, (word_id,))
            self.connection.commit()
            
            print(f"[成功] 已刪除單字 (ID: {word_id})")
            return True
            
        except sqlite3.Error as e:
            print(f"[錯誤] 刪除單字失敗: {e}")
            return False
    
    def get_all_folders(self) -> List[str]:
        """
        取得所有資料夾名稱
        
        回傳值：
        資料夾名稱的串列
        
        SELECT DISTINCT：選取不重複的資料
        例如資料庫有 unit1, unit1, unit2, unit1
        DISTINCT 會回傳 unit1, unit2（去除重複）
        """
        try:
            select_sql = """
                SELECT DISTINCT folder
                FROM words
                ORDER BY folder
            """
            
            self.cursor.execute(select_sql)
            rows = self.cursor.fetchall()
            
            # 把每一筆資料的第一個欄位（資料夾名稱）取出來
            # row[0] 就是資料夾名稱
            folders = [row[0] for row in rows]
            
            return folders
            
        except sqlite3.Error as e:
            print(f"[錯誤] 查詢資料夾失敗: {e}")
            return []
    
    def get_error_words(self) -> List[Word]:
        """
        取得所有有錯誤記錄的單字（按錯誤次數由高到低排序）
        
        回傳值：
        有錯誤記錄的單字物件串列
        """
        try:
            # WHERE error_count > 0：只選取錯誤次數大於 0 的單字
            # ORDER BY error_count DESC：按錯誤次數降序排列（DESC = descending）
            select_sql = """
                SELECT id, english, chinese, folder, error_count, part_of_speech
                FROM words
                WHERE error_count > 0
                ORDER BY error_count DESC, english
            """
            
            self.cursor.execute(select_sql)
            rows = self.cursor.fetchall()
            
            words = []
            for row in rows:
                word = Word(row[0], row[1], row[2], row[3], row[4], row[5])
                words.append(word)
            
            return words
            
        except sqlite3.Error as e:
            print(f"[錯誤] 查詢錯題失敗: {e}")
            return []
    
    def get_statistics(self) -> dict:
        """
        取得統計資訊
        
        回傳值：
        包含各種統計數字的字典（dictionary）
        
        什麼是「字典」(Dictionary)？
        就像是真實的字典，有「鍵」(key) 和「值」(value)
        例如：{'total_words': 100, 'total_folders': 5}
        可以用 stats['total_words'] 來取得 100
        """
        try:
            stats = {}
            
            # 統計總單字數
            # COUNT(*) 會計算有幾筆資料
            self.cursor.execute("SELECT COUNT(*) FROM words")
            stats['total_words'] = self.cursor.fetchone()[0]
            
            # 統計資料夾數量
            # COUNT(DISTINCT folder) 計算有幾個不同的資料夾
            self.cursor.execute("SELECT COUNT(DISTINCT folder) FROM words")
            stats['total_folders'] = self.cursor.fetchone()[0]
            
            # 統計有錯誤記錄的單字數
            self.cursor.execute("SELECT COUNT(*) FROM words WHERE error_count > 0")
            stats['words_with_errors'] = self.cursor.fetchone()[0]
            
            # 統計總錯誤次數
            # SUM(error_count) 會把所有錯誤次數加總
            self.cursor.execute("SELECT SUM(error_count) FROM words")
            result = self.cursor.fetchone()[0]
            stats['total_errors'] = result if result else 0
            
            # 取得各資料夾的單字數量
            # GROUP BY folder：按資料夾分組
            # 例如：unit1 有 5 個單字，unit2 有 3 個單字
            self.cursor.execute("""
                SELECT folder, COUNT(*) as count
                FROM words
                GROUP BY folder
                ORDER BY folder
            """)
            
            # 建立一個字典來存放每個資料夾的單字數量
            folder_counts = {}
            for row in self.cursor.fetchall():
                folder_counts[row[0]] = row[1]
            
            stats['folder_counts'] = folder_counts
            
            return stats
            
        except sqlite3.Error as e:
            print(f"[錯誤] 取得統計資訊失敗: {e}")
            return {}

    def get_word_morphology(self, word_id: int) -> Optional[dict]:
        """
        取得單字的構詞分析

        參數說明：
        word_id: 單字 ID

        回傳值：
        包含構詞分析資訊的字典，如果沒有分析資料則回傳 None
        """
        return self.morphology_db.get_word_morphology(word_id)

    def get_words_by_affix(self, affix: str, affix_type: str, owner_id: Optional[int] = None) -> List[dict]:
        """
        取得包含特定字首或字尾的單字

        參數說明：
        affix: 字首或字尾（不含 - 符號）
        affix_type: 'prefix' 或 'suffix'
        owner_id: 用戶 ID（可選）

        回傳值：
        包含相關單字的列表
        """
        return self.morphology_db.get_words_by_affix(affix, affix_type, owner_id)

    def batch_analyze_all_words(self, owner_id: Optional[int] = None):
        """
        批量分析所有單字的構詞結構

        參數說明：
        owner_id: 用戶 ID（可選），如果提供則只分析該用戶的單字
        """
        self.morphology_db.batch_analyze_all_words(owner_id)

    def get_affix_groups(self) -> dict:
        """
        取得所有字首字尾群組資訊

        回傳值：
        包含字首字尾群組資訊的字典
        """
        return self.morphology_db.analyzer.get_affix_groups()

    def get_morphology_groups_stats(self) -> List[dict]:
        """
        取得構詞群組統計資訊

        回傳值：
        包含每個字首字尾群組統計的列表
        """
        try:
            select_sql = """
                SELECT affix, affix_type, meaning, word_count
                FROM morphology_groups
                WHERE word_count > 0
                ORDER BY word_count DESC, affix
            """
            self.cursor.execute(select_sql)
            rows = self.cursor.fetchall()

            stats = []
            for row in rows:
                stats.append({
                    'affix': row[0],
                    'affix_type': row[1],
                    'meaning': row[2],
                    'word_count': row[3],
                })

            return stats

        except sqlite3.Error as e:
            print(f"[錯誤] 取得構詞群組統計失敗: {e}")
            return []

    def search_words_with_morphology(self, keyword: str, include_morphology: bool = True) -> List[dict]:
        """
        搜尋單字並包含構詞分析資訊

        參數說明：
        keyword: 搜尋關鍵字
        include_morphology: 是否包含構詞分析資訊

        回傳值：
        包含單字和構詞分析的列表
        """
        try:
            # 基本查詢
            base_query = """
                SELECT w.id, w.english, w.chinese, w.folder, w.part_of_speech, w.error_count
                FROM words w
                WHERE w.english LIKE ? OR w.chinese LIKE ?
                ORDER BY w.english
            """

            search_pattern = f"%{keyword}%"
            self.cursor.execute(base_query, (search_pattern, search_pattern))
            rows = self.cursor.fetchall()

            results = []
            for row in rows:
                word_data = {
                    'id': row[0],
                    'english': row[1],
                    'chinese': row[2],
                    'folder': row[3],
                    'part_of_speech': row[4],
                    'error_count': row[5],
                }

                # 如果需要構詞分析，添加相關資訊
                if include_morphology:
                    morphology = self.get_word_morphology(row[0])
                    word_data['morphology'] = morphology

                results.append(word_data)

            return results

        except sqlite3.Error as e:
            print(f"[錯誤] 搜尋單字失敗: {e}")
            return []
    
    def close(self):
        """
        關閉資料庫連線
        
        為什麼要關閉連線？
        - 釋放系統資源
        - 確保所有變更都已儲存
        - 避免資料損毀
        """
        if self.connection:
            self.connection.close()
            print("[資訊] 資料庫連線已關閉")


class VocabularySystem:
    """
    單字背誦系統主類別
    整合資料庫操作和使用者介面
    """
    
    def __init__(self, db_name: str = "vocabulary.db"):
        """
        初始化單字背誦系統
        
        參數說明：
        db_name: 資料庫檔案名稱
        """
        # 建立資料庫物件
        self.db = VocabularyDatabase(db_name)
        print("=" * 60)
        print("歡迎使用英文單字背誦系統（SQLite 資料庫版本）")
        print("=" * 60)
    
    def add_word_interface(self):
        """
        新增單字的使用者介面
        讓使用者可以輸入資料夾名稱和單字資料
        """
        print("\n===== 新增單字 =====")
        print("資料會自動儲存到資料庫\n")
        
        # 輸入資料夾名稱
        while True:
            folder = input("請輸入要存入的資料夾名稱: ").strip()
            if folder:
                break
            print("[錯誤] 資料夾名稱不能為空。")
        
        print("\n請輸入格式: [英文單字/片語] [Tab鍵] [中文意思]")
        print("💡 提示：建議使用 Tab 鍵分隔，特別是片語（例如：look at）")
        print("離開請輸入 'end'\n")
        
        # 持續讀取使用者輸入
        while True:
            user_input = input(">").strip()
            
            # 如果輸入 end 就離開
            if user_input.lower() == 'end':
                print("結束新增單字。")
                break
            
            # 分割輸入（優先使用 Tab，避免片語被錯誤切割）
            # 例如 "look at\t看" 正確切割為 ["look at", "看"]
            # 但 "look at 看" 會被錯誤切成 ["look", "at 看"]
            if '\t' in user_input:
                # 使用 Tab 分隔（推薦方式，適合所有情況）
                parts = user_input.split('\t', 1)
            else:
                # 使用空格分隔（可能有問題）
                # split(None, 1) 會用任何空白字元分隔，最多分成 2 部分
                parts = user_input.split(None, 1)
                
                if len(parts) >= 2:
                    # 檢查英文部分是否包含空格（可能是片語）
                    english_part = parts[0].strip()
                    # 注意：這裡只取第一個空格前的部分作為英文
                    # 所以 "look at 看" 會被切成 english="look", chinese="at 看"
                    # 這就是為什麼片語要用 Tab 的原因！
                    
                    # 給使用者警告
                    print("⚠️  警告：未使用 Tab 鍵分隔，可能無法正確辨識片語")
                    print(f"   系統辨識為：英文 = '{english_part}', 中文 = '{parts[1]}'")
                    confirm = input("   是否正確？繼續請按 y，重新輸入請按 n: ").strip().lower()
                    if confirm != 'y':
                        print("   💡 提示：請使用 Tab 鍵分隔英文和中文")
                        continue
            
            # 檢查格式是否正確
            if len(parts) < 2:
                print("[錯誤] 格式錯誤！")
                print("正確格式: [英文單字/片語] [Tab鍵] [中文意思]")
                print("範例: look at[按Tab鍵]看")
                continue
            
            english = parts[0].strip()
            chinese = parts[1].strip()
            
            # 檢查是否為空
            if not english or not chinese:
                print("[錯誤] 英文或中文不能為空。")
                continue
            
            # 新增到資料庫
            self.db.add_word(english, chinese, folder)
    
    def choose_folder(self) -> Optional[str]:
        """
        選擇資料夾的介面
        
        回傳值：
        None: 離開
        'all': 選擇全部單字
        其他: 資料夾名稱
        """
        # 取得所有資料夾
        folders = self.db.get_all_folders()
        
        if not folders:
            print("[錯誤] 目前沒有任何單字，請先新增單字。")
            return None
        
        print("\n選擇資料夾:")
        for i, folder in enumerate(folders, 1):
            print(f"{i}. {folder}")
        print("99. 全部單字")
        print("0. 離開")
        
        while True:
            try:
                choice = input("\n請選擇: ").strip()
                option = int(choice)
                
                if option == 0:
                    return None
                elif option == 99:
                    return 'all'
                elif 1 <= option <= len(folders):
                    return folders[option - 1]
                else:
                    print("[錯誤] 無效選擇，請重新輸入。")
            except ValueError:
                print("[錯誤] 請輸入數字。")
    
    def show_flashcards(self):
        """
        單字卡學習模式
        顯示英文，按 Enter 後顯示中文
        """
        print("\n===== 單字卡學習模式 =====")
        
        # 選擇資料夾
        folder_choice = self.choose_folder()
        if folder_choice is None:
            return
        
        # 取得單字
        if folder_choice == 'all':
            words = self.db.get_all_words()
        else:
            words = self.db.get_words_by_folder(folder_choice)
        
        if not words:
            print("沒有可顯示的單字。")
            return
        
        # 隨機打亂順序
        random.shuffle(words)
        
        print(f"\n共有 {len(words)} 個單字")
        print("按 Enter 顯示答案，輸入 'q' 離開\n")
        
        # 逐一顯示單字卡
        for i, word in enumerate(words, 1):
            print(f"\n[{i}/{len(words)}]")
            print(f"英文: {word.english}")
            
            user_input = input("按 Enter 顯示中文... ").strip()
            if user_input.lower() == 'q':
                print("離開單字卡模式。")
                break
            
            print(f"中文: {word.chinese}")
            if word.error_count > 0:
                print(f"💡 提示：這個單字你曾經錯過 {word.error_count} 次")
    
    def take_test(self):
        """
        單字測驗模式
        顯示中文，讓使用者輸入英文
        """
        print("\n===== 單字測驗模式 =====")
        
        # 選擇資料夾
        folder_choice = self.choose_folder()
        if folder_choice is None:
            return
        
        # 取得單字
        if folder_choice == 'all':
            words = self.db.get_all_words()
        else:
            words = self.db.get_words_by_folder(folder_choice)
        
        if not words:
            print("沒有可測驗的單字。")
            return
        
        # 隨機打亂順序
        random.shuffle(words)
        
        score = 0  # 得分
        error_list = []  # 錯誤清單
        
        print(f"\n開始測驗，共 {len(words)} 題\n")
        
        # 逐題測驗
        for i, word in enumerate(words, 1):
            print(f"{i}. {word.chinese}")
            answer = input("請輸入英文: ").strip().lower()
            
            # 判斷答案
            if answer == word.english:
                score += 1
                print(f"✓ 正確！目前得分: {score}/{i}\n")
            else:
                # 錯誤次數加 1
                word.error_count += 1
                # 更新資料庫
                self.db.update_error_count(word.id, word.error_count)
                # 加入錯誤清單
                error_list.append(word)
                
                print(f"✗ 錯誤！正確答案是: {word.english}")
                print(f"   (此單字已錯誤 {word.error_count} 次)")
                print(f"   目前得分: {score}/{i}\n")
        
        # 顯示測驗結果
        print("=" * 60)
        print(f"測驗結束！最終得分: {score}/{len(words)} ({score/len(words)*100:.1f}%)")
        
        if error_list:
            print(f"\n本次測驗錯誤單字 ({len(error_list)} 個):")
            for word in error_list:
                print(f"  ❌ {word.english} ({word.chinese})")
        else:
            print("\n🎉 太棒了！全部答對！")
    
    def search_word(self):
        """
        查詢單字功能
        可以用英文或中文關鍵字搜尋
        """
        print("\n===== 查詢單字 =====")
        
        while True:
            keyword = input("\n請輸入要查詢的關鍵字 (中文或英文，輸入 'end' 結束): ").strip()
            
            if keyword.lower() == 'end':
                print("結束查詢。")
                break
            
            if not keyword:
                continue
            
            # 搜尋單字
            found_words = self.db.search_words(keyword)
            
            if not found_words:
                print("❌ 查無此單字。")
            else:
                print(f"\n✓ 找到 {len(found_words)} 筆資料:")
                print("-" * 80)
                print(f"{'ID':<5} {'資料夾':<15} {'英文':<20} {'中文':<25} {'錯誤次數':<10}")
                print("-" * 80)
                
                for word in found_words:
                    print(f"{word.id:<5} {word.folder:<15} {word.english:<20} "
                          f"{word.chinese:<25} {word.error_count:<10}")
    
    def show_error_list(self):
        """
        顯示錯題本
        列出所有錯過的單字，並可進入複習模式
        """
        print("\n===== 錯題本 =====")
        
        # 取得所有錯誤的單字
        error_words = self.db.get_error_words()
        
        if not error_words:
            print("\n🎉 太棒了！目前沒有錯誤紀錄！")
            return
        
        print(f"\n共有 {len(error_words)} 個單字有錯誤記錄:")
        print("-" * 80)
        print(f"{'排名':<6} {'英文':<20} {'中文':<30} {'錯誤次數':<10}")
        print("-" * 80)
        
        for i, word in enumerate(error_words, 1):
            print(f"{i:<6} {word.english:<20} {word.chinese:<30} {word.error_count:<10}")
        
        # 詢問是否要複習
        print("\n是否要複習這些錯題？(y/n): ", end='')
        choice = input().strip().lower()
        
        if choice == 'y':
            self._review_errors(error_words)
    
    def _review_errors(self, error_words: List[Word]):
        """
        複習錯題
        
        參數說明：
        error_words: 要複習的單字串列
        """
        print("\n===== 錯題複習 =====")
        
        # 隨機打亂順序
        random.shuffle(error_words)
        
        score = 0
        
        for i, word in enumerate(error_words, 1):
            print(f"\n[{i}/{len(error_words)}] {word.chinese}")
            answer = input("請輸入英文: ").strip().lower()
            
            if answer == word.english:
                score += 1
                print(f"✓ 正確！")
            else:
                word.error_count += 1
                self.db.update_error_count(word.id, word.error_count)
                print(f"✗ 錯誤！正確答案: {word.english}")
        
        print(f"\n複習結束！得分: {score}/{len(error_words)} ({score/len(error_words)*100:.1f}%)")
    
    def show_statistics(self):
        """
        顯示統計資訊
        包括單字總數、資料夾數量、錯誤統計等
        """
        print("\n===== 統計資訊 =====")
        
        # 取得統計資料
        stats = self.db.get_statistics()
        
        print(f"\n📚 單字總數    : {stats['total_words']} 個")
        print(f"📁 資料夾數量  : {stats['total_folders']} 個")
        print(f"❌ 有錯誤記錄  : {stats['words_with_errors']} 個單字")
        print(f"📊 總錯誤次數  : {stats['total_errors']} 次")
        
        if stats['folder_counts']:
            print("\n各資料夾單字數量:")
            print("-" * 40)
            for folder, count in stats['folder_counts'].items():
                print(f"  {folder:<20} : {count:>5} 個單字")
    
    def delete_word_interface(self):
        """
        刪除單字的介面
        先搜尋單字，然後選擇要刪除的項目
        """
        print("\n===== 刪除單字 =====")
        
        keyword = input("請輸入要刪除的單字（英文或中文）: ").strip()
        
        if not keyword:
            print("未輸入關鍵字，取消刪除。")
            return
        
        # 搜尋單字
        found_words = self.db.search_words(keyword)
        
        if not found_words:
            print("查無此單字。")
            return
        
        print(f"\n找到 {len(found_words)} 筆資料:")
        for i, word in enumerate(found_words, 1):
            print(f"{i}. [ID:{word.id}] {word.english} - {word.chinese} ({word.folder})")
        
        print("0. 取消")
        
        # 選擇要刪除的單字
        try:
            choice = int(input("\n請選擇要刪除的單字編號: ").strip())
            
            if choice == 0:
                print("取消刪除。")
                return
            
            if 1 <= choice <= len(found_words):
                word_to_delete = found_words[choice - 1]
                
                # 再次確認
                confirm = input(f"確定要刪除 '{word_to_delete.english}' 嗎？(y/n): ").strip().lower()
                
                if confirm == 'y':
                    self.db.delete_word(word_to_delete.id)
                else:
                    print("取消刪除。")
            else:
                print("無效的選擇。")
                
        except ValueError:
            print("請輸入數字。")
    
    def run(self):
        """
        主程式執行迴圈
        顯示選單並處理使用者選擇
        """
        while True:
            # 顯示主選單
            print("\n" + "=" * 60)
            print("===== 英文單字背誦系統 (SQLite 版本) =====")
            print("=" * 60)
            print("1. 新增單字")
            print("2. 單字卡學習")
            print("3. 開始測驗")
            print("4. 錯題本")
            print("5. 查詢單字")
            print("6. 統計資訊")
            print("7. 構詞分析")
            print("8. 刪除單字")
            print("9. 離開程式")
            print("=" * 60)
            
            try:
                choice = input("請輸入 1~9 以選擇功能: ").strip()
                
                if choice == '1':
                    self.add_word_interface()
                elif choice == '2':
                    self.show_flashcards()
                elif choice == '3':
                    self.take_test()
                elif choice == '4':
                    self.show_error_list()
                elif choice == '5':
                    self.search_word()
                elif choice == '6':
                    self.show_statistics()
                elif choice == '7':
                    self.show_morphology_menu()
                elif choice == '8':
                    self.delete_word_interface()
                elif choice == '9':
                    print("\n👋 掰掰！要記得複習喔！")
                    break
                else:
                    print("[錯誤] 請輸入 1~9 的數字。")
            
            except KeyboardInterrupt:
                # 如果使用者按 Ctrl+C，優雅地結束程式
                print("\n\n程式被中斷。")
                print("掰掰！")
                break
            except Exception as e:
                # 捕捉其他錯誤
                print(f"[錯誤] 發生錯誤: {e}")
        
        # 關閉資料庫連線
        self.db.close()

    def show_morphology_menu(self):
        """
        構詞分析功能選單
        """
        while True:
            print("\n" + "=" * 60)
            print("===== 構詞分析功能 =====")
            print("=" * 60)
            print("1. 查看構詞群組統計")
            print("2. 查看特定群組單字")
            print("3. 分析單字構詞")
            print("4. 批量分析所有單字")
            print("5. 構詞學習模式")
            print("0. 返回主選單")
            print("=" * 60)

            try:
                choice = input("請輸入 0~5 以選擇功能: ").strip()

                if choice == '0':
                    break
                elif choice == '1':
                    self.show_morphology_groups()
                elif choice == '2':
                    self.show_group_words()
                elif choice == '3':
                    self.analyze_single_word()
                elif choice == '4':
                    self.batch_analyze_words()
                elif choice == '5':
                    self.morphology_learning()
                else:
                    print("[錯誤] 請輸入 0~5 的數字。")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[錯誤] 發生錯誤: {e}")

    def show_morphology_groups(self):
        """
        顯示構詞群組統計
        """
        print("\n===== 構詞群組統計 =====")

        stats = self.db.get_morphology_groups_stats()

        if not stats:
            print("目前沒有構詞群組資料，請先進行「批量分析所有單字」")
            return

        print(f"\n📊 找到 {len(stats)} 個構詞群組：\n")

        # 分類顯示
        prefixes = [s for s in stats if s['affix_type'] == 'prefix']
        suffixes = [s for s in stats if s['affix_type'] == 'suffix']

        if prefixes:
            print("🟦 字首群組：")
            for stat in prefixes:
                print(f"  {stat['affix']}- ({stat['meaning']}) - {stat['word_count']} 個單字")

        if suffixes:
            print("\n🟧 字尾群組：")
            for stat in suffixes:
                print(f"  -{stat['affix']} ({stat['meaning']}) - {stat['word_count']} 個單字")

        input("\n按 Enter 繼續...")

    def show_group_words(self):
        """
        顯示特定群組的單字
        """
        print("\n===== 查看群組單字 =====")

        stats = self.db.get_morphology_groups_stats()

        if not stats:
            print("目前沒有構詞群組資料")
            return

        # 顯示可選群組
        print("\n可選擇的群組：")
        for i, stat in enumerate(stats, 1):
            affix_display = f"{stat['affix']}-" if stat['affix_type'] == 'prefix' else f"-{stat['affix']}"
            print(f"{i}. {affix_display} ({stat['meaning']}) - {stat['word_count']} 個單字")

        print("0. 返回")

        try:
            choice = int(input("\n請選擇群組: ").strip())

            if choice == 0:
                return
            elif 1 <= choice <= len(stats):
                selected_stat = stats[choice - 1]
                words = self.db.get_words_by_affix(
                    selected_stat['affix'],
                    selected_stat['affix_type']
                )

                if words:
                    affix_display = f"{selected_stat['affix']}-" if selected_stat['affix_type'] == 'prefix' else f"-{selected_stat['affix']}"
                    print(f"\n=== {affix_display} 群組單字 ({selected_stat['meaning']}) ===")
                    print(f"共 {len(words)} 個單字：\n")

                    for i, word in enumerate(words, 1):
                        print(f"{i:3d}. {word['english']:15} - {word['chinese'][:50]}")
                        if i % 20 == 0 and i < len(words):
                            if input("\n繼續顯示？(y/n): ").lower() != 'y':
                                break
                else:
                    print("該群組目前沒有單字")

                input("\n按 Enter 繼續...")
            else:
                print("[錯誤] 無效選擇")

        except ValueError:
            print("[錯誤] 請輸入數字")

    def analyze_single_word(self):
        """
        分析單一單字的構詞
        """
        print("\n===== 分析單字構詞 =====")

        word = input("請輸入要分析的單字: ").strip().lower()

        if not word:
            print("單字不能為空")
            return

        # 使用構詞分析器分析
        from morphology_analyzer import MorphologyAnalyzer
        analyzer = MorphologyAnalyzer()
        analysis = analyzer.analyze_word(word)

        print(f"\n單字：{word}")
        print("構詞分析：")

        parts = []
        if analysis.prefix:
            parts.append(f"🟦 字首: {analysis.prefix.text} ({analysis.prefix.meaning})")
        if analysis.root:
            parts.append(f"🟩 詞根: {analysis.root.text} ({analysis.root.meaning})")
        if analysis.suffix:
            parts.append(f"🟧 字尾: {analysis.suffix.text} ({analysis.suffix.meaning})")

        if parts:
            for part in parts:
                print(f"  {part}")
        else:
            print("  無法識別明顯的構詞組件")

        # 檢查是否在資料庫中
        all_words = self.db.get_all_words()
        matching_words = [w for w in all_words if w.english == word]

        if matching_words:
            print(f"\n在資料庫中找到 {len(matching_words)} 個相符的單字：")
            for w in matching_words:
                print(f"  📁 {w.folder}: {w.chinese}")
        else:
            print("\n此單字不在您的資料庫中")

        input("\n按 Enter 繼續...")

    def batch_analyze_words(self):
        """
        批量分析所有單字的構詞
        """
        print("\n===== 批量構詞分析 =====")

        confirm = input("這個操作會分析您資料庫中所有的單字，可能需要一些時間。\n確定要繼續嗎？(y/n): ")

        if confirm.lower() != 'y':
            return

        print("\n開始批量分析...")

        try:
            self.db.batch_analyze_all_words()
            print("✅ 批量分析完成！")
            print("現在您可以查看構詞群組統計了。")
        except Exception as e:
            print(f"❌ 分析失敗: {e}")

        input("\n按 Enter 繼續...")

    def morphology_learning(self):
        """
        構詞學習模式
        """
        print("\n===== 構詞學習模式 =====")

        stats = self.db.get_morphology_groups_stats()

        if not stats:
            print("目前沒有構詞群組資料，請先進行「批量分析所有單字」")
            return

        # 顯示可選群組（只顯示有足夠單字的群組）
        valid_groups = [s for s in stats if s['word_count'] >= 3]

        if not valid_groups:
            print("沒有足夠的構詞群組進行學習（需要至少3個單字）")
            return

        print("\n可選擇的學習群組：")
        for i, stat in enumerate(valid_groups, 1):
            affix_display = f"{stat['affix']}-" if stat['affix_type'] == 'prefix' else f"-{stat['affix']}"
            print(f"{i}. {affix_display} ({stat['meaning']}) - {stat['word_count']} 個單字")

        print("0. 返回")

        try:
            choice = int(input("\n請選擇學習群組: ").strip())

            if choice == 0:
                return
            elif 1 <= choice <= len(valid_groups):
                selected_stat = valid_groups[choice - 1]
                self.start_morphology_learning(selected_stat)
            else:
                print("[錯誤] 無效選擇")

        except ValueError:
            print("[錯誤] 請輸入數字")

    def start_morphology_learning(self, group_stat):
        """
        開始構詞學習會話
        """
        affix_display = f"{group_stat['affix']}-" if group_stat['affix_type'] == 'prefix' else f"-{group_stat['affix']}"

        print(f"\n=== 學習 {affix_display} 群組 ({group_stat['meaning']}) ===")

        # 取得群組單字
        words = self.db.get_words_by_affix(group_stat['affix'], group_stat['affix_type'])

        if len(words) < 3:
            print("該群組單字數量不足")
            return

        # 隨機選擇最多10個單字
        import random
        if len(words) > 10:
            words = random.sample(words, 10)
        else:
            random.shuffle(words)

        print(f"將學習 {len(words)} 個單字")
        print("對於每個單字，輸入 'y' 表示認識，'n' 表示不認識")
        print("輸入 'q' 可隨時退出\n")

        correct_count = 0
        total_count = 0

        for i, word in enumerate(words, 1):
            print(f"[{i}/{len(words)}] {word['english']}")

            while True:
                answer = input("認識這個單字嗎？(y/n/q): ").strip().lower()

                if answer == 'q':
                    print("\n學習會話已結束")
                    return
                elif answer in ['y', 'n']:
                    total_count += 1
                    if answer == 'y':
                        correct_count += 1

                    # 顯示答案
                    print(f"✅ 答案：{word['chinese']}")

                    # 顯示構詞分析
                    morphology = self.db.get_word_morphology(word['id'])
                    if morphology:
                        parts = []
                        if morphology['prefix']:
                            parts.append(f"{morphology['prefix']}({morphology['prefix_meaning']})")
                        if morphology['root']:
                            parts.append(f"{morphology['root']}")
                        if morphology['suffix']:
                            parts.append(f"{morphology['suffix']}({morphology['suffix_meaning']})")
                        if parts:
                            print(f"🔍 構詞：{' + '.join(parts)}")

                    print() # 空行
                    break
                else:
                    print("請輸入 y、n 或 q")

        # 顯示學習結果
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        print("=" * 40)
        print(f"學習完成！")
        print(f"總單字數：{total_count}")
        print(f"認識單字：{correct_count}")
        print(f"正確率：{accuracy:.1f}%")
        print("=" * 40)

        input("\n按 Enter 繼續...")


def main():
    """
    主程式入口
    這是程式開始執行的地方
    """
    # 建立系統物件
    system = VocabularySystem()
    
    # 執行主程式
    system.run()


# 這行確保只有直接執行這個檔案時才會執行 main()
# 如果是被其他程式 import，就不會自動執行
if __name__ == "__main__":
    main()