import streamlit as st 
import pandas as pd
import numpy as np
import pyodbc 
import datetime as dt
import time
import os
import openai
import plotly.express as px
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
cursor = cnxn.cursor()
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
st.header(':orange[Gửi tiền tiết kiệm, chung tay vì người nghèo]', divider='rainbow')
st.markdown("""
            <style>
            .css-d1b1ld.edgvbvh6
            {
                visibilyti: hidden;
            }
            .css-1v8iw7l.eknhn3m4;
            {
                 visibilyti: hidden;
            }
            </style>
            """,unsafe_allow_html=True)
st.subheader("Đăng ký thông tin khách hàng")
with st.form("form2",clear_on_submit=True):
    today = dt.datetime.now()
    start_date = dt.datetime(1900, 1, 1,)
    col1,col2=st.columns(2)
    title=col1.text_input(":red[Họ và tên (*)]")
    d=col2.date_input("Ngày tháng năm sinh", min_value=start_date,max_value= today , format="DD-MM-YYYY",)
    col3,col4=st.columns(2)
    title0=col3.text_input("Số CMT cũ (nếu có)")
    title1=col4.text_input(":red[Số CCCD(*)]", "")
    col5,col6=st.columns(2)
    d0=col5.date_input ("Ngày cấp", today , format="DD-MM-YYYY",)
    title2=col6.text_input("Nơi cấp","Cục cảnh sát QLHC về TTXH")
    col7,col8=st.columns(2)
    title4=col7.text_input (":red[Số điện thoại(*)]", "")
    sotien=col8.number_input("Số tiền gửi",format="%f")
    #st.write(f"Giá trị:  :green[{sotien:,}]")
    #col9=st.columns(1)
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
    #col10=st.columns(1)
    title3=st.text_input(":red[Địa chỉ thường trú(*),ex: số nhà, đường, khối/thôn/bản, phường/xã,tỉnh...]", "")
    #col11=st.columns(1)
    combobox = st.selectbox(
   "Đơn vị ủy thác",
   ("Hội nông dân", "Hội phụ nữ","Hội cựu chiến binh", "Đoàn thanh niên"
        ,"Khác"
    ),
   index=None,
   placeholder="click để chọn...",
)
    #col12=st.columns(1)
    #title6=  st.text_input(":red[Đơn vị công tác(*)]", "")
    paraVAR = ()
  #query  = "select TOCHUCHOI N'Tổ chức hội',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY TOCHUCHOI"
    queryVAR  = " SELECT * FROM DONVICONGTAC ORDER BY TENDONVI"
    dataVAR=cursor.execute(queryVAR,paraVAR).fetchall()
#     combobox1 = st.selectbox(
#    ":red[Đơn vị công tác (*)]",
#    ("Công an tỉnh","Công an TP", "Sở nông nghiệp", "Sở tài chính","Sở tài nguyên môi trường","Sở lao động - Thương binh và xã hội","Sở nông nghiệp và Phát triển nông thôn"
#         ,"Sở kế hoạch và đầu tư", "Sở tư pháp", "Sở giáo dục và đào tạo","Sở xây dựng","Sở công thương","Sở khoa học và công nghệ",
#         "Sở ngoại vụ","Sở nội vụ","Sở thông tin và truyền thông","Sở y tế"
#         "Cục thuế tỉnh", "Cục Thống kê", "Cục thi hành án","Hội chữ thập đỏ","Viễn Thông Viettel","Bảo hiểm xã hội tỉnh","Báo Lạng Sơn","Bộ chỉ huy QS tỉnh"
#         "Bộ chỉ huy BP tỉnh", "Đảng ủy khối cơ quan"
#         ,"Khác"
#     ),
#    index=None,
#    placeholder="click để chọn...",
# )
    combobox1 = st.selectbox(
     ":red[Đơn vị công tác (*)]",( [item[1] for item in dataVAR]
       ),
    index=None,
    placeholder="click để chọn...",
    )
    st.write(":red[(*)]  bắt buộc")
    st.click=st.form_submit_button("Đồng ý")
    if st.click:
        #if st.title=="" and st.title0=="":
           #st.warning("This is a warning message!")
        d= d.strftime("%x")
        d0= d0.strftime("%x")
        d1=today.strftime("%x")
        para = (                          title,d,title0,title1,d0,title2,title3,title4,sotien,combobox,combobox1,combobox0,d1)
        query=""" insert into lephatdong (HOTEN,NGAYSINH,CMT_CU,CCCD,NGAYCAP,NOICAP,DIACHI,DIENTHOAI,SOTIEN,TOCHUCHOI,DONVI,POS,NGAYDANGKY) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"""
                #query  = "exec LEPHATDONG_INSERT @HOTEN=?,@NGAYSINH=?,@CMT_CU=?,@CCCD=?,@NGAYCAP=?,@DIACHI=?,@DIENTHOAI=?,@SOTIEN=?,@TOCHUCHOI=?,@DONVI=?"
        cursor.execute(query,para)
        cnxn.commit()
        #else:
        st.success(f"Cảm ơn bạn đã đăng ký:  {title}")
