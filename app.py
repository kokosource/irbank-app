import re
from io import StringIO
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

# =====================================
# 基本設定
# =====================================
st.set_page_config(
    page_title="IR Bank 推移データ",
    layout="wide"
)

st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.main { background-color: #ffffff; }
h1 { color: #1b3f91; font-weight: 700; }
h2 { color: #1b3f91; font-size: 22px; margin-top: 30px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }
</style>
    """,
    unsafe_allow_html=True
)

st.title("📊 IR Bank 財務推移")
stock_code = st.text_input("銘柄コードを入力", "7203")

# =====================================
# IR Bank 専用スクレイピング関数
# =====================================
@st.cache_data(ttl=3600)
def parse_irbank_table(code, target_keywords):
    """
    指定されたキーワード（'配当' や '営業活動'）が含まれるテーブルを
    BeautifulSoupでパースして正確に二次元配列（DataFrame）にする関数
    """
    url = f"https://irbank.net/{code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html5lib")
        tables = soup.find_all("table")
        
        for table in tables:
            # テーブル全体のテキストを確認してキーワードが含まれるか判定
            table_text = table.get_text()
            if not all(word in table_text for word in target_keywords):
                continue
                
            # --- ここからテーブルデータの正確な抽出 ---
            rows_data = []
            
            # 1. ヘッダー（年度）の取得
            thead = table.find("thead")
            header_row = []
            if thead:
                th_elements = thead.find_all("th")
                header_row = [th.get_text(strip=True) for th in th_elements]
            
            # 2. ボディ（項目名と数値）の取得
            tbody = table.find("tbody")
            if tbody:
                for tr in tbody.find_all("tr"):
                    row_cells = []
                    # 項目名 (th または td)
                    th_item = tr.find("th")
                    if th_item:
                        row_cells.append(th_item.get_text(strip=True))
                    
                    # 各年度の数値 (td)
                    for td in tr.find_all("td"):
                        row_cells.append(td.get_text(strip=True))
                    
                    if row_cells:
                        rows_data.append(row_cells)
            
            # theadがなくて一続きのテーブルの場合のフォールバック
            if not header_row and rows_data:
                # 最初の行をヘッダーと仮定
                header_row = rows_data.pop(0)
            
            if rows_data and header_row:
                # カラム数を合わせる調整
                max_cols = max(len(header_row), max(len(r) for r in rows_data))
                if len(header_row) < max_cols:
                    header_row += [""] * (max_cols - len(header_row))
                
                cleaned_rows = []
                for r in rows_data:
                    if len(r) < max_cols:
                        r += [""] * (max_cols - len(r))
                    cleaned_rows.append(r[:max_cols])
                
                # DataFrame化
                df = pd.DataFrame(cleaned_rows, columns=header_row[:max_cols])
                return df
                
        return None
    except Exception as e:
        st.error(f"エラー発生: {e}")
        return None

# =====================================
# メイン表示処理
# =====================================
if stock_code:
    
    # -------------------------------------
    # 1. 配当推移
    # -------------------------------------
    st.header("🔗 配当推移")
    # 「配当」という言葉が入っているテーブルを抽出
    dividend_df = parse_irbank_table(stock_code, ["配当"])
    
    if dividend_df is not None:
        # 表の見栄えをよくするため、最初の列をインデックスに設定
        first_col = dividend_df.columns[0]
        dividend_df = dividend_df.set_index(first_col)
        
        # IR Bankと同じ横長の表を表示
        st.dataframe(dividend_df, use_container_width=True)
    else:
        st.warning("配当データテーブルの取得に失敗したか、データがありません。")

    # -------------------------------------
    # 2. キャッシュ・フロー推移
    # -------------------------------------
    st.header("🔗 キャッシュ・フロー推移")
    # 「営業活動」と「投資活動」という言葉が入っているテーブルを抽出
    cf_df = parse_irbank_table(stock_code, ["営業活動", "投資活動"])
    
    if cf_df is not None:
        # 最初の列をインデックスに設定
        first_col = cf_df.columns[0]
        cf_df = cf_df.set_index(first_col)
        
        # IR Bankと同じ横長の表を表示
        st.dataframe(cf_df, use_container_width=True)
    else:
        st.warning("キャッシュ・フローデータテーブルの取得に失敗したか、データがありません。")
