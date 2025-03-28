import os
import time
import logging
from io import BytesIO
from datetime import datetime
import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đăng ký font Unicode (có fallback)
try:
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'timesbd.ttf'))
    DEFAULT_FONT = 'TimesNewRoman'
except:
    logger.warning("Font Times New Roman không khả dụng, sử dụng font mặc định")
    DEFAULT_FONT = 'Helvetica'

def export_to_pdf(df, selected_columns, report_title, output_filename, include_chart=True):
    """
    Xuất báo cáo PDF hoàn chỉnh với biểu đồ và bảng dữ liệu
    - Tự động xử lý lỗi và tối ưu hiệu suất
    - Hỗ trợ cả font Unicode và font mặc định
    - Đảm bảo hiển thị biểu đồ trên PDF
    """
    start_time = time.time()
    buffer = BytesIO()
    chart_path = None

    try:
        # 1. TIỀN XỬ LÝ DỮ LIỆU
        logger.info("Bắt đầu tạo báo cáo...")
        
        # Lọc cột
        selected_columns = selected_columns or df.columns.tolist()
        df_filtered = df[selected_columns].copy()
        
        if df_filtered.empty:
            raise ValueError("DataFrame đầu vào trống")

        # 2. TẠO KHUNG PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Tiêu đề
        title_style = ParagraphStyle(
            name='Title',
            fontName=f'{DEFAULT_FONT}-Bold',
            fontSize=16,
            alignment=1,  # Căn giữa
            spaceAfter=12
        )
        elements.append(Paragraph(report_title, title_style))
        
        # Ngày xuất báo cáo
        date_style = ParagraphStyle(
            name='Normal',
            fontName=DEFAULT_FONT,
            fontSize=10,
            alignment=1
        )
        elements.append(Paragraph(
            f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
            date_style
        ))
        elements.append(Spacer(1, 24))

        # 3. XỬ LÝ BIỂU ĐỒ (TỐI ƯU)
        if include_chart and len(df_filtered) <= 100:  # Chỉ vẽ với <=100 dòng
            try:
                logger.info("Đang tạo biểu đồ...")
                
                # Tìm cột nhãn (ưu tiên cột có tên PGD)
                label_col = next(
                    (col for col in ['TENPGD', 'TH_MAPGD', df_filtered.columns[0]] 
                    if col in df_filtered.columns),
                    None
                )
                
                # Chọn cột số (tối đa 3 cột để biểu đồ rõ ràng)
                numeric_cols = [
                    col for col in df_filtered.columns 
                    if pd.api.types.is_numeric_dtype(df_filtered[col])
                    and col != label_col
                ][:3]
                
                if label_col and numeric_cols:
                    # Tạo biểu đồ cột đơn giản
                    fig = px.bar(
                        df_filtered.head(30),  # Giới hạn 30 bản ghi để tăng tốc
                        x=label_col,
                        y=numeric_cols[0],     # Chỉ lấy cột số đầu tiên
                        title=f"Biểu đồ {numeric_cols[0]} theo {label_col}"
                    )
                    
                    # Tối ưu layout
                    fig.update_layout(
                        margin=dict(l=20, r=20, t=40, b=20),
                        showlegend=False,
                        font=dict(family=DEFAULT_FONT)
                    )
                    
                    # Lưu biểu đồ với chất lượng vừa phải
                    chart_path = f"temp_chart_{int(time.time())}.png"
                    fig.write_image(
                        chart_path,
                        engine="kaleido",
                        scale=1,  # Độ phân giải thấp
                        width=600,
                        height=350
                    )
                    
                    # Chắc chắn file tồn tại trước khi chèn
                    if os.path.exists(chart_path):
                        elements.append(Image(chart_path, width=550, height=300))
                        elements.append(Spacer(1, 20))
                    else:
                        logger.warning("Không tạo được file biểu đồ tạm")
                        
            except Exception as e:
                logger.error(f"Lỗi khi tạo biểu đồ: {str(e)[:200]}")
                if chart_path and os.path.exists(chart_path):
                    os.remove(chart_path)

        # 4. TẠO BẢNG DỮ LIỆU
        logger.info("Đang tạo bảng dữ liệu...")
        
        # Giới hạn số dòng hiển thị
        max_table_rows = 500
        if len(df_filtered) > max_table_rows:
            logger.warning(f"Chỉ hiển thị {max_table_rows}/{len(df_filtered)} dòng")
            df_display = df_filtered.head(max_table_rows)
        else:
            df_display = df_filtered
            
        # Chuẩn bị dữ liệu bảng
        table_data = [df_display.columns.tolist()] + df_display.fillna('').values.tolist()
        
        # Tạo bảng ReportLab
        table = Table(table_data, repeatRows=1)  # Lặp lại tiêu đề khi sang trang
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), f'{DEFAULT_FONT}-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#D9E1F2')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,1), (-1,-1), DEFAULT_FONT),
            ('FONTSIZE', (0,1), (-1,-1), 8),
        ]))
        
        elements.append(table)
        
        # 5. XUẤT PDF
        logger.info("Đang tạo file PDF...")
        doc.build(elements)
        
        logger.info(f"Hoàn thành trong {time.time()-start_time:.2f} giây")
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi tạo PDF: {str(e)}")
        raise
    finally:
        # Dọn dẹp file tạm
        if chart_path and os.path.exists(chart_path):
            os.remove(chart_path)

# Hàm test
def test_export():
    """Test hàm export với dữ liệu mẫu"""
    test_data = {
        'TENPGD': [f'PGD_{i}' for i in range(1, 6)],
        'DoanhThu': [100, 200, 150, 300, 250],
        'ChiPhi': [30, 50, 40, 70, 60]
    }
    df_test = pd.DataFrame(test_data)
    
    pdf_buffer = export_to_pdf(
        df=df_test,
        selected_columns=['TENPGD', 'DoanhThu'],
        report_title="Báo Cáo Doanh Thu",
        output_filename="test_report.pdf"
    )
    
    # Lưu file test
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_buffer.getbuffer())
    print("Đã xuất file test_output.pdf thành công!")

if __name__ == "__main__":
    test_export()