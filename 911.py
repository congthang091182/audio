import streamlit as st
# Page configuration
st.set_page_config(page_title="Hệ thống Báo cáo VBSP Lạng Sơn", page_icon="📊", layout="wide")
import pandas as pd
import pyodbc
import plotly.express as px
import datetime as dt
from datetime import datetime, timedelta
#from streamlit_cookies_manager import CookieManager
from extra_streamlit_components import CookieManager
from openpyxl import load_workbook
from io import BytesIO
import os
import uuid
#from reportlab.lib.pagesizes import A4  # Thay FPDF bằng reportlab
#from reportlab.pdfgen import canvas
#from reportlab.pdfbase import pdfmetrics
#from reportlab.pdfbase.ttfonts import TTFont
import base64  # Để nhúng PDF vào iframe

# Initialize Cookie Manager
try:
    cookies = CookieManager()
    # Kiểm tra phiên bản để xác định cách gọi get()
    import extra_streamlit_components
    if hasattr(extra_streamlit_components, '__version__'):
        # Phiên bản mới (>=0.1.60)
        remembered_user = cookies.get(key="remembered_user", default="")
        remember_me_flag = cookies.get(key="remember_me", default="False") == "True"
    else:
        # Phiên bản cũ
        remembered_user = cookies.get("remembered_user") or ""
        remember_me_flag = cookies.get("remember_me") == "True"
except Exception as e:
    st.warning(f"Không thể khởi tạo CookieManager: {e}")
    
    # Fallback implementation
    class LocalCookieManager:
        def __init__(self):
            self.cookies = {}
        
        def get(self, key, default=None):
            return self.cookies.get(key, default)
        
        def __setitem__(self, key, value):
            self.cookies[key] = value
    
    cookies = LocalCookieManager()
    remembered_user = ""
    remember_me_flag = False

# Import your custom functions
from def_N_fileXLS import write_to_excel_template9
from def_One_filexls import write_to_excel_template_one
from def_pos_to_xls import export_pos_to_excel
from def_pos_to_dvut_xls import export_pos_to_DVUT_excel
from def_tao_mat_khau import change_password_form

