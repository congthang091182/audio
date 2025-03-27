import pandas as pd
import streamlit as st
from openpyxl import load_workbook

# Hàm để ghi dữ liệu vào file Excel mẫu
def write_to_excel_template9(template_path, df1, df2, df3, df4, df5, df6, startrow, startcol, output_path):
    """
    Ghi dữ liệu vào file Excel mẫu.

    Parameters:
        template_path (str): Đường dẫn đến file Excel mẫu.
        df1, df2, df3, df4, df5, df6 (pd.DataFrame): Các DataFrame chứa dữ liệu.
        startrow (int): Dòng bắt đầu ghi dữ liệu.
        startcol (int): Cột bắt đầu ghi dữ liệu.
        output_path (str): Đường dẫn để lưu file Excel kết quả.
    """
    dfs = [df1, df2, df3, df4, df5, df6]
    for i, df in enumerate(dfs):
        if df.empty:
            st.warning(f"DataFrame {i+1} rỗng, không có dữ liệu để xuất Excel.")
            return

    # Đọc file Excel mẫu
    book = load_workbook(template_path)
    
    # Chuẩn hóa dữ liệu trước khi ghi
    for i in range(len(dfs)):
        df = dfs[i]
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()
            else:
                if not df[col].empty and df[col].notna().any():
                    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Ghi dữ liệu vào sheet đầu tiên (Sheet1)
    sheet1 = book[book.sheetnames[0]]  # Lấy sheet đầu tiên
    for r_idx, row in enumerate(df1.values, start=startrow):
        for c_idx, value in enumerate(row, start=startcol):
            sheet1.cell(row=r_idx, column=c_idx, value=value)
    
    # Ghi dữ liệu vào sheet thứ hai (Sheet2)
    if len(book.sheetnames) > 1:
        sheet2 = book[book.sheetnames[1]]  # Lấy sheet thứ hai
        for r_idx, row in enumerate(df2.values, start=startrow):
            for c_idx, value in enumerate(row, start=startcol):
                sheet2.cell(row=r_idx, column=c_idx, value=value)
    
    # Ghi dữ liệu vào sheet thứ ba (Sheet3)
    if len(book.sheetnames) > 2:
        sheet3 = book[book.sheetnames[2]]  # Lấy sheet thứ ba
        for r_idx, row in enumerate(df3.values, start=startrow):
            for c_idx, value in enumerate(row, start=startcol):
                sheet3.cell(row=r_idx, column=c_idx, value=value)
    
    # Ghi dữ liệu vào sheet thứ tư (Sheet4)
    if len(book.sheetnames) > 3:
        sheet4 = book[book.sheetnames[3]]  # Lấy sheet thứ tư
        for r_idx, row in enumerate(df4.values, start=startrow):
            for c_idx, value in enumerate(row, start=startcol):
                sheet4.cell(row=r_idx, column=c_idx, value=value)
    
    # Ghi dữ liệu vào sheet thứ năm (Sheet5)
    if len(book.sheetnames) > 4:
        sheet5 = book[book.sheetnames[4]]  # Lấy sheet thứ năm
        for r_idx, row in enumerate(df5.values, start=startrow):
            for c_idx, value in enumerate(row, start=startcol):
                sheet5.cell(row=r_idx, column=c_idx, value=value)
    
    # Ghi dữ liệu vào sheet thứ sáu (Sheet6)
    if len(book.sheetnames) > 5:
        sheet6 = book[book.sheetnames[5]]  # Lấy sheet thứ sáu
        for r_idx, row in enumerate(df6.values, start=startrow):
            for c_idx, value in enumerate(row, start=startcol):
                sheet6.cell(row=r_idx, column=c_idx, value=value)
    else:
        st.warning("File Excel mẫu không đủ sheet để ghi dữ liệu.")

    # Lưu file Excel
    book.save(output_path)