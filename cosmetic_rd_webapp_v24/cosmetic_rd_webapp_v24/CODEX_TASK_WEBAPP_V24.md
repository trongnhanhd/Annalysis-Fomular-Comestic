# Nhiệm vụ Codex tiếp theo — Cosmetic R&D V2.5

## Trạng thái bàn giao

V2.4 bổ sung Web App chạy không cần npm trong `backend/webapp/`, dùng FastAPI cùng nguồn với backend. Giao diện Next.js V2.3 vẫn giữ tại `frontend/`. Bộ giải, MCP và catalog nghiên cứu không bị thay đổi. Bản hiện tại dùng được trên máy cá nhân, chưa phải production.

## Quy tắc bất biến

1. Không thay bất kỳ tỷ lệ % tham khảo thành giá trị đo được hoặc nồng độ tối ưu nếu không có nghiên cứu chứng minh trực tiếp.
2. Giữ `engine.py` và `data/{evidence_catalog,preservation_systems,regulatory_catalog}.json` nguyên vẹn trừ khi có bằng chứng, thay đổi có kiểm toán và test.
3. Nguồn người dùng nhập phải có trạng thái `draft` và chưa trở thành bộ ràng buộc cứng.
4. Lưu lịch sử phiên bản phân tích/công thức, không ghi đè công thức cũ.
5. Giữ mọi nội dung UI tiếng Việt, tên INCI và thuật ngữ khoa học quốc tế đúng chuẩn.

## Ưu tiên P0 — hoàn thiện production Next.js

- Cài package từ registry và chạy `cd frontend && npm ci || npm install`, `npm run typecheck`, `npm run build` trên Node 22.
- Chạy FastAPI/PostgreSQL và ứng dụng Next.js trong `compose.yaml`, e2e với Playwright trực tiếp trên URL Next.js.
- Đồng bộ giao diện và luồng V2.4 về Next.js (hoặc giữ `/app` cho local), tránh duy trì hai bộ giao diện về lâu dài.
- Sửa thông báo lỗi API rõ ràng, xử lý trạng thái tải/hết hạn, kiểm thử keyboard và screen-reader cơ bản.
- Thay shared token thử nghiệm bằng đăng nhập người dùng, RBAC, CSRF protection, server-side session, audit log, HTTPS, secrets và rate limit.

## Ưu tiên P1 — dữ liệu và nghiên cứu

- Dùng Alembic migration cho PostgreSQL, thêm backup/restore, kiểm thử đọc/ghi với database thật.
- Thêm nguồn tham khảo có DOI/PMID, tác giả, năm, công thức nền, hiệu quả và điều kiện thí nghiệm; quy trình review hai người.
- Tạo trang so sánh nhiều công thức, so sánh hai nhãn cùng INCI, chuẩn xuất báo cáo khoa học với trích dẫn.
- Dựng bản đồ thiếu dữ liệu pháp lý cho EU, Mỹ, Hàn, Trung, Việt Nam, ASEAN, ngày hiệu lực từng luật.

## Ưu tiên P2 — MCP

- Chạy thử MCP SDK thật, contract test cho 9 công cụ, giới hạn quyền chỉ đọc cho ChatGPT mặc định.
- Áp quyền user-level, logging và cho phép tắt công cụ ghi khi kết nối AI.

## Tiêu chí nghiệm thu

- `pytest` backend và hợp đồng API đạt, không có số liệu tự tạo trong catalog.
- `npm run typecheck && npm run build` đạt; sáu màn hình Next.js và quy trình phân tích→lưu→xem báo cáo chạy trên Chromium desktop và mobile.
- PostgreSQL thật lưu và khôi phục được dữ liệu; API có auth, không bị lộ khóa trong browser bundle.
- Kết nối MCP giao thức thực được chứng minh bằng log và test, không chỉ kiểm tra cú pháp.
- Bản production có HTTPS, môi trường bí mật, backup và tài liệu quản trị.
