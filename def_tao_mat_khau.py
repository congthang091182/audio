import streamlit as st
import pyodbc
import time

def connect_to_sql_server():
    """Kết nối đến SQL Server sử dụng thông tin xác thực từ secrets"""
    try:
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
        
        conn = pyodbc.connect(connection_string)
        return conn
    except KeyError as ke:
        st.error(f"Lỗi cấu hình secrets: {ke}")
        return None
    except pyodbc.Error as pe:
        st.error(f"Lỗi kết nối database: {pe}")
        return None
    except Exception as e:
        st.error(f"Lỗi không xác định khi kết nối: {e}")
        return None

def check_old_password(username, old_password):
    """Kiểm tra mật khẩu cũ của người dùng"""
    conn = connect_to_sql_server()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        query = "SELECT matkhau FROM loggin WHERE macb = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        if result:
            stored_password = result[0].strip()
            input_password = old_password.strip()
            if stored_password == input_password:
                return True
            else:
                st.error("Mật khẩu cũ không khớp với dữ liệu trong cơ sở dữ liệu!")
                return False
        else:
            st.error("Không tìm thấy người dùng trong cơ sở dữ liệu!")
            return False
    except pyodbc.Error as e:
        st.error(f"Lỗi truy vấn database: {e}")
        return False
    finally:
        conn.close()

def update_password(username, new_password):
    """Cập nhật mật khẩu mới cho người dùng"""
    conn = connect_to_sql_server()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        query = "UPDATE loggin SET matkhau = ? WHERE macb = ?"
        cursor.execute(query, (new_password, username))
        cursor.execute("SELECT @@ROWCOUNT")
        rows_affected = cursor.fetchone()[0]
        #if user: insert de coi nhu la duoc chap nhan log in, để lsau k phải đăng doi mk
        session_id = "test"
        cursor.execute(
                "INSERT INTO LoginHistory (Username, LoginTime, SessionID) VALUES (?, GETDATE(), ?)",
                (username, session_id)
            )
           # cnxn.commit()
        ###
        conn.commit()
        return rows_affected > 0
    except pyodbc.Error as e:
        st.error(f"Lỗi khi cập nhật mật khẩu: {e}")
        return False
    finally:
        conn.close()

def change_password_form(username):
    st.title("Đổi Mật Khẩu")
    st.write(f"Username: {username}")
    
    with st.form(key=f'change_password_form_{username}'):
        old_password = st.text_input("Mật khẩu cũ", type="password", key=f"old_{username}")
        new_password = st.text_input("Mật khẩu mới", type="password", key=f"new_{username}")
        confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password", key=f"confirm_{username}")
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button(label="Đổi Mật Khẩu")
        with col2:
            cancel_button = st.form_submit_button(label="Hủy")
    
    if submit_button:
        if not all([old_password, new_password, confirm_password]):
            st.error("Vui lòng điền đầy đủ các trường!")
        elif not check_old_password(username, old_password):
            st.error("Mật khẩu cũ không đúng!")
        elif new_password != confirm_password:
            st.error("Mật khẩu mới và xác nhận không khớp!")
        elif len(new_password) < 6:
            st.error("Mật khẩu mới phải có ít nhất 6 ký tự!")
        elif update_password(username, new_password):
            st.success("Đổi mật khẩu thành công! Bạn sẽ được đăng xuất ngay bây giờ.")
            time.sleep(2)  # Đợi 2 giây để người dùng thấy thông báo
            # Đặt lại tất cả trạng thái để quay về màn hình đăng nhập
            st.session_state.logged_in = False
            st.session_state.show_change_password = False
            st.session_state.show_new_password_form = False
            st.rerun()
        else:
            st.error("Đổi mật khẩu thất bại!")
    
    if cancel_button:
        st.session_state.show_change_password = False
        st.rerun()