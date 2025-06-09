# AI 股票查詢系統

## 簡介

本系統是一個使用 AI 技術的股票分析工具，旨在為使用者提供快速、簡潔的股票資訊和投資建議。透過輸入股票代號，系統會自動分析股票的技術指標和基本面資訊，並生成易於理解的分析報告。

![螢幕擷取畫面 2025-06-06 152307](https://github.com/user-attachments/assets/5f936982-01e5-4d52-bdbd-1972d1345caf)

## 功能

-   **股票資訊查詢**：支援台股（4 位數字代碼）和美股（字母代碼）的股票資訊查詢。
-   **AI 分析報告**：使用 AI 模型（ChatGLM3-6B）生成股票分析報告，提供投資建議。
-   **技術分析圖表**：顯示股價走勢、移動平均線（MA）、相對強弱指標（RSI）和布林通道等技術分析圖表。
-   **基本統計資訊**：顯示股票的目前價格、漲跌幅、期間最高價和最低價等基本統計資訊。
-   **基本面資訊**：顯示股票的基本面資訊，如本益比、市值、股息殖利率等。

## 檔案結構

```
finance_agent/
├── agent.py          # 主要的 AI Agent 邏輯
├── app.py            # Streamlit 應用程式介面
├── stock_utils.py    # 股票資料相關的工具函式
├── utils.py          # 通用工具函式
└── README.md         # 說明文件
```

## 使用方法

1.  **安裝相依套件**

    ```bash
    pip install -r requirements.txt
    ```

    請確保 `requirements.txt` 檔案包含所有必要的套件，例如：

    ```
    streamlit
    yfinance
    pandas
    langgraph
    matplotlib
    ```

2.  **執行 Streamlit 應用程式**

    ```bash
    streamlit run app.py
    ```

3.  **在瀏覽器中打開應用程式**

    在 Streamlit 啟動後，瀏覽器會自動打開應用程式。如果沒有，請手動打開顯示的網址。

4.  **輸入股票代號**

    在應用程式的輸入框中輸入股票代號，然後點擊「查詢」按鈕。

5.  **查看分析結果**

    系統會顯示 AI 分析報告、技術分析圖表和基本統計資訊。

## 程式碼說明

-   `agent.py`：
    -   定義了 `StockAgent` 類別，負責執行股票分析查詢。
    -   使用 LangGraph 建立工作流程，包括查詢理解、資料獲取、金融分析和回應生成等節點。
    -   使用 `call_chatglm` 函數呼叫本地 ChatGLM 模型生成分析報告。
-   `app.py`：
    -   使用 Streamlit 建立使用者介面。
    -   接收使用者輸入的股票代號，並呼叫 `StockAgent` 進行分析。
    -   顯示 AI 分析報告和技術分析圖表。
-   `stock_utils.py`：
    -   包含股票資料相關的工具函式，例如：
        -   `fetch_us_stock`：抓取美股歷史資料。
        -   `fetch_tw_stock`：抓取台股歷史資料。
        -   `compute_technical_indicators`：計算技術指標，如移動平均線和 RSI。
        -   `get_fundamental_data`：獲取基本面資料。
        -   `generate_analysis_summary`：生成分析摘要。
-   `utils.py`：
    -   包含通用工具函式，例如：
        -   `call_chatglm`：呼叫本地 ChatGLM 模型。

## 注意事項

-   本系統使用 ChatGLM3-6B 模型，請確保已正確安裝和設定。
-   股票資料僅供參考，投資有風險，請謹慎決策。

## 貢獻

歡迎提交 Pull Request 來改進本系統。
