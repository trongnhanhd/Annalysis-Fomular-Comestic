# Formula Intelligence V4.5.1 — Tích hợp Web App R&D độc lập

## Phạm vi đã tích hợp

Phiên bản này kế thừa **nguyên trạng các module V4.1–V4.5** trong bộ mã nguồn được cung cấp: thư viện nhóm nguyên liệu, sàng lọc khoa học, optimizer, thiết kế DoE, quản lý protocol, mẻ và nhật ký đo. Không tạo hệ thống SkinSim mới và không ghi đè repository ComesticLab.

Bổ sung V4.5.1:

- Frontend Next.js dùng đường dẫn API cùng nguồn gốc `/backend/...` và reverse proxy nội bộ tới FastAPI. Không nhúng địa chỉ `localhost:8000` vào JavaScript trình duyệt.
- Trang `/experiments` có thể tìm và mở lại nghiên cứu đã lưu, nạp protocol/snapshot đã khóa, chọn mẻ có sẵn, tiếp tục nhập số đo và đánh giá. Khi đã mở nghiên cứu, JSON công thức/protocol chuyển sang read-only; dùng "Nghiên cứu mới" để tạo bản khác.
- Backend `api_v45.py` tự chọn SQLite demo (`V45_DB_PATH`) hoặc PostgreSQL (`V45_DATABASE_URL`).
- Repository PostgreSQL mới giữ hợp đồng API V4.5 với mã nghiên cứu/mẻ `STUDY-...` và `BATCH-...`, JSONB, khóa ngoại cùng nghiên cứu và trigger chống sửa/xóa quan sát.
- Migration PostgreSQL tại `migrations/001_v451_init.sql`, bộ thử HTTP thực tại `test_integration_v451.py`, Docker Compose mẫu cho máy local.

## Chạy ngay với SQLite demo trên Windows

Yêu cầu Python 3.11+ (khuyến nghị 3.12), Node.js 22, kết nối npm registry để tải Next/React.

**PowerShell — Terminal 1, thư mục dự án:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\scripts\run_backend.ps1
```

**PowerShell — Terminal 2, thư mục dự án:**

```powershell
.\scripts\run_frontend.ps1
```

Mở `http://127.0.0.1:3000/` (phân tích nguyên liệu), `http://127.0.0.1:3000/optimizer` (tối ưu cấu trúc), `http://127.0.0.1:3000/experiments` (DoE và nhật ký thí nghiệm). Backend test: `http://127.0.0.1:8000/health/v4.5`. Các trang mặc định chỉ hoạt động local. SQLite demo nằm trong `var/experiments_v45.sqlite3`.

**Linux/macOS:** cài dependencies, chạy `./scripts/run_backend.sh` trong terminal một; trong terminal hai chạy `cd frontend && npm install && RND_API_INTERNAL_URL=http://127.0.0.1:8000 npm run dev`.

## PostgreSQL local (có Docker)

1. Sao chép `.env.example` thành `.env`, đổi `POSTGRES_PASSWORD` thành mật khẩu mạnh không chứa ký tự cần URL encoding.
2. Chạy `docker compose up --build`.
3. Mở `http://127.0.0.1:3000/experiments`. Compose không xuất database hoặc API ra Internet.
4. Migration `migrations/001_v451_init.sql` **chỉ tự áp dụng khi PostgreSQL tạo volume dữ liệu mới**. Với database đã tồn tại, phải backup, rà soát và áp dụng migration thủ công. Không dùng `docker compose down -v` trên dữ liệu quan trọng.

`V45_DATABASE_URL` bắt buộc là PostgreSQL, ví dụ `postgresql+psycopg://formula_rd:***@db:5432/formula_rd`. Cài `requirements-postgres.txt` khi chạy ngoài container. Không dùng `schema_v45_postgres.sql` cũ để khởi tạo V4.5.1 vì schema đó dùng UUID, trong khi API V4.5 hiện dùng mã chuỗi.

## Kiểm thử

```bash
pytest -q test_engine.py test_scientific_v43.py test_optimizer_v44.py test_scientific_bridge_v44.py test_experimental_v45.py test_integration_v451.py
python -m compileall -q api_v45.py storage_factory_v451.py experimental_repository_postgres_v451.py
cd frontend
npm install
npm run build
```

Lệnh build Next.js yêu cầu tải dependency từ npm. Trong môi trường bàn giao hiện tại, `npm install` thất bại vì DNS `EAI_AGAIN`; **chưa thể xác nhận Next.js build hoặc hoạt động giao diện trong trình duyệt**. Mã TSX được kiểm tra cú pháp bằng TypeScript compiler toàn cục nhưng đây không thay thế kiểm tra type/build.

**Chưa kiểm thử trên PostgreSQL thực** trong môi trường này (không có server/driver kết nối). Đã xây dựng migration và repository, cần chạy integration test với database disposable trước khi áp dụng dữ liệu thật.

## Giới hạn bảo mật và khoa học

- Chưa có đăng nhập, phân quyền, CSRF, quản lý tệp đính kèm, sao lưu tự động, bộ quản lý phiên bản migrations, log truy cập, kiểm soát tenant. **Chỉ dùng trên máy cá nhân/mạng tin cậy, không triển khai công khai** trước khi bổ sung các tính năng này.
- `MEASURED` là khai báo của người nhập; bằng chứng URI và thiết bị chưa được hệ thống xác thực độc lập. `DEMO_SYNTHETIC` không góp vào kết quả đo.
- Mẻ đề xuất DoE và solver 100% vẫn chỉ là tính khả thi toán học. Số đo thực nghiệm phải do nhân viên R&D thu thập; không tạo số đo giả để tuyên bố hiệu quả, an toàn, ổn định hoặc phù hợp luật.
- `READY_FOR_RND_REVIEW` chỉ là đủ dữ liệu theo protocol R&D; mọi kết quả `approved_for_manufacturing` tiếp tục là `false`.
- Dữ liệu V4.1–V4.5 giữ trạng thái nguồn và giới hạn đã công bố trước đây; không tự coi 190 INCI ứng viên hay các dải template là dữ liệu khoa học đã xác minh.

## Gợi ý triển khai Codex

Xem `CODEX_HANDOFF_INTEGRATION_V451.md`. Ưu tiên kiểm thử Postgres và build Next.js trước khi kết nối với dịch vụ xác thực hoặc deploy. Không nhập vào repository Mountain Lab SkinSim.
