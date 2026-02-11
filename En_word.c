#include <stdio.h>     // 標準輸入輸出
// printf(...) -> 輸出到螢幕
// scanf(...)  -> 從使用者輸入讀取
// fopen/fclose/fprintf/fgets -> 檔案讀寫

#include <stdlib.h>    // 標準函式庫
// atoi(...) -> 字串轉整數
// system("cls") -> 清空螢幕
// exit(...) -> 結束程式

#include <string.h>    // 字串處理
// strcpy/strcmp/strstr/strtok

#include <ctype.h>     // 字元處理
// tolower(...) -> 字元轉小寫

#include <time.h>     //讀取時間

// ---------------- 常數 ----------------
#define word_amount 1000   // 單字庫上限
#define len_eninput 50     // 英文單字長度
#define len_chinput 100    // 中文意思長度
#define folder_max 50      // 資料夾上限

// ---------------- 結構 ----------------
typedef struct {
    char english[len_eninput];   // 英文單字
    char chinese[len_chinput];   // 中文意思
    char folder[len_eninput];    // 所在資料夾
    int ErrorCount;              // 錯誤次數
} Word;

// ---------------- 全域變數 ----------------
Word library[word_amount];      // 單字庫
int wordCount = 0;             // 單字數量
char folderList[folder_max][len_eninput]; // 資料夾清單
int folderCount = 0;           // 資料夾數量

// ---------------- 函數宣告 ----------------
int save();
void parseLine(char *line);
void read();
int check();
void updateFolderList(char *newFolder);
void secureInput(char *str, int max);
void AddWord();
int chooseFolder();
void showSingleCard(int i);
void allcards();
void showCards(int folderIndex);
void showCard();
int collectWordIndices(const char *folder, int result[]);
int askOneQuestion(int wordIndex, int qNum, int *score);
void takeTest();
int search();
void Errowlist();
void check_folder();
int choosefountion();

