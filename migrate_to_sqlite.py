#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料遷移工具
將舊的文字檔格式轉換成 SQLite 資料庫格式

使用方法：
python migrate_to_sqlite.py
"""

import sqlite3
import os


def create_database(db_name="vocabulary.db"):
    """
    建立 SQLite 資料庫和資料表
    
    這個函數會：
    1. 建立資料庫檔案
    2. 建立 words 資料表
    3. 建立索引
    """
    print(f"正在建立資料庫: {db_name}")
    
    # 連接資料庫（如果不存在會自動建立）
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 建立資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            folder TEXT NOT NULL,
            error_count INTEGER DEFAULT 0
        )
    """)
    
    # 建立索引（加快查詢速度）
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_folder ON words(folder)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_english ON words(english)
    """)
    
    conn.commit()
    print("✓ 資料庫建立完成")
    
    return conn, cursor


def migrate_from_txt(txt_file="english_word.txt", db_name="vocabulary.db"):
    """
    從文字檔遷移資料到 SQLite 資料庫
    
    參數說明：
    txt_file: 舊的文字檔路徑
    db_name: 要建立的資料庫檔案名稱
    """
    
    # 檢查文字檔是否存在
    if not os.path.exists(txt_file):
        print(f"❌ 找不到檔案: {txt_file}")
        print("請確認檔案名稱和路徑是否正確。")
        return
    
    print("=" * 60)
    print("開始資料遷移")
    print("=" * 60)
    
    # 建立資料庫
    conn, cursor = create_database(db_name)
    
    # 統計變數
    success_count = 0  # 成功匯入的筆數
    skip_count = 0     # 跳過的筆數（格式錯誤或重複）
    line_number = 0    # 目前處理到第幾行
    
    print(f"\n正在讀取: {txt_file}")
    
    try:
        # 開啟文字檔
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                
                # 去除前後空白
                line = line.strip()
                
                # 跳過空行
                if not line:
                    continue
                
                # 分割資料（用 Tab 分隔）
                # 格式：資料夾\t英文\t中文\t錯誤次數
                parts = line.split('\t')
                
                # 檢查格式是否正確（至少要有 3 個欄位）
                if len(parts) < 3:
                    print(f"⚠️  第 {line_number} 行格式錯誤，已跳過: {line}")
                    skip_count += 1
                    continue
                
                # 取得各欄位資料
                folder = parts[0].strip().lower()
                english = parts[1].strip().lower()
                chinese = parts[2].strip()
                
                # 錯誤次數（如果沒有就設為 0）
                if len(parts) >= 4:
                    try:
                        error_count = int(parts[3])
                    except ValueError:
                        error_count = 0
                else:
                    error_count = 0
                
                # 檢查必填欄位是否為空
                if not folder or not english or not chinese:
                    print(f"⚠️  第 {line_number} 行有空白欄位，已跳過")
                    skip_count += 1
                    continue
                
                # 檢查是否已經存在（避免重複）
                cursor.execute("""
                    SELECT id FROM words 
                    WHERE folder = ? AND english = ?
                """, (folder, english))
                
                if cursor.fetchone():
                    print(f"⚠️  重複: {english} (資料夾: {folder})，已跳過")
                    skip_count += 1
                    continue
                
                # 插入資料到資料庫
                try:
                    cursor.execute("""
                        INSERT INTO words (folder, english, chinese, error_count)
                        VALUES (?, ?, ?, ?)
                    """, (folder, english, chinese, error_count))
                    
                    success_count += 1
                    
                    # 每 10 筆顯示一次進度
                    if success_count % 10 == 0:
                        print(f"已匯入 {success_count} 筆資料...")
                
                except sqlite3.Error as e:
                    print(f"❌ 第 {line_number} 行插入失敗: {e}")
                    skip_count += 1
        
        # 提交所有變更（儲存到資料庫）
        conn.commit()
        
        # 顯示統計結果
        print("\n" + "=" * 60)
        print("遷移完成！")
        print("=" * 60)
        print(f"✓ 成功匯入: {success_count} 筆")
        print(f"⚠️  跳過: {skip_count} 筆")
        print(f"📊 總共處理: {line_number} 行")
        print(f"💾 資料庫檔案: {db_name}")
        
        # 顯示資料夾統計
        cursor.execute("""
            SELECT folder, COUNT(*) as count
            FROM words
            GROUP BY folder
            ORDER BY folder
        """)
        
        print("\n各資料夾單字數量:")
        print("-" * 40)
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} : {row[1]:>5} 個單字")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        conn.rollback()  # 發生錯誤時復原所有變更
    
    finally:
        # 關閉資料庫連線
        conn.close()
        print("\n資料庫連線已關閉")


def export_to_txt(db_name="vocabulary.db", output_file="export.txt"):
    """
    將 SQLite 資料庫匯出成文字檔
    
    參數說明：
    db_name: 資料庫檔案名稱
    output_file: 輸出的文字檔名稱
    """
    
    # 檢查資料庫是否存在
    if not os.path.exists(db_name):
        print(f"❌ 找不到資料庫: {db_name}")
        return
    
    print("=" * 60)
    print("開始匯出資料")
    print("=" * 60)
    
    try:
        # 連接資料庫
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # 查詢所有資料
        cursor.execute("""
            SELECT folder, english, chinese, error_count
            FROM words
            ORDER BY folder, english
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("⚠️  資料庫是空的，沒有資料可以匯出")
            return
        
        # 寫入文字檔
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in rows:
                # 格式：資料夾\t英文\t中文\t錯誤次數
                f.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n")
        
        print(f"✓ 成功匯出 {len(rows)} 筆資料")
        print(f"💾 輸出檔案: {output_file}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 匯出失敗: {e}")


