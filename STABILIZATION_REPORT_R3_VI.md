# Technical stabilization V4.5.2-R3 — báo cáo nghiệm thu từng phần

Ngày rà soát: 10/11/2026. Trạng thái: **prototype nội bộ, chưa được phép triển khai công khai**.

## Những kết quả xác minh được

| Hạng mục | Bằng chứng | Kết luận |
| --- | --- | --- |
| Python/API toàn bộ | `python -m pytest -q` | PASS — 104/104 |
| Logic biểu mẫu | `node frontend/tests/test_form_model.cjs` | PASS — 11 assertions |
| Chạy HTTP FastAPI thực | `python scripts/live_auth_smoke_r3.py` | PASS — 200/401/403/login/logout |
| Cookie/phiên/role bảo vệ API | `test_auth_r3.py` | PASS — 7 bài kiểm tra |
| Xác minh người tạo study | `test_auth_r3.py::test_creator_comes_from_session_not_request_body` | PASS — chống giả mạo trường created_by khi auth bật |
| Kiểm tra tĩnh TypeScript | 11 tệp .ts/.tsx (không tính .d.ts) | Không thấy lỗi cú pháp; **không thay thế Next build** |
| YAML CI | PyYAML parse, 15 bước | PASS cấu trúc; **chưa chạy workflow thật** |
| Next.js build | chưa cài được dependency npm | BLOCKED |
| Chromium E2E | yêu cầu Next.js đã build và đang chạy | BLOCKED |
| PostgreSQL `_test` thực | không có PostgreSQL server / Docker | BLOCKED |
| Backup/restore Postgres | không có PostgreSQL thật | BLOCKED |
| Xác thực / RBAC production | chỉ có demo local SQLite, chưa có bảo mật đa tenant / CSRF đầy đủ | NOT READY |

## Thay đổi R3

1. `auth_r3.py`: tài khoản cục bộ, scrypt password hashing, token phiên ngẫu nhiên lưu dưới dạng SHA-256, cookie HttpOnly SameSite Strict, khóa sau đăng nhập sai liên tiếp, giới hạn Origin cho thao tác có phiên.
2. `api_v45.py`: tích hợp middleware xác thực opt-in; ghi `created_by` từ phiên, không tin tham số client; giữ API khoa học và database V4.5.2.
3. `frontend/app/login/page.tsx` và `frontend/components/AuthBar.tsx`: giao diện đăng nhập và báo phiên.
4. `scripts/manage_users_r3.py`: tạo/vô hiệu hóa tài khoản cục bộ, không nhận mật khẩu qua tham số lệnh.
5. `scripts/browser_smoke_v452.py`: thêm bước đăng nhập browser nếu được cấp biến môi trường kiểm thử; cấu hình CI tạo tài khoản thử ngẫu nhiên.
6. `compose.yaml`: volume riêng `auth_data` giúp tài khoản thử không biến mất khi khởi động lại container.

## Giới hạn và rủi ro còn lại

- **KHÔNG mở cổng ra Internet** khi `RND_AUTH_MODE=disabled` (mặc định phục vụ tương thích thử nghiệm trước đây).
- `RND_AUTH_MODE=required` chỉ là lớp xác thực nguyên mẫu nội bộ. Thiếu SSO/MFA, CSRF token chuyên biệt, quyền từng nghiên cứu, khóa ứng dụng nhiều người dùng, giám sát đăng nhập, phòng chống tấn công theo IP, bảo vệ khi XSS, kiểm thử thâm nhập và chính sách lưu giữ phiên.
- PostgreSQL mới là tầng dữ liệu R&D, tài khoản của R3 vẫn ở SQLite cục bộ. Phải có backup riêng cho `auth_data` nếu dùng nội bộ. Chưa thử restore.
- Nguyên liệu, luật pháp lý và dữ liệu khoa học chưa thay đổi, không mở thêm phiên bản chức năng.
- Tất cả số đo DEMO vẫn phải bị loại khỏi đánh giá khoa học; việc xác thực người dùng không biến số đo thành bằng chứng đã kiểm định.

## Các Gate cần hoàn tất

- **Gate A:** commit lockfile Next.js, chạy build và browser Chromium thật qua cả ba màn hình và trang login.
- **Gate C:** PostgreSQL `_test` migration 001/002, kiểm thử lưu nghiên cứu/mẻ/đo, backup/restore trong môi trường thử riêng.
- **Gate D:** xác thực/RBAC production, quyền nghiên cứu, nhật ký người ghi dữ liệu, CSRF và bảo vệ triển khai ngoài localhost.

Không đánh dấu Gate A/C/D đạt trước khi có log từ môi trường thực.
