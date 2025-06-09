# agent.py

from typing import Any, TypedDict
import pandas as pd
from langgraph.graph import StateGraph, END
from utils import call_chatglm
from stock_utils import fetch_us_stock, fetch_tw_stock, compute_technical_indicators, get_fundamental_data, generate_analysis_summary
# -------------------------------
# 1. 呼叫本地 ChatGLM 的輔助函式  call_chatglm
# -------------------------------
# -------------------------------
# 2. 工具函式：抓取股票資料 fetch_us_stock, fetch_tw_stock
# -------------------------------
# -------------------------------
# 3. 工具函式：計算技術指標 compute_technical_indicators
# -------------------------------
# -------------------------------
# 4. LangGraph 節點實作
# -------------------------------
def query_understanding_node(state):
    """
    修改後的查詢理解節點：自動判斷市場類型，只需要股票代號
    """
    user_query: str = state["query"].strip()
    
    # 自動判斷市場類型
    market = None
    ticker = None
    
    # 判斷是否為台股代碼（4位數字）
    if user_query.isdigit() and len(user_query) == 4:
        market = "tw"
        ticker = user_query
    # 判斷是否為美股代碼（字母組合）
    elif user_query.replace('.', '').isalpha() and len(user_query) <= 5:
        market = "us"
        ticker = user_query.upper()
    else:
        # 如果不符合標準格式，嘗試解析
        import re
        
        # 嘗試提取台股代碼
        tw_match = re.search(r'\b(\d{4})\b', user_query)
        if tw_match:
            market = "tw"
            ticker = tw_match.group(1)
        else:
            # 嘗試提取美股代碼
            us_match = re.search(r'\b([A-Z]{1,5})\b', user_query.upper())
            if us_match:
                market = "us"
                ticker = us_match.group(1)
            else:
                # 無法識別，預設為基本分析
                market = "unknown"
                ticker = user_query.upper()
    
    # 分析意圖固定為基本分析（因為只有股票代號）
    intent = "basic"
    
    print(f"解析結果: market={market}, ticker={ticker}, intent={intent}")
    
    return {**state, "market": market, "ticker": ticker, "intent": intent}

def stock_api_tool(state):
    market = state["market"]
    ticker = state["ticker"]
    
    # 檢查是否能識別市場類型
    if market == "unknown":
        error_msg = f"無法識別股票代號 '{ticker}'，請確認輸入正確的台股代號（4位數字）或美股代號（字母）"
        return {
            **state, 
            "error": error_msg, 
            "df": pd.DataFrame(), 
            "current_price": 0, 
            "previous_close": 0,
            "period_high": 0,
            "period_low": 0,
            "avg_volume": 0,
            "data_points": 0
        }
    
    # 檢查是否有有效的股票代碼
    if not ticker:
        error_msg = f"請提供有效的{'台股' if market == 'tw' else '美股'}代碼"
        return {
            **state, 
            "error": error_msg, 
            "df": pd.DataFrame(), 
            "current_price": 0, 
            "previous_close": 0,
            "period_high": 0,
            "period_low": 0,
            "avg_volume": 0,
            "data_points": 0
        }
    
    try:
        if market == "us":
            df = fetch_us_stock(ticker)
        else:
            df = fetch_tw_stock(ticker)
        
        if len(df) < 1:
            raise ValueError("資料不足，無法進行分析")
            
        current_price = df["Close"].iloc[-1]
        prev_close = df["Close"].iloc[-2] if len(df) > 1 else current_price
        
        # 計算兩個月期間的統計資料
        max_price = df["Close"].max()
        min_price = df["Close"].min()
        avg_volume = df["Volume"].mean()
        
        return {
            **state, 
            "df": df, 
            "current_price": current_price, 
            "previous_close": prev_close,
            "period_high": max_price,
            "period_low": min_price,
            "avg_volume": avg_volume,
            "data_points": len(df)
        }
        
    except Exception as e:
        error_msg = f"取得股票資料失敗：{str(e)}"
        print(f"API 錯誤: {error_msg}")
        return {
            **state, 
            "error": error_msg, 
            "df": pd.DataFrame(), 
            "current_price": 0, 
            "previous_close": 0,
            "period_high": 0,
            "period_low": 0,
            "avg_volume": 0,
            "data_points": 0
        }

