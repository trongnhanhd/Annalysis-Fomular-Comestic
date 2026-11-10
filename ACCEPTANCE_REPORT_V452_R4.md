# Báo cáo nghiệm thu Formula Intelligence V4.5.2-R4

Ngày: 10/11/2026. Nhánh: `v452-r4-acceptance`. CI xanh: https://github.com/trongnhanhd/Annalysis-Fomular-Comestic/actions/runs/42765294470

## Kết quả theo Gate

| Gate | Trạng thái | Căn cứ |
|---|---|---|
| A. Frontend | **PASS** | `npm ci` từ lockfile, `npm run build` (Next 15.5.29), `tsc --noEmit`, `tests/test_form_model.cjs` 11/11, Chromium smoke qua `/backend` có đăng nhập: `/`, `/optimizer`, `/experiments`, `/login`, rewrite tới FastAPI, không lỗi JavaScript. |
| C. Database | **PASS (PostgreSQL 17.11 cục bộ, DB `*_test`)** | Migration 001 + 002 áp dụng; `verify_postgres_v452.py` pass; FK và CHECK chặn dữ liệu sai; trigger bất biến chặn UPDATE/DELETE; backup `pg_dump -Fc` và restore sang `formula_ci_restore_test` khớp số dòng (2/2/2/2/2), 6 trigger, 7 khóa ngoại; rollback từ chối khi còn dữ liệu, chạy sạch trên DB rỗng và migrate lại được. |
| D. Bảo mật | **CÓ ĐIỀU KIỆN: chỉ phù hợp bản thử nội bộ, không đủ điều kiện công khai** | Xem mục "Gate D" bên dưới. |

## Kiểm thử và số liệu

- Backend pytest: **110/110 pass**, cả khi `V45_DATABASE_URL` trỏ tới DB PostgreSQL rỗng và khi dùng SQLite mặc định.
- Contract script `scripts/check_frontend_api_contract_r4.py`: exit 0.
- CI GitHub Actions: 16 bước, toàn bộ **success**.

## Sửa lỗi đã thực hiện

1. **Thiếu lockfile**: tạo `frontend/package-lock.json`.
2. **Lỗi TypeScript chặn build**: `app/experiments/page.tsx` dùng `scenario` có thể `null`. Thêm guard.
3. **Thiếu dependency test**: `requirements.txt` không có `httpx2`, Starlette mới yêu cầu. Test không chạy được.
4. **Test phụ thuộc encoding Windows**: `test_integration_v451.py` đọc file không chỉ định UTF-8.
5. **Định danh ghi số đo** (Gate D): `operator` và `weighed_by` do trình duyệt gửi, có thể giả mạo. Khi `RND_AUTH_MODE=required`, hai trường này nay lấy từ phiên đăng nhập (`api_v45.py`, hàm `_bind_actor`).
6. **Unit test phụ thuộc trạng thái DB**: CI đặt `V45_DATABASE_URL` nhưng migration chạy sau pytest, gây 3 lỗi. Thêm `conftest.py` xóa biến này cho unit test.
7. **CI healthcheck PostgreSQL**: tham số `--health-cmd` có nháy đơn bị Docker từ chối (exit 125).
8. **Script in tiếng Việt trên Windows**: `verify_postgres_v452.py` và `browser_smoke_v452.py` lỗi cp1252.
9. **Thời gian chạy job**: tăng `timeout-minutes` từ 35 lên 45 (cài Playwright với `--with-deps`).

## Bổ sung

- `test_gate_d_rbac.py`: 4 test. Ma trận vai trò (viewer và reviewer bị 403 khi ghi; editor và admin được ghi); `operator` và `weighed_by` ghi theo phiên; khóa tài khoản sau 5 lần sai; logout vô hiệu hóa phiên.
- `migrations/rollback/001_v451_init.down.sql` và `002_v452_traceability.down.sql`. Chỉ chạy khi bảng rỗng, không xóa dữ liệu.

## Gate D: chi tiết

**Đã có:** cookie `HttpOnly` và `SameSite=strict`; kiểm tra Origin cho mọi thao tác ghi có phiên; viewer và reviewer không ghi được; `created_by`, `operator`, `weighed_by` lấy từ phiên; khóa tài khoản sau 5 lần sai (15 phút); phiên hết hạn sau 8 giờ và bị thu hồi khi tài khoản bị vô hiệu hóa.

**Chưa đạt, chặn công khai:**
- **HTTPS chưa được kiểm chứng.** Cookie `Secure` chỉ bật khi `RND_AUTH_COOKIE_SECURE=true`, mặc định tắt.
- **Chưa có phân quyền theo từng nghiên cứu.** Mọi editor ghi được mọi nghiên cứu.
- **Vai trò `reviewer` chưa có chức năng nào.**
- **Không có audit log riêng cho sự kiện đăng nhập, đăng xuất, khóa tài khoản.**
- **Khóa đăng nhập theo tài khoản, không theo IP.** Vẫn có thể bị thử mật khẩu dàn trải qua nhiều tài khoản.
- **Hệ xác thực là SQLite cục bộ**, không phải IdP sản xuất.
- Trạng thái `RND_AUTH_MODE=disabled` vẫn là mặc định, cho phép truy cập không xác thực.

## Vấn đề phát hiện, chưa sửa

- **`next.config.ts`: `RND_API_INTERNAL_URL` được đọc lúc build.** Đổi biến khi chạy `next start` không có tác dụng; phải build lại. Đã xác nhận trong `.next/routes-manifest.json`. CI không bị ảnh hưởng vì đặt biến trước khi build.
- **Log pytest của CI** không xem được khi chưa đăng nhập GitHub. Đã thêm annotation `::error::` và artifact để khắc phục.

## Môi trường thử và giới hạn

- PostgreSQL 17.11 cài bằng winget trên máy cục bộ, không phải Docker Compose (Docker không có sẵn).
- Cổng 8000 và 3000 đang bị tiến trình Node/Python không thuộc dự án này giữ. Chạy API ở 8100 và Next ở 3200 (ghi nhận; không kill tiến trình đó).
- Chưa kiểm thử: HTTPS/TLS, Docker Compose, khôi phục sau sự cố (PITR), tải cao, bảo mật ứng dụng bên ngoài.
- Dữ liệu DEMO_SYNTHETIC còn trong `formula_ci_test`; không đưa vào nghiên cứu thật.
- Không có production DB nào được kết nối hay thay đổi.

## Lệnh tái lập

```powershell
python -m pip install -r requirements.txt -r requirements-postgres.txt "playwright>=1.50,<2"
$env:TEST_POSTGRES_URL="postgresql+psycopg://formula_ci:...@127.0.0.1:5432/formula_ci_test"
python -m pytest -q
python scripts/apply_test_migrations_v452.py
python scripts/verify_postgres_v452.py
cd frontend; npm ci; node tests/test_form_model.cjs; npm run build
```
