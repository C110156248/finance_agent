import pandas as pd
import yfinance as yf
import numpy as np
def convert_tw_date(date_str):
    """
    將台灣民國年日期轉換為西元年
    例：111/01/01 -> 2022-01-01
    """
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            roc_year = int(parts[0])
            western_year = roc_year + 1911  # 民國年轉西元年
            month = parts[1].zfill(2)
            day = parts[2].zfill(2)
            return f"{western_year}-{month}-{day}"
        return date_str
    except (ValueError, IndexError):
        return date_str

def fetch_us_stock(ticker: str, period: str = "2mo", interval: str = "1d") -> pd.DataFrame:
    """
    使用 yfinance 抓取美股歷史資料（近兩個月、日線）。
    回傳 DataFrame，包含開高低收、成交量。
    """
    stock = yf.Ticker(ticker)
    
    # info = stock.info

    df = stock.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"無法取得 {ticker} 的美股資料。")
    df.reset_index(inplace=True)
    return df#,info

def fetch_tw_stock(ticker: str) -> pd.DataFrame:
    """
    使用 yfinance 抓取台股歷史資料（近兩個月、日線）
    """
    tw_ticker = f"{ticker}.TW"
    try:
        stock = yf.Ticker(tw_ticker)
        df = stock.history(period="2mo", interval="1d")
        
        if df.empty:
            raise ValueError(f"無法取得 {ticker} 的台股資料")
        
        # 重設索引，將日期變成一般欄位
        df.reset_index(inplace=True)
        
        # 統一欄位名稱格式
        df = df.rename(columns={
            'Date': 'Date',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        # 選擇需要的欄位並排序
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].sort_values("Date").reset_index(drop=True)
        return df
    except Exception as e:
        raise ValueError(f"抓取台股 {ticker} 資料時發生錯誤：{str(e)}")

def get_fundamental_data(ticker: str, market: str):
    """
    獲取基本面資料
    """
    fundamental_data = {}
    
    try:
        if market == "us":
            # 使用 yfinance 獲取美股基本面資料
            stock = yf.Ticker(ticker)
            info = stock.info
            
            fundamental_data = {
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
                'profit_margin': info.get('profitMargins', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'book_value': info.get('bookValue', 'N/A'),
                'price_to_book': info.get('priceToBook', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A')
            }
        else:
            # 台股基本面資料（簡化版本，實際應用可串接更詳細的API）
            fundamental_data = {
                'pe_ratio': 'N/A',
                'market_cap': 'N/A',
                'dividend_yield': 'N/A',
                'revenue_growth': 'N/A',
                'profit_margin': 'N/A',
                'debt_to_equity': 'N/A',
                'book_value': 'N/A',
                'price_to_book': 'N/A',
                'sector': '台股資料',
                'industry': '需要進一步API串接'
            }
            
    except Exception as e:
        print(f"基本面資料獲取失敗: {e}")
        fundamental_data = {
            'pe_ratio': 'N/A',
            'market_cap': 'N/A',
            'dividend_yield': 'N/A',
            'revenue_growth': 'N/A',
            'profit_margin': 'N/A',
            'debt_to_equity': 'N/A',
            'book_value': 'N/A',
            'price_to_book': 'N/A',
            'sector': 'N/A',
            'industry': 'N/A'
        }
    
    return fundamental_data

def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算簡單的技術指標：移動平均（MA）、相對強弱指標（RSI）等。
    統一使用 Close 欄位處理美股和台股
    """
    df = df.copy()
    
    # 確保有 Close 欄位
    if "Close" not in df.columns:
        raise ValueError("資料中缺少 Close 欄位")
    
    price = df["Close"]
    
    # 檢查資料是否足夠
    if len(price) < 5:
        print("警告：資料不足 5 筆，技術指標可能不準確")
    
    # 移動平均（使用 min_periods 避免 NaN）
    df["MA_5"] = price.rolling(window=5, min_periods=1).mean()
    df["MA_20"] = price.rolling(window=20, min_periods=1).mean()
    df["MA_60"] = price.rolling(window=60, min_periods=1).mean()  # 新增60日均線
    
    # RSI 計算
    if len(price) >= 14:
        delta = price.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-10)  # 避免除零
        df["RSI_14"] = 100 - (100 / (1 + rs))
    else:
        df["RSI_14"] = np.nan
    
    # 新增布林通道（Bollinger Bands）
    if len(price) >= 20:
        df["BB_Middle"] = price.rolling(window=20, min_periods=1).mean()
        bb_std = price.rolling(window=20, min_periods=1).std()
        df["BB_Upper"] = df["BB_Middle"] + (bb_std * 2)
        df["BB_Lower"] = df["BB_Middle"] - (bb_std * 2)
    else:
        df["BB_Middle"] = df["BB_Upper"] = df["BB_Lower"] = np.nan
    
    return df

def generate_analysis_summary(df: pd.DataFrame, intent: str, fundamental_data: dict) -> str:
    """
    根據資料和意圖生成分析摘要
    """
    try:
        latest_data = df.iloc[-1]
        current_price = latest_data["Close"]
        
        # 技術分析摘要
        tech_summary = []
        
        # 移動平均分析
        if pd.notna(latest_data.get("MA_5")) and pd.notna(latest_data.get("MA_20")):
            ma5 = latest_data["MA_5"]
            ma20 = latest_data["MA_20"]
            if current_price > ma5 > ma20:
                tech_summary.append("短期趨勢向上")
            elif current_price < ma5 < ma20:
                tech_summary.append("短期趨勢向下")
            else:
                tech_summary.append("趨勢震盪")
        
        # RSI 分析
        if pd.notna(latest_data.get("RSI_14")):
            rsi = latest_data["RSI_14"]
            if rsi > 70:
                tech_summary.append("RSI超買")
            elif rsi < 30:
                tech_summary.append("RSI超賣")
            else:
                tech_summary.append(f"RSI中性({rsi:.1f})")
        
        # 布林通道分析
        if pd.notna(latest_data.get("BB_Upper")) and pd.notna(latest_data.get("BB_Lower")):
            bb_upper = latest_data["BB_Upper"]
            bb_lower = latest_data["BB_Lower"]
            if current_price > bb_upper:
                tech_summary.append("突破布林上軌")
            elif current_price < bb_lower:
                tech_summary.append("跌破布林下軌")
        
        # 根據意圖組合摘要
        if intent == "technical":
            return "技術面：" + "、".join(tech_summary) if tech_summary else "技術指標中性"
        elif intent == "fundamental":
            fund_items = []
            if fundamental_data.get('pe_ratio') != 'N/A':
                fund_items.append(f"本益比{fundamental_data['pe_ratio']}")
            if fundamental_data.get('sector') != 'N/A':
                fund_items.append(f"屬於{fundamental_data['sector']}產業")
            return "基本面：" + "、".join(fund_items) if fund_items else "基本面資料有限"
        else:
            # 基本分析
            price_trend = "上漲" if len(df) > 1 and current_price > df["Close"].iloc[-2] else "下跌"
            return f"股價呈{price_trend}趨勢，" + "、".join(tech_summary[:2]) if tech_summary else f"股價呈{price_trend}趨勢"
            
    except Exception as e:
        return f"分析摘要生成失敗：{str(e)}"