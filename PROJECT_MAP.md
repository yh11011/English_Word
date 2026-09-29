# Word — 專案地圖

路徑相對於本檔目錄。先按功能讀第一站，只有涉及跨模組才擴大；程式與地圖不符時以程式為準並更新。

| 功能 | 第一站 | 需要時再看 | 驗證入口 |
| --- | --- | --- | --- |
| 網頁、權限與 API | `web.py` | `templates/vocabmaster.html`、`static/app.js`、`static/app.css` | tests/test_web_api.py、test_auth.py |
| 單字資料與 CLI | `english_word.py` | `tests/test_database.py` | tests/test_database.py |
| 構詞分析 | `morphology_analyzer.py` | `templates/morphology.html` | 隔離資料與 API 回歸 |
| AI 例句與翻譯 | `ai_services.py` | `enhanced_ai_service.py` | mock 外部模型 |
| 考試詞彙 | `exam_vocabulary.py` | `static/exam_vocabulary.js`、`tests/test_exam_vocabulary.py` | tests/test_exam_vocabulary.py |
| 資料遷移及匯出 | `tools` | `web.py` | 暫存 DB 與備份回復 |

## 部署與交付入口

目前正式服務為 english-word.service，從本目錄執行 gunicorn web:app，入口 https://word.nex11.me。更新後重啟此服務；舊 deploy.sh 使用廣泛 pkill 且涉及遷移，勿作為日常部署預設。

## 最近更新

每輪修改後核對並新增一筆，最多 20 筆，最新在前；純討論與唯讀查詢不新增。

- 2026-09-29：核對功能入口、驗證與部署方式，建立精簡導航並統一 Codex 工作規則。
