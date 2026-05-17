import streamlit as st
import pandas as pd

st.title("IR Bank Viewer")

code = st.text_input("銘柄コード", "3003")

url = f"https://irbank.net/{code}/results"

try:
    tables = pd.read_html(url)

    st.subheader("取得した表一覧")

    for i, table in enumerate(tables):
        st.write(f"### Table {i}")
        st.dataframe(table)

except:
    st.error("取得失敗")
