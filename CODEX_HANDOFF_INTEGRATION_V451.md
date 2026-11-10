# Nhiệm vụ Codex: Hoàn thiện tích hợp V4.5.1

Đọc `README_INTEGRATION_V451.md`, `api_v45.py`, `storage_factory_v451.py`, `experimental_repository_postgres_v451.py`, `migrations/001_v451_init.sql`, `frontend/next.config.ts` và `frontend/app/experiments/page.tsx`.

## Quy tắc bắt buộc

- Giữ Formula Intelligence là Web App R&D **độc lập**, không kết hợp với Mountain Lab SkinSim hoặc MixColor.
- Không thay số liệu thực nghiệm bằng giá trị mô phỏng, không tự coi `MEASURED` là được phê duyệt, không hợp thức hóa kết quả chỉ vì cân bằng 100%.
- Tiếp tục sử dụng API và cấu trúc dataset hiện có. Không phá vỡ 72 kiểm thử kế thừa.
- Giữ frontend tiếng Việt; không đưa secrets hoặc URL PostgreSQL vào client.

## Công việc tiếp theo

1. Dùng môi trường npm truy cập mạng để chạy `npm ci` (khi có lockfile) hoặc `npm install`, `npm run build`; khắc phục lỗi type nếu có, tạo `package-lock.json` và khóa phiên bản đã kiểm tra.
2. Bật PostgreSQL disposable, chạy migration và kiểm tra E2E: tạo nghiên cứu, tạo mẻ, ghi MEASURED với bằng chứng, thêm DEMO, supersede, đóng/mở lại, đánh giá báo cáo; xác nhận trigger UPDATE/DELETE bị chặn và không thể liên kết batch của study khác.
3. Thêm quản lý phiên bản migration, backup/restore, transaction retry khi DB tạm mất kết nối; đối chiếu SQL schema cũ (UUID) trước khi có migration từ database thật.
4. Bổ sung authentication, authorization, CSRF, HTTPS và audit trước khi đưa lên môi trường production. Cấm API phát hiện nhận dữ liệu từ người không có quyền.
5. Hoàn thiện giao diện không phụ thuộc nhập JSON thô: form chọn nguyên liệu và grade, quy trình DoE, chọn protocol theo mẫu; duy trì cảnh báo khoa học và nguồn.
6. Chạy regression tests; báo rõ phần chưa xác minh và test chưa chạy.

## Tiêu chí hoàn thành

- `pytest` tất cả pass, `npm run build` pass.
- E2E flow Next.js → same-origin `/backend` → FastAPI → PostgreSQL chạy trên máy dev.
- Reload trang vẫn mở lại study/batch/measurement.
- File snapshot không bị sửa khi đã lưu.
- Mọi trạng thái phê duyệt sản xuất vẫn `false`.
- Ghi rõ commit, đường dẫn file thay đổi, các rủi ro còn lại.
