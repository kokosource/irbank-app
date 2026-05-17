import pandas as pd
import streamlit as st

# =====================================
# 基本設定 ＆ 本家IR Bank風のCSS
# =====================================
st.set_page_config(
    page_title="IR Bank風 財務データ表示",
    layout="wide"
)

# IR Bankの象徴であるディープブルー（#1b3f91）と薄いグレーの境界線を再現
st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.main {
    background-color: #ffffff;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}
/* 本家風の見出しスタイル */
h1 {
    font-size: 28px !important;
    color: #1b3f91;
    font-weight: 700;
    margin-bottom: 25px;
}
h2 {
    color: #1b3f91;
    font-size: 20px !important;
    margin-top: 35px;
    margin-bottom: 15px;
    border-bottom: 2px solid #1b3f91; /* 本家風の青い下線 */
    padding-bottom: 5px;
}
/* 横スクロール可能なテーブルの枠組み調整 */
.stDataFrame {
    border: 1px solid #d9dfe8;
    border-radius: 4px;
}
</style>
    """,
    unsafe_allow_html=True
)

st.title("📊 IR Bank風 財務データ再現ダッシュボード")

# =====================================
# 1. AIが読み取った想定データ（生データ）
# =====================================
# ※AIがPDFや画像、テキストから抽出したデータをここに流し込みます。
# 本家通り「左端が項目名」「上の列が決算期」の構造をそのまま辞書で作ります。

raw_dividend_data = {
    "決算期": ["2021/03", "2022/03", "2023/03", "2024/03", "2025/03(予)"],
    "1株配当": ["240.0円", "280.0円", "300.0円", "310.0円", "330.0円"],
    "1株配当(調整後)": ["120.0円", "140.0円", "150.0円", "155.0円", "165.0円"],
    "配当性向": ["29.4%", "31.2%", "30.5%", "32.0%", "31.8%"],
    "DOE": ["3.1%", "3.4%", "3.6%", "3.5%", "3.8%"]
}

raw_cf_data = {
    "決算期": ["2021/03", "2022/03", "2023/03", "2024/03", "2025/03(予)"],
    "営業活動によるキャッシュ・フロー": ["2,500,000", "2,900,000", "3,100,000", "3,400,000", "3,600,000"],
    "投資活動によるキャッシュ・フロー": ["-1,200,000", "-1,500,000", "-1,800,000", "-1,600,000", "-1,900,000"],
    "財務活動によるキャッシュ・フロー": ["-800,000", "-600,000", "-900,000", "-1,100,000", "-850,000"],
    "現金及び現金同等物期末残高": ["4,100,000", "4,900,000", "5,300,000", "6,000,000", "6,850,000"]
}

# =====================================
# 2. 本家再現のためのデータ変形処理
# =====================================
def convert_to_irbank_style(raw_dict):
    # 一度普通の縦長データフレームにする
    df = pd.DataFrame(raw_dict)
    # 「決算期」をインデックス（行の主軸）に設定
    df = df.set_index("決算期")
    # 行と列を反転（転置：.T）させて、本家と同じ「横長」にする
    df_reversed = df.T
    return df_reversed

# データの変換
df_dividend = convert_to_irbank_style(raw_dividend_data)
df_cf = convert_to_irbank_style(raw_cf_data)

# =====================================
# 3. 画面への表示処理
# =====================================

# ーーー 配当推移の再現 ーーー
st.header("🔗 配当推移")
st.dataframe(
    df_dividend, 
    use_container_width=True, # 画面幅いっぱいに広げる
    height=210                # 項目数に応じた適切な高さ（無駄な余白を消す）
)

# ーーー キャッシュ・フロー推移の再現 ーーー
st.header("🔗 キャッシュ・フロー推移")

# 本家は金額の単位（百万円など）が表の上部や項目名に記載されるため、補足をつける
st.caption("単位：百万円")
st.dataframe(
    df_cf, 
    use_container_width=True,
    height=210
)

# =====================================
# 4. 実用的な活用アドバイス（サイドバー）
# =====================================
with st.sidebar:
    st.subheader("🤖 AIデータ連携ヒント")
    st.write(
        """
        ChatGPTやClaudeなどのAIに、
        「**この財務データを上記のPython辞書（PythonのDict型）の形式で出力して**」
        と命令し、その結果をそのまま `raw_dividend_data` や `raw_cf_data` の部分に貼り付けるだけで、どんな企業のデータでも瞬時にこの本家レイアウトで表示できるようになります。
        """
    )
