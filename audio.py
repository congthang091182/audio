import streamlit as st
st.title('Ngân hàng chính sách tôi yêu')
st.title('Nhạc: Xuân Hòa')
st.title('Thơ: Dương Quyết Thắng')
st.audio('Ngan Hang Chinh Sach - Top Nam Nu.mp3', loop=True)

with open("Ngan Hang Chinh Sach - Top Nam Nu.mp3", "rb") as file:
    btn = st.download_button(
            label="Download mp3",
             data = file.read(),
             file_name="Ngan Hang Chinh Sach - Top Nam Nu.mp3"
          )
st.video('Ngân Hàng Chính Sách Tôi Yêu  Tốp Nam Nữ_v720P.mp4')
with open("Ngân Hàng Chính Sách Tôi Yêu  Tốp Nam Nữ_v720P.mp4", "rb") as file:
    btn = st.download_button(
            label="Download mp4",
             data = file.read(),
             file_name="Ngân Hàng Chính Sách Tôi Yêu  Tốp Nam Nữ_v720P.mp4"
          )
st.sidebar.markdown('![Visitor count](http://10.22.0.234:8502)')