# Từ điển dữ liệu — Experimental Validation V4.5

| Trường | Kiểu | Ý nghĩa / ràng buộc |
|---|---|---|
| scenario | JSON | Snapshot đầu vào optimizer V4.4, phải có nghiệm FEASIBLE trước khi khóa nghiên cứu |
| formula_sha256 | CHAR(64) | Băm của canonical JSON, không dùng làm chứng chỉ khoa học |
| protocol.metrics[].code | string | Định danh chỉ tiêu duy nhất, ví dụ HARDNESS |
| kind | enum | numeric hoặc categorical |
| unit | string | Đơn vị phải nhất quán trong cùng metric |
| timepoints_days | int[] | Các ngày đo hợp lệ được R&D quy định |
| target_min, target_max | float/null | Quy cách nội bộ, không phải giới hạn pháp lý |
| criteria_source | string | Bằng chứng/nguồn ngưỡng, ví dụ USER_DEFINED_DEMO |
| batch_id | UUID/text | Khóa mẻ độc lập |
| evidence_uri | string | Truy vết hồ sơ thí nghiệm gốc; hệ thống demo chỉ kiểm tra có/không |
| data_kind | MEASURED / DEMO_SYNTHETIC | Chỉ MEASURED được tính vào đánh giá |
| supersedes_measurement_id | text/null | Sửa theo bản ghi mới; giữ bản cũ cho audit |
| required_slots | integer | Số mẻ × chỉ tiêu × các mốc đo |
| completed_slots | integer | Số tổ hợp mẻ/chỉ tiêu/ngày có ít nhất một số đo MEASURED |
| status | enum | NO_BATCH, NO_MEASUREMENTS, INCOMPLETE, OUT_OF_USER_SPEC, NEEDS_SPECIFICATION, READY_FOR_RND_REVIEW |
| approved_for_manufacturing | bool | Luôn FALSE trong V4.5, không phải workflow pháp lý |

**Cảnh báo:** Các giá trị độ cứng, nhiệt độ mềm hóa... trong `examples/lip_balm_study_v45.json` là *ngưỡng nội bộ minh họa* để test phần mềm. Không có kết quả thử nghiệm thật nào được cài sẵn.
