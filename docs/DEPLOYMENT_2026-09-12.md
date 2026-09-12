# 歷屆生字正式部署紀錄

日期：2026-09-12（UTC）。

## 已發布版本

- 單字功能 commit：`06507e8`。正式執行路徑：`/home/ubuntu/.local/share/nex11/word-releases/06507e8`。
- 保留既有本地登入；工作目錄中未提交的 SSO 改動未發布。舊帳號與 Auth ID 存在衝突，須另作帳號遷移設計，不能直接把工作目錄 web.py 重啟上線。
- 沿用既有 AI／構詞執行依賴，版本雜湊見下表。
- Study 入口已啟用，`.env.production.local` 保存 `VITE_EXAM_VOCABULARY_ENABLED=true`。舊 hashed assets 保留。
- word 使用 systemd drop-in 指向發布快照；固定 session key 位於 `/etc/nex11/word-session.env`，未加入版本控制。
- 正式資料庫、schema、既有學習資料未遷移；沒有建立正式測試帳號。

## 驗證

- 發布快照的資料庫／Web API／歷屆生字測試 15 項通過。
- 另以正式 DB 的隔離副本驗證既有註冊登入、2,969 候選字、收藏與 SRS 評分；未呼叫外部 API。
- 工作目錄先前 22 項測試包含尚未發布的 SSO 測試，不能用來宣稱本次舊登入發布版本通過全部 SSO 測試。
- Study TypeScript + Vite 啟用版建置成功；既有 bundle 超過 500 kB 警告不影響建置。
- 公開手機瀏覽器可載入新頁並提示登入，無 JS 例外或水平溢出。未以使用者真實帳號操作正式收藏。
- english-word、study、cloudflared 服務 active 且 enabled。

| 公開檢查 | HTTP |
|---|---|
| https://word.nex11.me/ | 200 |
| https://word.nex11.me/exam-vocabulary | 200 |
| https://word.nex11.me/static/exam_vocabulary.css | 200 |
| https://word.nex11.me/static/exam_vocabulary.js | 200 |
| https://word.nex11.me/api/exam-vocabulary | 401 |
| https://nex11.me/study/ | 200 |
| https://nex11.me/study/assets/index-DgDm4apc.js | 200 |
| https://nex11.me/study/practice | 200 |
| https://nex11.me/study/api/catalog | 401 |

## 備份與回復

- 備份路徑：`/home/ubuntu/.local/share/nex11/backups/word-study-20260912T112234Z`，包含兩站 SQLite backup API 快照及 Study 原建置。
- 單字回復版本：`/home/ubuntu/.local/share/nex11/word-releases/pre-exam-06507e8`；僅移除新功能註冊，保留舊登入。
- 回復程式時將 `/etc/systemd/system/english-word.service.d/20-exam-release.conf` 的 WorkingDirectory 指向回復版本，daemon-reload 後 restart english-word。不可直接刪除 drop-in，否則會載入未完成的工作目錄 SSO 改動。
- Study 回復時先將入口旗標設 false，再回復備份的 index.html；保留現有 assets。純程式回復不需覆蓋 SQLite，避免抹去部署後的學習紀錄。

## 執行檔 SHA-256

| 檔案 | SHA-256 |
|---|---|
| web.py | `24e6b328171d6ac6ddf4a7ed0ecaad823fa624d913bc723da3d6f9c68890cc45` |
| exam_vocabulary.py | `72784a1b9f5fc91e4094dcbd4b3060b00a5b5bafe19c78e1693ee7f953ec7127` |
| ai_services.py | `aae5c8103e9bb8db313389a14ada0148250e65c59725f1802b1dbf22971e9200` |
| enhanced_ai_service.py | `5710ce8977fbccf96939bdf238797a3e7867516b1affce511334202db61f7277` |
| morphology_analyzer.py | `28c03ebb106f6da1e3244611857bfd37f970394c9bfa88c9bd26abf53b4abf82` |
| data/exam_vocabulary.json | `ffc3c2b4b6f9c04a4eca027948f7da855214c5623f380fd1958a44cad0752b66` |