def show_database_info(db_name="vocabulary.db"):
    """
    顯示資料庫資訊
    
    參數說明：
    db_name: 資料庫檔案名稱
    """
    
    if not os.path.exists(db_name):
        print(f"❌ 找不到資料庫: {db_name}")
        return
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("資料庫資訊")
        print("=" * 60)
        
        # 總單字數
        cursor.execute("SELECT COUNT(*) FROM words")
        total = cursor.fetchone()[0]
        print(f"📚 總單字數: {total}")
        
        # 資料夾數量
        cursor.execute("SELECT COUNT(DISTINCT folder) FROM words")
        folder_count = cursor.fetchone()[0]
        print(f"📁 資料夾數量: {folder_count}")
        
        # 有錯誤記錄的單字
        cursor.execute("SELECT COUNT(*) FROM words WHERE error_count > 0")
        error_words = cursor.fetchone()[0]
        print(f"❌ 有錯誤記錄: {error_words} 個單字")
        
        # 總錯誤次數
        cursor.execute("SELECT SUM(error_count) FROM words")
        total_errors = cursor.fetchone()[0] or 0
        print(f"📊 總錯誤次數: {total_errors}")
        
        # 各資料夾統計
        cursor.execute("""
            SELECT folder, COUNT(*) as count
            FROM words
            GROUP BY folder
            ORDER BY count DESC
        """)
        
        print("\n各資料夾單字數量:")
        print("-" * 40)
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} : {row[1]:>5} 個單字")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")


def main():
    """
    主程式
    提供選單讓使用者選擇功能
    """
    
    print("\n" + "=" * 60)
    print("       英文單字資料遷移工具")
    print("=" * 60)
    
    while True:
        print("\n請選擇功能:")
        print("1. 從文字檔匯入到 SQLite")
        print("2. 從 SQLite 匯出到文字檔")
        print("3. 顯示資料庫資訊")
        print("4. 離開")
        print("-" * 60)
        
        choice = input("請輸入 1~4: ").strip()
        
        if choice == '1':
            # 匯入
            txt_file = input("\n請輸入文字檔路徑 (預設: english_word.txt): ").strip()
            if not txt_file:
                txt_file = "english_word.txt"
            
            db_name = input("請輸入資料庫名稱 (預設: vocabulary.db): ").strip()
            if not db_name:
                db_name = "vocabulary.db"
            
            # 如果資料庫已存在，詢問是否覆蓋
            if os.path.exists(db_name):
                confirm = input(f"\n⚠️  資料庫 {db_name} 已存在，是否覆蓋？(y/n): ").strip().lower()
                if confirm != 'y':
                    print("取消匯入。")
                    continue
                os.remove(db_name)
            
            migrate_from_txt(txt_file, db_name)
        
        elif choice == '2':
            # 匯出
            db_name = input("\n請輸入資料庫名稱 (預設: vocabulary.db): ").strip()
            if not db_name:
                db_name = "vocabulary.db"
            
            output_file = input("請輸入輸出檔案名稱 (預設: export.txt): ").strip()
            if not output_file:
                output_file = "export.txt"
            
            # 如果檔案已存在，詢問是否覆蓋
            if os.path.exists(output_file):
                confirm = input(f"\n⚠️  檔案 {output_file} 已存在，是否覆蓋？(y/n): ").strip().lower()
                if confirm != 'y':
                    print("取消匯出。")
                    continue
            
            export_to_txt(db_name, output_file)
        
        elif choice == '3':
            # 顯示資訊
            db_name = input("\n請輸入資料庫名稱 (預設: vocabulary.db): ").strip()
            if not db_name:
                db_name = "vocabulary.db"
            
            show_database_info(db_name)
        
        elif choice == '4':
            # 離開
            print("\n👋 掰掰！")
            break
        
        else:
            print("❌ 無效的選擇，請輸入 1~4")


if __name__ == "__main__":
    main()
