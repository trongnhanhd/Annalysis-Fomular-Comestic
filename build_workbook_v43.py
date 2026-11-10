from __future__ import annotations
import csv
from pathlib import Path
from artifact_tool import Workbook,SpreadsheetFile
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
OUT=ROOT/'Scientific_Ingredient_Database_V4_3.xlsx'

def readcsv(n):
    with (DATA/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

wb=Workbook.create()
navy='#152B4A';teal='#087D7B'; pale='#EAF5F3'; txt='#18283F'

def add_sheet(name,file,cols,title,desc):
    ws=wb.worksheets.add(name)
    src=readcsv(file)
    ws.merge_cells(f'A1:{chr(64+len(cols))}1')
    ws.get_range('A1').values=[[title]]
    ws.merge_cells(f'A2:{chr(64+len(cols))}2')
    ws.get_range('A2').values=[[desc]]
    ws.get_range_by_indexes(3,0,1,len(cols)).values=[[label for field,label in cols]]
    matrix=[[str(row.get(key,'')) if row.get(key,'') is not None else '' for key,label in cols] for row in src]
    if matrix:ws.get_range_by_indexes(4,0,len(matrix),len(cols)).values=matrix
    ws.get_range_by_indexes(0,0,1,len(cols)).format={'fill':navy,'font':{'bold':True,'color':'#FFFFFF','size':16},'row_height':30}
    ws.get_range_by_indexes(1,0,1,len(cols)).format={'fill':pale,'font':{'color':teal,'size':10},'row_height':29}
    ws.get_range_by_indexes(3,0,1,len(cols)).format={'fill':teal,'font':{'bold':True,'color':'#FFFFFF'},'row_height':26}
    ws.get_range_by_indexes(0,0,max(len(matrix)+4,7),len(cols)).format.column_width=22
    for j,(key,label) in enumerate(cols):
        width=35 if key.endswith('_url') or 'note' in key or 'scope' in key or key in ('inci_candidate','inci_declared','grade_name','source_title','qualitative_value','property_key','component_inci_candidate') else 19
        ws.get_range_by_indexes(0,j,max(5,len(matrix)+5),1).format.column_width=width
    ws.get_range_by_indexes(4,0,max(1,len(matrix)),len(cols)).format.row_height=20
    ws.freeze_panes.freeze_rows(4)
    return len(src)

summary=wb.worksheets.add('TONG_QUAN')
summary.merge_cells('A1:H2');summary.get_range('A1').values=[['FORMULA INTELLIGENCE V4.3 — SCIENTIFIC INGREDIENT DATA']]
summary.get_range('A1:H2').format={'fill':navy,'font':{'color':'#FFFFFF','bold':True,'size':16},'row_height':24}
summary.merge_cells('A3:H3');summary.get_range('A3').values=[['Dữ liệu tham chiếu khoa học theo grade — KHÔNG phải xác nhận an toàn hay giới hạn pháp lý']]
summary.get_range('A3:H3').format={'fill':pale,'font':{'color':teal}}
summary.get_range('A5:B5').values=[['Tập dữ liệu','Số lượng']]
summary.get_range('A5:B5').format={'fill':teal,'font':{'color':'#FFFFFF','bold':True}}
summary.get_range('A6:A10').values=[['INCI V4.2 kế thừa'],['Grade nguồn mới V4.3'],['Quan sát kỹ thuật V4.3'],['Cấu tử premix định tính'],['INCI ngoài master cần duyệt']]
summary.get_range('B6:B9').formulas=[['=COUNTA(BAO_PHU_INCI!A5:A194)'],['=COUNTA(GRADE_THUONG_MAI!A5:A15)'],['=COUNTA(QUAN_SAT_KHOA_HOC!A5:A26)'],['=COUNTA(PREMIX_DINH_TINH!A5:A16)']]
summary.get_range('B10').values=[[1]]
summary.get_range('A12:A16').values=[['Quy tắc 1 — không gộp claim % với raw material %'],['Quy tắc 2 — chỉ áp dải % cho đúng grade và phạm vi'],['Quy tắc 3 — premix chưa có tỷ phần => không phân rã định lượng'],['Quy tắc 4 — 190 INCI không có nghĩa 190 hồ sơ đã xác minh'],['Quy tắc 5 — không cấp quyền duyệt sản xuất từ mô phỏng']]
summary.get_range('A12:H16').format.column_width=20
summary.get_range('A12').format.column_width=65
summary.get_range('A5').format.column_width=47
summary.get_range('B5').format.column_width=20
summary.get_range('A6:B10').format.row_height=28
summary.get_range('B6:B10').format={'font':{'color':teal,'bold':True,'size':16},'horizontal_alignment':'center'}
summary.get_range('A12:A16').format={'font':{'color':txt},'row_height':26}
summary.freeze_panes.freeze_rows(3)

add_sheet('GRADE_THUONG_MAI','supplier_grade_reference_v43.csv',[('grade_id','ID grade'),('grade_name','Tên thương mại'),('inci_declared','INCI nhà cung cấp'),('supplier','Nhà cung cấp'),('use_context','Phạm vi'),('composition_status','Tình trạng thành phần'),('source_url','Nguồn trực tiếp'),('coa_verified','COA xác minh')],'11 GRADE THƯƠNG MẠI','Grade riêng biệt • không tự cho là nguyên liệu tinh khiết')
add_sheet('QUAN_SAT_KHOA_HOC','scientific_property_observations_v43.csv',[('observation_id','Mã quan sát'),('inci_candidate','INCI liên quan'),('grade_id','Grade'),('property_key','Thuộc tính'),('value_min','Giá trị từ'),('value_max','Giá trị đến'),('unit','Đơn vị'),('qualitative_value','Định tính'),('test_conditions_or_scope','Điều kiện phạm vi'),('source_url','Link nguồn'),('note_vi','Lưu ý')],'22 QUAN SÁT KHOA HỌC','Các giá trị % là mức khuyến nghị theo grade, không phải trần pháp lý')
add_sheet('PREMIX_DINH_TINH','grade_components_qualitative_v43.csv',[('grade_id','Premix'),('component_order','Thứ tự'),('component_inci_candidate','Cấu tử INCI'),('concentration_basis','Cơ sở %'),('status','Tình trạng'),('supplier_source_id','ID nguồn')],'CẤU TỬ PREMIX','Danh mục định tính: KHÔNG phân bổ % khi thiếu COA')
add_sheet('NGUON_KHOA_HOC','scientific_sources_v43.csv',[('source_id','Mã nguồn'),('source_title','Tên tài liệu'),('source_type','Loại nguồn'),('scope','Phạm vi'),('source_url','Địa chỉ nguồn'),('checked_date','Ngày đối chiếu'),('evidence_status','Trạng thái')],'THƯ VIỆN NGUỒN','Truy xuất tài liệu nhà cung cấp — cần lưu bản TDS/SDS có phiên bản')
add_sheet('BAO_PHU_INCI','ingredient_evidence_coverage_v43.csv',[('ingredient_id','ID'),('inci_candidate','INCI ứng viên'),('property_coverage_v42','Trạng thái V4.2'),('scientific_status','V4.3 grade tham chiếu'),('target_priorities','Dữ liệu còn thiếu'),('verification_required','Cần thẩm định')],'190 INCI ỨNG VIÊN','Không đánh dấu verified khi chưa có tài liệu đầy đủ')

ws=wb.worksheets.add('HUONG_DAN')
ws.merge_cells('A1:F1');ws.get_range('A1').values=[['HƯỚNG DẪN SỬ DỤNG CƠ SỞ DỮ LIỆU R&D']]
ws.get_range('A1:F1').format={'fill':navy,'font':{'color':'#FFFFFF','bold':True,'size':15},'row_height':32}
help_rows=[['1','Chọn nhóm sản phẩm','Lọc INCI và nhóm chức năng theo ngữ cảnh.'],['2','Chọn grade thương mại','Không lấy thông số grade khác dù cùng tên INCI.'],['3','Đọc quan sát kỹ thuật','Đối chiếu giá trị, đơn vị, phạm vi, source URL.'],['4','Tính khối lượng','Cân bằng tổng nguyên liệu thương mại = 100%.'],['5','Premix','Chưa có tỷ phần cấu tử => đánh dấu unresolved, không phân rã.'],['6','Sàng lọc kỹ thuật','Hiển thị cảnh báo dự kiến, không tự phê duyệt.'],['7','Pháp lý','Tra riêng luật từng thị trường, điều kiện sử dụng, thời điểm hiệu lực.'],['8','Thực nghiệm','COA, stability, challenge test, QC và an toàn thành phẩm.']]
ws.get_range('A3:C10').values=help_rows
ws.get_range('A3:A10').format.column_width=7
ws.get_range('B3:B10').format.column_width=30
ws.get_range('C3:C10').format.column_width=77
ws.get_range('A3:C10').format.row_height=24

out=SpreadsheetFile.export_xlsx(wb)
out.save(str(OUT))
print('EXPORT',OUT)
try:
 print('INSPECT',wb.inspect({'kind':'table','range':'TONG_QUAN!A5:B10','include':'values,formulas','table_max_rows':7,'table_max_cols':3}).ndjson[:1200])
except Exception as e:print('INSPECT_WARNING',type(e).__name__,str(e)[:150])
