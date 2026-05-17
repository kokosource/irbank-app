import lxml
import streamlit as st
import pandas as pd
import requests

st.title("IR Bank Viewer")

code = st.text_input("銘柄コード", "3003")

url = f"https://irbank.net/{code}/results"

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(url, headers=headers)

    tables = pd.read_html(response.text)

    found = False

    for table in tables:

        text = table.to_string()

        if "配当" in text:
            st.subheader("配当推移")
            st.dataframe(table)
            found = True

        if "キャッシュフロー" in text:
            st.subheader("キャッシュフロー")
            st.dataframe(table)
            found = True

    if not found:
        st.warning("表が見つかりませんでした")

except Exception as e:
    st.error(f"取得失敗: {e}")
