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

st.title("📊 IR Bank 財務データ再現")
stock_code = st.text_input("銘柄コード（例: 7203）", "7203")

# =====================================
# スクレイピングエンジン（対策回避版）
# =====================================
@st.cache_data(ttl=3600)
def fetch_and_parse_irbank(code):
    # 最新のブラウザを偽装するヘッダー設定（スクレイピングブロック対策）
    url = f"https://irbank.net/{code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    
    # 抽出ターゲット項目
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
        response = requests.get(url, headers=headers, timeout=20)
        
        # もしブロック等でページが取れなかった場合、詳細ページへのフォールバックを試みる
        if response.status_code != 200:
            # 決算まとめページ等、別のURL構成を試行
            url = f"https://irbank.net/{code}/c"
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                st.error(f"IR Bankへのアクセスが拒否されました (Status Code: {response.status_code})。時間を置いて試すか、別の銘柄をお試しください。")
                return None, None
            
        soup = BeautifulSoup(response.text, "html5lib")
        tables = soup.find_all("table")
        
        for table in tables:
            trs = table.find_all("tr")
            if not trs:
                continue
                
            # 各テーブルの見出し（年度など）を取得
            current_table_headers = []
            thead = table.find("thead")
            if thead:
                current_table_headers = [th.get_text(strip=True) for th in thead.find_all("th")]
            else:
                # theadがない場合は最初のtrから探す
                first_tr = trs[0]
                current_table_headers = [th.get_text(strip=True) for th in first_tr.find_all(["th", "td"])]
            
            for tr in trs:
                th_item = tr.find(["th", "td"])
                if not th_item:
                    continue
                
                # 項目名から余計な空白を排除
                item_name = re.sub(r'\s+', '', th_item.get_text(strip=True))
                
                # ターゲット項目との一致判定
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
                        
                    # ヘッダーリストが未取得なら更新
                    if len(current_table_headers) > len(headers_list):
                        headers_list = current_table_headers
                        
                    if matched_target not in extracted_data:
                        extracted_data[matched_target] = values

        if extracted_data:
            # カラムヘッダー（年度）の確定
            max_len = max(len(v) for v in extracted_data.values())
            
            # 見出し行の一番左端を「項目名」に固定
            if headers_list:
                headers_list[0] = "項目名"
            else:
                headers_list = ["項目名"] + [f"期_{i}" for i in range(max_len)]
                
            return extracted_data, headers_list[:max_len+1]
            
    except Exception as e:
        st.error(f"システムエラー: {e}")
        
    return None, None

# =====================================
# メイン表示処理
# =====================================
if stock_code:
    with st.spinner("IR Bankから最新のデータを解析中..."):
        data_dict, headers = fetch_and_parse_irbank(stock_code)
    
    if data_dict and headers:
        columns_years = headers[1:] # 2024/03 などの年度リスト
        
        # カラム名が不足している場合の安全処理
        max_vals_len = max(len(v) for v in data_dict.values())
        if len(columns_years) < max_vals_len:
            columns_years += [f"過去データ_{i}" for i in range(max_vals_len - len(columns_years))]

        # -------------------------------------
        # 1. 配当推移の本家再現
        # -------------------------------------
        st.header("🔗 配当推移")
        div_targets = ["1株配当", "1株配当(調整後)", "配当性向", "DOE"]
        div_rows, div_index = [], []
        
        for tgt in div_targets:
            if tgt in data_dict:
                vals = data_dict[tgt]
                # 長さ合わせ
                if len(vals) < len(columns_years):
                    vals += [""] * (len(columns_years) - len(vals))
                div_rows.append(vals[:len(columns_years)])
                div_index.append(tgt)
                
        if div_rows:
            df_div = pd.DataFrame(div_rows, columns=columns_years, index=div_index)
            st.dataframe(df_div, use_container_width=True)
        else:
            st.warning("配当データがサイト内に見つかりませんでした。")
            
        # -------------------------------------
        # 2. キャッシュ・フロー推移の本家再現
        # -------------------------------------
        st.header("🔗 キャッシュ・フロー推移")
        cf_targets = [
            "営業活動によるキャッシュ・フロー", 
            "投資活動によるキャッシュ・フロー", 
            "財務活動によるキャッシュ・フロー", 
            "現金及び現金同等物期末残高"
        ]
        cf_rows, cf_index = [], []
        
        for tgt in cf_targets:
            if tgt in data_dict:
                vals = data_dict[tgt]
                if len(vals) < len(columns_years):
                    vals += [""] * (len(columns_years) - len(vals))
                cf_rows.append(vals[:len(columns_years)])
                cf_index.append(tgt)
                
        if cf_rows:
            df_cf = pd.DataFrame(cf_rows, columns=columns_years, index=cf_index)
            st.dataframe(df_cf, use_container_width=True)
        else:
            st.warning("キャッシュ・フローデータがサイト内に見つかりませんでした。")
