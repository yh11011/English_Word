#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文單字背誦系統 - Python 版本
"""

import random
import os
from typing import List, Optional, Tuple


class Word:
    """單字類別"""
    def __init__(self, english: str, chinese: str, folder: str, error_count: int = 0):
        self.english = english.lower().strip()
        self.chinese = chinese.strip()
        self.folder = folder.lower().strip()
        self.error_count = error_count

    def __str__(self):
        return f"{self.folder}\t{self.english}\t{self.chinese}\t{self.error_count}"


class VocabularySystem:
    """單字背誦系統主類別"""
    
    def __init__(self, filename: str = "english_word.txt"):
        self.filename = filename
        self.library: List[Word] = []
        self.folder_list: List[str] = []
        self.max_words = 1000
        
    def load_data(self) -> bool:
        """讀取單字資料庫"""
        if not os.path.exists(self.filename):
            print(f"[Info] 找不到檔案 {self.filename}，將建立新檔案。")
            return False
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        folder = parts[0].strip()
                        english = parts[1].strip()
                        chinese = parts[2].strip()
                        error_count = int(parts[3]) if len(parts) >= 4 else 0
                        
                        word = Word(english, chinese, folder, error_count)
                        self.library.append(word)
                        self._update_folder_list(folder)
            
            print(f"讀取完成，共有 {len(self.folder_list)} 個資料夾，{len(self.library)} 個單字。")
            return True
        except Exception as e:
            print(f"[Error] 讀取檔案時發生錯誤: {e}")
            return False
    
    def save_data(self) -> bool:
        """儲存單字資料庫"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                for word in self.library:
                    f.write(str(word) + '\n')
            return True
        except Exception as e:
            print(f"[Error] 儲存檔案時發生錯誤: {e}")
            return False
    
    def _update_folder_list(self, folder: str):
        """更新資料夾清單"""
        folder = folder.lower().strip()
        if folder not in self.folder_list:
            self.folder_list.append(folder)
    
    def _check_capacity(self) -> bool:
        """檢查單字庫是否已滿"""
        if len(self.library) >= self.max_words:
            print(f"\n[Error] 單字庫已滿（上限 {self.max_words} 個）")
            return False
        return True
    
    def add_word(self):
        """新增單字"""
        print("\n===== 新增單字 =====")
        print("會自動存檔\n")
        
        # 輸入資料夾名稱
        while True:
            folder = input("請輸入要存入的資料夾名稱: ").strip().lower()
            if folder:
                break
            print("[Error] 資料夾名稱不能為空。")
        
        self._update_folder_list(folder)
        
        print("請輸入格式: [英文單字] [Tab鍵或空格] [中文意思]")
        print("離開請輸入 'end'\n")
        
        while True:
            if not self._check_capacity():
                return
            
            user_input = input(">").strip()
            
            if user_input.lower() == 'end':
                print("結束新增單字。")
                break
            
            # 分割輸入（支援 Tab 或空格）
            if '\t' in user_input:
                parts = user_input.split('\t', 1)
            else:
                parts = user_input.split(None, 1)
            
            if len(parts) < 2:
                print("[Error] 格式錯誤，請使用: [英文單字] [Tab/空格] [中文意思]")
                continue
            
            english = parts[0].strip().lower()
            chinese = parts[1].strip()
            
            if not english or not chinese:
                print("[Error] 英文或中文不能為空。")
                continue
            
            # 檢查重複（修正原程式 bug：應該只檢查英文單字是否重複）
            duplicate = False
            for word in self.library:
                if word.folder == folder and word.english == english:
                    duplicate = True
                    break
            
            if duplicate:
                print(f"[Warning] 單字 '{english}' 在資料夾 '{folder}' 中已存在。")
                choice = input("是否覆蓋？(y/n): ").strip().lower()
                if choice == 'y':
                    # 移除舊單字
                    self.library = [w for w in self.library 
                                  if not (w.folder == folder and w.english == english)]
                else:
                    continue
            
            # 新增單字
            new_word = Word(english, chinese, folder)
            self.library.append(new_word)
            print(f"[Success] 已新增單字: {english} - {chinese} (資料夾: {folder})")
            self.save_data()
    
    def choose_folder(self) -> Optional[int]:
        """
        選擇資料夾
        返回值: 
            None: 離開
            -1: 全部單字
            0~n-1: 資料夾索引
        """
        if len(self.library) == 0:
            print("[Error] 目前沒有任何單字，請先新增單字。")
            return None
        
        # 修正原程式 bug：移除不合理的 20 個單字限制
        print("\n選擇資料夾:")
        for i, folder in enumerate(self.folder_list):
            print(f"{i + 1}. {folder}")
        print("99. 全部單字")
        print("0. 離開")
        
        while True:
            try:
                choice = input("\n請選擇: ").strip()
                option = int(choice)
                
                if option == 0:
                    return None
                elif option == 99:
                    return -1
                elif 1 <= option <= len(self.folder_list):
                    return option - 1
                else:
                    print("[Error] 無效選擇，請重新輸入。")
            except ValueError:
                print("[Error] 請輸入數字。")
    
    def show_flashcards(self):
        """單字卡學習模式"""
        print("\n===== 單字卡學習模式 =====")
        
        if len(self.library) < 1:
            print("[Error] 至少需要 1 個單字才能使用此功能。")
            return
        
        folder_choice = self.choose_folder()
        if folder_choice is None:
            return
        
        # 收集要顯示的單字
        words_to_show = []
        if folder_choice == -1:
            words_to_show = self.library.copy()
        else:
            selected_folder = self.folder_list[folder_choice]
            words_to_show = [w for w in self.library if w.folder == selected_folder]
        
        if not words_to_show:
            print("沒有可顯示的單字。")
            return
        
        # 隨機打亂順序
        random.shuffle(words_to_show)
        
        print(f"\n共有 {len(words_to_show)} 個單字")
        print("按 Enter 顯示答案，輸入 'q' 離開\n")
        
        for i, word in enumerate(words_to_show, 1):
            print(f"\n[{i}/{len(words_to_show)}]")
            print(f"英文: {word.english}")
            
            user_input = input("按 Enter 顯示中文... ").strip()
            if user_input.lower() == 'q':
                print("離開單字卡模式。")
                break
            
            print(f"中文: {word.chinese}")
            if word.error_count > 0:
                print(f"(曾錯誤 {word.error_count} 次)")
    
    def take_test(self):
        """單字測驗模式"""
        print("\n===== 單字測驗模式 =====")
        
        if len(self.library) < 1:
            print("[Error] 至少需要 1 個單字才能測驗。")
            return
        
        folder_choice = self.choose_folder()
        if folder_choice is None:
            return
        
        # 收集要測驗的單字
        test_words = []
        if folder_choice == -1:
            test_words = self.library.copy()
        else:
            selected_folder = self.folder_list[folder_choice]
            test_words = [w for w in self.library if w.folder == selected_folder]
        
        if not test_words:
            print("沒有可測驗的單字。")
            return
        
        # 隨機打亂順序
        random.shuffle(test_words)
        
        score = 0
        error_list = []
        
        print(f"\n開始測驗，共 {len(test_words)} 題\n")
        
        for i, word in enumerate(test_words, 1):
            print(f"{i}. {word.chinese}")
            answer = input("請輸入英文: ").strip().lower()
            
            if answer == word.english:
                score += 1
                print(f"✓ 正確！目前得分: {score}/{i}\n")
            else:
                word.error_count += 1
                error_list.append(word)
                print(f"✗ 錯誤！正確答案是: {word.english}")
                print(f"   (此單字已錯誤 {word.error_count} 次)")
                print(f"   目前得分: {score}/{i}\n")
        
        # 顯示測驗結果
        print("=" * 50)
        print(f"測驗結束！最終得分: {score}/{len(test_words)} ({score/len(test_words)*100:.1f}%)")
        
        if error_list:
            print(f"\n本次測驗錯誤單字 ({len(error_list)} 個):")
            for word in error_list:
                print(f"  - {word.english} ({word.chinese})")
        else:
            print("\n🎉 太棒了！全部答對！")
        
        self.save_data()
    
    def search_word(self):
        """查詢單字"""
        print("\n===== 查詢單字 =====")
        
        while True:
            keyword = input("\n請輸入要查詢的關鍵字 (中文或英文，輸入 'end' 結束): ").strip()
            
            if keyword.lower() == 'end':
                print("結束查詢。")
                break
            
            if not keyword:
                continue
            
            keyword_lower = keyword.lower()
            found_words = []
            
            for word in self.library:
                if (keyword_lower in word.english.lower() or 
                    keyword in word.chinese):
                    found_words.append(word)
            
            if not found_words:
                print("查無此單字。")
            else:
                print(f"\n找到 {len(found_words)} 筆資料:")
                print(f"{'資料夾':<15} {'英文':<20} {'中文':<20} {'錯誤次數':<10}")
                print("-" * 70)
                for word in found_words:
                    print(f"{word.folder:<15} {word.english:<20} {word.chinese:<20} {word.error_count:<10}")
    
    def show_error_list(self):
        """顯示錯題本"""
        print("\n===== 錯題本 =====")
        
        # 收集有錯誤記錄的單字
        error_words = [w for w in self.library if w.error_count > 0]
        
        if not error_words:
            print("\n🎉 太棒了！目前沒有錯誤紀錄！")
            return
        
        # 按錯誤次數排序（由多到少）
        error_words.sort(key=lambda w: w.error_count, reverse=True)
        
        print(f"\n共有 {len(error_words)} 個單字有錯誤記錄:")
        print(f"{'排名':<6} {'英文':<20} {'中文':<25} {'錯誤次數':<10}")
        print("-" * 70)
        
        for i, word in enumerate(error_words, 1):
            print(f"{i:<6} {word.english:<20} {word.chinese:<25} {word.error_count:<10}")
        
        # 提供複習選項
        print("\n是否要複習這些錯題？(y/n): ", end='')
        choice = input().strip().lower()
        if choice == 'y':
            self._review_errors(error_words)
    
    def _review_errors(self, error_words: List[Word]):
        """複習錯題"""
        print("\n===== 錯題複習 =====")
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
                print(f"✗ 錯誤！正確答案: {word.english}")
        
        print(f"\n複習結束！得分: {score}/{len(error_words)}")
        self.save_data()
    
    def show_statistics(self):
        """顯示統計資訊"""
        print("\n===== 統計資訊 =====")
        print(f"資料夾數量: {len(self.folder_list)}")
        print(f"單字總數  : {len(self.library)}")
        print(f"錯誤記錄  : {sum(1 for w in self.library if w.error_count > 0)} 個單字有錯誤")
        
        if self.folder_list:
            print("\n各資料夾單字數量:")
            for folder in self.folder_list:
                count = sum(1 for w in self.library if w.folder == folder)
                print(f"  {folder}: {count} 個單字")
    
    def run(self):
        """主程式執行"""
        print("正在載入單字資料...")
        self.load_data()
        
        while True:
            print("\n" + "=" * 50)
            print("===== 英文單字背誦系統 =====")
            print("=" * 50)
            print("1. 新增單字")
            print("2. 單字卡學習")
            print("3. 開始測驗")
            print("4. 錯題本")
            print("5. 查詢單字")
            print("6. 統計資訊")
            print("7. 離開程式")
            print("=" * 50)
            
            try:
                choice = input("請輸入 1~7 以選擇功能: ").strip()
                
                if choice == '1':
                    self.add_word()
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
                    self.save_data()
                    print("\n掰掰！要記得複習喔！👋")
                    break
                else:
                    print("[Error] 請輸入 1~7 的數字。")
            
            except KeyboardInterrupt:
                print("\n\n程式被中斷，正在儲存...")
                self.save_data()
                print("掰掰！")
                break
            except Exception as e:
                print(f"[Error] 發生錯誤: {e}")


def main():
    """主程式入口"""
    system = VocabularySystem()
    system.run()


if __name__ == "__main__":
    main()