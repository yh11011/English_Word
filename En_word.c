/* ================================================================
   英文單字背誦系統
   ================================================================
   這個程式可以讓我：
     1. 把單字分資料夾儲存
     2. 用單字卡方式學習
     3. 做測驗並記錄錯誤次數
     4. 查看錯題本 / 針對錯題再練習
     5. 查詢 / 刪除單字

   單字資料存在程式同目錄下的 english_word.txt，
   每一行格式是：資料夾名稱 [Tab] 英文 [Tab] 中文 [Tab] 錯誤次數
   例如：ch1    apple    蘋果    3
   ================================================================ */


/* ========== 引入標頭檔 ==========
   就像使用工具箱前要先把工具帶來，
   這些 #include 讓我可以使用 C 語言內建的各種函數。
   少了這些，編譯器會說「我不知道 printf 是什麼」。 */
#include <stdio.h>   // printf（印出文字）、scanf（讀輸入）、fopen/fclose/fgets/fprintf（讀寫檔案）
#include <stdlib.h>  // atoi（把字串 "3" 變成整數 3）
#include <string.h>  // strcpy（複製字串）、strcmp（比較字串）、strstr（在字串裡找子字串）
                     // strtok（切割字串）、strcspn（找特定字元的位置）、strlen（字串長度）
#include <time.h>    // time()，用來讓每次執行時隨機順序不同


/* ========== 常數定義 ==========
   用 #define 給數字取一個有意義的名字。
   好處：之後要改上限，只需要改這裡一處，不用在程式碼裡到處找數字。
   慣例：常數名稱全部大寫，方便一眼看出這是常數不是變數。 */
#define WORD_MAX   1000  // 最多存幾個單字（陣列大小固定，不能超過）
#define EN_LEN       50  // 英文單字欄位最長幾個字元（最後一格存 '\0' 結尾）
#define CN_LEN      100  // 中文意思欄位最長幾個字元（UTF-8 中文一個字佔 3 bytes）
#define FOLDER_MAX   50  // 最多幾個資料夾
#define LINE_BUF    300  // 讀取一整行文字時的暫存空間大小


/* ========== 結構定義 ==========
   struct（結構）可以把相關的資料綁在一起，
   就像一張單字卡上面同時有英文、中文、資料夾、錯誤次數。
   typedef 讓我之後可以直接寫 Word，不用每次都寫 struct Word。 */
typedef struct {
    char english[EN_LEN];  // 英文單字，例如 "apple"
    char chinese[CN_LEN];  // 中文意思，例如 "蘋果"
    char folder[EN_LEN];   // 屬於哪個資料夾，例如 "ch1"
    int  errorCount;       // 答錯了幾次（測驗時答錯就 +1）
} Word;


/* ========== 全域變數 ==========
   寫在所有函數外面的變數，整個程式都可以直接使用，
   不需要當參數傳來傳去。

   什麼時候用全域變數？
   → 當很多函數都需要存取同一份資料時（這裡的單字庫就是好例子）。
   → 不建議把所有變數都設為全域，會讓程式很難追蹤誰改了什麼。 */
Word library[WORD_MAX];              // 單字庫：一個可以裝 1000 個 Word 的陣列
int  wordCount = 0;                  // 目前存了幾個單字（陣列用了幾格）

char folderList[FOLDER_MAX][EN_LEN]; // 資料夾名稱清單，避免重複顯示
int  folderCount = 0;                // 目前有幾個不同的資料夾


/* ========== 函數前置宣告 ==========
   C 語言從上往下讀，如果函數 A 呼叫函數 B，
   但 B 寫在 A 的後面，編譯器就會說「找不到 B」。
   解決方法：在最上面先「宣告」所有函數的名稱和參數，
   讓編譯器知道它們的存在，之後再寫實際內容。 */

// --- 工具函數（小工具，其他函數會用到）---
void toLowerEN(char *str);
void inputLine(char *str, int max);
void inputLineEN(char *str, int max);
void clearInputBuffer(void);

// --- 檔案讀寫 ---
int  isFull(void);
void updateFolderList(const char *name);
void parseLine(char *line);
int  saveToFile(void);
void loadFile(void);

// --- 洗牌 ---
void shuffle(int arr[], int n);

// --- 資料夾選擇 ---
int  chooseFolder(void);

// --- 單字卡 ---
void showSingleCard(int idx);
void showAllCards(void);
void showFolderCards(int folderIdx);
void showCard(void);

// --- 測驗 ---
int  collectIndices(const char *folder, int result[]);
int  askQuestion(int wordIdx, int qNum, int total, int *score);
void runTest(int indices[], int total);
void takeTest(void);
void takeErrorTest(void);

// --- 其他功能 ---
int  search(void);
void showErrorList(void);
void deleteWord(void);
void AddWord(void);
void showStats(void);

// --- 主選單 ---
int  mainMenu(void);


