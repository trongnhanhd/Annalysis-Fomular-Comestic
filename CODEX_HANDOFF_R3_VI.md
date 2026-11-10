# Codex — Stabilization R3 handoff

Không phát triển tính năng R&D mới. Giữ riêng repository Formula Intelligence, không đưa mã vào ComesticLab/SkinSim.

1. Xem `README_R3_VI.md`, `auth_r3.py`, `test_auth_r3.py`, `frontend/app/login/page.tsx` và `frontend/components/AuthBar.tsx`.
2. Cài dependency tại máy có Internet; tạo và commit `frontend/package-lock.json`, chạy `npm ci`, `npm run build`. Kiểm tra TypeScript và cả ba route.
3. Chạy GitHub Actions workflow `.github/workflows/stabilization-v452.yml` trong **repository Formula Intelligence** đã được người dùng chỉ định; workflow có PostgreSQL `_test`, build Next.js và Chromium smoke với đăng nhập.
4. Giữ các kiểm thử Python; rà soát HTTP 401/403/CSRF/role khi `RND_AUTH_MODE=required`. Không được coi lớp auth SQLite demo là hệ thống production.
5. Kiểm tra cookie Set-Cookie qua Next proxy và SameSite khi dùng `http://localhost:3000` thực tế; khắc phục bug nếu E2E phát hiện.
6. Chạy thử PostgreSQL `_test`, migration 001/002, cập nhật mã kiểm thử backup/restore **trên DB thử**, không chạm production.
7. Thiết kế giải pháp xác thực/RBAC production được duyệt trước khi triển khai public: tổ chức/nhóm, phân quyền hồ sơ, nhật ký audit, session management, CSRF, HTTPS, backup và disaster recovery.
8. Báo cáo riêng `PASS / FAIL / BLOCKED` cho Gate A/C/D với log và bằng chứng. Giữ cảnh báo scientific/regulatory chưa kiểm chứng.

Lưu ý không sử dụng repo `trongnhanhd/ComesticLab` làm nơi tích hợp nếu người dùng chưa thay đổi phạm vi độc lập.
