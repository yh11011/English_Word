# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

注意：從現在起，請僅以中文回覆。

## 概覽

小型以 SQLite 為後端的英語單字學習系統，提供 CLI 與 Flask Web API + 前端模板。支援 SRS（SM-2 間隔複習）、構詞分析（morphology）、AI 例句/翻譯服務。

## 快速上手

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 執行 Web 伺服器（開發用）
python3 web.py
# 執行 CLI
python3 english_word.py
```

## 測試

```bash
pip install pytest
pytest                                        # 全部測試
pytest tests/test_web_api.py                  # 僅 API 測試
pytest tests/test_database.py::test_add_word  # 單一測試函式
```

測試檔案位於 `tests/`：`test_database.py`（DB CRUD）、`test_web_api.py`（Flask test client）、`test_auth.py`（認證）。

## 重要環境變數

| 變數 | 說明 | 預設 |
|------|------|------|
| `SECRET_KEY` | Flask session 金鑰 | 隨機（開發用，警告） |
| `API_TOKEN` | Bearer token（mutating API） | 未設定（僅 CSRF） |
| `DB_NAME` | SQLite 檔案路徑 | `vocabulary.db` |
| `MIGRATE_SRS` | 設為 `1` 才允許 ALTER TABLE 加 SRS 欄位 | `0` |

## 高階架構

### 三層分工

1. **資料層** — `english_word.py`
   - `Word`（model）：`english_word.py:12`
   - `VocabularyDatabase`（SQLite CRUD + SM-2 SRS）：`english_word.py:49`

2. **業務/CLI 層** — `english_word.py`
   - `VocabularySystem`（CLI 互動迴圈）：`english_word.py:532`

3. **Web/API 層** — `web.py`
   - Flask app + REST API（`/api/words`、`/api/quiz`、`/api/srs` 等）
   - `get_db` / `init_db`：`web.py:44` / `web.py:60`
   - 主要路由起點：`web.py:60`（在 `init_db` 之後）
   - 前端模板：`templates/vocabmaster.html`（主視圖）、`static/app.js`、`static/app.css`

### 輔助模組

- `morphology_analyzer.py` — 英文字首/字根/字尾分析（`MorphologyDatabase`、`MorphologyAnalyzer`），web.py 與 CLI 共用。
- `ai_services.py` — `AIServiceManager`：統一管理 AI 功能（例句、翻譯、個性化推薦）；優先嘗試 `enhanced_ai_service.py`（需額外安裝）。
- `wsgi.py` — gunicorn 生產入口，搭配 `gunicorn.conf.py`。

### DB Schema（words 資料表）

核心欄位：`id, english, chinese, folder, error_count, owner_id`
SRS 欄位（需 `MIGRATE_SRS=1` 遷移後才存在）：`next_review, interval, efactor, repetitions`

### 工具腳本（tools/）

- `import_export.py` — CSV 匯入/匯出
- `migrate_add_srs.py` — 手動加入 SRS 欄位的遷移腳本
- `migrate_add_ai.py` — 加入 AI 相關欄位的遷移腳本

## 何時要先進入計畫模式（EnterPlanMode）

- 變更 DB schema（ALTER TABLE、新增遷移腳本）
- 同時修改多個檔案且影響 API 外部契約
- 新增背景服務、排程、外部 API 整合
- 大規模重構影響模組邊界

## 開發工作流程（必須遵守）

每次修改都要遵循以下順序，**不可跳步**：

1. **實作**：完成單一功能或修復
2. **測試**：啟動伺服器、執行 curl 或 pytest 驗證功能正常
3. **Commit + Push**：測試通過後才提交並推送到 GitHub
4. **下一個**：確認上傳成功後，才開始下一項修改

> 原則：一次只做一件事，測試通過再繼續。不允許累積多個未測試的修改後一次上傳。

## 安全注意

- 所有 SQL 使用參數化查詢（禁止 f-string 拼接 SQL）。
- `SECRET_KEY` / `API_TOKEN` 從環境變數讀取，勿硬編碼。
- 生產部署請關閉 `debug=True`（`web.py` 末段）。