/* ================================================================
   工具函數
   （這些函數很小，但很多地方會用到，所以先寫在最前面）
   ================================================================ */

/* toLowerEN：把字串裡的英文大寫字母全部換成小寫
   -------------------------------------------------------
   為什麼不直接用 C 內建的 tolower()？
   → tolower() 在有些系統上，遇到中文的 byte（多 byte 的 UTF-8）可能會出錯。
   → 我只想改英文的 A-Z，所以自己寫判斷式比較安全。

   原理：ASCII 編碼中，'A' = 65，'a' = 97，差距剛好是 32，
   所以把大寫加 32 就能得到對應的小寫。

   參數：
     str → 要修改的字串（直接改原本的，不會另外建一個新的）*/
void toLowerEN(char *str) {
    for (int i = 0; str[i] != '\0'; i++) {
        // str[i] != '\0' 是判斷「還沒到字串結尾」的寫法
        if (str[i] >= 'A' && str[i] <= 'Z') {
            str[i] += 32; // 'A'→'a', 'B'→'b', ... , 'Z'→'z'
        }
    }
}

/* inputLine：讀取使用者輸入的一整行文字
   -------------------------------------------------------
   為什麼不用 scanf("%s") 就好？
   → scanf 遇到空格就停止，無法讀「hello world」這種有空格的內容。
   → fgets 會讀整行，但會把使用者按的 Enter（'\n'）也存進去，
     所以要用 strcspn 找到 '\n' 的位置，把它換成 '\0'（字串結尾）。

   參數：
     str → 存放輸入內容的陣列
     max → 陣列大小（fgets 會確保不超出這個長度，防止 overflow）*/
void inputLine(char *str, int max) {
    fgets(str, max, stdin);
    str[strcspn(str, "\n")] = '\0'; // strcspn 找到第一個 '\n' 的位置，換成結尾
}

/* inputLineEN：讀取一行輸入，並把英文自動轉成小寫
   -------------------------------------------------------
   適合用在需要英文輸入的地方（資料夾名稱、單字輸入），
   這樣使用者打 APPLE 或 apple 都會被當成一樣。
   中文字元的 byte 值不在 A-Z 範圍，所以 toLowerEN 不會誤改它。*/
void inputLineEN(char *str, int max) {
    inputLine(str, max);  // 先讀一行
    toLowerEN(str);       // 再把英文大寫轉小寫
}

/* clearInputBuffer：清空鍵盤輸入緩衝區
   -------------------------------------------------------
   問題情境：
   用 scanf("%d") 讀完數字後，使用者按的 Enter 還留在緩衝區裡，
   下一個 fgets 就會直接讀到那個 Enter，看起來像「沒有等使用者輸入」。

   解法：一個一個讀走緩衝區裡的字元，直到讀到換行符或 EOF。

   為什麼要獨立成函數？
   → 程式裡很多地方都需要清緩衝區，寫成函數就不用一直重複寫。*/
void clearInputBuffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
    // 讀走所有字元，直到遇到換行或到達輸入結尾
}


/* ================================================================
   檔案讀寫
   ================================================================ */

/* isFull：確認單字庫是否已經滿了
   -------------------------------------------------------
   為什麼需要這個？
   → library[] 陣列大小固定（WORD_MAX 個），如果繼續寫入就會超出陣列邊界，
     這叫做「buffer overflow」，會讓程式當掉或行為異常，非常危險。
   → 每次要新增單字前都要先呼叫這個函數確認還有沒有空間。

   回傳值：1 = 已滿，請勿繼續新增；0 = 還有空間*/
int isFull(void) {
    if (wordCount >= WORD_MAX) {
        printf("[Error] 單字庫已滿（上限 %d 個），請先刪除一些單字。\n", WORD_MAX);
        return 1;
    }
    return 0;
}

/* updateFolderList：把資料夾名稱加入 folderList（如果還沒有的話）
   -------------------------------------------------------
   每次新增單字時都會呼叫，目的是讓 folderList 保持無重複的清單，
   這樣顯示選單時才不會出現同樣的資料夾兩次。*/
void updateFolderList(const char *name) {
    // 先掃描一遍，看看這個名稱是否已經存在
    for (int i = 0; i < folderCount; i++) {
        if (strcmp(folderList[i], name) == 0) {
            return; // 已經有了，不用再加，直接離開函數
        }
    }
    // 沒有的話，加到清單最後面（同時要確認還有空間）
    if (folderCount < FOLDER_MAX) {
        strcpy(folderList[folderCount], name);
        folderCount++;
    }
}

