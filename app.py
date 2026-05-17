!pip install streamlit pyngrok lxml html5lib

from pyngrok import ngrok
import threading
import streamlit as st
import pandas as pd

app_code = '''
import streamlit as st
import pandas as pd

st.title("IR Bank Viewer")

code = st.text_input("銘柄コード", "7203")

if code:
    url = f"https://irbank.net/{code}"

    try:
        tables = pd.read_html(url, flavor="html5lib")

        st.success("取得成功！")
        st.write(f"表の数: {len(tables)}")

        st.dataframe(tables[0])

    except Exception as e:
        st.error(f"取得失敗: {e}")
'''

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

def run():
    import os
    os.system("streamlit run app.py --server.port 8501")

threading.Thread(target=run).start()

public_url = ngrok.connect(8501)
print(public_url)
