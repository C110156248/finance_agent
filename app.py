# app.py

import streamlit as st
import matplotlib.pyplot as plt
from agent import StockAgent

st.set_page_config(page_title="AI 股票查詢系統", layout="wide")
st.title("📈 AI股票查詢")

# 初始化 Agent
@st.cache_resource
def get_agent():
    return StockAgent()

agent = get_agent()

# 使用者輸入區
with st.form(key="query_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        user_query = st.text_input(
            "請輸入股票代號：", 
            placeholder="台股請輸入4位數字（如：2330），美股請輸入代碼（如：AAPL）",
            label_visibility="collapsed",
            help="支援台股4位數字代碼和美股字母代碼"
        )
    with col2:
        submit = st.form_submit_button("🔍 查詢", use_container_width=True)

if submit and user_query:
    ticker = user_query.strip()
    
    # 簡單驗證輸入格式
    if not ticker:
        st.error("請輸入股票代號")
    elif len(ticker) > 7:
        st.error("股票代號格式不正確")
    else:
        with st.spinner("🤖 AI 代理人分析中..."):
            try:
                # 使用 AI Agent 生成分析報告
                response_text = agent.call(ticker)
                # 獲取股票資料用於圖表顯示
                df_ind, market = agent.get_stock_data(ticker)
                # 顯示 AI 分析結果
                st.subheader("🤖 AI 分析報告")
                st.markdown(response_text)
                # 顯示圖表
                if not df_ind.empty:
                    st.subheader("📊 技術分析圖表")
                    
                    # 創建兩欄布局
                    col1, col2 ,col3= st.columns(3)
                    
                    # 左邊：股價走勢與移動平均線
                    with col1:
                        fig1, ax1 = plt.subplots(figsize=(10, 6))
                        
                        # 繪製股價和移動平均線
                        ax1.plot(df_ind.index, df_ind["Close"], 
                                label="Closing Price", linewidth=2, color='#1f77b4')
                        
                        if "MA_5" in df_ind.columns:
                            ax1.plot(df_ind.index, df_ind["MA_5"], 
                                    label="MA5", linestyle="--", alpha=0.8, color='orange')
                        
                        if "MA_20" in df_ind.columns:
                            ax1.plot(df_ind.index, df_ind["MA_20"], 
                                    label="MA20", linestyle="--", alpha=0.8, color='green')
                        
                        if "MA_60" in df_ind.columns:
                            ax1.plot(df_ind.index, df_ind["MA_60"], 
                                    label="MA60", linestyle="--", alpha=0.8, color='red')
                        
                        ax1.set_title(f"{ticker}", 
                                     fontsize=14, fontweight='bold')
                        ax1.set_xlabel("Date")
                        ax1.set_ylabel("Price")
                        ax1.legend()
                        ax1.grid(True, alpha=0.3)
                        
                        # 自動調整日期標籤角度
                        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
                        
                        st.pyplot(fig1)
                        st.caption("股價走勢與移動平均線")
                    
                    # 右邊：RSI 指標
                    with col2:
                        if "RSI_14" in df_ind.columns and not df_ind["RSI_14"].isna().all():
                            fig2, ax2 = plt.subplots(figsize=(10, 6))
                            
                            ax2.plot(df_ind.index, df_ind["RSI_14"], 
                                    label="RSI(14)", linewidth=2, color='purple')
                            
                            # 超買超賣線
                            ax2.axhline(70, color="red", linestyle="--", alpha=0.7, label="Overbought Line(70)")
                            ax2.axhline(30, color="green", linestyle="--", alpha=0.7, label="Oversold Line(30)")
                            
                            ax2.set_title("RSI", fontsize=14, fontweight='bold')
                            ax2.set_xlabel("Date")
                            ax2.set_ylabel("RSI")
                            ax2.set_ylim(0, 100)
                            ax2.legend()
                            ax2.grid(True, alpha=0.3)
                            
                            # 自動調整日期標籤角度
                            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                            
                            st.pyplot(fig2)
                            st.caption("RSI 技術指標")
                        else:
                            st.info("RSI 指標資料不足，需要更多歷史資料計算")
                    with col3:
                        # 額外的布林通道圖表
                        if all(col in df_ind.columns for col in ["BB_Upper", "BB_Middle", "BB_Lower"]):                            
                            fig3, ax3 = plt.subplots(figsize=(12, 6))
                            # 繪製布林通道
                            ax3.plot(df_ind.index, df_ind["Close"], 
                                    label="Closing Price", linewidth=2, color='blue')
                            ax3.plot(df_ind.index, df_ind["BB_Upper"], 
                                    label="Upper Band", linestyle="--", alpha=0.8, color='red')
                            ax3.plot(df_ind.index, df_ind["BB_Middle"], 
                                    label="Middle Band(MA20)", linestyle="-", alpha=0.8, color='orange')
                            ax3.plot(df_ind.index, df_ind["BB_Lower"], 
                                    label="Lower Band", linestyle="--", alpha=0.8, color='green')
                            # 填充布林通道
                            ax3.fill_between(df_ind.index, df_ind["BB_Upper"], df_ind["BB_Lower"], 
                                            alpha=0.1, color='gray')
                            ax3.set_title("Bollinger Bands", fontsize=14, fontweight='bold')
                            ax3.set_xlabel("Day")
                            ax3.set_ylabel("Price")
                            ax3.legend()
                            ax3.grid(True, alpha=0.3)

                            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

                            st.pyplot(fig3)
                            st.caption("布林通道（20日移動平均 ± 2標準差）")
                
                # 顯示資料統計
                if not df_ind.empty:
                    st.subheader("📊 基本統計資訊")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("目前價格", f"{df_ind['Close'].iloc[-1]:.2f}")
                    
                    with col2:
                        price_change = df_ind['Close'].iloc[-1] - df_ind['Close'].iloc[-2] if len(df_ind) > 1 else 0
                        st.metric("日漲跌", f"{price_change:.2f}", f"{price_change:.2f}")
                    
                    with col3:
                        period_high = df_ind['Close'].max()
                        st.metric("期間最高", f"{period_high:.2f}")
                    
                    with col4:
                        period_low = df_ind['Close'].min()
                        st.metric("期間最低", f"{period_low:.2f}")

            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                st.info("請檢查股票代號是否正確：\n- 台股：4位數字（例如：2330）\n- 美股：字母代碼（例如：AAPL）")

# 側邊欄說明
with st.sidebar:
    st.header("📖 使用說明")
    st.markdown("""
    ### 🔍 如何使用
    1. 輸入股票代號
    2. 點擊查詢按鈕
    3. 查看 AI 分析報告和圖表
    
    ### 📊 支援的市場
    - **台股**：4位數字代碼（如 2330）
    - **美股**：字母代碼（如 AAPL）
    """)
    


# 頁尾
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 本系統使用 ChatGLM3-6B 模型</p>
    <p>📊 資料僅供參考，投資有風險，請謹慎決策</p>
</div>
""", unsafe_allow_html=True)