/* parseLine：解析一行文字，把單字資料存進 library[]
   -------------------------------------------------------
   檔案裡每行的格式是：
     資料夾 [Tab] 英文 [Tab] 中文 [Tab] 錯誤次數 [換行]

   strtok() 的工作原理：
   → 第一次呼叫：傳入字串和分隔符 "\t"，它會找到第一個 Tab，
     把那個位置換成 '\0'，然後回傳字串開頭的指標。
   → 之後呼叫：傳入 NULL，代表「繼續處理剛才那個字串」，
     從上次結束的地方繼續往後找下一個 Tab。
   → 注意！strtok 會破壞原始字串（把分隔符換成 '\0'），
     所以呼叫之後就不能再使用原本的 line 了。

   參數：
     line → 一行文字（會被 strtok 修改，呼叫後不能再用）*/
void parseLine(char *line) {
    if (isFull()) return; // 滿了就不繼續

    char *folder = strtok(line, "\t");           // 取第一段（資料夾名稱）
    char *en     = strtok(NULL, "\t");           // 取第二段（英文單字）
    char *ch     = strtok(NULL, "\t\r\n");       // 取第三段（中文意思，順便去掉 \r \n）
    char *errStr = strtok(NULL, "\t\r\n");       // 取第四段（錯誤次數，可能沒有）

    // 三個必要欄位缺一個就跳過這行（格式不對）
    if (!folder || !en || !ch) return;

    // 把資料寫進 library 的下一格
    strcpy(library[wordCount].folder,  folder);
    strcpy(library[wordCount].english, en);
    strcpy(library[wordCount].chinese, ch);
    // errStr 可能是 NULL（舊格式沒有這欄），用三元運算子設預設值
    library[wordCount].errorCount = errStr ? atoi(errStr) : 0;

    updateFolderList(folder); // 更新資料夾清單
    wordCount++;              // 最後才遞增，確保前面的寫入都成功了
}

/* saveToFile：把整個 library[] 寫入 english_word.txt
   -------------------------------------------------------
   每次新增或刪除單字、測驗結束後都會呼叫，
   確保關掉程式後資料還在。

   "w" 模式代表「寫入」：
   → 如果檔案已存在，會先清空再重寫（所以是整個重寫，不是追加）。
   → 如果檔案不存在，會自動建立一個新的。

   回傳值：1 = 儲存成功，0 = 開檔失敗*/
int saveToFile(void) {
    FILE *fp = fopen("english_word.txt", "w");
    if (!fp) {
        // 開檔失敗通常是因為沒有寫入權限
        printf("[Error] 無法儲存！請確認程式所在的資料夾有寫入權限。\n");
        return 0;
    }
    for (int i = 0; i < wordCount; i++) {
        // fprintf 跟 printf 一樣，但輸出目標是檔案（fp）而不是螢幕
        fprintf(fp, "%s\t%s\t%s\t%d\n",
                library[i].folder,
                library[i].english,
                library[i].chinese,
                library[i].errorCount);
    }
    fclose(fp); // 一定要記得關檔案！不然資料可能沒有真正寫進去
    return 1;
}

/* loadFile：程式啟動時，從 english_word.txt 讀取所有單字
   -------------------------------------------------------
   "r" 模式代表「唯讀」：
   → 如果檔案不存在，fopen 會回傳 NULL（不會建立新檔）。
   → 第一次使用這個程式時，english_word.txt 還不存在，是正常的。*/
void loadFile(void) {
    FILE *fp = fopen("english_word.txt", "r");
    if (!fp) {
        printf("[Notice] 還沒有單字資料，請先用「1. 新增單字」開始。\n");
        return;
    }

    char line[LINE_BUF];
    // fgets 每次讀一行（包含 '\n'），讀到檔案結尾時回傳 NULL，迴圈結束
    while (fgets(line, sizeof(line), fp)) {
        parseLine(line); // 解析這一行並存入 library[]
    }

    printf("讀取完成：%d 個資料夾，%d 個單字。\n", folderCount, wordCount);
    fclose(fp);
}


/* ================================================================
   洗牌（Fisher-Yates 演算法）
   ================================================================

   目的：把存放單字索引的陣列隨機打亂，讓測驗題目順序不固定。

   Fisher-Yates 演算法步驟（以 4 個元素為例）：
   → i=3：從 0~3 隨機選一個位置 j，把 arr[3] 和 arr[j] 交換
   → i=2：從 0~2 隨機選一個位置 j，把 arr[2] 和 arr[j] 交換
   → i=1：從 0~1 隨機選一個位置 j，把 arr[1] 和 arr[j] 交換
   → 完成！每種排列出現的機率完全相同。

   參數：
     arr → 要打亂的整數陣列（存放 library[] 的索引，例如 [0,1,2,3,...]）
     n   → 陣列長度*/
void shuffle(int arr[], int n) {
    for (int i = n - 1; i > 0; i--) {
        int j    = rand() % (i + 1); // 從 0 到 i 之間隨機選一個位置
        // 交換 arr[i] 和 arr[j]（需要一個暫存變數，就像交換兩杯飲料需要第三個杯子）
        int temp = arr[i];
        arr[i]   = arr[j];
        arr[j]   = temp;
    }
}


/* ================================================================
   資料夾選擇選單
   ================================================================ */

