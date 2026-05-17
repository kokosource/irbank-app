import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("IR Bank Viewer")

code = st.text_input("銘柄コード", "7203")

if code:
    url = f"https://irbank.net/{code}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        html = requests.get(url, headers=headers).text

        tables = pd.read_html(StringIO(html))

        st.success("取得成功！")

        st.write(f"表の数: {len(tables)}")

        st.dataframe(tables[0])

    except Exception as e:
        st.error(f"取得失敗: {e}")
