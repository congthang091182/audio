import streamlit as st 
#import pandas as pd
#import numpy as np
import pyodbc 
import datetime as dt
import time
import os
#Connect to database

#
db_user = st.secrets["db_credentials"]["user"]
db_user = st.secrets["db_credentials"]["user"]
db_password = st.secrets["db_credentials"]["password"]
db_host = st.secrets["db_credentials"]["host"]
db_database = st.secrets["db_credentials"]["Database"]
api_key = st.secrets["db_credentials"]["api_key"]
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
##clear txt
#
st.title('Đăng ký thông tin Khách hàng')
cursor = cnxn.cursor()
title = st.text_input(":red[Họ và tên (*)]","")

#title = st.text_input(":orange[Enter your text here]")
today = dt.datetime.now()
#st.button("Subit", type="primary")
d = st.date_input("Ngày tháng năm sinh", today , format="DD-MM-YYYY",)
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

#connect close
#cursor.close()
cnxn.close()


#st.text_input('Enter text here:', key='widget', on_change=clear_text)