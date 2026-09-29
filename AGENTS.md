# Word — 專案工作守則

開工先讀同目錄的 `PROJECT_MAP.md`，依功能入口定位；共同合作方式、獨立判斷及交付規則由 `~/.codex/AGENTS.md` 管理。此檔只補充本專案規則。

## 特殊規則

- SQL 參數化；保留 owner 隔離、CSRF／token 驗證與 SRS 狀態。
- 資料庫欄位變更需遷移與隔離測試，核對 MIGRATE_SRS 等 gate；不以正式詞庫驗證寫入。
- pytest 是產品測試入口；package.json 的 npm test 是 placeholder，不能當驗證。
- AI API、.env、詞庫 DB、備份及日誌不提交。

## 驗證與交付

`.venv/bin/python -m pytest tests/`；前端修改加上登入、單字 CRUD、複習與畫面驗證。

目前正式服務為 english-word.service，從本目錄執行 gunicorn web:app，入口 https://word.nex11.me。更新後重啟此服務；舊 deploy.sh 使用廣泛 pkill 且涉及遷移，勿作為日常部署預設。
