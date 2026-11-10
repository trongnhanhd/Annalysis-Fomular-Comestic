# YÊU CẦU TÍCH HỢP V4.5 VÀO WEB APP R&D HIỆN CÓ

Mục tiêu: **Tiếp tục dự án Web App R&D mỹ phẩm độc lập**, không tích hợp với Mountain Lab SkinSim, MixColor hoặc các hệ thống khác. Giữ frontend tiếng Việt, backend FastAPI, PostgreSQL, thư viện 33 Product Type / 32 Functional Group / 190 INCI ứng viên và Concentration Optimizer V4.4.

## Nhiệm vụ theo thứ tự

1. Đọc `README_V45.md`, `experimental_validation_v45.py`, `experimental_repository_v45.py`, `api_v45.py`, `test_experimental_v45.py` và các file nguồn V4.4. **Không viết lại solver V4.4 từ đầu.**
2. Đưa `build_doe` vào service `experiments/doe`, dùng V4.4 solver để revalidate từng mẻ; bổ sung bất biến `Σ x_i =100%` và báo lỗi có thể truy nguyên.
3. Chuyển SQLite demo thành PostgreSQL migrations được review theo schema `schema_v45_postgres.sql`. Gắn user/account/tenant thực của app; thiết lập RBAC, dòng ghi audit bất biến bằng DB trigger, bảo vệ nguồn chứng cứ, sao lưu, log và quản lý version.
4. Thiết lập CRUD thí nghiệm theo REST endpoint V4.5; giữ endpoint cũ `V4.3`/`V4.4`. Kiểm tra trường `MEASURED` luôn có người đo, thiết bị, method, evidence_uri; mọi `DEMO_SYNTHETIC` không tính vào báo cáo.
5. Bổ sung UI tại `/experiments`: chọn công thức từ thư viện, chọn 1–3 biến, chỉ định chất cân bằng, xem bảng DOE và cảnh báo; tạo study, mẻ, nhập đo, biểu đồ xu hướng, tính độ phủ, lọc data source.
6. Bổ sung xác nhận bằng người R&D (reviewer role), phê duyệt quy trình riêng, trạng thái stability testing / preservation testing. **Không gán 'approved_for_manufacturing=true' khi thiếu đánh giá an toàn/pháp lý/bảo quản.**
7. Nâng DoE từ factorial 2-level sơ bộ lên DOE có kế hoạch replicates, randomization, blocking, tương tác và mô hình phản ứng khi có đủ dữ liệu thực nghiệm; không tự suy luận hiệu năng từ tỷ lệ nguyên liệu.
8. Unit tests + integration tests + database migrations + frontend build; tạo screenshot khi ứng dụng thực tế chạy được. Không thông báo thành công nếu build/migration bị chặn.

## Điều kiện chấp nhận (definition of done)

- V4.4 và V4.5 tests đều xanh; các endpoint kế thừa còn hoạt động.
- Study giữ nguyên snapshot công thức (SHA-256), không thay đổi ngay cả khi sửa công thức gốc.
- Mỗi mẻ có lot code riêng và số đo có bằng chứng; correction có lịch sử; user-defined target được phân biệt legal limit.
- Tổng số đo DEMO_SYNTHETIC trong báo cáo chỉ nằm ở trường excluded, **không đóng góp vào coverage/trend/đạt quy cách**.
- 0 dữ liệu thí nghiệm được bịa; test fixtures không ghi trực tiếp vào database production.
- API docs OpenAPI, schema PostgreSQL và UI tiếng Việt đã kiểm thử; không tự điều chỉnh luật 6 thị trường.

## Ví dụ xác minh

```bash
python -m pytest -q test_engine.py test_scientific_v43.py test_optimizer_v44.py test_scientific_bridge_v44.py test_experimental_v45.py
uvicorn api_v45:app --reload --port 8000
curl http://localhost:8000/health/v4.5
curl -X POST http://localhost:8000/api/v4.5/design-experiments \
 -H 'Content-Type: application/json' \
 --data-binary @examples/lip_balm_doe_v45.json
```

## Rào chắn khoa học

- ISO/TR 18811 hướng dẫn xây protocol và không định nghĩa ngưỡng chung.
- ISO 11930 không thể bị thay bằng một lượng Phenoxyethanol nhập vào công thức.
- Mọi khoảng nhóm từ Oganic chỉ là **tham khảo giao diện**; phải phân biệt hard constraint người dùng và mức pháp lý được xác minh.
- Các tỷ lệ công bố 8% PAD có thể là nguyên liệu thương mại hay INCI thực; không gộp trong một biến duy nhất.