/* chooseFolder：顯示資料夾列表，讓使用者選要操作哪個範圍
   -------------------------------------------------------
   回傳值：
     1 ~ folderCount → 使用者選了某個資料夾（對應 folderList 的索引+1）
     99              → 使用者選了「全部單字」
     -1              → 使用者選擇離開，或目前完全沒有單字*/
int chooseFolder(void) {
    // 連單字都沒有，就沒什麼好選的
    if (wordCount == 0) {
        printf("[Notice] 目前沒有任何單字，請先新增。\n");
        return -1;
    }

    int option;
    while (1) { // 無限迴圈，直到使用者輸入有效選項才 return 離開
        printf("\n===== 選擇範圍 =====\n");
        for (int i = 0; i < folderCount; i++) {
            printf("  %d. %s\n", i + 1, folderList[i]);
        }
        printf(" 99. 全部單字\n");
        printf("100. 返回主選單\n");
        printf("請選擇: ");

        if (scanf("%d", &option) != 1) {
            // 使用者輸入了非數字（例如打了「abc」），scanf 回傳 0 表示讀取失敗
            clearInputBuffer(); // 清掉錯誤的輸入，不然下次還是會讀到它
            printf("[Error] 請輸入數字。\n");
            continue; // 回到迴圈開頭重新顯示選單
        }
        clearInputBuffer(); // 清掉數字後面殘留的換行符

        if (option == 100) return -1;  // 使用者要返回
        if (option == 99)  return 99;  // 全部單字
        if (option >= 1 && option <= folderCount) return option; // 某個資料夾

        printf("[Error] 沒有這個選項，請重新輸入。\n");
    }
}


/* ================================================================
   單字卡學習
   ================================================================ */

/* showSingleCard：顯示一張單字卡
   -------------------------------------------------------
   先秀英文，等使用者按 Enter 之後才顯示中文，
   這樣可以讓使用者先想一下答案再對照。

   參數：
     idx → 這張單字卡在 library[] 裡的位置（索引）*/
void showSingleCard(int idx) {
    printf("----------------------------\n");
    printf("英文: %s\n", library[idx].english);
    printf("（按 Enter 查看中文）");
    getchar(); // 等待使用者按 Enter（讀走那個換行符）
    printf("中文: %s\n", library[idx].chinese);
}

/* showAllCards：依序顯示所有單字的單字卡*/
void showAllCards(void) {
    printf("\n共 %d 個單字，按 Enter 逐張翻閱...\n", wordCount);
    for (int i = 0; i < wordCount; i++) {
        printf("\n[第 %d / %d 張]\n", i + 1, wordCount);
        showSingleCard(i);
    }
    printf("\n===== 學習完畢！=====\n");
}

/* showFolderCards：只顯示某個資料夾裡的單字卡
   -------------------------------------------------------
   參數：
     folderIdx → chooseFolder() 回傳的數字（從 1 開始）*/
void showFolderCards(int folderIdx) {
    // folderIdx 是 1 開始，但陣列索引從 0 開始，所以要 -1
    const char *target = folderList[folderIdx - 1];
    int count = 0;

    printf("\n資料夾「%s」的單字卡：\n", target);
    for (int i = 0; i < wordCount; i++) {
        // strcmp 比較兩個字串是否相同，相同回傳 0
        if (strcmp(library[i].folder, target) == 0) {
            printf("\n[第 %d 張]\n", ++count);
            showSingleCard(i);
        }
    }

    if (count == 0)
        printf("這個資料夾目前沒有單字。\n");
    else
        printf("\n===== 學習完畢，共 %d 個單字！=====\n", count);
}

/* showCard：單字卡學習功能的入口*/
void showCard(void) {
    printf("\n===== 單字卡學習模式 =====\n");
    int choice = chooseFolder();
    if (choice == -1) return;           // 使用者選擇離開
    if (choice == 99) showAllCards();   // 全部
    else              showFolderCards(choice); // 某個資料夾
}


/* ================================================================
   測驗功能
   ================================================================ */

/* collectIndices：收集符合條件的單字，把它們在 library[] 的索引存進 result[]
   -------------------------------------------------------
   為什麼用索引而不是直接複製單字資料？
   → 因為我們之後要修改 errorCount，如果是複製出來的副本，
     改了不會影響到原本的 library[]，所以必須用索引來操作原本的資料。

   參數：
     folder → 要篩選哪個資料夾；傳入 NULL 代表「全部都要」
     result → 由呼叫者提供的陣列，用來存結果

   回傳值：符合條件的單字數量*/
int collectIndices(const char *folder, int result[]) {
    int count = 0;
    for (int i = 0; i < wordCount; i++) {
        // folder == NULL 代表不篩選，全部收集
        if (folder == NULL || strcmp(library[i].folder, folder) == 0) {
            result[count] = i; // 把索引 i 存進結果陣列
            count++;
        }
    }
    return count;
}

