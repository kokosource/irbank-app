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
    if tables travels is None: return None
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
    
    # 全セルのテキストクレンジング（数値化）
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(r"[財政|,]清算|円|百万円|%|,", "", regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df

# =====================================
# グラフ生成関数
# =====================================
def make_combined_cf_chart(df, title):
    fig = go.Figure()
    
    # 存在するカラムだけ安全に描画
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
        legend=dict(orientation="h", ylink=1, y=1.1, x=0),
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
            # データ整形
            div_df = clean_and_transpose_dataframe(div_raw)
            
            # メインの配当列（通常は最初の列、または「配当」が含まれる列）を取得
            div_col = [c for c in div_df.columns if "配当" in c][0] if any("配当" in c for c in div_df.columns) else div_df.columns[0]

            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("配当データ一覧")
                # column_configで見た目を美しく
                st.dataframe(
                    div_df[[div_col]], 
                    use_container_width=True,
                    column_config={
                        div_col: st.column_config.NumberColumn(
                            "1株配当額", 
                            format="¥%.1f",
                            help="該当年度の年間配当金"
                        )
                    }
                )
            
            with col2:
                # Plotlyでラインチャート
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=div_df.index, y=div_df[div_col],
                    mode="lines+markers+text",
                    text=div_df[div_col].map(lambda x: f"¥{x:.0f}" if pd.notnull(x) else ""),
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
            
            # IR Bankの元の項目名と一致させる（部分一致でカラム特定）
            col_map = {}
            for c in cf_df.columns:
                if "営業" in c: col_map[c] = "営業活動"
                elif "投資" in c: col_map[c] = "投資活動"
                elif "財務" in c: col_map[c] = "財務活動"
                elif "現金" in c: col_map[c] = "現金等"
            
            cf_df = cf_df.rename(columns=col_map)
            # 必要なカラムだけ順序を整えて抽出
            available_cols = [c for c in ["営業活動", "投資活動", "財務活動", "現金等"] if c in cf_df.columns]
            display_cf_df = cf_df[available_cols]

            # カラムごとのスタイルを設定
            config = {
                c: st.column_config.NumberColumn(format="%,d 百万円") 
                for c in available_cols if c != "現金等"
            }
            # 営業CFにはミニバー（視覚効果）を追加
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
