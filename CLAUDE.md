# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Overview
- This repository is a small Python-based English vocabulary study system backed by an SQLite database.
- Two runnable entry points are present:
  - CLI application: english_word.py (main CLI and database classes)
  - Web backend: web.py (Flask app serving a simple frontend in templates/)
- Database file: vocabulary.db (created next to the scripts).

Quick commands (recommended developer workflow)
- Create virtual environment and activate
  - python3 -m venv .venv
  - source .venv/bin/activate
- Install minimal runtime deps
  - pip install Flask
  - Optionally install linters / formatters: pip install black flake8 mypy

Run the CLI app (interactive)
- python3 english_word.py
  - Entry point: /home/ubuntu/English_Word/english_word.py:981
  - Primary CLI class: VocabularySystem in /home/ubuntu/English_Word/english_word.py:532

Run the web app (development)
- python3 web.py
  - Flask app instance: /home/ubuntu/English_Word/web.py:14
  - Home route renders templates/vocabmaster.html: /home/ubuntu/English_Word/web.py:60
  - Common API endpoints: list (GET /api/words) / add (POST /api/words) / delete (DELETE /api/words/<id>)
  - App startup code: /home/ubuntu/English_Word/web.py:263

Database and migration
- The app uses SQLite and creates vocabulary.db in the project root.
- Migration helper: migrate_to_sqlite.py (use to import/export older text formats).
- DB schema is created by both english_word.py (VocabularyDatabase.create_tables) and web.py (init_db).
  - Core DB table: words (id, english, chinese, folder, part_of_speech, error_count)
  - See creation code: /home/ubuntu/English_Word/english_word.py:116 and /home/ubuntu/English_Word/web.py:34

Files of interest (high level)
- english_word.py — main CLI, data layer and business logic
  - Word model: /home/ubuntu/English_Word/english_word.py:12
  - VocabularyDatabase (SQLite wrapper): /home/ubuntu/English_Word/english_word.py:49
  - VocabularySystem (CLI UI, commands): /home/ubuntu/English_Word/english_word.py:532
- web.py — Flask backend + REST API (templates/vocabmaster.html is the frontend)
  - DB helpers and endpoints: /home/ubuntu/English_Word/web.py:21 (get_db) and routes starting at /home/ubuntu/English_Word/web.py:60
- GUI.py — an alternate UI (inspect before running; likely uses a GUI toolkit)
- migrate_to_sqlite.py — import/export tools for older text formats
- templates/vocabmaster.html — web frontend used by Flask

Important repository notes / gotchas
- README and guide files mention a file named vocabulary_system_sqlite.py which is not present in the tree. The working CLI entrypoint is english_word.py (see /home/ubuntu/English_Word/english_word.py:981). Be careful when following docs — they appear to reference a different filename.
- web.py sets app.secret_key = 'your-secret-key-change-this-in-production' (hard-coded). Replace with a secure secret in production and avoid committing real secrets.
- There are no automated tests or CI config in the repository. Add tests under tests/ and use pytest for automation.

Suggested lint / format / test commands
- Format code with Black
  - black .
- Run flake8 linter (target files or the whole repo)
  - flake8 english_word.py web.py
- Type-check with mypy (if types are added / improved)
  - mypy .
- Run tests (add pytest)
  - Install: pip install pytest
  - Run all tests: pytest
  - Run a single test function/file: pytest tests/test_file.py::test_function_name
    - Example: pytest tests/test_english_db.py::test_add_word

When to enter plan mode vs small edits
- Use EnterPlanMode for tasks that will touch multiple files or require design decisions (adding a web feature, changing DB schema, adding authentication, or creating tests + CI).
- Small edits (typos, single-file bugfixes, doc string fixes) can be done directly.

Security-sensitive places to review before changes
- web.py: hard-coded secret key and debug=True in app.run — do not enable debug or commit secrets for production. See /home/ubuntu/English_Word/web.py:14 and /home/ubuntu/English_Word/web.py:267
- SQL usage uses parameterized queries in most places (good). If you add raw SQL, prefer parameterized placeholders (avoid f-strings for SQL).

Where to add tests and common targets
- Tests go in tests/ (pytest default). Create small unit tests for VocabularyDatabase operations (add/get/search/update/delete) and for Flask endpoints using the Flask test client.
- Suggested test targets:
  - tests/test_database.py (unit test for VocabularyDatabase)
  - tests/test_web_api.py (Flask test client tests for endpoints)

How to run the Flask test client (example)
- In a pytest test, import web and use app.test_client():
  from web import app
  client = app.test_client()
  resp = client.get('/api/words')

Notes for future Claude Code instances
- Start by reading english_word.py and web.py (they contain the core logic). Use the file references above to jump directly to the main classes and routes.
- Check README.md and guide/QUICKSTART.md for user-facing instructions but verify filenames mentioned there against the actual repository contents.
- For any change that affects the database schema, ask for approval (schema changes are high-impact).

If this CLAUDE.md should be improved
- I intentionally kept this focused. If you want more: add a CONTRIBUTING section, a recommended requirements.txt, or a small pytest-based smoke-test that runs in CI.
