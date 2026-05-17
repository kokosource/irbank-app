import numpy as np
import pandas as pd
import streamlit as st

# =====================================
# 1. ページ基本設定 & 本家IR Bankの見た目CSS
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
    padding-top: 1.5rem;
    max-width: 1400px;
}
h2 {
    color: #1b3f91;
    font-size: 18px !important;
    font-weight: bold;
    margin-top: 30px;
    margin-bottom: 10px;
    border-bottom: 2px solid #1b3f91;
    padding-bottom: 6px;
}
.stDataFrame {
    border: 1px solid #b4c7e7;
    border-radius: 4px;
}
</style>
    """,
    unsafe_allow_html=True
)

st.title("📊 IR Bank 財務データビジュアル完全再現")

# =====================================
# 2. 財務データ群（データはそのまま維持）
# =====================================
years_div = ["2009/03", "2010/03", "2011/03", "2012/03", "2013/03", "2014/03", "2015/03", "2016/03", "2017/03", "2018/03", "2019/03", "2020/03", "2021/03", "2022/03", "2023/03", "2024/03", "2025/03", "2026/03", "27/03予"]
div_raw = {
    "一株配当": [np.nan, 5.56, 5.56, 3.33, 3.33, 3.33, 3.33, 3.33, 6.67, 6.67, 11.11, 8.89, 8.89, 11.11, 23.33, 43.67, 48.33, 50.33, 42.0],
    "配当性向": [np.nan, np.nan, 8.92, 61.1, 12.1, 8.5, 12.2, 10.2, 4.2, 8.5, 9.6, 7.3, 7.4, 11.4, 29.2, 30.2, 22.6, 30.0, np.nan],
    "剰余金の配当": [np.nan, np.nan, 2.84, 2.84, 1.7, 1.7, 1.7, 1.7, 1.7, 3.46, 3.47, 5.85, 4.7, 4.71, 5.9, 12.3, 30.3, 28.7, np.nan],
    "純資産配当率": [np.nan, np.nan, np.nan, 0.6, 0.6, 0.6, 0.5, 0.5, 0.9, 0.8, 1.1, 0.8, 0.7, 0.9, 1.7, 2.9, 2.9, 2.8, np.nan],
    "自社株買い": [0.03, 0.01, 0.01, 0.0, 0.01, 0.03, 0.07, 0.03, 0.03, 0.04, 0.59, 0.91, 0.67, 0.63, 2.12, 10.0, 0.02, 0.04, np.nan],
    "総還元額": [0.03, 0.01, 2.85, 2.84, 1.71, 1.73, 1.77, 1.73, 1.73, 3.5, 4.06, 6.76, 5.37, 5.34, 8.02, 22.4, 30.4, 28.8, np.nan],
    "総還元性向": [0.3, 0.0, 9.0, 61.1, 12.2, 8.6, 12.7, 10.4, 4.2, 8.6, 10.6, 8.7, 8.5, 12.6, 34.2, 43.5, 22.6, 30.0, np.nan]
}
df_div = pd.DataFrame(div_raw, index=years_div)

years_cf = ["2009/03", "2010/03", "2011/03", "2012/03", "2013/03", "2014/03", "2015/03", "2016/03", "2017/03", "2018/03", "2019/03", "2020/03", "2021/03", "2022/03", "2023/03", "2024/03", "2025/03", "2026/03"]
cf_raw = {
    "営業CF": [51.4, 118.0, 11.1, 72.4, 33.2, -4.25, -14.6, 76.2, 139.0, 33.3, 130.0, -41.3, -25.5, 204.0, -96.7, 133.0, 98.4, 152.0],
    "投資CF": [-11.5, -7.36, -9.13, -16.5, -11.0, -21.5, -11.9, -18.2, -33.4, -32.3, -38.1, -27.6, -41.8, -19.5, -15.0, -25.5, -29.8, -18.3],
    "財務CF": [-28.1, -79.3, -10.5, -58.0, -19.7, 16.0, 40.9, -67.8, -82.2, 27.7, -98.5, 55.4, 82.2, -158.0, 122.0, -103.0, -86.6, -101.0],
    "フリーCF": [39.9, 111.0, 1.94, 55.9, 22.2, -25.8, -26.5, 58.0, 105.0, 0.96, 92.2, -68.9, -67.3, 184.0, -112.0, 108.0, 68.6, 133.0],
    "設備投資": [-12.9, -15.3, -12.7, -24.1, -14.7, -24.7, -17.2, -21.2, -38.3, -34.3, -27.6, -38.4, -33.2, -25.5, -40.9, -38.9, -26.5, -31.5],
    "現金等": [42.3, 73.5, 64.9, 62.8, 65.9, 56.1, 70.6, 60.8, 83.7, 112.0, 106.0, 92.8, 108.0, 137.0, 157.0, 161.0, 143.0, 175.0],
    "営業CFマージン": [4.29, 10.76, 1.13, 9.07, 3.79, -0.47, -1.4, 8.01, 13.39, 3.1, 11.01, -3.25, -2.2, 19.65, -8.19, 10.32, 7.4, 13.18]
}
df_cf = pd.DataFrame(cf_raw, index=years_cf)

# =====================================
# 3. カリスマ再現 ＆ 挙動安定化設定（width追加）
# =====================================
COLOR_BLUE = "#7ecbfb"
COLOR_RED = "#ffb3ba"

def generate_fixed_column_config(df, is_cf=False):
    """
    widthを指定して列幅を完全固定し、画面のブレやカタつきを無くす関数
    """
    config = {}
    for col in df.columns:
        max_val = float(df[col].max()) if pd.notna(df[col].max()) else 1.0
        min_val = float(df[col].min()) if pd.notna(df[col].min()) else 0.0
        
        # フォーマットの設定
        if "性向" in col or "マージン" in col or "純資産" in col:
            fmt = "%.2f" if "純資産" in col else "%.2f %%"
        elif "一株" in col:
            fmt = "¥%.2f"
        else:
            fmt = "%.2f 億" if is_cf or col in ["剰余金の配当", "自社株買い", "総還元額"] else "%.2f"
            
        chosen_color = COLOR_RED if "投資" in col or "財務" in col or (min_val < 0 and max_val <= 0) else COLOR_BLUE
        
        # 【解決策】width=160 を設定して列の自動伸縮を完全にロックする
        config[col] = st.column_config.ProgressColumn(
            col,
            format=fmt,
            min_value=min_val if min_val < 0 else 0.0,
            max_value=max_val if max_val > 0 else 1.0,
            color=chosen_color,
            width=160  # ← ここで幅をしっかり固定
        )
    return config

# =====================================
# 4. 画面レンダリング（幅固定版）
# =====================================

# ーーーー 配当推移 ーーーー
st.markdown("<h2>📈 配当推移</h2>", unsafe_allow_html=True)
div_config = generate_fixed_column_config(df_div)

st.dataframe(
    df_div,
    use_container_width=True,
    height=550,
    column_config=div_config
)

# ーーーー キャッシュ・フロー推移 ーーーー
st.markdown("<h2>💵 キャッシュ・フロー推移</h2>", unsafe_allow_html=True)
cf_config = generate_fixed_column_config(df_cf, is_cf=True)

st.dataframe(
    df_cf,
    use_container_width=True,
    height=530,
    column_config=cf_config
)
