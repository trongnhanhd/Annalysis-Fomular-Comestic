# Formula Intelligence V4.5.2 — Stabilization R3

**Đây là bản ổn định / bảo mật nguyên mẫu nội bộ, KHÔNG phải V4.6.** Không gộp với SkinSim.

## Phạm vi bản vá

- Bổ sung xác thực **tùy chọn** `RND_AUTH_MODE=required` với tài khoản cục bộ lưu trong SQLite riêng; cookie HttpOnly, SameSite=Strict, phiên 8 giờ và khóa tạm tài khoản sau nhiều lần đăng nhập sai.
- Phân quyền sơ bộ: `viewer`, `reviewer` được xem và tính toán; `editor`, `admin` được tạo nghiên cứu, ghi mẻ và số đo.
- Khi xác thực bật, trường `created_by` của nghiên cứu được ghi bằng người dùng đã đăng nhập; không tin tên do client tự gửi.
- Giao diện `/login` và thanh trạng thái tài khoản; tài khoản vô hiệu hóa sẽ thu hồi phiên.
- Mở rộng bài thử Chromium của CI để đăng nhập và thực hiện kiểm tra ba màn hình qua `/backend`.
- Giữ nguyên các module tính toán và dữ liệu khoa học V4.5.2-R2.

## Cài đặt thử cục bộ

Chạy theo `README_V452.md` để cài backend + frontend; vẫn cần kết nối mạng để tải các gói npm lần đầu.

```bash
# Tại thư mục project. Tạo người dùng lần đầu bằng terminal tương tác:
python scripts/manage_users_r3.py --username admin.local --role admin
# Đặt RND_AUTH_MODE=required và RND_AUTH_DB_PATH=var/auth_r3.sqlite3
python -m uvicorn api_v45:app --host 127.0.0.1 --port 8000
# Ở terminal khác:
cd frontend && npm install && npm run build && npm run start
```

Sau khi bật mode required, mở `http://localhost:3000/login` và đăng nhập. Nếu chạy Next trên `127.0.0.1:3000` thì truy cập đúng host đó để đồng bộ cookie.

Vô hiệu hóa tài khoản bằng lệnh terminal:

```bash
python scripts/manage_users_r3.py --username employee.old --disable
```

Trong Docker Compose, tài khoản được lưu trên volume `auth_data` tách khỏi PostgreSQL dữ liệu R&D. Có thể tạo tài khoản bằng `docker compose exec api python scripts/manage_users_r3.py --username admin.local --role admin` (đặt `RND_AUTH_MODE=required` và `POSTGRES_PASSWORD` trong `.env`).

## Kiểm thử đã xác nhận tại môi trường hiện tại

- 104/104 kiểm thử Python/API (gồm 7 bài xác thực mới).
- 11/11 kiểm thử logic biểu mẫu Node.
- HTTP thật: health 200, chưa đăng nhập 401, đăng nhập 200, GET sau đăng nhập 200, viewer ghi bị từ chối 403, đăng xuất 200, phiên hết hiệu lực 401.
- `Next.js build` và Chromium E2E thật **chưa chạy** do không tải được dependency Next.js.
- PostgreSQL server thật **chưa có**, migration/backup/restore chưa xác minh ở môi trường này.

## Ranh giới bảo mật (rất quan trọng)

- Mặc định `RND_AUTH_MODE=disabled` để giữ nguyên luồng dùng thử cục bộ trước đây; **không đưa ra Internet khi còn disabled**. Docker Compose chỉ mở web tại `127.0.0.1:3000`.
- Chế độ `required` vẫn chỉ dành cho **demo mạng nội bộ, chưa đáp ứng yêu cầu production**: cơ sở tài khoản dùng SQLite cục bộ khác với PostgreSQL, chưa có SSO, MFA, phân quyền từng nghiên cứu/tenant, CSRF token độc lập, giới hạn request theo IP, giám sát an ninh, CSP, kiểm thử thâm nhập, backup tài khoản, khôi phục và quản trị tài khoản đầy đủ.
- Không được triển khai ra Internet chỉ nhờ bật `required`; cần HTTPS, Secure cookie, reverse proxy, xác thực/RBAC hoàn chỉnh, chính sách dữ liệu, backup/restore, rà soát bảo mật và kiểm thử browser/PostgreSQL thực.
- `recorded_by` / chữ ký điện tử của người ghi số đo chưa có trường bất biến riêng. `operator` vẫn là người thao tác mẻ do R&D khai báo, không đồng nghĩa người đang đăng nhập. Không sử dụng mẻ này làm hồ sơ GxP được phê duyệt.
- File SQLite xác thực được bảo vệ theo quyền file OS và nên được backup/giám sát riêng. Đừng đưa lên Git.

## Gate tiếp theo

1. **Gate A:** `npm ci` với lockfile đã commit; Next build và Chromium thật qua cả ba màn hình, gồm đăng nhập.
2. **Gate C:** áp dụng migration vào PostgreSQL `_test` bằng CI; xác nhận backup/restore và đường đi DoE → mẻ → đo.
3. **Gate D:** chọn hệ thống auth production/nhân sự, hoàn thiện RBAC theo nghiên cứu, nhật ký audit thao tác và CSRF trước khi công khai.

Không cập nhật phiên bản khoa học hoặc tự sửa dữ liệu nguồn chưa xác minh.
