# Formula Intelligence V4.5.2 — Stabilization R4 (không nâng chức năng khoa học)

Ngày kiểm tra: 10/11/2026. Trạng thái: **prototype nội bộ; chưa được triển khai công khai**.

## Phạm vi

- Kế thừa V4.5.2-R3, không tích hợp SkinSim, không thêm dữ liệu INCI/giới hạn pháp lý/AI.
- Kiểm tra hợp đồng API giữa các màn hình Next.js và OpenAPI FastAPI.
- Cứng hóa cấu hình đăng nhập ở mức nguyên mẫu: đăng nhập yêu cầu Origin nằm trong danh sách cho phép, kể cả khi request thiếu Origin; Docker Compose mặc định `RND_AUTH_MODE=required`.
- Chặn CI dùng `npm install` không có lockfile: Gate A yêu cầu **frontend/package-lock.json được tạo và commit** rồi mới chạy `npm ci` + build + Chromium.
- Có script tiền kiểm `scripts/gate_preflight_r4.py` báo tình trạng, **không tự suy đoán PASS**.

## Kiểm thử thực chạy

| Kiểm thử | Trạng thái |
|---|---|
| `python -m pytest -q` | **106/106 PASS** |
| `node frontend/tests/test_form_model.cjs` | **11/11 PASS** |
| `python scripts/check_frontend_api_contract_r4.py` | **22 hợp đồng UI → API khớp OpenAPI** |
| `python scripts/live_auth_smoke_r3.py` | **PASS** (200/401/403, login/logout) |
| `typescript.transpileModule` | **11 tệp, không phát hiện lỗi cú pháp**; KHÔNG thay thế type-check/build |
| Workflow YAML | **Đọc được**, nhưng chưa chạy trong GitHub Actions |
| `npm ci` / `next build` | **BLOCKED** — chưa có lockfile và Next.js dependency; npm registry DNS EAI_AGAIN |
| Chromium trên Next thực tế | **NOT RUN** — chưa build Next |
| PostgreSQL migration, E2E, backup và restore | **NOT RUN** — không có server PostgreSQL/Docker trong phiên này |
| Pen-test, quyền per-study và production auth | **NOT READY** |

## Gate A — Bắt buộc chạy trên máy có npm registry

1. Tại `frontend`, chạy `npm install --package-lock-only`, kiểm tra phiên bản được resolve; commit `package-lock.json` vào **repository Formula Intelligence độc lập**.
2. Chạy `npm ci`, `npm run build` và `npm run start`.
3. Chạy FastAPI với `RND_AUTH_MODE=required`, tạo tài khoản demo qua `scripts/manage_users_r3.py`.
4. Chạy `python scripts/browser_smoke_v452.py` với tài khoản thử. Đính kèm log và ảnh màn hình. Không chuyển trạng thái đạt chỉ bằng check cú pháp.

## Gate C — PostgreSQL test riêng

1. Tạo database thử kết thúc `_test` và thiết lập `TEST_POSTGRES_URL`.
2. Chạy `python scripts/apply_test_migrations_v452.py` rồi `python scripts/verify_postgres_v452.py`.
3. Tạo backup, phục hồi vào một database *_test khác; đối chiếu số nghiên cứu, mẻ, số đo, candidate hash và trigger bất biến.
4. Chưa có script tự động kiểm tra restore: đây vẫn là công việc P0 đang mở.

## Gate D — bảo mật

- Bản `required` mới ở mức cục bộ. `viewer/reviewer` không ghi được studies, nhưng chưa có phân quyền theo từng nghiên cứu.
- `created_by` lấy từ phiên đăng nhập, nhưng `operator`/`weighed_by` của mẻ và số đo vẫn do người dùng khai báo. **Chưa có `recorded_by` bất biến gắn phiên cho từng số đo**; chưa được xem là hồ sơ audit/GxP.
- Chưa có MFA, CSRF token chuyên biệt, rate limit theo IP, HTTPS và secure-cookie trong môi trường production, giám sát và backup riêng cho SQLite auth.
- **Không đưa ra Internet**; không coi các kiểm thử auth hiện tại là kiểm thử an ninh production.

## Quyết định

Đóng băng V4.5.2; sử dụng R4 chỉ như bản vá nghiệm thu. Điều kiện mở lại phát triển chức năng: Gate A/C và vòng kiểm soát Gate D được kiểm thử trên môi trường đầy đủ. Mọi dữ liệu khoa học từ V4.5.2 giữ nguyên.