// ---------------- 新增：洗牌函數 ----------------
void shuffle(int arr[], int n) {
    for (int i = n - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

// ---------------- 主程式 ----------------
int main(void) {
    srand(time(NULL));
    read(); // 讀取單字庫

    int choice;
    do {
        printf("\n===== 英文單字背誦系統 =====\n");
        printf("1. 新增單字\n");
        printf("2. 單字卡學習\n");
        printf("3. 開始測驗\n");
        printf("4. 錯題本\n");
        printf("5. 查詢單字\n");
        printf("6. 檢視檔案內容\n");
        printf("7. 離開程式\n");
        printf("請輸入 1~7 以選擇功能: ");
        choice = choosefountion();
    } while (choice != 7);

    return 0;
}

// ---------------- 函數實作 ----------------

// 儲存資料庫到檔案
int save() {
    FILE *file = fopen("english_word.txt", "w");
    if (!file) return 0;

    for (int i = 0; i < wordCount; i++) {
        fprintf(file, "%s\t%s\t%s\t%d\n",
                library[i].folder,
                library[i].english,
                library[i].chinese,
                library[i].ErrorCount);
    }
    fclose(file);
    return 1;
}

// 解析檔案行，存入 library
void parseLine(char *line) {
    if (!check()) return;
    char *folder = strtok(line, "\t");
    char *en = strtok(NULL, "\t");
    char *ch = strtok(NULL, "\t\r\n");
    char *err = strtok(NULL, "\t\r\n");

    if (folder && en && ch) {
        strcpy(library[wordCount].folder, folder);
        strcpy(library[wordCount].english, en);
        strcpy(library[wordCount].chinese, ch);
        updateFolderList(folder);
    }

    if (err)
        library[wordCount].ErrorCount = atoi(err);
    else
        library[wordCount].ErrorCount = 0;

    wordCount++;
}

// 讀取資料庫
void read() {
    FILE *fp = fopen("english_word.txt", "r");
    if (!fp) {
        printf("[Error] 無法讀取檔案。\n");
        return;
    }

    char line[300];
    while (fgets(line, sizeof(line), fp)) {
        parseLine(line);
    }

    printf("讀取完成，共有 %d 個資料夾，%d 個單字。\n",
           folderCount, wordCount);
    fclose(fp);
}

// 單字庫是否滿
int check() {
    if (wordCount >= word_amount) {
        printf("\n[Error] 單字庫已滿（上限 %d 個）\n", word_amount);
        return 0;
    }
    return 1;
}

// 更新資料夾清單
void updateFolderList(char *newFolder) {
    for (int i = 0; i < folderCount; i++)
        if (strcmp(folderList[i], newFolder) == 0) return; // 已存在
    strcpy(folderList[folderCount++], newFolder);
}

// 安全輸入
void secureInput(char *str, int max) {
    fgets(str, max, stdin);
    str[strcspn(str, "\n")] = '\0';
    for (int i = 0; str[i]; i++)
        if (str[i] >= 'A' && str[i] <= 'Z') str[i] += 32;
}

// 新增單字
void AddWord() {
    if (!check()) return;
    getchar(); // 清除換行

    printf("===== 新增單字 =====\n");
    printf("會自動存檔\n\n");

    char Folder[len_eninput];
    while (1) {
        printf("請輸入要存入的資料夾名稱: ");
        secureInput(Folder, len_eninput);
        if (strlen(Folder) > 0) break;
        printf("[Error] 資料夾名稱不能為空。\n");
    }
    updateFolderList(Folder);

    printf("請輸入: [英文單字] + [Tab鍵] + [中文意思]\n");
    printf("離開請輸入 'end'\n");

    while (1) {
        printf(">");
        char line[300], whole_line[300];
        secureInput(line, 300);

        if (strcmp(line, "end") == 0) {
            printf("結束新增單字。\n");
            break;
        }

        // ------------------- 重複檢查 -------------------
        int duplicate = 0;
        char *en = strtok(line, "\t");
        char *ch = strtok(NULL, "\t");

        for (int i = 0; i < wordCount; i++) {
            if (strcmp(library[i].folder, Folder) == 0 &&
                strcmp(library[i].english, en) == 0 &&
                strcmp(library[i].chinese, ch) == 0) {
                duplicate = 1;
                break;
            }
        }
        if (duplicate) {
            printf("[Warning] 該單字已存在，新增取消。\n");
            continue;
        }

        sprintf(whole_line, "%s\t%s\t%s", Folder, en, ch);
        parseLine(whole_line);
        printf("[Success] 已新增單字: %s - %s (資料夾: %s)\n",
               library[wordCount - 1].english,
               library[wordCount - 1].chinese,
               Folder);
        save();
        if (!check()) return;
    }
}

// 選擇資料夾
int chooseFolder() {
    if (wordCount <= 20) {
        printf("目前單字少於20個，只可選擇全部單字。\n");
        return 0;
    }

    int option;
    do {
        printf(" 選擇資料夾\n");
        for (int i = 0; i < folderCount; i++)
            printf("%d. %s\n", i + 1, folderList[i]);
        printf("99. 全部單字\n");
        printf("100. 離開\n");

        if (scanf("%d", &option) != 1) { getchar(); continue; }
        getchar();

        if(option == 100) return -1;
        if (option == 0 || (option >= 1 && option <= folderCount) || option == 99)
            return option;
        printf("[Error] 無效選擇，請重新輸入。\n");
    } while (1);
}

// 顯示單字卡
void showSingleCard(int i) {
    printf("英文: %s\n", library[i].english);
    printf("按 Enter 顯示中文...");
    getchar();
    printf("中文: %s\n\n", library[i].chinese);
}

// 顯示全部單字
void allcards() {
    for (int i = 0; i < wordCount; i++)
        showSingleCard(i);
}

// 顯示指定資料夾單字
void showCards(int folderIndex) {
    char *selectedFolder = folderList[folderIndex - 1];
    int found = 0;

    for (int i = 0; i < wordCount; i++) {
        if (strcmp(library[i].folder, selectedFolder) == 0) {
            found = 1;
            showSingleCard(i);
        }
    }

    if (!found)
        printf("資料夾 '%s' 中沒有單字。\n", selectedFolder);
}

// 單字卡主函數
void showCard() {
    printf("\n===== 單字卡學習模式 =====\n");
    int choice = chooseFolder();
    if (choice == -1) return;
    if (wordCount < 10) {
        printf("單字少於10個，請新增%d個。\n", 10 - wordCount);
        return;
    }
    if (choice == 0 || choice == 99) allcards();
    else showCards(choice);
}

// -------------------- 測驗 --------------------

// 收集單字索引
int collectWordIndices(const char *folder, int result[]) {
    int count = 0;
    for (int i = 0; i < wordCount; i++)
        if (folder == NULL || strcmp(library[i].folder, folder) == 0)
            result[count++] = i;
    return count;
}

// 問一題
int askOneQuestion(int wordIndex, int qNum, int *score) {
    char answer[len_eninput];

    printf("%d. %s\n", qNum, library[wordIndex].chinese);
    scanf("%49s", answer); getchar();

    if (strcmp(answer, library[wordIndex].english) == 0) {
        (*score)++;
        printf("正確！\n");
        printf("%d / %d\n", *score,qNum);
        return 1;
    } else {
        library[wordIndex].ErrorCount++;
        printf("錯誤，正確答案: %s（已錯 %d 次）\n\n",
               library[wordIndex].english, library[wordIndex].ErrorCount);
        return 0;
    }
}

// 測驗主程式（已整合洗牌）
void takeTest() {
    printf("===== 單字測驗模式 =====\n");

    int folderChoice = chooseFolder();
    if (folderChoice == -1) return;

    const char *folder =
        (folderChoice == 0 || folderChoice == 99) ? NULL : folderList[folderChoice - 1];

    int indices[word_amount];
    int total = collectWordIndices(folder, indices);
    if (total == 0) {
        printf("沒有可測驗的單字。\n");
        return;
    }

    // 洗牌
    shuffle(indices, total);

    int score = 0;
    int errorList[word_amount], errorCount = 0;

    // 依洗牌後順序出題
    for (int i = 0; i < total; i++) {
        int idx = indices[i];
        if (!askOneQuestion(idx, i + 1, &score))
            errorList[errorCount++] = idx;
    }

    printf("測驗結束：%d / %d\n", score, total);
    if (errorCount > 0) {
        printf("錯題清單：\n");
        for (int i = 0; i < errorCount; i++)
            printf("- %s\n", library[errorList[i]].english);
    }

    save(); // 測驗後存檔
}

// -------------------- 查詢功能 --------------------
int search() {
    char aim[len_chinput];
    int foundCount = 0;
    printf("請輸入要查詢的中文或英文 (結束輸入 'end')\n");

    do {
        printf(">");
        secureInput(aim, len_chinput);
        if (strlen(aim) == 0) continue;
        if (!strcmp(aim, "end")) { printf("結束查詢。\n"); return 0; }
        break;
    } while (1);

    for (int i = 0; i < wordCount; i++) {
        if (strstr(library[i].english, aim) != NULL ||
            strstr(library[i].chinese, aim) != NULL) {
            foundCount++;
            printf("%d. %s\t%s\t%s\t錯誤次數: %d\n",
                   foundCount,
                   library[i].folder,
                   library[i].english,
                   library[i].chinese,
                   library[i].ErrorCount);
        }
    }

    if (foundCount == 0) printf("查無此單字。\n");
    else printf("共找到 %d 筆相關資料。\n", foundCount);

    return 1;
}

// 顯示錯題本
void Errowlist() {
    int errorIndices[word_amount], errorTotal = 0;

    for (int i = 0; i < wordCount; i++)
        if (library[i].ErrorCount > 0) errorIndices[errorTotal++] = i;

    if (errorTotal == 0) {
        printf("\n!!!太棒了!!! 目前沒有錯誤紀錄！\n");
        return;
    }

    // 按錯誤次數排序
    for (int i = 0; i < errorTotal - 1; i++)
        for (int j = i + 1; j < errorTotal; j++)
            if (library[errorIndices[j]].ErrorCount >
                library[errorIndices[i]].ErrorCount) {
                int t = errorIndices[i];
                errorIndices[i] = errorIndices[j];
                errorIndices[j] = t;
            }

    printf("\n===== 錯題本 =====\n");
    printf("%-15s %-15s %-10s\n", "英文", "中文", "錯誤次數");
    for (int i = 0; i < errorTotal; i++) {
        int idx = errorIndices[i];
        printf("%-15s %-15s %-10d 次\n",
               library[idx].english,
               library[idx].chinese,
               library[idx].ErrorCount);
    }
}

// 檢視檔案內容
void check_folder() {
    printf("\n===== 檔案內容 =====\n");
    printf("資料夾: %d 個\n", folderCount);
    printf("單字  : %d 個\n", wordCount);
}

// 主選單選擇
int choosefountion() {
    int local_choice;
    if (scanf("%d", &local_choice) != 1) {
        while (getchar() != '\n');
        return 0;
    }
    getchar();

    switch (local_choice) {
        case 1: AddWord(); return local_choice;
        case 2: showCard(); return local_choice;
        case 3: takeTest(); return local_choice;
        case 4: Errowlist(); return local_choice;
        case 5: while(search()); return local_choice;
        case 6: check_folder(); printf("按 Enter 返回..."); getchar(); return local_choice;
        case 7: save(); printf("掰掰！要記得複習喔！\n"); return local_choice;
        default: printf("輸入錯誤...\n"); return 0;
    }
}
