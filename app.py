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
    page_title="IR Bank 完全再現",
    layout="wide"
)

# タイトル
st.title("📊 IR Bank 財務データ再現（配当・CF）")
stock_code = st.text_input("銘柄コード（例: 7203）", "7203")

# =====================================
# 本家再現：汎用データ抽出エンジン
# =====================================
@st.cache_data(ttl=3600)
def fetch_and_parse_irbank(code):
    """
    IR BankのHTMLを解析し、本家と同一の見出し（年度）をカラムに、
    左端の各項目名をインデックスにした巨大な1つのマスタ辞書を生成する
    """
    url = f"https://irbank.net/{code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # 抽出したい本家の正確な項目名リスト
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
        if response.status_code != 200:
            return None, None
            
        soup = BeautifulSoup(response.text, "html5lib")
        tables = soup.find_all("table")
        
        for table in tables:
            # テーブル内の全trをスキャン
            trs = table.find_all("tr")
            if not trs:
                continue
                
            # 各テーブルにおける「年度ヘッダー」を仮取得
            current_table_headers = []
            thead = table.find("thead")
            if thead:
                current_table_headers = [th.get_text(strip=True) for th in thead.find_all("th")]
            
            for tr in trs:
                # 左端の項目名 (th または 最初のtd)
                th_item = tr.find(["th", "td"])
                if not th_item:
                    continue
                
                # 項目名のテキストを綺麗に掃除
                item_name = re.sub(r'\s+', '', th_item.get_text(strip=True))
                
                # ターゲット項目に部分一致・完全一致するか判定
                matched_target = None
                for target in target_rows:
                    if target in item_name:
                        matched_target = target
                        break
                        
                if matched_target:
                    # 値 (td) の全取得
                    tds = tr.find_all("td")
                    # 項目名がthに入っていてtdが値になっているケース
                    values = [td.get_text(strip=True) for td in tds]
                    
                    # 万が一、ヘッダー行がtheadにない場合は最上部から生成を試みる
                    if not headers_list and current_table_headers:
                        headers_list = current_table_headers
                        
                    if matched_target not in extracted_data:
                        extracted_data[matched_target] = values

        # 最適なカラムヘッダー（年度リスト）の自動補正
        # 一番データが多く取れている配列の長さを基準にする
        if extracted_data:
            max_len = max(len(v) for v in extracted_data.values())
            if len(headers_list) < max_len:
                # 足りない場合は適当なダミーではなく、右側を起点に合わせる
                headers_list = ["項目名"] + [f"期_{i}" for i in range(max_len - 1)]
            else:
                # 最初の「決算期」や「年月」という見出しを「項目名」に固定
                headers_list[0] = "項目名"
                
            return extracted_data, headers_list[:max_len+1]
            
    except Exception as e:
        st.error(f"パース中にエラーが発生しました: {e}")
        
    return None, None

# =====================================
# メイン表示処理
# =====================================
if stock_code:
    data_dict, headers = fetch_and_parse_irbank(stock_code)
    
    if data_dict and headers:
        columns_years = headers[1:] # 年度の一覧（例: '2021/03', '2022/03' ...）
        
        # -------------------------------------
        # 1. 配当推移の本家再現
        # -------------------------------------
        st.header("🔗 配当推移（本家再現）")
        
        div_targets = ["1株配当", "1株配当(調整後)", "配当性向", "DOE"]
        div_rows = []
        div_index = []
        
        for tgt in div_targets:
            if tgt in data_dict:
                # カラム数に長さを適合させる
                vals = data_dict[tgt]
                if len(vals) < len(columns_years):
                    vals += [""] * (len(columns_years) - len(vals))
                div_rows.append(vals[:len(columns_years)])
                div_index.append(tgt)
                
        if div_rows:
            df_div = pd.DataFrame(div_rows, columns=columns_years, index=div_index)
            st.dataframe(df_div, use_container_width=True)
        else:
            st.warning("配当に関する項目が見つかりませんでした。")
            
        # -------------------------------------
        # 2. キャッシュ・フロー推移の本家再現
        # -------------------------------------
        st.header("🔗 キャッシュ・フロー推移（本家再現）")
        
        cf_targets = [
            "営業活動によるキャッシュ・フロー", 
            "投資活動によるキャッシュ・フロー", 
            "財務活動によるキャッシュ・フロー", 
            "現金及び現金同等物期末残高"
        ]
        cf_rows = []
        cf_index = []
        
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
            st.warning("キャッシュ・フローに関する項目が見つかりませんでした。")
            
    else:
        st.error("IR Bankからデータを解析できませんでした。銘柄コードが正しいか確認してください。")