/* askQuestion：出一道題目，讀取使用者的答案，判斷對錯
   -------------------------------------------------------
   為什麼 score 要用「指標（*score）」而不是直接傳整數？
   → C 語言函數的參數是「複製一份」傳進來的，
     如果直接傳 score 這個整數，在函數裡改它，
     改的是「複製品」，不會影響呼叫者的 score。
   → 傳指標（&score）相當於傳「score 的地址」，
     這樣函數就能直接到那個地址去修改它。

   參數：
     wordIdx → 這題的單字在 library[] 的索引
     qNum    → 目前是第幾題（顯示用）
     total   → 總共幾題（顯示用）
     score   → 分數的指標，答對時 *score 加 1

   回傳值：1 = 答對，0 = 答錯*/
int askQuestion(int wordIdx, int qNum, int total, int *score) {
    char answer[EN_LEN];

    printf("\n--- 第 %d / %d 題 ---\n", qNum, total);
    printf("中文：%s\n", library[wordIdx].chinese);
    printf("請輸入英文單字：");

    // %49s 最多讀 49 個字元（比陣列大小 EN_LEN=50 少 1，留給 '\0'）
    scanf("%49s", answer);
    clearInputBuffer(); // 清掉 scanf 後面殘留的換行符

    toLowerEN(answer); // 把使用者的答案轉小寫，讓大小寫都算對

    if (strcmp(answer, library[wordIdx].english) == 0) {
        (*score)++;   // *score 代表「解開指標，取得它指向的值」，然後 +1
        printf("✓ 答對了！目前得分：%d / %d\n", *score, qNum);
        return 1;
    } else {
        library[wordIdx].errorCount++; // 直接修改 library[] 裡的資料
        printf("✗ 答錯了，正確答案是：%s（這題已答錯 %d 次）\n",
               library[wordIdx].english,
               library[wordIdx].errorCount);
        printf("  目前得分：%d / %d\n", *score, qNum);
        return 0;
    }
}

/* runTest：執行一次完整的測驗流程，顯示最終結果
   -------------------------------------------------------
   為什麼要獨立成一個函數？
   → takeTest（一般測驗）和 takeErrorTest（錯題測驗）的流程幾乎一樣，
     把共用的部分抽出來，就不用寫兩遍一樣的程式碼。
   → 這種概念叫做「避免重複（Don't Repeat Yourself）」。

   參數：
     indices → 要測驗的單字索引陣列（已經洗牌過）
     total   → 陣列長度，也就是總題數*/
void runTest(int indices[], int total) {
    int score      = 0;
    int wrongList[WORD_MAX]; // 記錄這次答錯的單字索引
    int wrongCount = 0;

    for (int i = 0; i < total; i++) {
        if (!askQuestion(indices[i], i + 1, total, &score)) {
            // askQuestion 回傳 0 表示答錯
            wrongList[wrongCount] = indices[i];
            wrongCount++;
        }
    }

    // 顯示最終結果
    printf("\n===== 測驗結束 =====\n");
    // (double) 是強制型別轉換，讓除法結果是小數而不是整數
    printf("最終得分：%d / %d（正確率 %.0f%%）\n",
           score, total, (double)score / total * 100);

    if (wrongCount > 0) {
        printf("\n這次答錯的單字（共 %d 個）：\n", wrongCount);
        for (int i = 0; i < wrongCount; i++) {
            printf("  ✗  %-20s %s\n",
                   library[wrongList[i]].english,
                   library[wrongList[i]].chinese);
        }
    } else {
        printf("太厲害了！全部答對！\n");
    }

    saveToFile(); // 把更新後的錯誤次數存回檔案
}

/* takeTest：一般測驗（可選資料夾，隨機出題）*/
void takeTest(void) {
    printf("\n===== 單字測驗模式 =====\n");

    int folderChoice = chooseFolder();
    if (folderChoice == -1) return;

    // 選了 99 就是全部，否則取對應資料夾名稱
    const char *folder = (folderChoice == 99) ? NULL : folderList[folderChoice - 1];

    int indices[WORD_MAX];
    int total = collectIndices(folder, indices);
    if (total == 0) {
        printf("這個範圍裡沒有任何單字可以測驗。\n");
        return;
    }

    shuffle(indices, total); // 洗牌：打亂出題順序
    runTest(indices, total);
}

/* takeErrorTest：錯題加強測驗（只針對有答錯過的單字）*/
void takeErrorTest(void) {
    int errorIndices[WORD_MAX];
    int errorTotal = 0;

    // 找出所有錯誤次數 > 0 的單字
    for (int i = 0; i < wordCount; i++) {
        if (library[i].errorCount > 0) {
            errorIndices[errorTotal] = i;
            errorTotal++;
        }
    }

    if (errorTotal == 0) {
        printf("目前沒有任何錯誤紀錄，繼續加油！\n");
        return;
    }

    printf("\n===== 錯題加強測驗（共 %d 題）=====\n", errorTotal);
    shuffle(errorIndices, errorTotal); // 打亂順序，避免記住題目位置
    runTest(errorIndices, errorTotal);
}


