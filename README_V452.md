# Formula Intelligence V4.5.2 — Giao diện trực quan và tiền kiểm R&D

Ứng dụng **độc lập**, không nhập vào repository Mountain Lab SkinSim / ComesticLab.

## Đã triển khai

- Tại `frontend/app/experiments`, giao diện thiết kế công thức dạng bảng: nhập INCI, mã nhóm, khoảng min/max, tỷ lệ mục tiêu; thêm/xóa nguyên liệu; cân bằng 100% khi nguyên liệu cân bằng được chọn nằm trong khoảng được phép.
- Quản lý protocol qua biểu mẫu: mã, tên, ngày đo, điều kiện, đơn vị, chỉ tiêu định lượng/định tính, ngưỡng người dùng và nguồn quy cách.
- Form nhập đo được cải thiện: số hữu hạn, chọn loại dữ liệu, giá trị phân loại; yêu cầu bằng chứng/phương pháp/thiết bị trước khi gửi số đo thực tế.
- Chế độ JSON nâng cao vẫn được giữ trong `<details>`, dành cho nghiên cứu cấu trúc premix/claims, không bắt buộc với thao tác thông thường.
- `POST /api/v4.5/review-draft`: tính nghiệm V4.4 và báo trạng thái claim, grade chưa rõ; không lưu xuống DB, không duyệt sản xuất.
- Backend kế thừa API V4.5.1, SQLite để chạy thử và PostgreSQL tùy chọn qua `V45_DATABASE_URL`; migration giữ tại `migrations/001_v451_init.sql`.

## Chạy với SQLite (Windows)

Tại thư mục project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\scripts\run_backend.ps1
```

Tại cửa sổ terminal khác:

```powershell
.\scripts\run_frontend.ps1
```

Mở `http://127.0.0.1:3000/experiments`. API: `http://127.0.0.1:8000/health/v4.5`.

## Chạy kiểm thử

```bash
python -m pytest -q test_engine.py test_scientific_v43.py test_optimizer_v44.py test_scientific_bridge_v44.py test_experimental_v45.py test_integration_v451.py test_v452_integration.py
node frontend/tests/test_form_model.cjs
```

Kiểm thử Node helper phía frontend dùng TypeScript cài đặt sẵn, không thay thế `npm run build` hoặc kiểm thử tương tác trong trình duyệt.

```bash
cd frontend
npm install
npm run build
npm run dev
```

Chỉ thực hiện được ba lệnh npm khi có kết nối npm registry để tải `next`, `react`, `typescript` và type declarations. Trong môi trường bàn giao, chưa xác nhận build Next.js hoặc chạy UI qua trình duyệt.

## PostgreSQL

Chạy trên máy có Docker: cấu hình `.env` với mật khẩu mạnh, sau đó `docker compose up --build`; giao diện chạy local tại `127.0.0.1:3000`. Migration chỉ chạy tự động ở **volume trống**. Không xóa volume với dữ liệu thực tế.

Để chạy thử PostgreSQL thực, cần một **database riêng kết thúc bằng `_test`** và apply `migrations/001_v451_init.sql`. Đặt `TEST_POSTGRES_URL`, rồi chạy `python scripts/verify_postgres_v452.py`. Script đọc/ghi bản ghi DEMO và kiểm tra trigger chống sửa; tuyệt đối không trỏ vào production.

## Giới hạn, an toàn và dữ liệu khoa học

- Preview chỉ chứng minh nghiệm toán học và cảnh báo một số vấn đề, không dự đoán độ ổn định, pH, hiệu lực hay an toàn.
- Premix `composition.complete=false` vẫn chưa có thành phần đủ để suy ngược INCI thực tế.
- Giá trị mục tiêu không phải số đo thực tế. Các chỉ tiêu protocol minh họa là tiêu chí R&D do người dùng chọn.
- Người sử dụng chịu trách nhiệm kiểm tra chứng cứ được nhập; URI không được hệ thống xác minh độc lập.
- V4.5.2 chưa có authentication, RBAC/tenant, CSRF, quản lý upload/virus scan, log truy cập, lưu trữ backup và chạy production migrations. **Không mở app công khai ra Internet.**
- Không thay đổi các số liệu pháp lý/khoa học gốc chưa được xác minh.
