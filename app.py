import streamlit as st
import pandas as pd
import requests

st.title("IR Bank Viewer")

code = st.text_input("銘柄コード", "7203")

if code:
    url = f"https://irbank.net/{code}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)

        tables = pd.read_html(response.text)

        st.success("取得成功！")

        st.dataframe(tables[0])

    except Exception as e:
        st.error(f"取得失敗: {e}")
