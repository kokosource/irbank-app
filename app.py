import re
from io import StringIO
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =====================================
# 基本設定
# =====================================
st.set_page_config(
    page_title="IR Bank ダッシュボード",
    layout="wide"
)

# CSS調整
st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.main { background-color: #f8fafc; }
.block-container { padding-top: 2rem; max-width: 1400px; }
h1 { size: 30px; color: #1e3a8a; font-weight: 700; }
h2 { color: #1e3a8a; font-size: 20px; margin-top: 30px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
</style>
    """,
    unsafe_allow_html=True
)

st.title("📊 IR Bank 財務データアナライザー")
stock_code = st.text_input("銘柄コードを入力（例: 7203）", "7203")

# =====================================
# データ取得 & 整形関数
# =====================================
@st.cache_data(ttl=3600)
def fetch_tables(code):
    url = f"https://irbank.net/{code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        tables = pd.read_html(StringIO(response.text))
        return tables
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None

def search_table(tables, keywords):
    if tables is None: return None
    for table in tables:
        text = " ".join(table.astype(str).fillna("").values.flatten())
        if all(word in text for word in keywords):
            return table
    return None

def clean_and_transpose_dataframe(df):
    """
    IR Bankの横長テーブルを縦長に変換し、数値をクレンジングする共通関数
    """
    # 最初の列（項目名）をインデックスに設定
    df = df.set_index(df.columns[0])
    
    # 行列を反転（年度がインデックス、項目名がカラムになる）
    df = df.T
    
    # インデックス（年度）から「2024」などの4桁数値を抽出して整形
    clean_years = []
    for idx in df.index:
        match = re.search(r"(20\d{2}|19\d{2})", str(idx))
        clean_years.append(f"{match.group(1)}年度" if match else str(idx))
    df.index = clean_years
    df.index.name = "年度"
    
    # 全セルのテキストクレンジング（要素単位で安全に実行）
    def clean_value(val):
        if pd.isna(val):
            return np.nan
        s = re.sub(r"[財政|,]清算|円|百万円|%|,", "", str(val))
        try:
            return float(s)
        except ValueError:
            return np.nan

    # df.map で一括適用（重複列名のエラーを回避）
    df = df.map(clean_value)
        
    return df

# =====================================
# グラフ生成関数
# =====================================
def make_combined_cf_chart(df, title):
    fig = go.Figure()
    
    if "営業活動" in df.columns:
        fig.add_trace(go.Bar(x=df.index, y=df["営業活動"], name="営業CF", marker_color="#10b981"))
    if "投資活動" in df.columns:
        fig.add_trace(go.Bar(x=df.index, y=df["投資活動"], name="投資活動CF", marker_color="#ef4444"))
    if "財務活動" in df.columns:
        fig.add_trace(go.Bar(x=df.index, y=df["財務活動"], name="財務活動CF", marker_color="#3b82f6"))
    if "現金等" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["現金等"], name="現金等残高", mode="lines+markers", line=dict(color="#f59e0b", width=3)))

    fig.update_layout(
        title=title, height=400, barmode="group",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.1, x=0),
        yaxis=dict(gridcolor="#e2e8f0", title="百万円")
    )
    return fig

# =====================================
# メインロジック
# =====================================
if stock_code:
    tables = fetch_tables(stock_code)
    
    if tables:
        # -------------------------------------
        # 1. 配当推移セクション
        # -------------------------------------
        st.header("📈 配当推移")
        div_raw = search_table(tables, ["配当"])
        
        if div_raw is not None:
            div_df = clean_and_transpose_dataframe(div_raw)
            
            # 「配当」が含まれる列名を取得し、重複があっても最初の1列に絞る
            available_div_cols = [c for c in div_df.columns if "配当" in c]
            div_col = available_div_cols[0] if available_div_cols else div_df.columns[0]
            
            # 表示用データフレームの切り出し（重複列対策を徹底）
            display_div_df = div_df[[div_col]]
            if isinstance(display_div_df, pd.DataFrame) and display_div_df.shape[1] > 1:
                display_div_df = display_div_df.iloc[:, [0]]

            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("配当データ一覧")
                st.dataframe(
                    display_div_df, 
                    use_container_width=True,
                    column_config={
                        div_col: st.column_config.NumberColumn(
                            "1株配当額", 
                            format="¥%.1f"
                        )
                    }
                )
            
            with col2:
                # Plotlyでラインチャート
                fig = go.Figure()
                # 描画時はシリーズ（1次元）に確定させるため .iloc[:, 0] を指定
                y_data = display_div_df.iloc[:, 0]
                fig.add_trace(go.Scatter(
                    x=display_div_df.index, y=y_data,
                    mode="lines+markers+text",
                    text=y_data.map(lambda x: f"¥{x:.0f}" if pd.notnull(x) else ""),
                    textposition="top center",
                    line=dict(color="#1e3a8a", width=3),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    title="1株配当金の推移", height=350,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis=dict(gridcolor="#e2e8f0")
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("配当データが見つかりません。")

        # -------------------------------------
        # 2. キャッシュ・フロー推移セクション
        # -------------------------------------
        st.header("💵 キャッシュ・フロー推移")
        cf_raw = search_table(tables, ["営業活動", "投資活動"])
        
        if cf_raw is not None:
            cf_df = clean_and_transpose_dataframe(cf_raw)
            
            # 表内の表記ゆれ・重複列を吸収して名前を統一
            col_map = {}
            for c in cf_df.columns:
                if "営業" in c and "営業活動" not in col_map.values(): col_map[c] = "営業活動"
                elif "投資" in c and "投資活動" not in col_map.values(): col_map[c] = "投資活動"
                elif "財務" in c and "財務活動" not in col_map.values(): col_map[c] = "財務活動"
                elif "現金" in c and "現金等" not in col_map.values(): col_map[c] = "現金等"
            
            cf_df = cf_df.rename(columns=col_map)
            available_cols = [c for c in ["営業活動", "投資活動", "財務活動", "現金等"] if c in cf_df.columns]
            
            # 1列ずつ確実に抽出して重複カラムを完全に排除
            extracted_cols = []
            for col_name in available_cols:
                sub_df = cf_df[col_name]
                if isinstance(sub_df, pd.DataFrame):
                    sub_df = sub_df.iloc[:, 0]
                extracted_cols.append(sub_df.rename(col_name))
            
            display_cf_df = pd.concat(extracted_cols, axis=1)

            # カラムごとのスタイル設定
            config = {
                c: st.column_config.NumberColumn(format="%,d 百万円") 
                for c in display_cf_df.columns if c != "現金等"
            }
            if "営業活動" in display_cf_df.columns:
                config["営業活動"] = st.column_config.ProgressColumn(
                    "営業活動CF", 
                    format="%,d 百万円",
                    min_value=int(display_cf_df["営業活動"].min()) if display_cf_df["営業活動"].min() < 0 else 0,
                    max_value=int(display_cf_df["営業活動"].max())
                )

            st.subheader("キャッシュ・フロー詳細データ")
            st.dataframe(display_cf_df, use_container_width=True, column_config=config)
            
            # 複数CFをまとめたリッチなグラフを表示
            cf_fig = make_combined_cf_chart(display_cf_df, "キャッシュ・フロー多角比較")
            st.plotly_chart(cf_fig, use_container_width=True)
            
        else:
            st.warning("キャッシュ・フローデータが見つかりません。")
