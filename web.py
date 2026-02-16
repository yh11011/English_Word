#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文單字背誦系統 - 網頁版後端 (Flask)
提供 RESTful API 和網頁介面
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# 資料庫設定
DB_NAME = "vocabulary.db"


def get_db():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 讓查詢結果可以用欄位名稱存取
    return conn


def init_db():
    """初始化資料庫"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 建立資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            folder TEXT NOT NULL,
            error_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 建立索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_folder ON words(folder)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_english ON words(english)
    """)
    
    conn.commit()
    conn.close()


# ==================== API 路由 ====================

@app.route('/')
def index():
    """首頁"""
    return render_template('vocabmaster.html')


@app.route('/api/words', methods=['GET'])
def get_words():
    """取得所有單字或指定資料夾的單字"""
    folder = request.args.get('folder')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if folder and folder != 'all':
        cursor.execute("""
            SELECT * FROM words WHERE folder = ? ORDER BY english
        """, (folder,))
    else:
        cursor.execute("""
            SELECT * FROM words ORDER BY folder, english
        """)
    
    words = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(words)


@app.route('/api/words', methods=['POST'])
def add_word():
    """新增單字"""
    data = request.json
    english = data.get('english', '').strip().lower()
    chinese = data.get('chinese', '').strip()
    folder = data.get('folder', '').strip().lower()
    
    if not english or not chinese or not folder:
        return jsonify({'success': False, 'message': '所有欄位都必須填寫'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 檢查是否已存在
    cursor.execute("""
        SELECT id FROM words WHERE folder = ? AND english = ?
    """, (folder, english))
    
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '單字已存在'}), 400
    
    # 新增單字
    cursor.execute("""
        INSERT INTO words (english, chinese, folder, error_count)
        VALUES (?, ?, ?, 0)
    """, (english, chinese, folder))
    
    conn.commit()
    word_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '新增成功',
        'id': word_id
    })


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    """刪除單字"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '刪除成功'})


@app.route('/api/words/<int:word_id>/error', methods=['PUT'])
def update_error_count(word_id):
    """更新錯誤次數"""
    data = request.json
    error_count = data.get('error_count', 0)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE words SET error_count = ? WHERE id = ?
    """, (error_count, word_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/api/folders', methods=['GET'])
def get_folders():
    """取得所有資料夾"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT folder FROM words ORDER BY folder
    """)
    
    folders = [row['folder'] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(folders)


@app.route('/api/search', methods=['GET'])
def search_words():
    """搜尋單字"""
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify([])
    
    conn = get_db()
    cursor = conn.cursor()
    
    search_pattern = f"%{keyword}%"
    cursor.execute("""
        SELECT * FROM words
        WHERE english LIKE ? OR chinese LIKE ?
        ORDER BY folder, english
    """, (search_pattern, search_pattern))
    
    words = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(words)


@app.route('/api/errors', methods=['GET'])
def get_error_words():
    """取得錯題"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM words
        WHERE error_count > 0
        ORDER BY error_count DESC, english
    """)
    
    words = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(words)


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """取得統計資訊"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 總單字數
    cursor.execute("SELECT COUNT(*) as count FROM words")
    total_words = cursor.fetchone()['count']
    
    # 資料夾數
    cursor.execute("SELECT COUNT(DISTINCT folder) as count FROM words")
    total_folders = cursor.fetchone()['count']
    
    # 錯誤單字數
    cursor.execute("SELECT COUNT(*) as count FROM words WHERE error_count > 0")
    words_with_errors = cursor.fetchone()['count']
    
    # 總錯誤次數
    cursor.execute("SELECT SUM(error_count) as total FROM words")
    total_errors = cursor.fetchone()['total'] or 0
    
    # 各資料夾統計
    cursor.execute("""
        SELECT folder, COUNT(*) as count
        FROM words
        GROUP BY folder
        ORDER BY folder
    """)
    
    folder_stats = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'total_words': total_words,
        'total_folders': total_folders,
        'words_with_errors': words_with_errors,
        'total_errors': total_errors,
        'folder_stats': folder_stats
    })


if __name__ == '__main__':
    # 初始化資料庫
    init_db()
    
    # 啟動伺服器
    print("🚀 伺服器啟動中...")
    print("📱 請開啟瀏覽器訪問: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)