# Custom CSS (giữ nguyên)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
        font-family: 'Segoe UI', Tahoma, sans-serif;
    }
    .css-1d391kg {
        background-color: #2E86C1;
        color: white;
    }
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1E6BA8;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stTabs [aria-selected="false"] {
        background-color: #E8ECEF;
        color: #2E86C1;
        border-radius: 8px;
    }
    h1, h2, h3 {
        color: #2E86C1;
        font-weight: 600;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .login-counter {
        background-color: #2E86C1;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        animation: glow 2s infinite;
    }
    .login-counter::before {
        content: '👤';
        font-size: 24px;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px #2E86C1; }
        50% { box-shadow: 0 0 20px #2E86C1; }
        100% { box-shadow: 0 0 5px #2E86C1; }
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 14px;
        padding: 20px 0;
    }
    .sidebar .sidebar-content img {
        position: fixed;
        top: 10px;
        left: 10px;
        width: 150px;
        height: auto;
        transition: none !important;
        z-index: 999;
    }
    .sidebar .sidebar-content {
        overflow: hidden;
    }
    .login-logo {
        display: block;
        margin: 0 auto 20px auto;
        width: 150px;
        height: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Database connection function
def connect_to_sql_server():
    db_user = st.secrets["db_credentials"]["user"]
    db_password = st.secrets["db_credentials"]["password"]
    db_host = st.secrets["db_credentials"]["host"]
    db_database = st.secrets["db_credentials"]["Database"]
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={db_host};"
        f"DATABASE={db_database};"
        f"UID={db_user};"
        f"PWD={db_password};"
    )
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        st.error(f"Lỗi kết nối đến SQL Server: {e}")
        return None

# Login check function with login counter (giữ nguyên)
def check_login(username, password):
    cnxn = connect_to_sql_server()
    if cnxn:
        cursor = cnxn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM LoginHistory WHERE Username = ?", (username,))
        user_exists_in_history = cursor.fetchone()[0] > 0
        
        if not user_exists_in_history:
            cnxn.close()
            return None
        
        query = "exec get_web_login @username=?,@password=?"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            session_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO LoginHistory (Username, LoginTime, SessionID) VALUES (?, GETDATE(), ?)",
                (username, session_id)
            )
            cnxn.commit()
        cnxn.close()
        return user is not None
    return False

# Get login count (giữ nguyên)
def get_login_count():
    cnxn = connect_to_sql_server()
    if cnxn:
        cursor = cnxn.cursor()
        cursor.execute("SELECT COUNT(*) FROM LoginHistory")
        count = cursor.fetchone()[0]
        cnxn.close()
        return count
    return 0

# Handle Remember Me (giữ nguyên)
def handle_remember_me(username, remember_me):
    if remember_me:
        cookies["remembered_user"] = username
        cookies["remember_me"] = "True"
    else:
        cookies["remembered_user"] = ""
        cookies["remember_me"] = "False"

# Hàm tạo PDF từ DataFrame bằng reportlab
# def create_pdf_report(df, report_title, file_date_str):
#     pdf_output = BytesIO()
#     c = canvas.Canvas(pdf_output, pagesize=A4)
    
#     # Đăng ký font Times New Roman hỗ trợ Unicode
#     try:
#         pdfmetrics.registerFont(TTFont("Times", "times.ttf"))
#         c.setFont("Times", 12)
#     except Exception as e:
#         st.error(f"Lỗi khi tải font Times: {e}. Vui lòng kiểm tra file times.ttf trong thư mục.")
#         c.setFont("Helvetica", 12)  # Fallback về Helvetica nếu không có Times
    
    # Kích thước trang
    # width, height = A4
    # margin = 50
    # col_width = 100  # Độ rộng mỗi cột
    # row_height = 20   # Chiều cao mỗi dòng
    
    # # Tiêu đề
    # c.setFont("Times" if "Times" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 16)
    # c.drawCentredString(width / 2, height - margin, report_title)
    # c.setFont("Times" if "Times" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 12)
    # c.drawCentredString(width / 2, height - margin - 20, f"Ngày báo cáo: {file_date_str}")
    
    # # Vị trí bắt đầu bảng
    # y = height - margin - 60
    
    # # Tiêu đề cột
    # for i, col in enumerate(df.columns):
    #     c.drawString(margin + i * col_width, y, str(col))
    # y -= row_height
    # c.line(margin, y + 5, margin + len(df.columns) * col_width, y + 5)  # Đường kẻ ngang
    
    # # Dữ liệu
    # for index, row in df.iterrows():
    #     for i, item in enumerate(row):
    #         item_str = str(item)[:20]  # Giới hạn độ dài để tránh tràn
    #         c.drawString(margin + i * col_width, y, item_str)
    #     y -= row_height
    #     if y < margin:  # Nếu hết trang, tạo trang mới
    #         c.showPage()
    #         c.setFont("Times" if "Times" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 12)
    #         y = height - margin
    #         for i, col in enumerate(df.columns):
    #             c.drawString(margin + i * col_width, y, str(col))
    #         y -= row_height
    #         c.line(margin, y + 5, margin + len(df.columns) * col_width, y + 5)
    
    # # Hoàn thành PDF
    # c.showPage()
    # c.save()
    # pdf_output.seek(0)
    # return pdf_output

# Hàm hiển thị PDF trong iframe
def display_pdf(pdf_file):
    pdf_data = pdf_file.getvalue()
    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Enhanced Home Page
def home_page():
    st.markdown("<h1 style='text-align: center;'>Hệ thống Báo cáo VBSP Lạng Sơn</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Quản lý báo cáo hiệu quả - Dễ dàng - Chuyên nghiệp</p>", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("logo.png", width=150)
        st.markdown("<h3 style='color: white;'>Tùy chọn báo cáo</h3>", unsafe_allow_html=True)
        report_type = st.selectbox(
            "Loại báo cáo",
            ("Điện báo hàng ngày", "BC kết quả cho vay các chương trình tín dụng", "BC đơn vị ủy thác", "Thông tin điều hành", "Báo cáo khác"),
            key="report_type",
            help="Chọn loại báo cáo cần xem"
        )
        today = datetime.now()
        previous_date = today - timedelta(days=1)
        selected_date = st.date_input("Chọn ngày", previous_date, format="DD-MM-YYYY", key="selected_date")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if st.button("Đổi mật khẩu", key="change_password_btn"):
            st.session_state.show_change_password = True
        
        if st.button("Đăng xuất", key="logout"):
            handle_remember_me("", False)
            st.session_state.logged_in = False
            st.rerun()
        
        login_count = get_login_count()
        st.markdown(f"<div class='login-counter'>Lượt đăng nhập: {login_count}</div>", unsafe_allow_html=True)

    # Store selected values in session state
    st.session_state.current_report_type = report_type
    if isinstance(selected_date, dt.date):
        date_str = selected_date.strftime("%Y-%m-%d")
        st.session_state.current_date = date_str
        file_date_str = selected_date.strftime("%d_%m_%y")
    else:
        st.error("Ngày chọn không hợp lệ. Vui lòng chọn lại.")
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Báo cáo", "📈 Biểu đồ", "⚙️ Dashboard"])

    # Tab 1: Báo cáo
    with tab1:
        if st.session_state.show_change_password:
            change_password_form(st.session_state.username)
        else:
            cnxn = connect_to_sql_server()
            if cnxn:
                cursor = cnxn.cursor()
                date = st.session_state.current_date
                with st.spinner("Đang tải dữ liệu..."):
                    if st.session_state.current_report_type == "Điện báo hàng ngày":
                        try:
                            df = pd.read_sql("exec get_THA_SAVE_DIENBAO @NGAYBC=?", cnxn, params=[date])
                            #st.write("Dữ liệu thô từ SQL:", df)  # Debug dữ liệu
                            st.dataframe(df, use_container_width=True)
                            
                            # Tạo PDF
                            #pdf_file = create_pdf_report(df, "Điện báo hàng ngày", file_date_str)
                            
                            # Hiển thị PDF trong iframe
                            #st.subheader("Xem trước báo cáo PDF")
                            #display_pdf(pdf_file)
                            
                            # Nút "Tải xuống PDF"
                            # st.download_button(
                            #     label="Tải xuống PDF",
                            #     data=pdf_file,
                            #     file_name=f"Dienbaohangngay_{file_date_str}.pdf",
                            #     mime="application/pdf",
                            #     key="download_pdf_dienbao"
                            # )
                            
                            # Tùy chọn xuất Excel
                            query_page1 = "exec get_THA_SAVE_DIENBAO_xls @NGAYBC=?"
                            data_xls = pd.read_sql(query_page1, cnxn, params=[date])
                            query_page2 = "exec get_THA_SAVE_DIENBAO_PAGE2 @NGAYBC=?"
                            data_xls2 = pd.read_sql(query_page2, cnxn, params=[date])
                            query_page3 = "exec get_THA_SAVE_DIENBAO_PAGE3 @NGAYBC=?"
                            data_xls3 = pd.read_sql(query_page3, cnxn, params=[date])
                            query_page4 = "exec get_THA_SAVE_DIENBAO_PAGE4 @NGAYBC=?"
                            data_xls4 = pd.read_sql(query_page4, cnxn, params=[date])
                            query_page5 = "exec get_THA_SAVE_DIENBAO_PAGE5 @NGAYBC=?"
                            data_xls5 = pd.read_sql(query_page5, cnxn, params=[date])
                            query_page6 = "exec get_THA_SAVE_DIENBAO_PAGE6 @NGAYBC=?"
                            data_xls6 = pd.read_sql(query_page6, cnxn, params=[date])
                            if st.button("Xuất báo cáo Excel", key="export_dienbao"):
                                #template_path = 'FILE_MAU/Dien_bao_trang_01.XLSX'
                                template_path = 'Dien_bao_trang_01.XLSX'
                                output_file = f"Dienbaohangngay_{file_date_str}.xlsx"
                                try:
                                    write_to_excel_template9(template_path, data_xls, data_xls2, data_xls3, data_xls4, data_xls5, data_xls6, 15, 2, output_file)
                                    if os.path.exists(output_file):
                                        with open(output_file, "rb") as f:
                                            st.download_button("Tải xuống Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                        st.success("File Excel đã được tạo và sẵn sàng tải xuống!")
                                    else:
                                        st.error(f"Không tìm thấy file: {output_file}.")
                                except Exception as e:
                                    st.error(f"Lỗi khi tạo file Excel: {e}")
                        except Exception as e:
                            st.error(f"Lỗi khi truy vấn dữ liệu: {e}")
                    if st.session_state.current_report_type == "BC kết quả cho vay các chương trình tín dụng":
                        try:
                            df = pd.read_sql("exec get_THA_SAVE_BCHSCV @NGAYBC=?", cnxn, params=[date])
                            tenpgd = st.sidebar.multiselect(("Chọn PGD"), options=df["TENPGD"].unique(), default=df["TENPGD"].unique())
                            df_selection = df.query("TENPGD==@tenpgd ")
                            #st.write("Dữ liệu thô từ SQL:", df_selection)
                            st.write(df_selection)
                            
                            # Tạo PDF
                            #pdf_file = create_pdf_report(df_selection, "BC kết quả cho vay các chương trình tín dụng", file_date_str)
                            
                            # Hiển thị PDF trong iframe
                            #st.subheader("Xem trước báo cáo PDF")
                            #display_pdf(pdf_file)
                            
                            # Nút "Tải xuống PDF"
                            # st.download_button(
                            #     label="Tải xuống PDF",
                            #     data=pdf_file,
                            #     file_name=f"Bao_cao_hongheo_dtcs_{file_date_str}.pdf",
                            #     mime="application/pdf",
                            #     key="download_pdf_hscv"
                            # )
                            
                            left_colum, right_colum = st.columns(2)
                            with left_colum:  
                                if st.button("Xuất báo cáo Excel", key="export_dienbao_hscv"):
                                    #template_path = 'FILE_MAU/BC_HONGHEO_DTCS.XLSX'
                                    template_path = 'BC_HONGHEO_DTCS.XLSX'
                                    output_file = f"Bao_cao_hongheo_dtcs_{file_date_str}.xlsx"
                                    try:
                                        startrow = 15
                                        startcol = 1
                                        write_to_excel_template_one(template_path, df_selection, startrow, startcol, output_file)
                                        if os.path.exists(output_file):
                                            with open(output_file, "rb") as f:
                                                st.download_button("Tải xuống Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                            st.success("File Excel đã được tạo và sẵn sàng tải xuống!")
                                        else:
                                            st.error(f"Không tìm thấy file: {output_file}.")
                                    except Exception as e:
                                        st.error(f"Lỗi khi tạo file Excel: {e}")
                            with right_colum:
                                if st.button("Xuất báo cáo Excel (Tất cả POS)"):
                                    template_path = 'BC_HONGHEO_DTCS.XLSX'
                                    output_file = f"Bao_cao_hongheo_dtcs_{file_date_str}.xlsx"
                                    try:
                                        startrow = 15
                                        startcol = 1
                                        export_pos_to_excel(df_selection, template_path, output_file)
                                        if os.path.exists(output_file):
                                            with open(output_file, "rb") as f:
                                                st.download_button("Tải xuống Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                            st.success("File Excel đã được tạo và sẵn sàng tải xuống!")
                                        else:
                                            st.error(f"Không tìm thấy file: {output_file}.")
                                    except Exception as e:
                                        st.error(f"Lỗi khi tạo file Excel: {e}")            
                        except Exception as e:
                            st.error(f"Lỗi khi truy vấn dữ liệu: {e}")  
                    if st.session_state.current_report_type == "BC đơn vị ủy thác":
                        try:
                            df = pd.read_sql("exec get_THA_SAVE_BCDVUT @NGAYBC=?", cnxn, params=[date])
                            tenpgd = st.sidebar.multiselect(("Chọn PGD"), options=df["TENPGD"].unique(), default=df["TENPGD"].unique())
                            df_selection = df.query("TENPGD==@tenpgd ")
                            #st.write("Dữ liệu thô từ SQL:", df_selection)
                            st.write(df_selection)
                            
                            # Tạo PDF
                            #pdf_file = create_pdf_report(df_selection, "BC đơn vị ủy thác", file_date_str)
                            
                            # Hiển thị PDF trong iframe
                            #st.subheader("Xem trước báo cáo PDF")
                            #display_pdf(pdf_file)
                            
                            # Nút "Tải xuống PDF"
                            # st.download_button(
                            #     label="Tải xuống PDF",
                            #     data=pdf_file,
                            #     file_name=f"Bao_cao_theo_DVUT_{file_date_str}.pdf",
                            #     mime="application/pdf",
                            #     key="download_pdf_dvut"
                            # )
                            
                            left_colum, right_colum = st.columns(2)
                            with left_colum:  
                                if st.button("Xuất báo cáo Excel", key="export_dienbao_dvut"):
                                    #template_path = 'FILE_MAU/BC_TOCHUCHOI_M01.XLSX'
                                    template_path = 'BC_TOCHUCHOI_M01.XLSX'
                                    output_file = f"Bao_cao_theo_DVUT_{file_date_str}.xlsx"
                                    try:
                                        startrow = 15
                                        startcol = 1
                                        write_to_excel_template_one(template_path, df_selection, startrow, startcol, output_file)
                                        if os.path.exists(output_file):
                                            with open(output_file, "rb") as f:
                                                st.download_button("Tải xuống Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                            st.success("File Excel đã được tạo và sẵn sàng tải xuống!")
                                        else:
                                            st.error(f"Không tìm thấy file: {output_file}.")
                                    except Exception as e:
                                        st.error(f"Lỗi khi tạo file Excel: {e}")
                            with right_colum:
                                if st.button("Xuất báo cáo Excel (Tất cả POS)"):
                                    #template_path = 'FILE_MAU/BC_TOCHUCHOI_M01.XLSX'
                                    template_path = 'BC_TOCHUCHOI_M01.XLSX'
                                    output_file = f"Bao_cao_theo_DVUT_{file_date_str}.xlsx"
                                    try:
                                        startrow = 15
                                        startcol = 1
                                        export_pos_to_DVUT_excel(df_selection, template_path, output_file)
                                        if os.path.exists(output_file):
                                            with open(output_file, "rb") as f:
                                                st.download_button("Tải xuống Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                            st.success("File Excel đã được tạo và sẵn sàng tải xuống!")
                                        else:
                                            st.error(f"Không tìm thấy file: {output_file}.")
                                    except Exception as e:
                                        st.error(f"Lỗi khi tạo file Excel: {e}")            
                        except Exception as e:
                            st.error(f"Lỗi khi truy vấn dữ liệu: {e}")
                cnxn.close()

    # Tab 2: Biểu đồ (giữ nguyên)
    with tab2:
        st.markdown("<div class='card'><h2>Biểu đồ phân tích</h2>", unsafe_allow_html=True)
        if st.session_state.current_report_type == "Điện báo hàng ngày":
            cnxn = connect_to_sql_server()
            if cnxn:
                with st.spinner("Đang tạo biểu đồ..."):
                    try:
                        df_nqh = pd.read_sql("exec get_THA_SAVE_DIENBAO_NQH @NGAYBC=?", cnxn, params=[st.session_state.current_date])
                        color_map = {"Thành phố": "red", "Cao Lộc": "green", "Lộc Bình": "blue", "Đình lập": "orange"}
                        fig1 = px.bar(df_nqh, x="TENPGD", y="QHAN", title="Dư nợ quá hạn theo đơn vị", 
                                      color="TENPGD", color_discrete_map=color_map, barmode="group")
                        st.plotly_chart(fig1, use_container_width=True)
                    except Exception as e:
                        st.error(f"Lỗi khi tạo biểu đồ: {e}")
                cnxn.close()
            else:
                st.error("Không thể kết nối để tạo biểu đồ.")
        else:
            st.info("Chọn 'Điện báo hàng ngày' để xem biểu đồ.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 3: Dashboard (giữ nguyên)
    with tab3:
        st.markdown("<div class='card'><h2>Dashboard (Đang phát triển)</h2>", unsafe_allow_html=True)
        st.write("Chức năng này sẽ được cập nhật trong tương lai.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer (giữ nguyên)
    st.markdown("""
        <div class='footer'>
            © 2025 Hệ thống Báo cáo VBSP Lạng Sơn | Phát triển bởi Vi Công Thắng, PTP Tin học Chi nhánh Lạng Sơn<br>
            <a href='https://www.facebook.com/profile.php?id=100083312079198'>Fanpage</a> | 
            <a href='https://vbsp.org.vn/gioi-thieu/lai-suat-huy-dong.html'>Lãi suất</a> | 
            <a href='https://vbsp.org.vn/gioi-thieu/co-cau-to-chuc/diem-giao-dich-xa-phuong.html'>Điểm giao dịch</a>|
            <a href='https://www.youtube.com/watch?v=YA74YE1bw1k'>Lạng Sơn tiên cảnh</a>
        </div>
    """, unsafe_allow_html=True)

# Enhanced Login Page with Centered Logo (giữ nguyên)
def login_page():
    st.markdown("<h1 style='text-align: center;'>Đăng nhập</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Chào mừng đến với Hệ thống Báo cáo VBSP Lạng Sơn</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        try:
            # Sử dụng cách gọi phù hợp với phiên bản mới
            remembered_user = cookies.get(key="remembered_user", default="")
            remember_me_flag = cookies.get(key="remember_me", default="False") == "True"
        except:
            remembered_user = ""
            remember_me_flag = False
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", value=remembered_user, key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            remember_me = st.checkbox("Ghi nhớ đăng nhập", value=remember_me_flag, key="remember_me")
            submit = st.form_submit_button("Đăng nhập", type="primary")
        
        if submit:
            login_result = check_login(username, password)
            if login_result is None:
                st.session_state.username = username
                st.session_state.show_new_password_form = True
                st.rerun()
            elif login_result:
                try:
                    if remember_me:
                        cookies["remembered_user"] = username
                        cookies["remember_me"] = "True"
                    else:
                        cookies["remembered_user"] = ""
                        cookies["remember_me"] = "False"
                except:
                    pass
                
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Tên đăng nhập hoặc mật khẩu không đúng!")

# Session state initialization (giữ nguyên)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_new_password_form" not in st.session_state:
    st.session_state.show_new_password_form = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "show_change_password" not in st.session_state:
    st.session_state.show_change_password = False

# Main logic (giữ nguyên)
if st.session_state.logged_in:
    home_page()
elif st.session_state.show_new_password_form:
    change_password_form(st.session_state.username)
else:
    login_page()