def financial_analyzer(state):
    """
    金融分析節點：計算技術指標並進行基本面分析
    """
    # 檢查是否有錯誤
    if "error" in state:
        return state
    
    df = state["df"]
    market = state["market"]
    ticker = state["ticker"]
    intent = state["intent"]
    
    try:
        # 計算技術指標
        df_with_indicators = compute_technical_indicators(df)
        
        # 獲取基本面資料
        fundamental_data = get_fundamental_data(ticker, market)
        
        # 生成分析摘要
        analysis_summary = generate_analysis_summary(df_with_indicators, intent, fundamental_data)
        
        return {
            **state,
            "df_ind": df_with_indicators,
            "fundamental_data": fundamental_data,
            "analysis_summary": analysis_summary
        }
        
    except Exception as e:
        error_msg = f"分析過程發生錯誤：{str(e)}"
        print(f"分析錯誤: {error_msg}")
        return {**state, "error": error_msg}



def response_generator(state):
    # 檢查是否有錯誤
    if "error" in state:
        return {**state, "response_text": f"很抱歉，{state['error']}"}
    
    market_name = "美股" if state['market'] == 'us' else "台股"
    current_price = state['current_price']
    previous_close = state['previous_close']
    price_change = current_price - previous_close
    price_change_pct = (price_change / previous_close * 100) if previous_close != 0 else 0
    data_points = state.get('data_points', 0)
    
    # 安全格式化函數
    def safe_format_price(value, decimal_places=2):
        try:
            return f"{float(value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    # 修正格式化問題 - 將 :>+8 改為分開處理
    price_change_str = safe_format_price(price_change, 2)
    if price_change > 0:
        price_change_str = "+" + price_change_str
    
    price_change_pct_str = safe_format_price(price_change_pct, 2)
    if price_change_pct > 0:
        price_change_pct_str = "+" + price_change_pct_str
    
    # 建構基本回應，不依賴 LLM
    basic_info = (
        f"📊 {market_name} {state['ticker']} 股票資訊（近兩個月資料）\n"
        f"\n"
        f"💰 目前價格：{safe_format_price(current_price)}\n"
        f"📈 前日收盤：{safe_format_price(previous_close)}\n"
        f"📊 漲跌幅：{price_change_str} ({price_change_pct_str}%)\n"
        f"📅 資料天數：{data_points} 個交易日\n"
        f"\n"
        f"🔍 綜合分析：{state['analysis_summary']}\n"
    )
    # 添加基本面詳細資訊（如果有的話）
    fundamental_data = state.get('fundamental_data', {})
    if fundamental_data and any(v != 'N/A' for v in fundamental_data.values()):
        basic_info += f"\n"
        basic_info += f"📈 基本面詳細資訊：\n"
        
        if fundamental_data.get('sector') != 'N/A':
            basic_info += f"🏢 產業：{fundamental_data.get('sector')}\n"
        if fundamental_data.get('pe_ratio') != 'N/A':
            basic_info += f"📊 本益比：{fundamental_data.get('pe_ratio')}\n"
        if fundamental_data.get('market_cap') != 'N/A':
            market_cap = fundamental_data.get('market_cap')
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap > 1000000000:
                    basic_info += f"💼 市值：${market_cap/1000000000:.1f}B\n"
                elif market_cap > 1000000:
                    basic_info += f"💼 市值：${market_cap/1000000:.1f}M\n"
        if fundamental_data.get('dividend_yield') != 'N/A':
            div_yield = fundamental_data.get('dividend_yield')
            if isinstance(div_yield, (int, float)) and div_yield > 0:
                basic_info += f"💰 股息殖利率：{div_yield*100:.2f}%\n"
        if fundamental_data.get('profit_margin') != 'N/A':
            profit_margin = fundamental_data.get('profit_margin')
            if isinstance(profit_margin, (int, float)) and profit_margin > 0:
                basic_info += f"📈 毛利率：{profit_margin*100:.2f}%\n"

    # 添加智能建議
    if price_change_pct > 3:
        suggestion = "💡 投資建議：股價表現強勁，但請注意風險管理，適時獲利了結"
    elif price_change_pct < -3:
        suggestion = "⚠️  投資建議：股價下跌較多，可關注是否為逢低買進時機，但需搭配基本面分析"
    elif abs(price_change_pct) < 1:
        suggestion = "📝 投資建議：股價波動溫和，可持續觀察後續走勢，適合定期定額投資"
    else:
        suggestion = "📊 投資建議：股價波動正常，建議綜合技術面和基本面進行投資決策"

    # 根據RSI給出額外建議
    try:
        df_ind = state.get('df_ind')
        if df_ind is not None and not df_ind.empty:
            latest_rsi = df_ind.iloc[-1]['RSI_14']
            if pd.notna(latest_rsi):
                if latest_rsi > 70:
                    suggestion += "，RSI顯示超買狀態，短期可能回調"
                elif latest_rsi < 30:
                    suggestion += "，RSI顯示超賣狀態，可能反彈"
    except Exception:
        pass
   
    # 嘗試使用 LLM 生成更詳細的回應
    final_response = basic_info + "\n" + suggestion

    try:
        llm_prompt = (
            f"你是一位專業的股票分析師，請根據以下資訊給出投資建議。 使用繁體中文回答\n"
            f"請分析 {state['ticker']} 的股票資訊：\n"
            f"目前價格：{current_price}\n"
            f"漲跌幅：{price_change_pct}%\n"
            f"技術指標：{state['analysis_summary']}\n"
            f"基本面資訊：{fundamental_data}\n"
            f"請給出專業的投資建議，字數控制在150字內。"
        )
        llm_response = call_chatglm(llm_prompt)
        final_response += f"\n\n🤖 AI分析：\n {llm_response}"
    except Exception as e:
        print(f"LLM 回應生成失敗: {e}")
    return {**state, "response_text": final_response}

