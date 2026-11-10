# Codex — Tích hợp / Kiểm thử V4.5.2

1. Giữ Formula Intelligence là dự án R&D độc lập, KHÔNG merge vào SkinSim.
2. Mở `README_V452.md` và kiểm tra mã `frontend/components/{FormulaEditor,ProtocolEditor}.tsx` và `frontend/lib/form-model.ts`.
3. `npm install && npm run build`: sửa lỗi type/build nếu có; dùng Playwright để thử biểu mẫu trên `/experiments` với viewport desktop và mobile.
4. Chạy đầy đủ pytest và `node frontend/tests/test_form_model.cjs`.
5. Trên PostgreSQL test DB, chạy migrations/001_v451_init.sql và `scripts/verify_postgres_v452.py` với TEST_POSTGRES_URL; không dùng production.
6. Test người dùng: tạo Lip Balm, thay % Beeswax/Jojoba, chọn nền lipid để cân bằng 100%, tiền kiểm nháp, tạo DoE, tạo nghiên cứu, ghi mẻ và số đo có nguồn, đọc lại.
7. Test PAD 8% chưa rõ basis: cần hiển thị cảnh báo và chặn khóa nghiên cứu khi chưa xác minh. Không tự chia PAD dựa trên phần trăm grade.
8. Giữ nguyên bản ghi thí nghiệm và nguồn, không tự tạo số đo hoặc quy định pháp lý.
9. Bổ sung hệ thống đăng nhập/phân quyền, audit logs, sao lưu và quản lý migrations trước khi triển khai trên máy chủ công khai.
10. Báo cáo kết quả build thực tế, Playwright, PostgreSQL; không tự tuyên bố đã kiểm thử môi trường chưa chạy.
