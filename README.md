# 英文單字背誦系統 - SQLite 資料庫版本

> 🎓 專為英文學習者設計的單字管理系統，使用 SQLite 資料庫儲存

## ✨ 特色功能

### 📚 核心功能
- ✅ **單字管理** - 新增、查詢、刪除單字
- ✅ **資料夾分類** - 按主題或課程分類管理
- ✅ **單字卡學習** - 互動式學習模式
- ✅ **測驗模式** - 自動記錄錯誤次數
- ✅ **錯題本** - 追蹤學習弱點
- ✅ **統計報表** - 全面的學習數據分析

### 🚀 技術特色
- ⚡ **SQLite 資料庫** - 快速、可靠、零配置
- 🔒 **資料安全** - 交易機制保護資料完整性
- 🎯 **索引優化** - 查詢速度快
- 💻 **詳細註釋** - 每行程式碼都有中文說明
- 📖 **新手友善** - 完整的教學文件

---

## 📋 目錄

- [系統需求](#系統需求)
- [安裝說明](#安裝說明)
- [快速開始](#快速開始)
- [功能說明](#功能說明)
- [檔案結構](#檔案結構)
- [常見問題](#常見問題)
- [進階使用](#進階使用)
- [貢獻指南](#貢獻指南)
- [授權條款](#授權條款)

---

## 🔧 系統需求

- **Python 3.6 或以上版本**
- **SQLite3**（Python 內建，無需額外安裝）
- **作業系統**: Windows / macOS / Linux

---

## 📥 安裝說明

### 方法 1: 直接執行（推薦）

1. 下載所有檔案到同一個資料夾
2. 打開終端機（命令提示字元）
3. 切換到檔案所在目錄
4. 執行程式：

```bash
python vocabulary_system_sqlite.py
```

### 方法 2: 克隆專案

```bash
git clone https://github.com/yourusername/vocabulary-system.git
cd vocabulary-system
python vocabulary_system_sqlite.py
```

---

## 🚀 快速開始

### 第一次使用

1. **執行程式**
   ```bash
   python vocabulary_system_sqlite.py
   ```
   
2. **新增單字**（選擇功能 1）
   ```
   請輸入要存入的資料夾名稱: unit1
   >apple 蘋果
   >banana 香蕉
   >orange 橘子
   >end
   ```

3. **開始學習**
   - 功能 2: 單字卡學習
   - 功能 3: 開始測驗

### 從舊版升級

如果你之前使用文字檔版本，使用遷移工具：

```bash
python migrate_to_sqlite.py
```

選擇功能 1，即可將 `english_word.txt` 轉換成 SQLite 資料庫。

---

## 📖 功能說明

### 1️⃣ 新增單字

**操作步驟：**
1. 選擇功能 1
2. 輸入資料夾名稱（例如：unit1）
3. 輸入格式：`英文單字 [空格或Tab] 中文意思`
4. 輸入 `end` 結束

**範例：**
```
請輸入要存入的資料夾名稱: daily
>amazing 令人驚奇的
>brilliant 絕妙的
>challenge 挑戰
>end
```

**特色：**
- ✅ 自動檢查重複
- ✅ 即時儲存到資料庫
- ✅ 支援 Tab 或空格分隔

---

### 2️⃣ 單字卡學習

**操作步驟：**
1. 選擇功能 2
2. 選擇資料夾或全部單字
3. 看到英文，按 Enter 顯示中文
4. 輸入 `q` 離開

**特色：**
- ✅ 隨機順序
- ✅ 顯示錯誤次數提示
- ✅ 適合快速複習

---

### 3️⃣ 開始測驗

**操作步驟：**
1. 選擇功能 3
2. 選擇資料夾或全部單字
3. 看到中文，輸入英文
4. 系統判斷對錯並記錄

**特色：**
- ✅ 自動記錄錯誤次數
- ✅ 即時顯示得分
- ✅ 測驗結束顯示錯題清單
- ✅ 隨機出題順序

**範例：**
```
1. 蘋果
請輸入英文: apple
✓ 正確！目前得分: 1/1

2. 香蕉
請輸入英文: banna
✗ 錯誤！正確答案是: banana
   (此單字已錯誤 1 次)
   目前得分: 1/2
```

---

### 4️⃣ 錯題本

**操作步驟：**
1. 選擇功能 4
2. 查看所有錯過的單字
3. 可選擇進入複習模式

**特色：**
- ✅ 按錯誤次數排序
- ✅ 一目了然找出弱點
- ✅ 可直接複習錯題

**範例：**
```
===== 錯題本 =====

共有 3 個單字有錯誤記錄:
排名   英文                 中文                      錯誤次數
----------------------------------------------------------------------
1      embarrass            使尷尬                     5
2      necessary            必要的                     3
3      separate             分開的                     2

是否要複習這些錯題？(y/n):
```

---

### 5️⃣ 查詢單字

**操作步驟：**
1. 選擇功能 5
2. 輸入中文或英文關鍵字
3. 查看搜尋結果

**特色：**
- ✅ 支援模糊搜尋
- ✅ 中英文都可搜尋
- ✅ 顯示完整資訊（包含資料夾、錯誤次數）

**範例：**
```
請輸入要查詢的關鍵字: app

✓ 找到 3 筆資料:
ID    資料夾          英文                 中文                      錯誤次數
-------------------------------------------------------------------------------
1     unit1          apple                蘋果                       0
15    unit2          application          應用程式                    1
23    unit3          pineapple           鳳梨                       0
```

---

### 6️⃣ 統計資訊

**操作步驟：**
1. 選擇功能 6
2. 查看完整的學習數據

**特色：**
- ✅ 總單字數和資料夾數量
- ✅ 錯誤統計
- ✅ 各資料夾單字分佈

**範例：**
```
===== 統計資訊 =====

📚 單字總數    : 150 個
📁 資料夾數量  : 5 個
❌ 有錯誤記錄  : 23 個單字
📊 總錯誤次數  : 45 次

各資料夾單字數量:
----------------------------------------
  unit1                :    30 個單字
  unit2                :    35 個單字
  unit3                :    40 個單字
  daily                :    25 個單字
  important            :    20 個單字
```

---

### 7️⃣ 刪除單字

**操作步驟：**
1. 選擇功能 7
2. 輸入要刪除的單字（英文或中文）
3. 選擇要刪除的項目
4. 確認刪除

**特色：**
- ✅ 先搜尋再刪除
- ✅ 需要確認，避免誤刪
- ✅ 立即生效

---

## 📁 檔案結構

```
vocabulary-system/
│
├── vocabulary_system_sqlite.py    # 主程式（有詳細註釋）
├── migrate_to_sqlite.py          # 資料遷移工具
│
├── vocabulary.db                 # SQLite 資料庫（自動生成）
│
├── README_SQLITE.md              # 本檔案
├── SQLITE_TUTORIAL.md            # SQLite 新手教學
├── QUICKSTART.md                 # 快速開始指南
│
└── english_word.txt              # 舊版文字檔（可選）
```

---

## 🗄️ 資料庫結構

### words 資料表

| 欄位名稱     | 資料型態 | 說明             | 限制          |
|-------------|---------|------------------|--------------|
| id          | INTEGER | 主鍵（自動遞增）   | PRIMARY KEY  |
| english     | TEXT    | 英文單字          | NOT NULL     |
| chinese     | TEXT    | 中文意思          | NOT NULL     |
| folder      | TEXT    | 資料夾名稱        | NOT NULL     |
| error_count | INTEGER | 錯誤次數          | DEFAULT 0    |

### 索引

- `idx_folder`: 在 `folder` 欄位建立索引（加快按資料夾查詢）
- `idx_english`: 在 `english` 欄位建立索引（加快按英文查詢）

---

## ❓ 常見問題

### Q1: 為什麼同一個單字可以出現在不同資料夾？

**A:** 這是刻意設計的功能！

**使用情境：**
```
unit1/review - 複習（課本第一單元）
unit2/review - 複習（課本第二單元）
important/review - 複習（重要單字集）
```

同一個英文單字可能：
- 出現在不同課程單元
- 同時是重點複習單字
- 需要在不同情境下學習

**重複檢查邏輯：**
- ✅ 同一資料夾 + 相同英文 = 重複（不允許）
- ✅ 不同資料夾 + 相同英文 = 允許
- ✅ 同一資料夾 + 相同英文 + 不同中文 = 重複（會提示覆蓋）

---

### Q2: 為什麼建議用 Tab 鍵而不是空格？

**A:** 因為英文片語中可能包含空格！

**問題範例：**
```
# 使用空格分隔（錯誤）
>look at 看
系統會切割成：英文 = "look", 中文 = "at 看" ❌

# 使用 Tab 分隔（正確）
>look at[按Tab]看
系統會切割成：英文 = "look at", 中文 = "看" ✅
```

**常見片語範例：**
- look at（看）
- give up（放棄）
- take care of（照顧）
- in front of（在...前面）

**建議做法：**
1. 養成使用 Tab 鍵的習慣
2. 如果不小心用空格，系統會給警告
3. 確認無誤後可以繼續

---

### Q3: 資料庫檔案在哪裡？

**A:** 在程式同一個目錄下，檔名是 `vocabulary.db`

你可以：
- 複製這個檔案來備份
- 用 [DB Browser for SQLite](https://sqlitebrowser.org/) 打開查看
- 移動到其他電腦繼續使用

---

### Q4: 如何備份資料？

**方法 1: 直接複製資料庫檔案**
```bash
cp vocabulary.db vocabulary_backup.db
```

**方法 2: 匯出成文字檔**
```bash
python migrate_to_sqlite.py
# 選擇功能 2
```

---

### Q5: 可以在手機上使用嗎？

**A:** 目前是命令列版本，主要在電腦使用。

未來計畫：
- 開發網頁版（可用手機瀏覽器）
- 開發 App 版本

---

### Q6: 資料會不會遺失？

**A:** SQLite 非常可靠，但建議：
- 定期備份 `vocabulary.db`
- 重要操作後關閉程式（會自動儲存）
- 不要在程式運行時刪除或移動資料庫檔案

---

### Q7: 可以多人使用同一個資料庫嗎？

**A:** 目前版本是單人使用。

如果需要多人使用：
1. 每個人用自己的資料庫檔案
2. 或改用 MySQL/PostgreSQL（需要修改程式）

---

### Q8: 如何匯入大量單字？

**方法 1: 準備文字檔**

建立 `my_words.txt`，格式：
```
資料夾\t英文\t中文\t錯誤次數
unit1	apple	蘋果	0
unit1	banana	香蕉	0
```

然後執行：
```bash
python migrate_to_sqlite.py
# 選擇功能 1，輸入檔案名稱
```

**方法 2: 寫個簡單的 Python 腳本**

```python
import sqlite3

conn = sqlite3.connect("vocabulary.db")
cursor = conn.cursor()

words = [
    ("apple", "蘋果", "unit1"),
    ("banana", "香蕉", "unit1"),
    # ... 更多單字
]

for english, chinese, folder in words:
    cursor.execute("""
        INSERT INTO words (english, chinese, folder, error_count)
        VALUES (?, ?, ?, 0)
    """, (english, chinese, folder))

conn.commit()
conn.close()
```

---

## 🔨 進階使用

### 用 DB Browser 管理資料

1. 下載 [DB Browser for SQLite](https://sqlitebrowser.org/)
2. 開啟 `vocabulary.db`
3. 可以：
   - 直接查看和編輯資料
   - 執行 SQL 查詢
   - 匯出資料
   - 建立備份

### 自訂 SQL 查詢

連接到資料庫後可以執行各種查詢：

```python
import sqlite3

conn = sqlite3.connect("vocabulary.db")
cursor = conn.cursor()

# 找出最常錯的 10 個單字
cursor.execute("""
    SELECT english, chinese, error_count
    FROM words
    WHERE error_count > 0
    ORDER BY error_count DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]} (錯誤 {row[2]} 次)")

conn.close()
```

### 匯出成 CSV

```python
import sqlite3
import csv

conn = sqlite3.connect("vocabulary.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM words")
rows = cursor.fetchall()

with open('words.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', '英文', '中文', '資料夾', '錯誤次數'])
    writer.writerows(rows)

conn.close()
```

---

## 🎓 學習建議

### 每日學習計劃

**早上（10分鐘）**
- 用「單字卡」快速複習昨天的單字

**中午（5分鐘）**
- 新增 3-5 個新單字

**晚上（15分鐘）**
- 做一次「測驗」
- 複習錯題本

### 長期策略

**每週**
- 週末做一次「全部單字」測驗
- 整理錯題本，找出常錯的單字類型

**每月**
- 重置錯誤次數，重新開始
- 統計學習成果

**小技巧**
- ✅ 按主題分資料夾（動物、食物、動詞等）
- ✅ 建立「每日一字」資料夾
- ✅ 重要單字單獨放一個資料夾
- ✅ 利用零碎時間複習

---

## 🤝 貢獻指南

歡迎提供改進建議！

### 如何貢獻

1. Fork 本專案
2. 建立新的分支 (`git checkout -b feature/新功能`)
3. 提交你的修改 (`git commit -am '新增某功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 建立 Pull Request

### 改進方向

- [ ] 加入語音發音功能
- [ ] 開發網頁版介面
- [ ] 加入間隔重複演算法
- [ ] 支援圖片和例句
- [ ] 多使用者系統
- [ ] 學習進度圖表
- [ ] 匯出 Anki 格式

---

## 📄 授權條款

MIT License

Copyright (c) 2024

本專案採用 MIT 授權，可以自由使用、修改和分發。

---

## 🙏 致謝

感謝所有使用本程式的學習者！

特別感謝：
- Python 社群
- SQLite 團隊
- 所有提供回饋的使用者

---

## 📞 聯絡方式

- 問題回報: [GitHub Issues](https://github.com/yourusername/vocabulary-system/issues)
- 功能建議: [GitHub Discussions](https://github.com/yourusername/vocabulary-system/discussions)

---

## 🎉 開始你的學習之旅！

記住：**持續學習比一次學很多更重要！**

每天 15 分鐘，一年後你會累積超過 1000 個單字！

**Good luck and have fun learning! 🚀**