# -------------------------------
# 5. 狀態定義
# -------------------------------
class StockState(TypedDict):
    query: str
    market: str
    ticker: str
    intent: str
    df: Any
    current_price: float
    previous_close: float
    period_high: float
    period_low: float
    avg_volume: float
    data_points: int
    df_ind: Any
    analysis_summary: str
    fundamental_data: dict
    response_text: str
    error: str

# -------------------------------
# 6. 建構 LangGraph Graph
# -------------------------------
def build_stock_agent():
    workflow = StateGraph(StockState)

    workflow.add_node("query_function", query_understanding_node)
    workflow.add_node("fetch_function", stock_api_tool)
    workflow.add_node("analyze_function", financial_analyzer)
    workflow.add_node("respond", response_generator)

    workflow.set_entry_point("query_function")
    workflow.add_edge("query_function", "fetch_function")
    workflow.add_edge("fetch_function", "analyze_function")
    workflow.add_edge("analyze_function", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()

# -------------------------------
# 7. Agent 執行介面
# -------------------------------
class StockAgent:
    def __init__(self):
        self.graph = build_stock_agent()
    def call(self, ticker: str) -> str:
        """
        執行股票分析查詢
        Args:
            ticker: 股票代號（台股4位數字或美股字母代碼）
        Returns:
            分析結果字串
        """
        inputs = {"query": ticker}
        try:
            outputs = self.graph.invoke(inputs)
            return outputs["response_text"]
        except Exception as e:
            return f"Agent 執行失敗：{str(e)}"
    
    def get_stock_data(self, ticker: str):
        """
        獲取股票資料用於前端圖表顯示
        Args:
            ticker: 股票代號
        Returns:
            tuple: (df, market) - 股票資料DataFrame和市場類型
        """
        ticker = ticker.strip()
        
        # 判斷市場類型
        if ticker.isdigit() and len(ticker) == 4:
            market = "tw"
            df = fetch_tw_stock(ticker)
        elif ticker.replace('.', '').isalpha() and len(ticker) <= 5:
            market = "us"
            df = fetch_us_stock(ticker.upper())
        else:
            raise ValueError(f"無法識別股票代號 '{ticker}'")
        
        # 計算技術指標
        df_with_indicators = compute_technical_indicators(df)
        
        return df_with_indicators, market
# -------------------------------
# 8. 測試程式
# -------------------------------
# if __name__ == "__main__":
#     agent = StockAgent()
    
#     # 測試案例 - 現在只需要股票代號
#     test_cases = [
#         "AAPL",      # 美股蘋果
#         "2330",      # 台股台積電
#         "TSLA",      # 美股特斯拉
#         "2454"       # 台股聯發科
#     ]
    
#     for ticker in test_cases:
#         market_type = "台股" if ticker.isdigit() else "美股"
#         print(f"\n查詢：{ticker} ({market_type})")
#         print("="*50)
#         result = agent.call(ticker)
#         print(result)
#         print("="*50)