import streamlit as st
st.set_page_config(page_title="Hệ thống Báo cáo VBSP Lạng Sơn", page_icon="📊", layout="wide")
import pandas as pd
import sqlalchemy as sa
from urllib.parse import quote_plus
import plotly.express as px
from datetime import datetime, timedelta
from extra_streamlit_components import CookieManager
from openpyxl import load_workbook
from io import BytesIO
import os
import uuid
import base64
import time
import bcrypt  # Thêm import bcrypt
# Custom functions import
from def_N_fileXLS import write_to_excel_template9
from def_One_filexls import write_to_excel_template_one
from def_pos_to_xls import export_pos_to_excel
from def_pos_to_dvut_xls import export_pos_to_DVUT_excel
from def_tao_mat_khau import change_password_form
from def_export_pdf import export_to_pdf  # Import hàm xuất PDF

# Custom CSS (giữ nguyên)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%); font-family: 'Segoe UI', Tahoma, sans-serif; }
    .css-1d391kg { background-color: #2E86C1; color: white; }
    .stButton>button { background-color: #2E86C1; color: white; border-radius: 10px; padding: 10px 20px; font-weight: bold; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #1E6BA8; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [aria-selected="true"] { background-color: #2E86C1; color: white; border-radius: 8px; font-weight: bold; }
    .stTabs [aria-selected="false"] { background-color: #E8ECEF; color: #2E86C1; border-radius: 8px; }
    h1, h2, h3 { color: #2E86C1; font-weight: 600; }
    .card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }
    .login-counter { background-color: #2E86C1; color: white; padding: 10px 20px; border-radius: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); font-size: 18px; font-weight: bold; text-align: center; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 10px; animation: glow 2s infinite; }
    .login-counter::before { content: '👤'; font-size: 24px; }
    @keyframes glow { 0% { box-shadow: 0 0 5px #2E86C1; } 50% { box-shadow: 0 0 20px #2E86C1; } 100% { box-shadow: 0 0 5px #2E86C1; } }
    .footer { text-align: center; color: #666; font-size: 14px; padding: 20px 0; }
    .sidebar .sidebar-content img { position: fixed; top: 10px; left: 10px; width: 150px; height: auto; z-index: 999; }
    </style>
""", unsafe_allow_html=True)

# Cookie Manager Initialization
def init_cookie_manager():
    """Khởi tạo CookieManager hoặc fallback nếu lỗi."""
    try:
        cookies = CookieManager()
        # Kiểm tra phiên bản và sử dụng cách gọi phù hợp
        import extra_streamlit_components
        if hasattr(extra_streamlit_components, '__version__') and extra_streamlit_components.__version__ >= '0.1.60':
            remembered_user = cookies.get("remembered_user") or ""
            remember_me_flag = cookies.get("remember_me") == "True"
        else:
            remembered_user = cookies.get("remembered_user") or ""
            remember_me_flag = cookies.get("remember_me") == "True"
    except Exception as e:
        st.warning(f"Không thể khởi tạo CookieManager: {e}")
        class LocalCookieManager:
            def __init__(self): self.cookies = {}
            def get(self, key): return self.cookies.get(key, "")
            def set(self, key, value, **kwargs): self.cookies[key] = value
            def __setitem__(self, key, value): self.cookies[key] = value
        cookies = LocalCookieManager()
        remembered_user = ""
        remember_me_flag = False
    return cookies, remembered_user, remember_me_flag

cookies, remembered_user, remember_me_flag = init_cookie_manager()

# Database Connection with SQLAlchemy
def get_db_engine():
    """Tạo engine SQLAlchemy để kết nối SQL Server."""
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={st.secrets['db_credentials']['host']};"
            f"DATABASE={st.secrets['db_credentials']['Database']};"
            f"UID={st.secrets['db_credentials']['user']};"
            f"PWD={st.secrets['db_credentials']['password']};"
        )
        connection_string_encoded = quote_plus(connection_string)
        sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={connection_string_encoded}"
        engine = sa.create_engine(sqlalchemy_url)
        return engine
    except Exception as e:
        st.error(f"Lỗi kết nối đến SQL Server: {e}")
        return None

# Login Functions
def check_login(username, password):
    """Kiểm tra đăng nhập và ghi lại lịch sử nếu thành công."""
    engine = get_db_engine()
    if not engine:
        return False
    
    with engine.connect() as conn:
        result = conn.execute(
            sa.text("SELECT macb, matkhau, TRANGTHAI FROM loggin WHERE macb = :username"),
            {"username": username}
        ).fetchone()
        
        if not result:
            st.error("Tên đăng nhập không tồn tại!")
            time.sleep(5)
            return False
        
        stored_username, stored_hash, trangthai = result
        
        # Kiểm tra định dạng chuỗi băm
        if not isinstance(stored_hash, str) or not stored_hash.startswith('$2'):
            st.error("Mật khẩu trong cơ sở dữ liệu không hợp lệ. Vui lòng reset mật khẩu.")
            time.sleep(5)
            return False
        
        # Chuyển stored_hash thành bytes
        try:
            stored_hash_bytes = stored_hash.encode('utf-8')
        except Exception as e:
            st.error(f"Lỗi khi chuyển đổi chuỗi băm: {e}")
            time.sleep(5)
            return False
        
        # Kiểm tra mật khẩu bằng bcrypt
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                st.error("Mật khẩu không đúng!")
                time.sleep(5)
                return False
        except ValueError as e:
            st.error(f"Lỗi kiểm tra mật khẩu: {e}")
            time.sleep(5)
            return False
        
        if trangthai != 'A':
            st.error("Tài khoản chưa được cấp quyền đăng nhập!")
            time.sleep(5)
            return False
        
        login_count = conn.execute(
            sa.text("SELECT COUNT(*) FROM LoginHistory WHERE Username = :username"),
            {"username": username}
        ).scalar()
        
        if login_count == 0:
            return None
        
        session_id = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO LoginHistory (Username, LoginTime, SessionID) VALUES (:username, GETDATE(), :session_id)"),
            {"username": username, "session_id": session_id}
        )
        conn.commit()
        
        return True

def get_login_count():
    """Lấy tổng số lượt đăng nhập từ LoginHistory."""
    engine = get_db_engine()
    if engine:
        with engine.connect() as conn:
            return conn.execute(sa.text("SELECT COUNT(*) FROM LoginHistory")).scalar()
    return 0

def handle_remember_me(username, remember_me):
    """Xử lý lưu thông tin đăng nhập vào cookie với key duy nhất."""
    if hasattr(cookies, 'set'):
        if remember_me:
            cookies.set("remembered_user", username, key="set_remembered_user")
            cookies.set("remember_me", "True", key="set_remember_me_true")
        else:
            cookies.set("remembered_user", "", key="set_remembered_user_clear")
            cookies.set("remember_me", "False", key="set_remember_me_false")
    else:
        cookies["remembered_user"] = username if remember_me else ""
        cookies["remember_me"] = "True" if remember_me else "False"

# Data Processing and Export
def fetch_report_data(engine, report_type, date):
    """Lấy dữ liệu báo cáo từ database dựa trên loại báo cáo và xử lý cột trùng lặp."""
    queries = {
        "Điện báo hàng ngày": "exec get_THA_SAVE_DIENBAO @NGAYBC=:date",
        "BC kết quả cho vay các chương trình tín dụng": "exec get_THA_SAVE_BCHSCV @NGAYBC=:date",
        "BC đơn vị ủy thác": "exec get_THA_SAVE_BCDVUT @NGAYBC=:date"
    }
    query = queries.get(report_type)
    if not query:
        st.info("Loại báo cáo này chưa được hỗ trợ.")
        return None
    try:
        with engine.connect() as conn:
            df = pd.read_sql(sa.text(query), conn, params={"date": date})
            if df.empty:
                st.warning("Dữ liệu trả về rỗng.")
                return None
            # Kiểm tra và đổi tên cột trùng lặp
            if df.columns.duplicated().any():
                st.warning(f"Các cột trùng lặp được tìm thấy: {df.columns[df.columns.duplicated()].tolist()}")
                new_columns = []
                column_count = {}
                for col in df.columns:
                    if col in column_count:
                        column_count[col] += 1
                        new_columns.append(f"{col}_{column_count[col]}")
                    else:
                        column_count[col] = 0
                        new_columns.append(col)
                df.columns = new_columns
                st.info("Đã đổi tên các cột trùng lặp.")
            return df
    except Exception as e:
        st.error(f"Lỗi khi truy vấn dữ liệu: {e}")
        return None

def export_to_excel(df, report_type, template_path, output_file, engine=None, date=None, multi_file=False):
    """Xuất dữ liệu ra file Excel dựa trên template."""
    if not os.path.exists(template_path):
        st.error(f"File mẫu không tồn tại tại: {template_path}")
        return False
    try:
        if multi_file and engine and date:
            with engine.connect() as conn:
                extra_dfs = []
                for i in range(2, 7):
                    df_temp = pd.read_sql(sa.text(f"exec get_THA_SAVE_DIENBAO_PAGE{i} @NGAYBC=:date"), conn, params={"date": date})
                    if df_temp is None or df_temp.empty:
                        st.warning(f"Không có dữ liệu cho trang {i} của Điện báo hàng ngày.")
                        return False
                    # Kiểm tra và đổi tên cột trùng lặp cho extra_dfs
                    if df_temp.columns.duplicated().any():
                        st.warning(f"Các cột trùng lặp được tìm thấy trong extra_df {i}: {df_temp.columns[df_temp.columns.duplicated()].tolist()}")
                        new_columns = []
                        column_count = {}
                        for col in df_temp.columns:
                            if col in column_count:
                                column_count[col] += 1
                                new_columns.append(f"{col}_{column_count[col]}")
                            else:
                                column_count[col] = 0
                                new_columns.append(col)
                        df_temp.columns = new_columns
                        st.info(f"Đã đổi tên các cột trùng lặp trong extra_df {i}.")
                    extra_dfs.append(df_temp)
            # Debug trước khi gọi write_to_excel_template9
            #st.write("Debug df:", type(df), df.head())
            #for i, extra_df in enumerate(extra_dfs):
                #st.write(f"Debug extra_df {i+1}:", type(extra_df), extra_df.head())
            write_to_excel_template9(template_path, df, *extra_dfs, startrow=15, startcol=2, output_path=output_file)
        else:
            # Debug trước khi gọi write_to_excel_template_one
            #st.write("Debug df:", type(df), df.head())
            write_to_excel_template_one(template_path, df, startrow=15, startcol=1, output_path=output_file)
        return True
    except AttributeError as e:
        st.error(f"Lỗi khi tạo file Excel: Kiểm tra DataFrame - {e}")
        return False
    except Exception as e:
        st.error(f"Lỗi khi tạo file Excel: {e}")
        return False

def export_to_excel_pos(df, report_type, template_path, output_file):
    """Xuất dữ liệu ra file Excel cho POS."""
    if not os.path.exists(template_path):
        st.error(f"File mẫu không tồn tại tại: {template_path}")
        return False
    try:
        if report_type == "BC kết quả cho vay các chương trình tín dụng":
            export_pos_to_excel(df, template_path, output_file)
        else:
            export_pos_to_DVUT_excel(df, template_path, output_file)
        return True
    except AttributeError as e:
        st.error(f"Lỗi khi tạo file Excel POS: Kiểm tra DataFrame - {e}")
        return False
    except Exception as e:
        st.error(f"Lỗi khi tạo file Excel POS: {e}")
        return False

def render_download_button(output_file, mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
    """Hiển thị nút tải file (Excel hoặc PDF)."""
    if os.path.exists(output_file):
        with open(output_file, "rb") as f:
            st.download_button(f"Tải xuống {os.path.splitext(output_file)[1][1:].upper()}", f, file_name=output_file, mime=mime_type)
        st.success(f"File {os.path.splitext(output_file)[1][1:].upper()} đã được tạo!")
    else:
        st.error(f"Không tìm thấy file: {output_file}")

# Home Page
def home_page():
    """Trang chính của ứng dụng sau khi đăng nhập."""
    st.markdown("<h1 style='text-align: center;'>Hệ thống Báo cáo VBSP Lạng Sơn</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Quản lý báo cáo hiệu quả - Dễ dàng - Chuyên nghiệp</p>", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("logo.png", width=150)
        st.markdown("<h3 style='color: white;'>Tùy chọn báo cáo</h3>", unsafe_allow_html=True)
        report_type = st.selectbox("Loại báo cáo", ("Điện báo hàng ngày", "BC kết quả cho vay các chương trình tín dụng", "BC đơn vị ủy thác", "Thông tin điều hành", "Báo cáo khác"), key="report_type")
        selected_date = st.date_input("Chọn ngày", datetime.now() - timedelta(days=1), format="DD-MM-YYYY", key="selected_date")
        st.markdown("<hr>", unsafe_allow_html=True)
        st.button("Đổi mật khẩu", key="change_password_btn", on_click=lambda: st.session_state.update(show_change_password=True))
        st.button("Đăng xuất", key="logout", on_click=lambda: [handle_remember_me("", False), st.session_state.update(logged_in=False), st.rerun()])
        st.markdown(f"<div class='login-counter'>Lượt đăng nhập: {get_login_count()}</div>", unsafe_allow_html=True)

    # Session state
    date_str = selected_date.strftime("%Y-%m-%d")
    file_date_str = selected_date.strftime("%d_%m_%y")
    st.session_state.update(current_report_type=report_type, current_date=date_str)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Báo cáo", "📈 Biểu đồ", "⚙️ Dashboard"])

    with tab1:
        if st.session_state.get("show_change_password", False):
            change_password_form(st.session_state.username)
        else:
            engine = get_db_engine()
            if not engine:
                return
            with st.spinner("Đang tải dữ liệu..."):
                df = fetch_report_data(engine, report_type, date_str)
                if df is None or df.empty:
                    st.warning("Không có dữ liệu cho ngày đã chọn.")
                    return

                # Filter for multi-select reports
                if report_type in ["BC kết quả cho vay các chương trình tín dụng", "BC đơn vị ủy thác"]:
                    tenpgd = st.sidebar.multiselect("Chọn PGD", options=df["TENPGD"].unique(), default=df["TENPGD"].unique())
                    df = df[df["TENPGD"].isin(tenpgd)]
                    if df.empty:
                        st.warning("Không có dữ liệu cho PGD đã chọn.")
                        return

                st.dataframe(df, use_container_width=True)

                # Export options
                templates = {
                    "Điện báo hàng ngày": "Dien_bao_trang_01.xlsx",
                    "BC kết quả cho vay các chương trình tín dụng": "BC_HONGHEO_DTCS.xlsx",
                    "BC đơn vị ủy thác": "BC_TOCHUCHOI_M01.xlsx"
                }
                output_file_excel = f"{report_type.replace(' ', '_')}_{file_date_str}.xlsx"
                output_file_pdf = f"{report_type.replace(' ', '_')}_{file_date_str}.pdf"
                template_path = templates.get(report_type, "")

                # Thêm lựa chọn cột cho PDF
                st.markdown("### Tùy chỉnh cột cho báo cáo PDF")
                selected_columns = st.multiselect(
                    "Chọn cột để xuất PDF",
                    options=df.columns.tolist(),
                    default=df.columns.tolist()[:3],  # Mặc định chọn 3 cột đầu tiên
                    key=f"select_columns_{report_type}"
                )

                col1, col2, col3 = st.columns(3)  # Thêm cột cho nút PDF
                with col1:
                    if st.button("Xuất báo cáo Excel", key=f"export_{report_type}"):
                        if export_to_excel(df, report_type, template_path, output_file_excel, engine, date_str, multi_file=report_type == "Điện báo hàng ngày"):
                            render_download_button(output_file_excel)
                with col2:
                    if report_type in ["BC kết quả cho vay các chương trình tín dụng", "BC đơn vị ủy thác"] and st.button("Xuất Excel (Tất cả POS)", key=f"export_pos_{report_type}"):
                        if export_to_excel_pos(df, report_type, template_path, output_file_excel):
                            render_download_button(output_file_excel)
                with col3:
                    # Khởi tạo trạng thái để kiểm soát việc tạo PDF
                    if "pdf_generated" not in st.session_state:
                        st.session_state.pdf_generated = False

                    # Thêm tùy chọn bỏ qua biểu đồ
                    include_chart = st.checkbox("Bao gồm biểu đồ trong PDF", value=True, key=f"include_chart_{report_type}")

                    if st.button("Xuất báo cáo PDF", key=f"export_pdf_{report_type}"):
                        if not selected_columns:
                            st.warning("Vui lòng chọn ít nhất một cột để xuất PDF.")
                        else:
                            # Debug: Hiển thị kiểu dữ liệu của các cột được chọn
                            # st.write("Kiểu dữ liệu của các cột được chọn:")
                            # for col in selected_columns:
                            #     st.write(f"{col}: {df[col].dtype}")
                            # # Debug: Hiển thị một số dòng dữ liệu
                            # st.write("Dữ liệu mẫu:", df[selected_columns].head())
            
                            # Hiển thị spinner trong khi tạo PDF
                            with st.spinner("Đang tạo báo cáo PDF..."):
                                start_time = time.time()
                                pdf_buffer = export_to_pdf(df, selected_columns, f"Báo cáo: {report_type}", output_file_pdf, include_chart=include_chart)
                                end_time = time.time()
                                st.session_state.pdf_buffer = pdf_buffer  # Lưu buffer vào trạng thái
                                st.session_state.pdf_generated = True  # Đánh dấu đã tạo PDF
                                st.session_state.pdf_time = end_time - start_time  # Lưu thời gian xử lý

            # Hiển thị nút tải xuống nếu PDF đã được tạo
            if st.session_state.pdf_generated:
                st.download_button(
                    label="Tải xuống PDF",
                    data=st.session_state.pdf_buffer,
                    file_name=output_file_pdf,
                    mime="application/pdf"
                )
                st.success(f"File PDF đã được tạo! Thời gian xử lý: {st.session_state.pdf_time:.2f} giây.")
                # Reset trạng thái sau khi tải xuống
                if st.button("Tạo PDF mới", key=f"reset_pdf_{report_type}"):
                   st.session_state.pdf_generated = False

    with tab2:
        st.markdown("<div class='card'><h2>Biểu đồ phân tích</h2>", unsafe_allow_html=True)
        if report_type == "Điện báo hàng ngày":
            engine = get_db_engine()
            if engine:
                with st.spinner("Đang tạo biểu đồ..."):
                    with engine.connect() as conn:
                        df_nqh = pd.read_sql(sa.text("exec get_THA_SAVE_DIENBAO_NQH @NGAYBC=:date"), conn, params={"date": date_str})
                    if not df_nqh.empty:
                        fig = px.bar(df_nqh, x="TENPGD", y="QHAN", title="Dư nợ quá hạn theo đơn vị", color="TENPGD", 
                                     color_discrete_map={"Thành phố": "red", "Cao Lộc": "green", "Lộc Bình": "blue", "Đình lập": "orange"}, barmode="group")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Không có dữ liệu để tạo biểu đồ.")
        else:
            st.info("Chọn 'Điện báo hàng ngày' để xem biểu đồ.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='card'><h2 style='text-align: center;'>Dashboard Báo cáo</h2>", unsafe_allow_html=True)
        
        # CSS hiện đại hóa với viền cho các nhóm
        st.markdown("""
            <style>
            .metric-card {
                background: linear-gradient(135deg, #2E86C1 0%, #87CEEB 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                text-align: center;
                margin: 10px 0;
                transition: transform 0.3s ease;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
            }
            .metric-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; }
            .metric-value { font-size: 20px; font-weight: 600; }
            .highlight-overdue {
                background: linear-gradient(135deg, #FF6347 0%, #FF9980 100%);
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { box-shadow: 0 0 5px #FF6347; }
                50% { box-shadow: 0 0 20px #FF6347; }
                100% { box-shadow: 0 0 5px #FF6347; }
            }
            /* Thêm viền và kiểu dáng cho nhóm */
            .metric-group {
                border: 2px solid #2E86C1;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: rgba(255, 255, 255, 0.9);
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }
            .group-title {
                font-size: 18px;
                font-weight: bold;
                color: #2E86C1;
                margin-bottom: 15px;
                text-align: center;
            }
            </style>
        """, unsafe_allow_html=True)
        
        engine = get_db_engine()
        if not engine:
            st.error("Không thể kết nối tới cơ sở dữ liệu!")
            return
        
        date_str = st.session_state.current_date
        report_type = st.session_state.current_report_type
        
        with st.spinner("Đang tải dữ liệu Dashboard..."):
            # Lấy dữ liệu báo cáo
            df = fetch_report_data(engine, report_type, date_str)
            if df is None or df.empty:
                st.warning("Không có dữ liệu để hiển thị Dashboard.")
                return
            
            # --- Nhóm 1: Cho vay và Thu nợ ---
            st.markdown("<div class='metric-group'><div class='group-title'>Cho vay và Thu nợ</div>", unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns(5)
            metrics_group1 = [
                ("Cho vay", "CHOVAY", "#32CD32"),
                ("Thu nợ", "THUNO", "#87CEEB"),
                ("Tăng giảm Dư nợ", "TG_DUNO", "#5f9ea0"),
                ("Tăng giảm NQH", "TG_QHAN", "#008b8b"),
                ("Tăng giảm khoanh", "TG_KHOANH", "#bdb76b")
            ]
            for i, (label, column, color) in enumerate(metrics_group1):
                with [col1, col2, col3, col4, col5][i]:
                    if column in df.columns:
                        total_value = df[column].sum()
                        st.markdown(
                            f"""
                            <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, #FFFFFF 100%);">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{total_value:,.0f} VNĐ</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- Nhóm 2: Kế hoạch, Dư nợ, Còn phải thực hiện, Tỷ lệ hoàn thành ---
            st.markdown("<div class='metric-group'><div class='group-title'>Kế hoạch và Dư nợ</div>", unsafe_allow_html=True)
            col6, col7, col8, col9 = st.columns(4)
            metrics_group2 = [
                ("Kế hoạch", "TONG_KH", "#2E86C1"),
                ("Dư nợ", "DUNO", "#4682B4"),
                ("Còn phải thực hiện", "CPTHUCHIEN", "#ADD8E6"),
                ("Tỷ lệ hoàn thành", "TYLE", "#FFD700")
            ]
            for i, (label, column, color) in enumerate(metrics_group2):
                with [col6, col7, col8, col9][i]:
                    if column in df.columns:
                        if column == "TYLE":
                            total_value = df[column].mean()
                            value_display = f"{total_value:.2f}%"
                        else:
                            total_value = df[column].sum()
                            value_display = f"{total_value:,.0f} VNĐ"
                        st.markdown(
                            f"""
                            <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, #FFFFFF 100%);">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{value_display}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- Nhóm 3: Chỉ thị 40 ---
            st.markdown("<div class='metric-group'><div class='group-title'>Chỉ thị 40</div>", unsafe_allow_html=True)
            col10, col11, col12, col13 = st.columns(4)
            metrics_group3 = [
                ("Kế hoạch CT40", "KH_CHITHI40", "#FF6347", "highlight-overdue"),
                ("Thực hiện CT40", "TH_CHITHI40", "#FFA500"),
                ("Còn phải thực hiện CT40", "CP_THCT40", "#6495ed"),
                ("Lũy kế số dư CT40", "LK_CT40", "#ff1493")
            ]
            for i, (label, column, color, *extra_class) in enumerate(metrics_group3):
                with [col10, col11, col12, col13][i]:
                    if column in df.columns:
                        total_value = df[column].sum()
                        class_name = "metric-card " + (extra_class[0] if extra_class else "")
                        st.markdown(
                            f"""
                            <div class="{class_name}" style="background: linear-gradient(135deg, {color} 0%, #FFFFFF 100%);">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{total_value:,.0f} VNĐ</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- Nhóm 4: Nợ quá hạn và Nợ khoanh ---
            st.markdown("<div class='metric-group'><div class='group-title'>Nợ quá hạn và Nợ khoanh</div>", unsafe_allow_html=True)
            col15, col16 = st.columns(2)
            metrics_group4 = [
                ("Nợ quá hạn", "QHAN", "#FF6347", "highlight-overdue"),
                ("Nợ khoanh", "KHOANH", "#FFA500")
            ]
            for i, (label, column, color, *extra_class) in enumerate(metrics_group4):
                with [col15, col16][i]:
                    if column in df.columns:
                        total_value = df[column].sum()
                        class_name = "metric-card " + (extra_class[0] if extra_class else "")
                        st.markdown(
                            f"""
                            <div class="{class_name}" style="background: linear-gradient(135deg, {color} 0%, #FFFFFF 100%);">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{total_value:,.0f} VNĐ</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- Biểu đồ cột: Nợ quá hạn và Nợ khoanh cùng nhau ---
            df_sorted_combined = df.sort_values(by=["QHAN", "KHOANH"], ascending=False)
            fig_bar_combined = px.bar(
                df_sorted_combined,
                x="TENPGD",
                y=["QHAN", "KHOANH"],
                title="Nợ quá hạn và Nợ khoanh theo PGD (Sắp xếp giảm dần)",
                barmode="group",
                color_discrete_map={"QHAN": "#FF6347", "KHOANH": "#FFA500"},
                text_auto=True,
                height=450
            )
            fig_bar_combined.update_traces(
                textposition="auto",
                marker=dict(line=dict(width=1, color="#FFFFFF"))
            )
            fig_bar_combined.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=14),
                title_font_size=20
            )
            st.plotly_chart(fig_bar_combined, use_container_width=True, key="chart_combined_qhan_khoanh")
            
            # --- Biểu đồ cột: Nợ quá hạn riêng ---
            df_sorted_qhan = df.sort_values(by="QHAN", ascending=False)
            fig_bar_qhan = px.bar(
                df_sorted_qhan,
                x="TENPGD",
                y="QHAN",
                title="Nợ quá hạn theo PGD (Sắp xếp giảm dần)",
                color="TENPGD",
                color_discrete_sequence=px.colors.sequential.Reds,
                text_auto=True,
                height=450
            )
            fig_bar_qhan.update_traces(
                textposition="auto",
                marker=dict(line=dict(width=1, color="#FFFFFF"))
            )
            fig_bar_qhan.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=14),
                title_font_size=20
            )
            st.plotly_chart(fig_bar_qhan, use_container_width=True, key="chart_qhan")
            
            # --- Biểu đồ cột: Nợ khoanh riêng ---
            if "TENPGD" in df.columns and "KHOANH" in df.columns:
                st.subheader("Phân tích Nợ khoanh theo PGD")
                df_sorted_noikhoanh = df.sort_values(by="KHOANH", ascending=False)
                fig_bar_noikhoanh = px.bar(
                    df_sorted_noikhoanh,
                    x="TENPGD",
                    y="KHOANH",
                    title="Nợ khoanh theo PGD (Sắp xếp giảm dần)",
                    color="TENPGD",
                    color_discrete_sequence=px.colors.sequential.Oranges,
                    text_auto=True,
                    height=450
                )
                fig_bar_noikhoanh.update_traces(
                    textposition="auto",
                    marker=dict(line=dict(width=1, color="#FFFFFF"))
                )
                fig_bar_noikhoanh.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=14),
                    title_font_size=20
                )
                st.plotly_chart(fig_bar_noikhoanh, use_container_width=True, key="chart_khoanh")
            
            # --- Biểu đồ xu hướng: Cho vay, Thu nợ, Nợ quá hạn ---
            st.subheader("Xu hướng Cho vay, Thu nợ, Nợ quá hạn (7 ngày gần nhất)")
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            df_trend = pd.DataFrame()
            with engine.connect() as conn:
                for d in dates:
                    df_temp = pd.read_sql(sa.text("exec get_THA_SAVE_DIENBAO @NGAYBC=:date"), conn, params={"date": d})
                    if not df_temp.empty:
                        df_trend = pd.concat([df_trend, df_temp.assign(Ngay=d)])
            
            if not df_trend.empty and all(col in df_trend.columns for col in ["CHOVAY", "THUNO", "QHAN"]):
                df_trend_grouped = df_trend.groupby("Ngay")[["CHOVAY", "THUNO", "QHAN"]].sum().reset_index()
                fig_trend = px.line(
                    df_trend_grouped.melt(id_vars=["Ngay"], value_vars=["CHOVAY", "THUNO", "QHAN"]),
                    x="Ngay",
                    y="value",
                    color="variable",
                    title="Xu hướng Cho vay, Thu nợ, Nợ quá hạn",
                    height=450,
                    line_shape="spline",
                    color_discrete_map={"CHOVAY": "#32CD32", "THUNO": "#87CEEB", "QHAN": "#FF6347"}
                )
                fig_trend.update_traces(line=dict(width=3))
                fig_trend.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=14),
                    title_font_size=20,
                    legend_title_text="Chỉ tiêu"
                )
                st.plotly_chart(fig_trend, use_container_width=True, key="chart_trend")
            else:
                st.info("Không đủ dữ liệu lịch sử để vẽ xu hướng. Cần ít nhất 2 ngày dữ liệu với các cột CHOVAY, THUNO, QHAN.")
        
            st.markdown("</div>", unsafe_allow_html=True)
 #----------------------------------------------------------------------------------------ket thuc dash           
            # --- Biểu đồ cột: Nợ quá hạn và Nợ khoanh cùng nhau ---
            df_sorted_combined = df.sort_values(by=["QHAN", "KHOANH"], ascending=False)
            fig_bar_combined = px.bar(
                df_sorted_combined,
                x="TENPGD",
                y=["QHAN", "KHOANH"],
                title="Nợ quá hạn và Nợ khoanh theo PGD (Sắp xếp giảm dần)",
                barmode="group",
                color_discrete_map={"QHAN": "#FF6347", "KHOANH": "#FFA500"},
                text_auto=True,
                height=450
            )
            fig_bar_combined.update_traces(
                textposition="auto",
                marker=dict(line=dict(width=1, color="#FFFFFF"))
            )
            fig_bar_combined.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=14),
                title_font_size=20
            )
            st.plotly_chart(fig_bar_combined, use_container_width=True)
            
            # --- Biểu đồ cột: Nợ quá hạn riêng ---
            # Sắp xếp theo QHAN giảm dần
            df_sorted_qhan = df.sort_values(by="QHAN", ascending=False)
            fig_bar_qhan = px.bar(
                df_sorted_qhan,
                x="TENPGD",
                y="QHAN",
                title="Nợ quá hạn theo PGD (Sắp xếp giảm dần)",
                color="TENPGD",
                color_discrete_sequence=px.colors.sequential.Reds,
                text_auto=True,
                height=450
            )
            fig_bar_qhan.update_traces(
                textposition="auto",
                marker=dict(line=dict(width=1, color="#FFFFFF"))
            )
            fig_bar_qhan.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=14),
                title_font_size=20
            )
            st.plotly_chart(fig_bar_qhan, use_container_width=True)
            
            # --- Biểu đồ cột: Nợ khoanh riêng ---
            if "TENPGD" in df.columns and "KHOANH" in df.columns:
                st.subheader("Phân tích Nợ khoanh theo PGD")
                # Sắp xếp theo NOIKHOANH giảm dần
                df_sorted_noikhoanh = df.sort_values(by="KHOANH", ascending=False)
                fig_bar_noikhoanh = px.bar(
                    df_sorted_noikhoanh,
                    x="TENPGD",
                    y="KHOANH",
                    title="Nợ khoanh theo PGD (Sắp xếp giảm dần)",
                    color="TENPGD",
                    color_discrete_sequence=px.colors.sequential.Oranges,
                    text_auto=True,
                    height=450
                )
                fig_bar_noikhoanh.update_traces(
                    textposition="auto",
                    marker=dict(line=dict(width=1, color="#FFFFFF"))
                )
                fig_bar_noikhoanh.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=14),
                    title_font_size=20
                )
                st.plotly_chart(fig_bar_noikhoanh, use_container_width=True)
            
            # --- Biểu đồ xu hướng: Cho vay, Thu nợ, Nợ quá hạn ---
            st.subheader("Xu hướng Cho vay, Thu nợ, Nợ quá hạn (7 ngày gần nhất)")
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            df_trend = pd.DataFrame()
            with engine.connect() as conn:
                for d in dates:
                    df_temp = pd.read_sql(sa.text(f"exec get_THA_SAVE_DIENBAO @NGAYBC=:date"), conn, params={"date": d})
                    if not df_temp.empty:
                        df_trend = pd.concat([df_trend, df_temp.assign(Ngay=d)])
            
            if not df_trend.empty and all(col in df_trend.columns for col in ["CHOVAY", "THUNO", "QHAN"]):
                df_trend_grouped = df_trend.groupby("Ngay")[["CHOVAY", "THUNO", "QHAN"]].sum().reset_index()
                fig_trend = px.line(
                    df_trend_grouped.melt(id_vars=["Ngay"], value_vars=["CHOVAY", "THUNO", "QHAN"]),
                    x="Ngay",
                    y="value",
                    color="variable",
                    title="Xu hướng Cho vay, Thu nợ, Nợ quá hạn",
                    height=450,
                    line_shape="spline",
                    color_discrete_map={"CHOVAY": "#32CD32", "THUNO": "#87CEEB", "QHAN": "#FF6347"}
                )
                fig_trend.update_traces(line=dict(width=3))
                fig_trend.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=14),
                    title_font_size=20,
                    legend_title_text="Chỉ tiêu"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Không đủ dữ liệu lịch sử để vẽ xu hướng. Cần ít nhất 2 ngày dữ liệu với các cột CHOVAY, THUNO, QHAN.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <div class='footer'>
            © 2025 Hệ thống Báo cáo VBSP Lạng Sơn | Phát triển bởi Vi Công Thắng, PTP Tin học Chi nhánh Lạng Sơn<br>
            <a href='https://www.facebook.com/profile.php?id=100083312079198'>Fanpage</a> | 
            <a href='https://vbsp.org.vn/gioi-thieu/lai-suat-huy-dong.html'>Lãi suất</a> | 
            <a href='https://vbsp.org.vn/gioi-thieu/co-cau-to-chuc/diem-giao-dich-xa-phuong.html'>Điểm giao dịch</a>|
            <a href='https://www.youtube.com/watch?v=YA74YE1bw1k'>Lạng Sơn tiên cảnh</a>
        </div>
    """, unsafe_allow_html=True)

# Login Page
def login_page():
    """Trang đăng nhập với giao diện tối ưu."""
    st.markdown("<h1 style='text-align: center;'>Đăng nhập</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Chào mừng đến với Hệ thống Báo cáo VBSP Lạng Sơn</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", value=remembered_user, key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            remember_me = st.checkbox("Ghi nhớ đăng nhập", value=remember_me_flag, key="remember_me")
            if st.form_submit_button("Đăng nhập", type="primary"):
                login_result = check_login(username, password)
                if login_result is None:
                    st.session_state.update(username=username, show_new_password_form=True)
                elif login_result:
                    handle_remember_me(username, remember_me)
                    st.session_state.update(logged_in=True, username=username)
                    st.success("Đăng nhập thành công!")
                else:
                    # Thông báo lỗi đã được xử lý trong check_login, không cần thêm ở đây
                    pass
                st.rerun()

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_new_password_form" not in st.session_state:
    st.session_state.show_new_password_form = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "show_change_password" not in st.session_state:
    st.session_state.show_change_password = False

# Main Logic
# st.write("Debug: logged_in =", st.session_state.logged_in)
# st.write("Debug: show_new_password_form =", st.session_state.show_new_password_form)
# st.write("Debug: show_change_password =", st.session_state.show_change_password)

if st.session_state.logged_in:
    home_page()
elif st.session_state.show_new_password_form:
    change_password_form(st.session_state.username)
else:
    login_page()