st.header(':white[Thống kê số liệu]', divider='rainbow')
click0=st.button("Xem số lượng khách hàng đã đăng ký")
if click0:
  colors = ['virginica', 'blue','red', 'green', 'yellow','aqua','azure','azure','beige','black','brown','cyan','darkblue','darkcyan','darkgreen','darkkhaki'
            ,'darkmagenta','darkolivegreen','darkorchid','darkred','darksalmon','darkviolet','fuchsia','gold','indigo','lightblue','navy']

  para = ()
  #query  = "select TOCHUCHOI N'Tổ chức hội',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY TOCHUCHOI"
  query  = "exec get_LPD_TOCHUCHOI"
  data=cursor.execute(query,para).fetchall()
  df = pd.DataFrame.from_records(
                    data=data,
                    columns=[column_info[0] for column_info in cursor.description],
                    coerce_float=True,
                    #Color= adjusted_colors
                )
  para0 = ()
  #query0  = "select POS N'Nơi gửi',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY POS"
  query0  = "exec get_LPD_THEOPOS"
  data0=cursor.execute(query0,para0).fetchall()
  df0 = pd.DataFrame.from_records(
                    data=data0,
                    columns=[column_info[0] for column_info in cursor.description],
                    coerce_float=True
                )
  para1 = ()
  #query1  = "select DONVI N'Đơn vị công tác',COUNT(CCCD) N'Số khách hàng' from LEPHATDONG where HOTEN is not null and TOCHUCHOI is not null GROUP BY DONVI order by DONVI"
  query1 = "exec get_LPD_THEODONVI"
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
          #adjusted_colors = colors[:len("Tổ chức hội")]
          st.write(df, theme="streamlit", use_container_width=True)
          color_discrete_map = {'virginica': 'blue', 'setosa': 'red', 'versicolor': 'green'}
          fig = px.bar(df, x='Tổ chức hội', y='Số khách hàng', title='Biểu đồ số lượng tổ chức hội', color=colors[:len(df['Tổ chức hội'])])#, color=['red', 'green', 'blue','orange'])

          # Displaying the Plotly chart in Streamlit
          st.plotly_chart(fig)
  with tab2:
          st.write(df0, theme=None, use_container_width=True)
          fig = px.bar(df0, x='Nơi gửi', y='Số khách hàng', title='Biểu đồ số lượng POS', color=colors[:len(df0['Nơi gửi'])] )
          st.plotly_chart(fig)
  with tab3:
          st.write(df1, theme=None, use_container_width=True)
          fig = px.bar(df1, x='Đơn vị công tác', y='Số khách hàng', title='Biểu đồ theo ĐVCT', color=colors[:len(df1['Đơn vị công tác'])] )
          st.plotly_chart(fig)
#connect close
#cursor.close()
  # with st.form("form2"):
  #   col1,col2=st.columns(2)
  #   col1.text_input("Họ và tên")
  #   col2.text_input("Năm sinh")
  #   st.form_submit_button("Đồng ý")
st.image('bbb.jpg', caption='Sản phẩm tiền gửi')
cnxn.close()