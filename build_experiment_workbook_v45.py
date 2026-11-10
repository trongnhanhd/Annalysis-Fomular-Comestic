"""Artifact_tool only. Export workbook with modelled DOE and blank lab measurement log."""
from artifact_tool import Workbook, SpreadsheetFile
from experimental_validation_v45 import build_doe
from formula_group_service import Catalog
import json
from pathlib import Path

root=Path(__file__).parent
source=json.loads((root/'examples/lip_balm_doe_v45.json').read_text(encoding='utf8'))
protocol=json.loads((root/'examples/lip_balm_study_v45.json').read_text(encoding='utf8'))['protocol']
doe=build_doe(source,Catalog())
wb=Workbook.create()
HEADER={'fill':'#153C55','font':{'color':'#FFFFFF','bold':True},'row_height':29,'vertical_alignment':'center'}
TITLE={'fill':'#127C75','font':{'color':'#FFFFFF','bold':True,'size':15},'row_height':38,'vertical_alignment':'center'}


def make_sheet(name,headers,rows,widths=None):
    s=wb.worksheets.add(name)
    cols=len(headers)
    s.get_range_by_indexes(0,0,1,cols).values=[headers]
    s.get_range_by_indexes(0,0,1,cols).format=HEADER
    if rows:s.get_range_by_indexes(1,0,len(rows),cols).values=rows
    s.freeze_panes.freeze_rows(1)
    for idx,w in enumerate(widths or [22]*cols):
        s.get_range_by_indexes(0,idx,max(len(rows),1)+1,1).format.column_width=w
    if rows:
        s.get_range_by_indexes(1,0,len(rows),cols).format.row_height=21
    return s

summary=wb.worksheets.add('TONG_QUAN')
summary.merge_cells('A1:F1');summary.get_range('A1').values=[['FORMULA INTELLIGENCE V4.5 | R&D THỰC NGHIỆM']]
summary.get_range('A1:F1').format=TITLE
summary.get_range('A3:B8').values=[
    ['Nội dung','Trạng thái'],['Nguồn công thức','V4.4 — Lip Balm minh họa'],
    ['Phương án DoE',doe['candidate_count']],['Phương án khả thi',doe['feasible_count']],
    ['Kết quả đo thực tế',0],['Đã phê duyệt sản xuất','KHÔNG']]
summary.get_range('A3:B3').format=HEADER
summary.get_range('A10').values=[['CẢNH BÁO: Kế hoạch DoE chỉ là nghiệm toán học. Số đo trong nhật ký đang để trống; không tự tạo dữ liệu.']]
summary.merge_cells('A10:F10')
summary.get_range('A10:F10').format.wrap_text=True
summary.get_range('A10:F10').format.row_height=42
summary.get_range('A1:A12').format.column_width=25
summary.get_range('B1:B12').format.column_width=28
summary.get_range('C1:F12').format.column_width=20

ids=['base_premix','jojoba_oil','beeswax','antioxidant_blend','flavour','bisabolol']
rows=[]
for row in doe['results']:
    if row['status']!='FEASIBLE':continue
    values=[row['composition_percent'].get(i,0) for i in ids]
    rows.append([row['candidate_id'],row['design_point'],row['status'],*values,None,'CHƯA THỬ NGHIỆM'])
cols=['Mã phương án','Điểm thiết kế','Nghiệm V4.4','Lipid Base %','Jojoba Oil %','Beeswax %','Antioxidant %','Flavour %','Bisabolol %','Tổng % (tính)','Trạng thái đo']
s=make_sheet('DOE_PLAN',cols,rows,[18,20,19,16,17,15,18,15,17,17,22])
for row_idx in range(2,2+len(rows)):
    s.get_range(f'J{row_idx}').formulas=[[f'=SUM(D{row_idx}:I{row_idx})']]
s.get_range(f'D2:J{len(rows)+1}').set_number_format('0.00')
s.get_range(f'J2:J{len(rows)+1}').conditional_formats.add_cell_is({'operator':'notEqual','formula':100,'format':{'fill':'#FEE2E2'}})

