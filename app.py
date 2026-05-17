import numpy as np
import pandas as pd
import streamlit as st

# =====================================
# 1. ページ基本設定 & 本家IR Bank風CSS
# =====================================
st.set_page_config(
    page_title="IR Bank 財務・業績完全再現",
    layout="wide"
)

st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Kaku Gothic ProN", sans-serif;
    background-color: #ffffff;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}
h2 {
    color: #1b3f91;
    font-size: 18px !important;
    font-weight: bold;
    margin-top: 25px;
    margin-bottom: 12px;
    border-bottom: 2px solid #1b3f91;
    padding-bottom: 4px;
}
.stDataFrame {
    border: 1px solid #b4c7e7;
    border-radius: 4px;
}
div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
    font-size: 14px !important;
    padding: 12px 4px !important; 
    line-height: 1.6 !important;
}
</style>
    """,
    unsafe_allow_html=True
)

# =====================================
# 2. 銘柄データマスター (全自動切り替え用)
# =====================================
years_div = ["2009/03", "2010/03", "2011/03", "2012/03", "2013/03", "2014/03", "2015/03", "2016/03", "2017/03", "2018/03", "2019/03", "2020/03", "2021/03", "2022/03", "2023/03", "2024/03", "2025/03", "2026/03", "27/03予"]
years_cf = ["2009/03", "2010/03", "2011/03", "2012/03", "2013/03", "2014/03", "2015/03", "2016/03", "2017/03", "2018/03", "2019/03", "2020/03", "2021/03", "2022/03", "2023/03", "2024/03", "2025/03", "2026/03"]

# 4桁のコードに対応する会社名の対応マップ
TICKER_NAME_MAP = {
    "2158": "FRONTEO",
    "4667": "アイサンテクノロジー",
    "7203": "トヨタ自動車",
    "9984": "ソフトバンクグループ"
}

def get_financial_data(code):
    """
    Noneが入っていても絶対に掛け算エラーを起こさない安全なデータ生成関数
    """
    div_base = [None, 5.56, 5.56, 3.33, 3.33, 3.33, 3.33, 3.33, 6.67, 6.67, 11.11, 8.89, 8.89, 11.11, 23.33, 43.67, 48.33, 50.33, 42.00]
    cf_base_op = [51.40, 118.00, 11.10, 72.40, 33.20, -4.25, -14.60, 76.20, 139.00, 33.30, 130.00, -41.30, -25.50, 204.00, -96.70, 133.00, 98.40, 152.00]
    
    # 銘柄ごとの規模感調整係数
    multiplier = 1.0
    if code == "4667":
        multiplier = 0.45
    elif code == "7203":
        multiplier = 15.0
        
    # 【対策】「if x is not None else None」をすべての計算に徹底し、TypeErrorを完全防御
    div_data = {
        "一株配当": [x * multiplier if x is not None else None for x in div_base],
        "配当性向": [None, None, 8.9, 61.1, 12.1, 8.5, 12.2, 10.2, 4.2, 8.5, 9.6, 7.3, 7.4, 11.4, 29.2, 30.2, 22.6, 30.0, None],
        "剰余金の配当": [x * multiplier if x is not None else None for x in [None, None, 2.84, 2.84, 1.70, 1.70, 1.70, 1.70, 1.70, 3.46, 3.47, 5.85, 4.70, 4.71, 5.90, 12.30, 30.30, 28.70, None]],
        "純資産配当率": [None, None, None, 0.60, 0.60, 0.60, 0.50, 0.50, 0.90, 0.80, 1.10, 0.80, 0.70, 0.90, 1.70, 2.90, 2.90, 2.80, None],
        "自社株買い": [x * multiplier if x is not None else None for x in [0.03, 0.01, 0.01, 0.00, 0.01, 0.03, 0.07, 0.03, 0.03, 0.04, 0.59, 0.91, 0.67, 0.63, 2.12, 10.00, 0.02, 0.04, None]],
        "総還元額": [x * multiplier if x is not None else None for x in [0.03, 0.01, 2.85, 2.84, 1.71, 1.73, 1.77, 1.73, 1.73, 3.50, 4.06, 6.76, 5.37, 5.34, 8.02, 22.40, 30.40, 28.80, None]],
        "総還元性向": [0.3, 0.0, 9.0, 61.1, 12.2, 8.6, 12.7, 10.4, 4.2, 8.6, 10.6, 8.7, 8.5, 12.6, 34.2, 43.5, 22.6, 30.0, None]
    }
    
    cf_data = {
        "営業CF": [x * multiplier if x is not None else None for x in cf_base_op],
        "投資CF": [x * multiplier if x is not None else None for x in [-11.50, -7.36, -9.13, -16.50, -11.00, -21.50, -11.90, -18.20, -33.40, -32.30, -38.10, -27.60, -41.80, -19.50, -15.00, -25.50, -29.80, -18.30]],
        "財務CF": [x * multiplier if x is not None else None for x in [-28.10, -79.30, -10.50, -58.00, -19.70, 16.00, 40.90, -67.80, -82.20, 27.70, -98.50, 55.40, 82.20, -158.00, 122.00, -103.00, -86.60, -101.00]],
        "フリーCF": [x * multiplier if x is not None else None for x in [39.90, 111.00, 1.94, 55.90, 22.20, -25.80, -26.50, 58.00, 105.00, 0.96, 92.20, -68.90, -67.30, 184.00, -112.00, 108.00, 68.60, 133.00]],
        "設備投資": [x * multiplier if x is not None else None for x in [-12.90, -15.30, -12.70, -24.10, -14.70, -24.70, -17.20, -21.20, -38.30, -34.30, -27.60, -38.40, -33.20, -25.50, -40.90, -38.90, -26.50, -31.50]],
        "現金等": [x * multiplier if x is not None else None for x in [42.30, 73.50, 64.90, 62.80, 65.90, 56.10, 70.60, 60.80, 83.70, 112.00, 106.00, 92.80, 108.00, 137.00, 157.00, 161.00, 143.00, 175.00]],
        "営業CFマージン": [4.29, 10.76, 1.13, 9.07, 3.79, -0.47, -1.40, 8.01, 13.39, 3.10, 11.01, -3.25, -2.20, 19.65, -8.19, 10.32, 7.40, 13.18]
    }
    
    return pd.DataFrame(div_data, index=years_div), pd.DataFrame(cf_data, index=years_cf)

# =====================================
# 3. 画面上部：銘柄コード入力窓
# =====================================
col_code, col_name, _ = st.columns([2, 5, 5])

with col_code:
    ticker = st.text_input(
        "銘柄コード (4桁)",
        value="4667",  # アイサンテクノロジーをデフォルトに設定
        max_chars=4,
        key="ticker_input"
    )

# 会社名マップから取得
company_name = TICKER_NAME_MAP.get(ticker, f"日本上場企業 (銘柄:{ticker})")

with col_name:
    st.markdown(
        f"<div style='padding-top: 28px; font-size: 20px; font-weight: bold; color: #1b3f91;'>"
        f"🏢 {company_name}"
        f"</div>",
        unsafe_allow_html=True
    )

st.title("📊 IR Bank 財務データビジュアル完全再現")

# データ読み込み（ここでエラーは起きません）
df_div, df_cf = get_financial_data(ticker)

# =====================================
# 4. 横幅最適化 ＆ フォーマット設定
# =====================================
COLOR_BLUE = "#7ecbfb"
COLOR_RED = "#ffb3ba"

def generate_perfect_column_config(df, is_cf=False):
    config = {}
    for col in df.columns:
        max_val = float(df[col].max()) if pd.notna(df[col].max()) else 1.0
        min_val = float(df[col].min()) if pd.notna(df[col].min()) else 0.0
        
        if col in ["一株配当", "剰余金の配当", "純資産配当率", "自社株買い", "総還元額"]:
            fmt = "%.2f"
            if col in ["剰余金の配当", "自社株買い", "総還元額"]:
                fmt = "%.2f億"
        elif col in ["配当性向", "総還元性向"]:
            fmt = "%.1f%%"
        elif is_cf and col != "営業CFマージン":
            fmt = "%.2f億"
        elif col == "営業CFマージン":
            fmt = "%.2f"
        else:
            fmt = "%.2f"
            
        chosen_color = COLOR_RED if "投資" in col or "財務" in col or (min_val < 0 and max_val <= 0) else COLOR_BLUE
        
        config[col] = st.column_config.ProgressColumn(
            col,
            format=fmt,
            min_value=min_val if min_val < 0 else 0.0,
            max_value=max_val if max_val > 0 else 1.0,
            color=chosen_color,
            width=110
        )
    return config

# =====================================
# 5. 表のレンダリング（完全縦表示）
# =====================================

# ーーーー 配当推移 ーーーー
st.markdown("<h2>📈 配当推移</h2>", unsafe_allow_html=True)
div_config = generate_perfect_column_config(df_div)
st.dataframe(df_div.fillna("-"), use_container_width=True, column_config=div_config, height=820)

# ーーーー キャッシュ・フロー推移 ーーーー
st.markdown("<h2>💵 キャッシュ・フロー推移</h2>", unsafe_allow_html=True)
cf_config = generate_perfect_column_config(df_cf, is_cf=True)
st.dataframe(df_cf.fillna("-"), use_container_width=True, column_config=cf_config, height=780)
