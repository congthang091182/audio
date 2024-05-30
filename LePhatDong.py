import streamlit as st 
import pandas as pd
import numpy as np
import pyodbc 
import datetime as dt
import time
import os
import openai
import plotly.express as px
#import matplotlib.pyplot as plt
#import altair as alt
#Connect to database
db_user = st.secrets["db_credentials"]["user"]
db_password = st.secrets["db_credentials"]["password"]
db_host = st.secrets["db_credentials"]["host"]
db_database = st.secrets["db_credentials"]["Database"]
openai.api_key=st.secrets["db_credentials"]["api_key"]
#st.write("db_credentials abc:", openai.api_key)
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      f'SERVER={db_host};'
                      f'DATABASE={db_database};'
                      f'UID={db_user};'
                      f'PWD={db_password}')
  #username=st.secrets.db_credentials.username, password=st.secrets.db_credentials.password)
#//connect open
st.header(':orange[Gửi tiền tiết kiệm, chung tay vì người nghèo]', divider='rainbow')
#st.header('_Streamlit_ is :blue[cool] :sunglasses:')
#//
#cac ham xuly input
button_style = """
<style>
div.stButton > button:first-child {
    background-color: #4CAF50;  /* Green background */
    color: white;  /* White text */
    border: none;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    transition-duration: 0.4s;
    cursor: pointer;
}

div.stButton > button:first-child:hover {
    background-color: white;
    color: black;
    border: 2px solid #4CAF50;
}
</style>
"""
##clear txt
#
st.title('Đăng ký thông tin Khách hàng')
cursor = cnxn.cursor()
title = st.text_input(":red[Họ và tên (*)]","")
#title = st.text_input(":orange[Enter your text here]")
today = dt.datetime.now()
start_date = dt.datetime(1900, 1, 1,)
#st.button("Subit", type="primary")
d = st.date_input("Ngày tháng năm sinh", min_value=start_date,max_value= today , format="DD-MM-YYYY",)
title0 = st.text_input("Số CMT (nếu có)", "")
title1 = st.text_input(":red[Số CCCD(*)]", "")
d0 = st.date_input("Ngày cấp", today , format="DD-MM-YYYY",)
title2 = st.text_input("Nơi cấp", "Cục cảnh sát QLHC về TTXH")
title3 = st.text_input(":red[Địa chỉ thường trú(*)]", "")
title4 = st.text_input(":red[Số điện thoại(*)]", "")
sotien=st.number_input("Nhập số tiền gửi ",format="%f")
st.write(f"Giá trị:  :green[{sotien:,}]")
#st.write("Combining **bold and :green[colored text] is totally** fine! Just like with other markdown features.")
#sotien=sotien.format("%f")
combobox0 = st.selectbox(
   ":red[Nơi gửi tiết kiệm (*)]",
   ("Thành phố", "Cao Lộc", "Lộc Bình"
        ,"Đình Lập", "Văn Lãng", "Tràng Định",
        "Văn Quan", "Bình Gia", "Bắc Sơn",
        "Chi Lăng", "Hữu Lũng"
    ),
   index=None,
   placeholder="click để chọn...",
)
combobox = st.selectbox(
   "Đơn vị ủy thác",
   ("Hội nông dân", "Hội phụ nữ","Hội cựu chiến binh", "Đoàn thanh niên"
        ,"Khác"
    ),
   index=None,
   placeholder="click để chọn...",
)
title6 = st.text_input("Đơn vị công tác", "")
st.write(":red[(*)]  bắt buộc")
st.markdown(button_style, unsafe_allow_html=True)
click=st.button("Đồng ý")
if click:
  d= d.strftime("%x")
  d0= d0.strftime("%x")
  para = (title,d,title0,title1,d0,title2,title3,title4,sotien,combobox,title6,combobox0)
  query=""" insert into lephatdong (HOTEN,NGAYSINH,CMT_CU,CCCD,NGAYCAP,NOICAP,DIACHI,DIENTHOAI,SOTIEN,TOCHUCHOI,DONVI,POS) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"""
  #query  = "exec LEPHATDONG_INSERT @HOTEN=?,@NGAYSINH=?,@CMT_CU=?,@CCCD=?,@NGAYCAP=?,@DIACHI=?,@DIENTHOAI=?,@SOTIEN=?,@TOCHUCHOI=?,@DONVI=?"
  cursor.execute(query,para)
  def clear_text():
    title = st.empty()
    title0 = st.empty()
  cnxn.commit()
  clear_text()
  
  #st.button("Clear", on_click=on_click)
  st.success('Cảm ơn bạn đã đăng ký')
#nếu click xem
st.header(':white[Thống kê số liệu]', divider='rainbow')
click0=st.button("Xem số lượng khách hàng đã đăng ký")
if click0:
  para = ()
  query  = "select TOCHUCHOI N'Tổ chức hội',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY TOCHUCHOI"
  data=cursor.execute(query,para).fetchall()
  df = pd.DataFrame.from_records(
                    data=data,
                    columns=[column_info[0] for column_info in cursor.description],
                    coerce_float=True
                )
  para0 = ()
  query0  = "select POS N'Nơi gửi',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY POS"
  data0=cursor.execute(query0,para0).fetchall()
  df0 = pd.DataFrame.from_records(
                    data=data0,
                    columns=[column_info[0] for column_info in cursor.description],
                    coerce_float=True
                )
  para1 = ()
  query1  = "select DONVI N'Đơn vị công tác',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY DONVI order by DONVI"
  data1=cursor.execute(query1,para1).fetchall()
  df1 = pd.DataFrame.from_records(
                    data=data1,
                    columns=[column_info[0] for column_info in cursor.description],
                    coerce_float=True
                )
  #st.write(df)
# chart = alt.Chart(df).mark_bar().encode(
#         alt.X("SOKH", bin=True),
#         y='count()',
#     )
  tab1, tab2, tab3 = st.tabs(["Theo đơn vị ủy thác", "Theo nơi gửi","Theo đơn vị công tác"])
  with tab1:
          st.write(df, theme="streamlit", use_container_width=True)
          fig = px.bar(df, x='Tổ chức hội', y='Số khách hàng', title='Biểu đồ số lượng tổ chức hội', color=['red', 'green', 'blue','orange'])

          # Displaying the Plotly chart in Streamlit
          st.plotly_chart(fig)
  with tab2:
          st.write(df0, theme=None, use_container_width=True)
          fig = px.bar(df0, x='Nơi gửi', y='Số khách hàng', title='Biểu đồ số lượng POS')
          st.plotly_chart(fig)
  with tab3:
          st.write(df1, theme=None, use_container_width=True)
          fig = px.line(df1, x='Đơn vị công tác', y='Số khách hàng', title='Biểu đồ theo ĐVCT')
          st.plotly_chart(fig)
#connect close
#cursor.close()
   
cnxn.close()


#st.text_input('Enter text here:', key='widget', on_change=clear_text)