/* ================================================================
   查詢功能
   ================================================================ */

/* search：讓使用者輸入關鍵字，同時搜尋英文和中文欄位
   -------------------------------------------------------
   回傳值：1 = 繼續查詢，0 = 使用者輸入 end 要離開

   為什麼回傳 int？
   → 在 mainMenu 裡是用 while(search()) 呼叫的，
     回傳 1 就繼續查，回傳 0 就停止。這是一種讓迴圈能「從函數裡控制」的技巧。*/
int search(void) {
    char keyword[CN_LEN];     // 原始輸入，保留中文不轉換
    char keyLower[CN_LEN];    // 英文搜尋用的小寫版本

    printf("\n請輸入要查詢的英文或中文（輸入 end 結束查詢）：");
    inputLine(keyword, CN_LEN);

    if (strlen(keyword) == 0) return 1; // 什麼都沒輸入，繼續
    if (strcmp(keyword, "end") == 0) {
        printf("結束查詢。\n");
        return 0; // 告訴呼叫者停止 while 迴圈
    }

    // 製作小寫版本，讓英文搜尋不分大小寫
    strcpy(keyLower, keyword);
    toLowerEN(keyLower);

    int foundCount = 0;
    for (int i = 0; i < wordCount; i++) {
        // strstr(a, b) → 在 a 裡面找 b，找到回傳非 NULL，找不到回傳 NULL
        int matchEN = (strstr(library[i].english, keyLower) != NULL);
        int matchCN = (strstr(library[i].chinese, keyword)  != NULL);

        if (matchEN || matchCN) {
            foundCount++;
            printf("  %d. [%s]  %-20s ／ %s  （已錯 %d 次）\n",
                   foundCount,
                   library[i].folder,
                   library[i].english,
                   library[i].chinese,
                   library[i].errorCount);
        }
    }

    if (foundCount == 0)
        printf("找不到包含「%s」的單字。\n", keyword);
    else
        printf("共找到 %d 筆。\n", foundCount);

    return 1; // 查詢結束，繼續等下一次輸入
}


/* ================================================================
   錯題本
   ================================================================ */

/* showErrorList：顯示所有有答錯紀錄的單字，按錯誤次數從多到少排列
   -------------------------------------------------------
   排序方式：選擇排序（Selection Sort）
   → 每輪從「還沒排好的部分」找出錯誤次數最多的，
     把它放到最前面，然後繼續處理剩下的。
   → 第一輪：找全部裡最多的 → 放到第 0 位
   → 第二輪：找剩下的最多的 → 放到第 1 位
   → 以此類推...

   為什麼用索引陣列而不是直接排序 library[]？
   → 直接排序 library[] 會改變單字的儲存順序，影響其他功能。
   → 用一個獨立的索引陣列來排序，library[] 本身不動，
     只是「觀看的順序」不同。*/
void showErrorList(void) {
    int errorIdx[WORD_MAX]; // 存放「有答錯的單字」在 library[] 裡的索引
    int errorTotal = 0;

    // 收集所有有錯誤紀錄的單字索引
    for (int i = 0; i < wordCount; i++) {
        if (library[i].errorCount > 0) {
            errorIdx[errorTotal] = i;
            errorTotal++;
        }
    }

    if (errorTotal == 0) {
        printf("\n太棒了！目前完全沒有錯誤紀錄！繼續保持！\n");
        return;
    }

    // 選擇排序：讓錯最多的排在前面
    for (int i = 0; i < errorTotal - 1; i++) {
        int maxPos = i; // 先假設「目前這個位置」的錯誤次數是最多的
        for (int j = i + 1; j < errorTotal; j++) {
            if (library[errorIdx[j]].errorCount > library[errorIdx[maxPos]].errorCount) {
                maxPos = j; // 找到更多的，更新「最多」的位置
            }
        }
        if (maxPos != i) {
            // 把「錯最多的」和「目前位置」交換
            int tmp        = errorIdx[i];
            errorIdx[i]    = errorIdx[maxPos];
            errorIdx[maxPos] = tmp;
        }
    }

    // 顯示排序後的錯題清單
    printf("\n===== 錯題本（共 %d 個單字）=====\n", errorTotal);
    printf("%-5s  %-22s  %-22s  %s\n", "名次", "英文", "中文", "錯誤次數");
    printf("-----------------------------------------------\n");
    for (int i = 0; i < errorTotal; i++) {
        int idx = errorIdx[i];
        printf("%-5d  %-22s  %-22s  %d 次\n",
               i + 1,
               library[idx].english,
               library[idx].chinese,
               library[idx].errorCount);
    }

    // 詢問是否要立刻針對這些錯題測驗
    printf("\n要針對這些錯題進行加強測驗嗎？(1=是 / 其他=否): ");
    int yn;
    if (scanf("%d", &yn) == 1 && yn == 1) {
        clearInputBuffer();
        takeErrorTest();
    } else {
        clearInputBuffer();
    }
}


