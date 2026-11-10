# FORMULA INTELLIGENCE — RÀ SOÁT V4.5.2-R2 (không phát triển tính năng mới)

**Ngày:** 10/11/2026. **Nguồn:** V4.5.2-R1. **Đích:** R2, giữ nguyên các chức năng R&D.

## 1. Kết quả đã chạy trong môi trường hiện tại

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Kiểm thử Python/API | **PASS** | `python -m pytest -q`: **97/97** |
| Kiểm tra logic biểu mẫu | **PASS** | `node frontend/tests/test_form_model.cjs`: 11 assertions |
| Script kiểm soát migration an toàn | **PASS unit** | Từ chối URL thiếu, SQLite, DB không kết thúc `_test`; **chưa chạy PG thật** |
| Phân tích cú pháp CI YAML | **PASS** | PyYAML đọc một job `validate` |
| Build Next.js | **BLOCKED** | Không có module Next trong môi trường; npm registry trả `EAI_AGAIN` khi truy cập |
| PostgreSQL thật và migration 001/002 | **BLOCKED** | Không có máy chủ/binary PostgreSQL trong môi trường; không được đánh dấu PASS |
| Trình duyệt Chromium qua Next | **BLOCKED** | Có Chromium, nhưng Next chưa cài được; chưa chạy E2E |
| Xác thực/RBAC và sao lưu phục hồi | **NOT IMPLEMENTED** | Chưa cho phép truy cập công khai |

## 2. Thay đổi của R2

- `scripts/apply_test_migrations_v452.py`: tạo schema trên **database PostgreSQL dùng để kiểm thử** với guard `_test`, từ chối trạng thái schema một nửa, bỏ qua nếu đã đủ 001/002. Không phải công cụ migration production.
- `scripts/browser_smoke_v452.py`: bài thử Chromium (Playwright) mở trang `/`, `/optimizer`, `/experiments`, gọi `/backend/health/v4.5` và xác minh giao diện hiển thị kết nối API. Chỉ đọc, không ghi dữ liệu thử vào database.
- `.github/workflows/stabilization-v452.yml`: CI chạy pytest, migration và test trên PostgreSQL 17, cài và build Next 15, chạy Chromium smoke thực tế. **Chưa được kích hoạt hoặc chạy trên GitHub** vì chưa đăng lên repository của chính ứng dụng này.
- `test_stabilization_gates_v452.py`: 8 bài kiểm tra guard migration và điều kiện môi trường local.

## 3. Các cổng nghiệm thu và định nghĩa hoàn thành

**Gate A — Frontend:** sau khi npm truy cập được registry, cài dependency; tạo/commit `package-lock.json`; `npm ci`, `npm run build`, Chromium test và thao tác bằng trình duyệt phải đạt. Không tạo lockfile giả.

**Gate B — API:** giữ OpenAPI không trùng endpoint; xác minh Next rewrite qua trình duyệt. Kết quả R2 chỉ được xác nhận tại mức unit/API và cấu hình pipeline.

**Gate C — PostgreSQL:** tạo DB *riêng*, tên `_test`; apply migration 001 và 002 bằng script test; chạy `verify_postgres_v452.py` và sao lưu/phục hồi kiểm chứng trước production. Không chạy migration thật lên DB hiện có khi chưa backup.

**Gate D — Bảo mật:** còn thiếu đăng nhập, phân quyền R&D/QC/Admin, nhật ký thao tác và giải pháp sao lưu. Chỉ sử dụng nội bộ trên localhost; cấu hình Docker chỉ public web trên `127.0.0.1`.

**Gate E — Khoa học/pháp lý:** không thay đổi trạng thái xác minh của dữ liệu INCI/grade/giới hạn. Không dùng kết quả mô phỏng như phê duyệt sản xuất.

## 4. Cách chạy trên máy có mạng

```bash
python -m pip install -r requirements.txt -r requirements-postgres.txt 'playwright>=1.50,<2'
python -m pytest -q
node frontend/tests/test_form_model.cjs
cd frontend && npm install && npm run build && cd ..
```

Chạy PostgreSQL 17 trên database kiểm thử `formula_rd_test`, sau đó:

```bash
export TEST_POSTGRES_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/formula_rd_test'
python scripts/apply_test_migrations_v452.py
python scripts/verify_postgres_v452.py
```

Chạy backend và frontend theo README R1, rồi:

```bash
python -m playwright install chromium
python scripts/browser_smoke_v452.py http://127.0.0.1:3000
```

## 5. Quyết định

**Đóng băng V4.5.2; R2 là bản chuẩn bị kiểm thử nghiệm thu, chưa phải bản nghiệm thu cuối.** Không triển khai V4.6, không đẩy vào dự án SkinSim/ComesticLab; giữ nguyên tất cả dữ liệu nghiên cứu.
