import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
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
# 2. バックアップ用固定データ（万が一の通信エラー時に表示）
# =====================================
years_backup = ["2009/03", "2010/03", "2011/03", "2012/03", "2013/03", "2014/03", "2015/03", "2016/03", "2017/03", "2018/03", "2019/03", "2020/03", "2021/03", "2022/03", "2023/03", "2024/03", "2025/03", "2026/03", "27/03予"]
div_backup_raw = {
    "一株配当": [None, 5.56, 5.56, 3.33, 3.33, 3.33, 3.33, 3.33, 6.67, 6.67, 11.11, 8.89, 8.89, 11.11, 23.33, 43.67, 48.33, 50.33, 42.00],
    "配当性向": [None, None, 8.9, 61.1, 12.1, 8.5, 12.2, 10.2, 4.2, 8.5, 9.6, 7.3, 7.4, 11.4, 29.2, 30.2, 22.6, 30.0, None],
    "剰余金の配当": [None, None, 2.84, 2.84, 1.70, 1.70, 1.70, 1.70, 1.70, 3.46, 3.47, 5.85, 4.70, 4.71, 5.90, 12.30, 30.30, 28.70, None],
    "純資産配当率": [None, None, None, 0.60, 0.60, 0.60, 0.50, 0.50, 0.90, 0.80, 1.10, 0.80, 0.70, 0.90, 1.70, 2.90, 2.90, 2.80, None],
    "自社株買い": [0.03, 0.01, 0.01, 0.00, 0.01, 0.03, 0.07, 0.03, 0.03, 0.04, 0.59, 0.91, 0.67, 0.63, 2.12, 10.00, 0.02, 0.04, None],
    "総還元額": [0.03, 0.01, 2.85, 2.84, 1.71, 1.73, 1.77, 1.73, 1.73, 3.50, 4.06, 6.76, 5.37, 5.34, 8.02, 22.40, 30.40, 28.80, None],
    "総還元性向": [0.3, 0.0, 9.0, 61.1, 12.2, 8.6, 12.7, 10.4, 4.2, 8.6, 10.6, 8.7, 8.5, 12.6, 34.2, 43.5, 22.6, 30.0, None]
}
df_div_backup = pd.DataFrame(div_backup_raw, index=years_backup)

cf_backup_raw = {
    "営業CF": [51.40, 118.00, 11.10, 72.40, 33.20, -4.25, -14.60, 76.20, 139.00, 33.30, 130.00, -41.30, -25.50, 204.00, -96.70, 133.00, 98.40, 152.00],
    "投資CF": [-11.50, -7.36, -9.13, -16.50, -11.00, -21.50, -11.90, -18.20, -33.40, -32.30, -38.10, -27.60, -41.80, -19.50, -15.00, -25.50, -29.80, -18.30],
    "財務CF": [-28.10, -79.30, -10.50, -58.00, -19.70, 16.00, 40.90, -67.80, -82.20, 27.70, -98.50, 55.40, 82.20, -158.00, 122.00, -103.00, -86.60, -101.00],
    "フリーCF": [39.90, 111.00, 1.94, 55.90, 22.20, -25.80, -26.50, 58.00, 105.00, 0.96, 92.20, -68.90, -67.30, 184.00, -112.00, 108.00, 68.60, 133.00],
    "設備投資": [-12.90, -15.30, -12.70, -24.10, -14.70, -24.70, -17.20, -21.20, -38.30, -34.30, -27.60, -38.40, -33.20, -25.50, -40.90, -38.90, -26.50, -31.50],
    "現金等": [42.30, 73.50, 64.90, 62.80, 65.90, 56.10, 70.60, 60.80, 83.70, 112.00, 106.00, 92.80, 108.00, 137.00, 157.00, 161.00, 143.00, 175.00],
    "営業CFマージン": [4.29, 10.76, 1.13, 9.07, 3.79, -0.47, -1.40, 8.01, 13.39, 3.10, 11.01, -3.25, -2.20, 19.65, -8.19, 10.32, 7.40, 13.18]
}
df_cf_backup = pd.DataFrame(cf_backup_raw, index=years_backup[:-1]) # 予想を除く

