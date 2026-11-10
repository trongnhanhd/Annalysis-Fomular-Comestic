# BÀN GIAO CODEX — FORMULA INTELLIGENCE V4.5.2-R2

Mục tiêu: đóng Gate A (Next.js), Gate C (PostgreSQL), rồi Gate D (auth/RBAC), không mở tính năng R&D mới.

1. Đọc `STABILIZATION_REPORT_R2_VI.md`, `STABILIZATION_REPORT_VI.md` và toàn bộ schema.
2. Không tích hợp vào `ComesticLab` hoặc `SkinSim`. Dùng repository độc lập của Formula Intelligence.
3. Có mạng: tại `frontend/` chạy `npm install`, tạo/commit lockfile thật; kiểm tra dependency, `npm ci`, `npm run build`.
4. Dùng riêng PostgreSQL 17 với tên database kết thúc `_test`. Chạy `scripts/apply_test_migrations_v452.py`, `scripts/verify_postgres_v452.py`. Ghi log PASS/FAIL; không chạy trên DB đang vận hành.
5. Chạy hai server, thực thi `scripts/browser_smoke_v452.py`, xác nhận `/backend/health/v4.5` hoạt động từ chính trình duyệt.
6. Sau khi Gate A/C đạt, thiết kế xác thực bằng session cookie httpOnly, CSRF protection và RBAC theo vai trò trước khi public, không nhúng API secret trong `NEXT_PUBLIC_*` hoặc phía client.
7. Thử backup/restore có bằng chứng, bảo đảm mẻ/candidate/đo không bị thay đổi và dữ liệu lịch sử được giữ nguyên.
8. Ghi trạng thái khách quan: PASS, FAIL, BLOCKED, NOT TESTED. Chưa đủ nguồn thì để trống, không bịa mức % hay kết quả thực nghiệm.

Các bước 3–7 **chưa chạy hoàn chỉnh trong môi trường đóng gói**. Workflow `.github/workflows/stabilization-v452.yml` được cung cấp để có thể chạy trên CI sau khi dự án được đưa vào đúng repository.