/* ================================================================
   刪除單字
   ================================================================ */

/* deleteWord：讓使用者輸入單字名稱，從 library[] 中刪除
   -------------------------------------------------------
   刪除的方法（以最後元素覆蓋）：
   → 找到要刪的單字後，把 library[] 最後一格的資料複製過來蓋掉它，
     再把 wordCount 減 1，這格就等於「消失」了。

   這個方法的優缺點：
   ✓ 優點：速度快，O(1)，不需要移動其他元素
   ✗ 缺點：單字的儲存順序會改變（但這個程式不依賴順序，所以沒關係）*/
void deleteWord(void) {
    if (wordCount == 0) {
        printf("目前沒有任何單字可以刪除。\n");
        return;
    }

    clearInputBuffer(); // 清掉主選單 scanf 留下的換行
    char target[EN_LEN];
    printf("\n請輸入要刪除的英文單字（輸入 end 取消）：");
    inputLineEN(target, EN_LEN);

    if (strcmp(target, "end") == 0) {
        printf("已取消刪除。\n");
        return;
    }

    // 在 library[] 裡找這個單字
    for (int i = 0; i < wordCount; i++) {
        if (strcmp(library[i].english, target) == 0) {
            printf("\n找到：\n");
            printf("  英文：%s\n  中文：%s\n  資料夾：%s\n",
                   library[i].english, library[i].chinese, library[i].folder);
            printf("確定要刪除嗎？(1=確定 / 其他=取消): ");

            int yn;
            scanf("%d", &yn);
            clearInputBuffer();

            if (yn != 1) {
                printf("已取消。\n");
                return;
            }

            // 用最後一個元素覆蓋，縮短陣列
            library[i] = library[wordCount - 1];
            wordCount--;
            saveToFile();
            printf("[Success] 已成功刪除「%s」。\n", target);
            return;
        }
    }

    printf("找不到「%s」這個單字。\n", target);
}


/* ================================================================
   新增單字
   ================================================================ */

/* AddWord：讓使用者一次新增多個單字，輸入 end 才結束
   -------------------------------------------------------
   輸入格式：英文單字 [Tab鍵] 中文意思
   例如：apple    蘋果*/
void AddWord(void) {
    if (isFull()) return;
    clearInputBuffer(); // 清掉主選單 scanf 留下的換行

    printf("===== 新增單字 =====\n");
    printf("（每次新增都會自動存檔）\n\n");

    // 第一步：選擇要存入哪個資料夾
    char folder[EN_LEN];
    while (1) {
        printf("請輸入資料夾名稱（英文，例如 ch1 / unit2）：");
        inputLineEN(folder, EN_LEN); // 讀入並轉小寫
        if (strlen(folder) > 0) break;
        printf("[Error] 資料夾名稱不能空白，請重新輸入。\n");
    }
    updateFolderList(folder); // 確保這個資料夾有被記錄起來

    printf("\n輸入格式：英文 [Tab鍵] 中文，例如：apple\t蘋果\n");
    printf("輸入 end 結束新增。\n\n");

    // 第二步：重複接收單字，直到輸入 end 或單字庫滿為止
    while (!isFull()) {
        printf("> ");
        char raw[LINE_BUF];
        inputLineEN(raw, LINE_BUF); // 讀入並把英文轉小寫（中文不受影響）

        if (strcmp(raw, "end") == 0) {
            printf("新增結束。\n");
            break;
        }

        /* 為什麼要先複製到 copy 再用 strtok 切割？
           → strtok 會直接修改傳入的字串（把 Tab 換成 '\0'）。
           → 如果直接切割 raw，之後就沒辦法用 raw 的內容來組合 wholeLine 了。
           → 用複本 copy 來切割，raw 保持原樣可以繼續使用。*/
        char copy[LINE_BUF];
        strcpy(copy, raw);
        char *en = strtok(copy, "\t"); // 切出英文部分
        char *ch = strtok(NULL, "\t"); // 切出中文部分

        // 檢查格式是否正確（兩個部分都要有）
        if (!en || !ch || strlen(en) == 0 || strlen(ch) == 0) {
            printf("[Error] 格式錯誤，記得用 Tab 鍵分隔英文和中文。\n");
            continue; // 跳回迴圈開頭，讓使用者重新輸入
        }

        // 重複檢查：同一個資料夾裡，英文和中文都完全一樣就算重複
        int duplicate = 0;
        for (int i = 0; i < wordCount; i++) {
            if (strcmp(library[i].folder,  folder) == 0 &&
                strcmp(library[i].english, en)     == 0 &&
                strcmp(library[i].chinese, ch)     == 0) {
                duplicate = 1;
                break; // 找到就不用繼續找了
            }
        }
        if (duplicate) {
            printf("[Warning] 這個單字在「%s」已經存在了，跳過。\n", folder);
            continue;
        }

        /* 為什麼要組合成 wholeLine 再傳給 parseLine？
           → parseLine 負責解析「資料夾\t英文\t中文」這種格式，
             並把它寫入 library[]。
           → 我們直接重用這個函數，不用再寫一遍存入的邏輯。*/
        char wholeLine[LINE_BUF];
        sprintf(wholeLine, "%s\t%s\t%s", folder, en, ch);
        parseLine(wholeLine);

        printf("[Success] 已新增：%s ／ %s（資料夾：%s）\n",
               library[wordCount - 1].english,
               library[wordCount - 1].chinese,
               folder);
        saveToFile(); // 每新增一個就存一次，避免中途出錯遺失資料
    }
}