metric_rows=[]
for m in protocol['metrics']:
    metric_rows.append([m['code'],m['name'],m['kind'],m.get('unit',''), ', '.join(map(str,m['timepoints_days'])),
                        m.get('target_min'),m.get('target_max'),', '.join(m.get('acceptable_values',[])),
                        m.get('method',''),m.get('criteria_source',''), 'MẪU THAM KHẢO - CẦN CHỐT'])
make_sheet('PROTOCOL', ['Mã','Chỉ tiêu','Loại','Đơn vị','Ngày đo','Mức dưới','Mức trên','Giá trị chấp nhận','Phương pháp','Nguồn tiêu chí','Trạng thái'],metric_rows,
           [20,25,16,12,16,15,15,25,37,27,34])

# Leave all measured values EMPTY. This is intentionally NOT populated with dummy lab results.
measure_cols=['Mã nghiên cứu','Mã mẻ','Công thức SHA-256','Chỉ tiêu','Ngày','Giá trị thực đo','Đơn vị','SOP/method','Thiết bị','Người đo','Nguồn bằng chứng','Ngày ghi','Loại dữ liệu','Trạng thái kiểm tra']
log=make_sheet('NHAT_KY_DO',measure_cols,[],[20,19,38,23,11,20,12,25,20,18,34,23,18,25])
log.get_range('A2:N51').format.row_height=23
log.get_range('M2:M51').data_validation={'rule':{'type':'list','values':['MEASURED','DEMO_SYNTHETIC']}}
log.get_range('N2:N51').formulas=[['=IF(F2="","",IF(M2="DEMO_SYNTHETIC","KHÔNG DÙNG LÀM BẰNG CHỨNG",IF(K2="","THIẾU NGUỒN","CHỜ RÀ SOÁT")))']]
log.get_range('N2:N51').fill_down()

make_sheet('NGUON', ['Tài liệu','Ý nghĩa','URL nguồn'],[
    ['ISO/TR 18811:2018','Hướng dẫn phương pháp lập protocol độ ổn định; không áp ngưỡng chung','https://www.iso.org/standard/63465.html'],
    ['ISO 11930:2019','Đánh giá bảo vệ vi sinh; không thể suy từ nồng độ chất bảo quản','https://www.iso.org/standard/75058.html'],
    ['V4.4 Engine','Dải INCI và nghiệm khả thi chỉ theo ràng buộc đầu vào','Tài liệu nội bộ V4.4'],
    ['Tài liệu gốc Oganic','Dải nhóm giao diện; không phải quy định pháp lý','Nguồn ảnh người dùng cung cấp']
], [25,70,67])
make_sheet('HUONG_DAN', ['Bước','Việc cần làm','Lưu ý'],[
    [1,'Chọn DOE-001...DOE-005 và xác nhận thành phần grade','Không cân trực tiếp từ công thức chưa xác minh chất mang'],
    [2,'Lập protocol thực tế theo loại mỹ phẩm, môi trường, bao bì, thời gian','Mọi mục tiêu hiện trong mẫu đều do người dùng xác lập'],
    [3,'Tạo từng mẻ thực trong Web App và lưu lot code','Mỗi mẻ có ID độc lập'],
    [4,'Ghi số đo, thiết bị, SOP và bằng chứng từ thí nghiệm','Không ghi số liệu mô phỏng là MEASURED'],
    [5,'Đánh giá độ phủ và ngoài quy cách','READY_FOR_RND_REVIEW ≠ phê duyệt'],
    [6,'Lưu hồ sơ thử hiệu quả bảo quản/vi sinh riêng khi cần','Không suy luận chứng nhận ISO từ dữ liệu mẻ']
], [12,67,65])

output=root/'Experimental_Validation_V4_5.xlsx'
try:
    print(wb.inspect({'kind':'table','range':'DOE_PLAN!A1:K7','include':'values,formulas','table_max_rows':7,'table_max_cols':11}).ndjson[:1500])
except Exception as e:print('Inspect warning:',str(e)[:150])
try:
    print('error scan',wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':20}}).ndjson[:700])
except Exception as e:print('Scan warning:',str(e)[:150])
SpreadsheetFile.export_xlsx(wb).save(str(output))
print('EXPORTED',output,output.stat().st_size)
