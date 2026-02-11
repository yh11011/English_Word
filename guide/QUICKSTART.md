# 快速開始指南

## 🚀 三步驟開始使用

### 步驟 1: 執行主程式
```bash
python vocabulary_system_sqlite.py
```

第一次執行會自動建立 `vocabulary.db` 資料庫。

### 步驟 2: 新增你的第一個單字
```
選擇功能: 1
請輸入要存入的資料夾名稱: unit1
>apple 蘋果
>banana 香蕉
>end
```

### 步驟 3: 開始學習！
- 選擇功能 2: 單字卡學習
- 選擇功能 3: 開始測驗

---

## 📦 檔案說明

### 主程式檔案
- **vocabulary_system_sqlite.py** - 主程式（有詳細註釋）
- **vocabulary.db** - SQLite 資料庫檔案（自動生成）

### 文件檔案
- **SQLITE_TUTORIAL.md** - SQLite 新手教學
- **README_SQLITE.md** - 完整說明文件
- **QUICKSTART.md** - 本檔案（快速開始）

### 工具檔案
- **migrate_to_sqlite.py** - 資料遷移工具

---

## 🔄 從舊版文字檔升級

如果你之前使用文字檔版本（english_word.txt），可以使用遷移工具：

```bash
python migrate_to_sqlite.py
```

選擇功能 1，輸入舊檔案名稱即可自動轉換！

---

## 💡 常用功能

### 查看統計資訊
```
主選單 → 6. 統計資訊
```
可以看到：
- 總單字數
- 各資料夾的單字數量
- 錯誤統計

### 查詢單字
```
主選單 → 5. 查詢單字
輸入關鍵字: apple
```
支援模糊搜尋，英文中文都可以！

### 複習錯題
```
主選單 → 4. 錯題本
```
會顯示所有錯過的單字，還可以直接進入複習模式。

---

## 🎯 學習技巧

### 1. 分資料夾管理
```
unit1: 基礎單字
unit2: 進階單字
daily: 每日一字
important: 重要單字
```

### 2. 善用測驗功能
- 測驗後會自動記錄錯誤次數
- 常錯的單字會出現在錯題本
- 可以針對錯題加強練習

### 3. 定期複習
- 每天用「單字卡」快速複習
- 每週做一次「全部單字」測驗
- 每月清理一次錯題本

---

## 🛠️ 進階使用

### 用 DB Browser 查看資料庫
1. 下載 [DB Browser for SQLite](https://sqlitebrowser.org/)
2. 開啟 `vocabulary.db`
3. 可以直接查看、編輯資料

### 備份資料
```bash
# 方法 1: 複製資料庫檔案
cp vocabulary.db vocabulary_backup.db

# 方法 2: 匯出成文字檔
python migrate_to_sqlite.py
選擇功能 2
```

### 在其他電腦使用
只要複製 `vocabulary.db` 檔案到新電腦即可！

---

## ❓ 遇到問題？

### 問題 1: 找不到資料庫檔案
**解答**: 資料庫檔案在程式同一個目錄下，檔名是 `vocabulary.db`

### 問題 2: 資料不見了
**解答**: 檢查是否在正確的目錄執行程式，或查看是否有備份檔案

### 問題 3: 程式執行錯誤
**解答**: 確認 Python 版本是否為 3.6 以上

---

## 📚 延伸閱讀

- **SQLITE_TUTORIAL.md** - 詳細的 SQLite 教學
- **README_SQLITE.md** - 完整功能說明
- [SQLite 官方文件](https://www.sqlite.org/docs.html)

---

## 🎉 開始你的英文學習之旅！

記住：
- ✅ 每天持續練習比一次大量背誦更有效
- ✅ 複習錯題比不斷學新單字更重要
- ✅ 建立自己的學習節奏

祝你學習愉快！🚀