/* ================================================================
   統計資訊
   ================================================================ */

/* showStats：顯示目前單字庫的整體數據*/
void showStats(void) {
    printf("\n===== 統計資訊 =====\n");
    printf("資料夾數量  : %d 個\n", folderCount);
    printf("單字總量    : %d 個\n", wordCount);

    // 計算有答錯過的單字數和總錯誤次數
    int hasErrorCount = 0;
    int totalErrors   = 0;
    for (int i = 0; i < wordCount; i++) {
        if (library[i].errorCount > 0) {
            hasErrorCount++;
            totalErrors += library[i].errorCount;
        }
    }
    printf("有錯誤紀錄  : %d 個單字\n", hasErrorCount);
    printf("累計總錯誤  : %d 次\n",     totalErrors);

    // 顯示每個資料夾有幾個單字（讓使用者知道各章節的進度）
    if (folderCount > 0) {
        printf("\n各資料夾單字數：\n");
        for (int f = 0; f < folderCount; f++) {
            int count = 0;
            for (int i = 0; i < wordCount; i++) {
                if (strcmp(library[i].folder, folderList[f]) == 0) count++;
            }
            printf("  %-20s %d 個\n", folderList[f], count);
        }
    }
}


/* ================================================================
   主選單與程式進入點
   ================================================================ */

/* mainMenu：讀取使用者選擇的數字，呼叫對應的功能函數
   -------------------------------------------------------
   回傳值：使用者輸入的數字（8 代表離開程式）*/
int mainMenu(void) {
    int choice;
    if (scanf("%d", &choice) != 1) {
        clearInputBuffer(); // 讀取失敗（輸入了非數字），清空緩衝區
        printf("[Error] 請輸入 1~8 的數字。\n");
        return 0; // 回傳 0，do-while 迴圈會繼續（因為 0 != 8）
    }
    clearInputBuffer(); // 清掉數字後面殘留的換行

    switch (choice) {
        case 1: AddWord();        break;
        case 2: showCard();       break;
        case 3: takeTest();       break;
        case 4: showErrorList();  break;
        case 5: while (search()); break; // search 回傳 0（使用者輸入 end）才停止
        case 6:
            showStats();
            printf("\n按 Enter 返回主選單...");
            getchar();
            break;
        case 7: deleteWord();     break;
        case 8:
            saveToFile();
            printf("掰掰！記得定期複習喔！\n");
            break;
        default:
            printf("[Error] 請輸入 1~8 的數字。\n");
            return 0;
    }
    return choice;
}

/* main：程式的起點，C 語言程式一定從這裡開始執行
   -------------------------------------------------------
   srand(time(NULL)) 的作用：
   → rand() 產生的數字序列其實是固定的「偽隨機」，
     每次執行都一樣（好比說固定是 4, 1, 3, 2...）。
   → 用 time(NULL) 取得目前時間（秒數），當作「起始點（種子）」，
     這樣每次執行的起始點不同，洗牌結果也就不同了。
   → (unsigned) 是型別轉換，讓負的時間值也能正常使用。*/
int main(void) {
    srand((unsigned)time(NULL)); // 設定隨機種子，讓每次洗牌結果不同
    loadFile();                  // 讀取之前儲存的單字資料

    int choice;
    do {
        // 每次迴圈都顯示主選單
        printf("\n+============================+\n");
        printf("|      英文單字背誦系統        |\n");
        printf("+============================+\n");
        printf("|  1. 新增單字               |\n");
        printf("|  2. 單字卡學習             |\n");
        printf("|  3. 開始測驗               |\n");
        printf("|  4. 錯題本                 |\n");
        printf("|  5. 查詢單字               |\n");
        printf("|  6. 統計資訊               |\n");
        printf("|  7. 刪除單字               |\n");
        printf("|  8. 離開程式               |\n");
        printf("+============================+\n");
        printf("請選擇功能 (1~8)：");
        choice = mainMenu();
    } while (choice != 8); // 選 8 才離開迴圈，結束程式

    return 0; // main 回傳 0 代表「程式正常結束」
}