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
    page_title="IR Bank 財務データ再現",
    layout="wide"
)

st.title("📊 IR Bank 財務データ再現（エラー検証版）")
stock_code = st.text_input("銘柄コード（例: 7203）", "7203")

# =====================================
# スクレイピングエンジン（検証機能付き）
# =====================================
@st.cache_data(ttl=3600)
def fetch_and_parse_irbank(code):
    url = f"https://irbank.net/{code}"
    
    # 最高精度のブラウザ偽装ヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://irbank.net/",
        "Connection": "keep-alive"
    }
    
    target_rows = [
        "1株配当", "1株配当(調整後)", "配当性向", "DOE",
        "営業活動によるキャッシュ・フロー", 
        "投資活動によるキャッシュ・フロー", 
        "財務活動によるキャッシュ・フロー", 
        "現金及び現金同等物期末残高"
    ]
    
    extracted_data = {}
    headers_list = []

    try:
        # セッションを維持してアクセス
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        
        # 【重要】アクセス状況を画面に報告する
        if response.status_code == 403:
            st.error("❌ IR Bankからアクセスが拒否されました (403 Forbidden)。サイトのスクレイピング対策にブロックされています。ローカルPC環境で実行するか、時間を空けてください。")
            return None, None
        elif response.status_code != 200:
            st.error(f"❌ サイトに接続できませんでした。ステータスコード: {response.status_code}")
            return None, None
            
        soup = BeautifulSoup(response.text, "html5lib")
        tables = soup.find_all("table")
        
        if not tables:
            st.warning("⚠️ ページは開けましたが、テーブル（表）のデータが空っぽです（HTML構造の遮断）。")
            return None, None
        
        for table in tables:
            trs = table.find_all("tr")
            if not trs:
                continue
                
            current_table_headers = []
            thead = table.find("thead")
            if thead:
                current_table_headers = [th.get_text(strip=True) for th in thead.find_all("th")]
            else:
                first_tr = trs[0]
                current_table_headers = [th.get_text(strip=True) for th in first_tr.find_all(["th", "td"])]
            
            for tr in trs:
                th_item = tr.find(["th", "td"])
                if not th_item:
                    continue
                
                item_name = re.sub(r'\s+', '', th_item.get_text(strip=True))
                
                matched_target = None
                for target in target_rows:
                    if target in item_name:
                        matched_target = target
                        break
                        
                if matched_target:
                    tds = tr.find_all("td")
                    values = [td.get_text(strip=True) for td in tds]
                    
                    if not values:
                        continue
                        
                    if len(current_table_headers) > len(headers_list):
                        headers_list = current_table_headers
                        
                    if matched_target not in extracted_data:
                        extracted_data[matched_target] = values

        if extracted_data:
            max_len = max(len(v) for v in extracted_data.values())
            if headers_list:
                headers_list[0] = "項目名"
            else:
                headers_list = ["項目名"] + [f"期_{i}" for i in range(max_len)]
                
            return extracted_data, headers_list[:max_len+1]
            
    except Exception as e:
        st.error(f"❌ 通信/システムエラー: {e}")
        
    return None, None

# =====================================
# メイン表示処理
# =====================================
if stock_code:
    with st.spinner("IR Bankから最新データを通信・解析中..."):
        data_dict, headers = fetch_and_parse_irbank(stock_code)
    
    if data_dict and headers:
        st.success("🎉 データの取得・解析に成功しました！本家と同じ表を出力します。")
        columns_years = headers[1:]
        
        max_vals_len = max(len(v) for v in data_dict.values())
        if len(columns_years) < max_vals_len:
            columns_years += [f"過去データ_{i}" for i in range(max_vals_len - len(columns_years))]

        # 1. 配当推移
        st.header("🔗 配当推移")
        div_targets = ["1株配当", "1株配当(調整後)", "配当性向", "DOE"]
        div_rows, div_index = [], []
        for tgt in div_targets:
            if tgt in data_dict:
                vals = data_dict[tgt]
                if len(vals) < len(columns_years): vals += [""] * (len(columns_years) - len(vals))
                div_rows.append(vals[:len(columns_years)])
                div_index.append(tgt)
        if div_rows:
            st.dataframe(pd.DataFrame(div_rows, columns=columns_years, index=div_index), use_container_width=True)
            
        # 2. キャッシュ・フロー推移
        st.header("🔗 キャッシュ・フロー推移")
        cf_targets = ["営業活動によるキャッシュ・フロー", "投資活動によるキャッシュ・フロー", "財務活動によるキャッシュ・フロー", "現金及び現金同等物期末残高"]
        cf_rows, cf_index = [], []
        for tgt in cf_targets:
            if tgt in data_dict:
                vals = data_dict[tgt]
                if len(vals) < len(columns_years): vals += [""] * (len(columns_years) - len(vals))
                cf_rows.append(vals[:len(columns_years)])
                cf_index.append(tgt)
        if cf_rows:
            st.dataframe(pd.DataFrame(cf_rows, columns=columns_years, index=cf_index), use_container_width=True)
