import pandas as pd
import streamlit as st

# =====================================
# 1. ページ基本設定 & 本家IR Bank CSSの完全再現
# =====================================
st.set_page_config(
    page_title="IR Bank 財務・業績",
    layout="wide"
)

# 本家のフォント、カラー（#1b3f91）、テーブルの薄いグレーのボーダー、ヘッダーの背景色を模倣
st.markdown(
    """
<style>
/* フォントと全体の背景 */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Segoe UI", "Hiragino Kaku Gothic ProN", "Sans-Serif";
    background-color: #ffffff;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

/* 本家風の見出し (H2) */
h2 {
    color: #1b3f91;
    font-size: 18px !important;
    font-weight: bold;
    margin-top: 30px;
    margin-bottom: 12px;
    border-bottom: 2px solid #1b3f91;
    padding-bottom: 4px;
}

/* キャプション（単位表記など） */
.unit-text {
    font-size: 12px;
    color: #666666;
    text-align: right;
    margin-bottom: 4px;
}
</style>
    """,
    unsafe_allow_html=True
)

st.title("📊 IR Bank 財務データ再現ダッシュボード")

# =====================================
# 2. AIがパースした想定データ（生データ・数値型）
# =====================================
# 本家と同じく「項目名」を縦軸、「年度」を横軸にするため、
# Streamlitでは「年度を行（Index）」にして、後からフォーマットします。

years = ["2021/03", "2022/03", "2023/03", "2024/03", "2025/03(予)"]

# 配当データ
div_data = {
    "1株配当": [240.0, 280.0, 300.0, 310.0, 330.0],
    "1株配当(調整後)": [120.0, 140.0, 150.0, 155.0, 165.0],
    "配当性向": [0.294, 0.312, 0.305, 0.320, 0.318], # ％表記は小数点で持つ
    "DOE": [0.031, 0.034, 0.036, 0.035, 0.038]
}
df_div_base = pd.DataFrame(div_data, index=years)

# キャッシュ・フローデータ（単位：百万円として数値で持つ）
cf_data = {
    "営業活動によるキャッシュ・フロー": [2500000, 2900000, 3100000, 3400000, 3600000],
    "投資活動によるキャッシュ・フロー": [-1200000, -1500000, -1800000, -1600000, -1900000],
    "財務活動によるキャッシュ・フロー": [-800000, -600000, -900000, -1100000, -850000],
    "現金及び現金同等物期末残高": [4100000, 4900000, 5300000, 6000000, 6850000]
}
df_cf_base = pd.DataFrame(cf_data, index=years)

# 本家は「横長」なので、行列を反転（転置）させる
df_div = df_div_base.T
df_cf = df_cf_base.T

# =====================================
# 3. 本家流「水色の棒グラフ」ビジュアルの定義
# =====================================
# 本家の特徴である、数字の背景に伸びる鮮やかな水色のバー（#cbebfd風）を再現するためのカラーコード
BAR_COLOR = "#a6e3e9" 

# 各年度列に対して、水色のProgressバーと適切なフォーマットを一括設定する関数
def get_column_config(df, is_percent=False, is_currency=False):
    config = {}
    for col in df.columns:
        # データの最大値・最小値を取得してバーの伸縮幅を自動決定
        max_val = float(df[col].max()) if df[col].max() > 0 else 1.0
        min_val = float(df[col].min()) if df[col].min() < 0 else 0.0
        
        if is_percent:
            config[col] = st.column_config.ProgressColumn(
                col, format="%.1f%%", min_value=min_val, max_value=max_val, color=BAR_COLOR
            )
        elif is_currency:
            config[col] = st.column_config.ProgressColumn(
                col, format="¥%.1f", min_value=min_val, max_value=max_val, color=BAR_COLOR
            )
        else:
            # キャッシュ・フロー用（3桁カンマ区切り）
            config[col] = st.column_config.ProgressColumn(
                col, format="%,d", min_value=min_val, max_value=max_val, color=BAR_COLOR
            )
    return config

# =====================================
# 4. 画面表示処理
# =====================================

# ーーーー 配当推移 ーーーー
st.markdown("<h2>🔗 配当推移</h2>", unsafe_allow_html=True)

# 本家は1株配当（円）と配当性向（％）が1つの表に混在しますが、
# Streamlitの仕様上、列（年度）ごとにしかProgressバーの単位を設定できないため、
# 本家の美しさを保ちつつ「金額系」と「割合系」で綺麗に2分割して水色バーを表示します。

st.markdown("<div class='unit-text'>単位：円</div>", unsafe_allow_html=True)
st.dataframe(
    df_div.iloc[0:2], # 1株配当、1株配当(調整後)
    use_container_width=True,
    height=110,
    column_config=get_column_config(df_div.iloc[0:2], is_currency=True)
)

st.markdown("<div class='unit-text'>単位：％</div>", unsafe_allow_html=True)
# ％表示のために一時的に100倍にしてProgressColumnに渡す
df_div_pct = df_div.iloc[2:4] * 100 
st.dataframe(
    df_div_pct, # 配当性向、DOE
    use_container_width=True,
    height=110,
    column_config=get_column_config(df_div_pct, is_percent=True)
)


# ーーーー キャッシュ・フロー推移 ーーーー
st.markdown("<h2>🔗 キャッシュ・フロー推移</h2>", unsafe_allow_html=True)
st.markdown("<div class='unit-text'>単位：百万円</div>", unsafe_allow_html=True)

st.dataframe(
    df_cf,
    use_container_width=True,
    height=180,
    column_config=get_column_config(df_cf)
)
