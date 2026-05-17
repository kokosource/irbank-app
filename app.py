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
    page_title="IR Bank",
    layout="wide"
)

# =====================================
# CSS（IR Bank風）
# =====================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.main {
    background-color: #ffffff;
}

.block-container {
    padding-top: 1rem;
    max-width: 1500px;
}

h1 {
    font-size: 34px !important;
    color: #1b3f91;
    font-weight: 700;
    margin-bottom: 20px;
}

h2 {
    color: #1b3f91;
    font-size: 24px !important;
    margin-top: 40px;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 10px;
}

.stDataFrame {
    border: 1px solid #d9dfe8;
    border-radius: 8px;
    overflow: hidden;
}

[data-testid="stMetric"] {
    background-color: #f8fafc;
    border: 1px solid #dbe2ea;
    padding: 15px;
    border-radius: 10px;
}

</style>
    """,
    unsafe_allow_html=True
)

# =====================================
# タイトル
# =====================================

st.title("IR Bank")

stock_code = st.text_input(
    "銘柄コード",
    "7203"
)

# =====================================
# データ取得
# =====================================

@st.cache_data(ttl=3600)
def fetch_tables(code):

    url = f"https://irbank.net/{code}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    html = response.text

    tables = pd.read_html(StringIO(html))

    return tables

# =====================================
# 数値整形
# =====================================

def to_number(x):

    if pd.isna(x):
        return np.nan

    x = str(x)

    x = x.replace(",", "")
    x = x.replace("円", "")
    x = x.replace("%", "")
    x = x.replace("百万円", "")

    try:
        return float(x)
    except:
        return np.nan

# =====================================
# テーブル検索
# =====================================

def search_table(tables, keywords):

    for table in tables:

        text = " ".join(
            table.astype(str)
            .fillna("")
            .values
            .flatten()
        )

        if all(word in text for word in keywords):
            return table

    return None

# =====================================
# グラフ生成
# =====================================

def make_line_chart(df, x, y, title, y_title=""):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines+markers",
            line=dict(width=3),
            marker=dict(size=8)
        )
    )

    fig.update_layout(
        title=title,
        height=450,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis_title="",
        yaxis_title=y_title,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e5e7eb")
    )

    return fig


def make_bar_chart(df, x, y, title, y_title=""):

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df[x],
            y=df[y]
        )
    )

    fig.update_layout(
        title=title,
        height=450,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis_title="",
        yaxis_title=y_title,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e5e7eb")
    )

    return fig

# =====================================
# メイン処理
# =====================================

if stock_code:

    try:

        tables = fetch_tables(stock_code)

        st.success("IR Bank データ取得成功")

        # =====================================
        # 配当推移
        # =====================================

        st.header("配当推移")

        dividend_table = search_table(
            tables,
            ["配当"]
        )

        if dividend_table is not None:

            st.dataframe(
                dividend_table,
                use_container_width=True,
                height=300
            )

            try:

                years = []
                dividends = []

                for col in dividend_table.columns[1:]:

                    year_match = re.search(
                        r"(20\d{2}|19\d{2})",
                        str(col)
                    )

                    if year_match:

                        year = year_match.group(1)

                        value = to_number(
                            dividend_table.iloc[0][col]
                        )

                        if not np.isnan(value):
                            years.append(year)
                            dividends.append(value)

                dividend_df = pd.DataFrame({
                    "年度": years,
                    "配当": dividends
                })

                fig = make_line_chart(
                    dividend_df,
                    "年度",
                    "配当",
                    "1株配当推移",
                    "円"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            except Exception as e:
                st.warning(f"配当グラフ生成失敗: {e}")

        else:
            st.warning("配当データが見つかりません")

        # =====================================
        # キャッシュフロー推移
        # =====================================

        st.header("キャッシュ・フロー推移")

        cf_table = search_table(
            tables,
            ["営業活動", "投資活動"]
        )

        if cf_table is not None:

            st.dataframe(
                cf_table,
                use_container_width=True,
                height=350
            )

            try:

                years = []
                operating_cf = []

                for col in cf_table.columns[1:]:

                    year_match = re.search(
                        r"(20\d{2}|19\d{2})",
                        str(col)
                    )

                    if year_match:

                        year = year_match.group(1)

                        value = to_number(
                            cf_table.iloc[0][col]
                        )

                        if not np.isnan(value):
                            years.append(year)
                            operating_cf.append(value)

                cf_df = pd.DataFrame({
                    "年度": years,
                    "営業CF": operating_cf
                })

                fig = make_bar_chart(
                    cf_df,
                    "年度",
                    "営業CF",
                    "営業キャッシュ・フロー推移",
                    "百万円"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            except Exception as e:
                st.warning(f"CFグラフ生成失敗: {e}")

        else:
            st.warning("キャッシュフローデータが見つかりません")

    except Exception as e:

        st.error(f"取得失敗: {e}")
