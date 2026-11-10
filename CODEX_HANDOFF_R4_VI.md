# Codex — nghiệm thu Formula Intelligence V4.5.2-R4

Không phát triển V4.6. Không gộp với Mountain Lab SkinSim. Không cập nhật số liệu INCI/COA/giới hạn pháp lý thiếu bằng chứng.

1. Đọc `STABILIZATION_REPORT_R4_VI.md`, `CODEX_HANDOFF_R3_VI.md` và `scripts/gate_preflight_r4.py`.
2. **Gate A:** trên máy có npm registry, tại `frontend`, tạo `package-lock.json` bằng `npm install --package-lock-only`; commit lockfile, chạy `npm ci && npm run build`. Sửa lỗi TypeScript, React hoặc Next thật nếu có, không bỏ qua lỗi. Chạy `scripts/browser_smoke_v452.py` qua `/backend` với backend `RND_AUTH_MODE=required` và tài khoản test.
3. **Gate C:** chuẩn bị PostgreSQL database riêng tên `_test`, áp dụng migration bằng `scripts/apply_test_migrations_v452.py`, chạy `scripts/verify_postgres_v452.py`, thực hiện backup và restore trên DB thử, so sánh nội dung và trigger bất biến.
4. **Gate D:** đánh giá rủi ro RBAC theo từng nghiên cứu, bất biến hóa danh tính tài khoản ghi số đo (recorded_by), CSRF và HTTPS. Thực hiện migration có rollback; không giả mạo danh tính thao tác bằng `operator` do trình duyệt gửi.
5. Chạy `python -m pytest -q`, `node frontend/tests/test_form_model.cjs` và `python scripts/check_frontend_api_contract_r4.py`; lưu log và ảnh E2E. Viết báo cáo PASSED/BLOCKED/FAILED từng Gate.
6. **Không** đưa dữ liệu thí nghiệm DEMO_SYNTHETIC vào kết quả nghiên cứu thật hoặc thuật toán học.

R4 là bản chạy thử nội bộ. Việc có script nghiệm thu không phải bằng chứng nghiệm thu thành công.
