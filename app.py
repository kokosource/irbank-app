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
# 2. 【核心】本家IR Bankからデータを自動取得する関数
# =====================================
@st.cache_data(ttl=3600)  # 1時間キャッシュして、何度も読み込んで本家に負荷をかけるのを防ぎます
def fetch_irbank_data(code):
    """
    入力された4桁のコードを使って、本家IR Bankから
    企業名・配当データ・CFデータを自動取得する関数
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # ーーーー ① 企業名と配当データの取得 ーーーー
    div_url = f"https://irbank.net/{code}/dividend"
    try:
        response_div = requests.get(div_url, headers=headers, timeout=10)
        if response_div.status_code != 200:
            return None, None, None
    except:
        return None, None, None

    soup_div = BeautifulSoup(response_div.text, "lxml")
    
    # ページタイトルから企業名を抜き出す (例: 「2158 FRONTEO 配当」 -> 「FRONTEO」)
    title_text = soup_div.title.text if soup_div.title else ""
    company_name = title_text.replace(str(code), "").replace("配当", "").replace("業績", "").strip()
    if not company_name:
        company_name = "企業名取得エラー"

    # 配当テーブルを読み込む
    tables_div = pd.read_html(response_div.text)
    df_div_raw = tables_div[0] if tables_div else None
    
    # ーーーー ② キャッシュ・フローデータの取得 ーーーー
    cf_url = f"https://irbank.net/{code}/cf"
    try:
        response_cf = requests.get(cf_url, headers=headers, timeout=10)
        tables_cf = pd.read_html(response_cf.text) if response_cf.status_code == 200 else []
        df_cf_raw = tables_cf[0] if tables_cf else None
    except:
        df_cf_raw = None

    return company_name, df_div_raw, df_cf_raw

# =====================================
# 3. データの整形（本家の表示形式に整える）
# =====================================
def preprocess_dataframe(df, target_cols, index_name="年度"):
    if df is None:
        return None
    
    # 本家のテーブル構造に合わせて縦横を整える
    df = df.set_index(df.columns[0])
    df = df.T
    df.index.name = index_name
    
    # 必要な列だけに絞り込み、存在しない列は空で作成
    available_cols = [c for c in target_cols if c in df.columns]
    df = df[available_cols]
    for col in target_cols:
        if col not in df.columns:
            df[col] = np.nan
            
    # 文字列データを数値に変換（「億」や「%」を剥ぎ取って純粋な数字にする）
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace("円", "").str.replace("億", "").str.replace("%", "").str.replace(",", "")
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    return df

# =====================================
# 4. 画面上部：銘柄コード4桁 入力エリア
# =====================================
col_code, col_name, _ = st.columns([2, 5, 5])

with col_code:
    # ユーザーが自由に打ち込める4桁ボックス
    ticker = st.text_input(
        "銘柄コード (4桁)",
        value="2158", # 初期値はFRONTEO
        max_chars=4,
        key="ticker_input"
    )

# データの自動取得を実行
company_name, raw_div, raw_cf = fetch_irbank_data(ticker)

with col_name:
    # 【新設】データが取れたら、右側に自動で企業名を表示する
    if company_name and raw_div is not None:
        st.markdown(
            f"<div style='padding-top: 28px; font-size: 20px; font-weight: bold; color: #1b3f91;'>"
            f"🏢 {company_name}"
            f"</div>",
            unsafe_allow_html=True
        )
    elif ticker:
        st.markdown(
            f"<div style='padding-top: 28px; font-size: 15px; font-weight: bold; color: #cc0000;'>"
            f"⚠️ 該当データがありません"
            f"</div>",
            unsafe_allow_html=True
        )

st.title("📊 IR Bank 財務データビジュアル完全再現")

# =====================================
# 5. 横幅最適化 ＆ フォーマット設定
# =====================================
COLOR_BLUE = "#7ecbfb"
COLOR_RED = "#ffb3ba"

def generate_perfect_column_config(df, is_cf=False):
    config = {}
    if df is None:
        return config
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
# 6. 表のレンダリング
# =====================================
div_cols = ["一株配当", "配当性向", "剰余金の配当", "純資産配当率", "自社株買い", "総還元額", "総還元性向"]
cf_cols = ["営業CF", "投資CF", "財務CF", "フリーCF", "設備投資", "現金等", "営業CFマージン"]

df_div = preprocess_dataframe(raw_div, div_cols)
df_cf = preprocess_dataframe(raw_cf, cf_cols)

if df_div is not None:
    # ーーーー 配当推移 ーーーー
    st.markdown("<h2>📈 配当推移</h2>", unsafe_allow_html=True)
    div_config = generate_perfect_column_config(df_div)
    st.dataframe(df_div.fillna("-"), use_container_width=True, column_config=div_config, height=820)

if df_cf is not None:
    # ーーーー キャッシュ・フロー推移 ーーーー
    st.markdown("<h2>💵 キャッシュ・フロー推移</h2>", unsafe_allow_html=True)
    cf_config = generate_perfect_column_config(df_cf, is_cf=True)
    st.dataframe(df_cf.fillna("-"), use_container_width=True, column_config=cf_config, height=780)