# =====================================
# 3. 安全装置付き・データ自動取得関数
# =====================================
@st.cache_data(ttl=600)  # 通信負荷軽減のため10分間キャッシュ
def fetch_irbank_data(code):
    # 人間がブラウザ（WindowsのChrome）でアクセスしているように見せかける偽装ヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    div_url = f"https://irbank.net/{code}/dividend"
    cf_url = f"https://irbank.net/{code}/cf"
    
    company_name = None
    df_div_raw = None
    df_cf_raw = None

    # 【重要】すべての処理を個別にtry-exceptで囲み、どこが失敗しても絶対にクラッシュさせない
    try:
        response_div = requests.get(div_url, headers=headers, timeout=10)
        if response_div.status_code == 200:
            soup_div = BeautifulSoup(response_div.text, "lxml")
            title_text = soup_div.title.text if soup_div.title else ""
            company_name = title_text.replace(str(code), "").replace("配当", "").replace("業績", "").strip()
            
            # 内部処理エラー（FileNotFoundError）を完全に防ぐセーフティ
            tables_div = pd.read_html(response_div.text)
            if tables_div:
                df_div_raw = tables_div[0]
    except Exception as e:
        pass # エラーが発生しても何もしない（Noneを返す）

    try:
        response_cf = requests.get(cf_url, headers=headers, timeout=10)
        if response_cf.status_code == 200:
            tables_cf = pd.read_html(response_cf.text)
            if tables_cf:
                df_cf_raw = tables_cf[0]
    except Exception as e:
        pass

    return company_name, df_div_raw, df_cf_raw

# =====================================
# 4. データの成形用関数
# =====================================
def preprocess_dataframe(df, target_cols):
    if df is None:
        return None
    try:
        df = df.set_index(df.columns[0])
        df = df.T
        df.index.name = "年度"
        
        available_cols = [c for c in target_cols if c in df.columns]
        df = df[available_cols]
        for col in target_cols:
            if col not in df.columns:
                df[col] = np.nan
                
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace("円", "").str.replace("億", "").str.replace("%", "").str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except:
        return None

# =====================================
# 5. 画面上部：銘柄コード4桁 入力エリア
# =====================================
col_code, col_name, _ = st.columns([2, 5, 5])

with col_code:
    ticker = st.text_input(
        "銘柄コード (4桁)",
        value="2158",
        max_chars=4,
        key="ticker_input"
    )

# データの自動取得を実行
company_name, raw_div, raw_cf = fetch_irbank_data(ticker)

# 表用データの最終割り当て
div_cols = ["一株配当", "配当性向", "剰余金の配当", "純資産配当率", "自社株買い", "総還元額", "総還元性向"]
cf_cols = ["営業CF", "投資CF", "財務CF", "フリーCF", "設備投資", "現金等", "営業CFマージン"]

df_div = preprocess_dataframe(raw_div, div_cols)
df_cf = preprocess_dataframe(raw_cf, cf_cols)

# 【バックアップ連動】取得に失敗した場合は、エラーを出さずに初期データ（FRONTEO）で安全に埋める
is_backup_mode = False
if df_div is None or df_cf is None:
    df_div = df_div_backup
    df_cf = df_cf_backup
    is_backup_mode = True

with col_name:
    if not is_backup_mode and company_name:
        st.markdown(f"<div style='padding-top: 28px; font-size: 20px; font-weight: bold; color: #1b3f91;'>🏢 {company_name}</div>", unsafe_allow_html=True)
    elif ticker == "2158":
        st.markdown("<div style='padding-top: 28px; font-size: 20px; font-weight: bold; color: #1b3f91;'>🏢 FRONTEO (固定表示)</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='padding-top: 28px; font-size: 14px; font-weight: bold; color: #cc0000;'>⚠️ 通信ブロック中またはデータ無効（サンプルを表示中）</div>", unsafe_allow_html=True)

st.title("📊 IR Bank 財務データビジュアル完全再現")

# =====================================
# 6. 横幅最適化 ＆ フォーマット設定
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
            col, format=fmt, min_value=min_val if min_val < 0 else 0.0, max_value=max_val if max_val > 0 else 1.0, color=chosen_color, width=110
        )
    return config

# =====================================
# 7. 表のレンダリング（スクロールなし仕様）
# =====================================

# ーーーー 配当推移 ーーーー
st.markdown("<h2>📈 配当推移</h2>", unsafe_allow_html=True)
div_config = generate_perfect_column_config(df_div)
st.dataframe(df_div.fillna("-"), use_container_width=True, column_config=div_config, height=820)

# ーーーー キャッシュ・フロー推移 ーーーー
st.markdown("<h2>💵 キャッシュ・フロー推移</h2>", unsafe_allow_html=True)
cf_config = generate_perfect_column_config(df_cf, is_cf=True)
st.dataframe(df_cf.fillna("-"), use_container_width=True, column_config=cf_config, height=780)
