# CODEX TASK — Cosmetic R&D Intelligence V2.3

## Vai trò
Senior Frontend Engineer + QA cho một phần mềm R&D mỹ phẩm độc lập. Sửa trực tiếp repository này, giữ toàn bộ UI tiếng Việt, không gộp với dự án khác.

## Việc đã có
- Frontend Next.js App Router / React / TypeScript; layout responsive 6 mục, login + BFF có session.
- Component chính trong `frontend/components`: `Workspace.tsx`, `AnalysisView.tsx`, `LibraryViews.tsx`, `UI.tsx`, `Icons.tsx`.
- API và solver FastAPI, cơ sở dữ liệu, MCP từ V2.2. Không thay đổi các catalog khoa học V2.1.
- `preview/` là HTML tĩnh với dữ liệu ví dụ, không phải bản chạy Next.

## Thứ tự nhiệm vụ BẮT BUỘC
1. Đọc `README.md`, `docs/FRONTEND_SPEC.md` và mã nguồn hiện tại.
2. Chạy `npm ci` nếu bổ sung lockfile hợp lệ; nếu chưa có lockfile, `npm install` để tạo rồi commit `package-lock.json`. Chạy `npm run typecheck` và `npm run build`. Sửa tất cả lỗi **thực tế**; không xóa type safety để né lỗi.
3. Khởi động backend và frontend, kiểm thử đăng nhập và BFF có cùng `WORKSPACE_API_KEY`. Không nhúng token server vào mã client.
4. Kiểm thử workflow: nhập INCI EU → exact Niacinamide 5% có nguồn → chạy → xem miền LP → xem bằng chứng → CSV/JSON → lưu → mở từ thư viện → sao chép/lưu công thức giả thuyết tổng 100%.
5. Kiểm thử CN `trace_inci` ≤0,1%; nhiều công bố với ppm/mg/g; khi người dùng sửa input phải xóa kết quả cũ; công bố marketing approximate không khóa chính xác.
6. Kiểm thử kho nghiên cứu: thêm nguồn (nháp), đánh giá thủ công, không thay đổi solver; lọc thị trường khi không có dữ liệu phải cảnh báo chứ không cho là hợp pháp.
7. Kiểm thử mobile (390px), tablet (768px), desktop (1440px), keyboard, screen-reader label, loading, lỗi 401/502/422, empty states.
8. Tạo Playwright e2e tests chạy trên Next.js thật, tích hợp CI cho typecheck + build + tests. Chụp screenshot từ ứng dụng thật thay cho bản preview tĩnh.

## Giới hạn khoa học không được vi phạm
- `estimated_pct=null` phải hiện "Chưa có", tuyệt đối không gán số để đẹp biểu đồ.
- Không coi dữ liệu nghiên cứu là nồng độ tối ưu hoặc pháp lý. Không giả định mọi thành phần sau vị trí thứ N dưới 1%.
- Với CN, `trace_inci` tách riêng danh sách INCI chính.
- Không tự gắn một giới hạn EU cho toàn bộ sáu thị trường.
- Không ghép `min_pct`/`max_pct` độc lập thành công thức tổng 100% và gọi là công thức thực.
- Bản nháp nghiên cứu không tự được dùng làm nguồn đã tuyển chọn.
- Dữ liệu công thức giả thuyết không được gọi là đã kiểm nghiệm hoặc đạt pháp lý.

## Cấu trúc cần bảo toàn
- `backend/engine.py` (solver), `backend/data/evidence_catalog.json`, `backend/data/regulatory_catalog.json`, `backend/data/preservation_systems.json` — không sửa dữ liệu nguồn không có công bố kiểm chứng.
- Không viết lại backend nếu yêu cầu chỉ là sửa frontend; thay đổi hợp đồng API phải kèm test và tài liệu.

## Tiêu chí nghiệm thu
- `npm run typecheck`, `npm run build`, `pytest -q` và `python scripts/frontend_contract_smoke.py` đều đạt.
- Luồng thực chạy với FastAPI và PostgreSQL; không dùng dữ liệu giả để giả vờ lưu thành công.
- Playwright screenshot + báo cáo lỗi được bổ sung vào `docs/QA_FRONTEND.md`.
- Không để lộ API key, session token hay cơ sở dữ liệu trong client bundle.
- Báo cáo rõ chức năng đã hoạt động thực tế, chưa làm và các rủi ro tồn đọng.

## Sau khi nghiệm thu
Có thể phát triển V2.4: bảng nhiều giả thuyết cạnh nhau, diff phiên bản công thức, import từ tệp CSV INCI, báo cáo in, kiểm tra khả năng tiếp cận và hệ thống tài khoản nhiều vai trò. Chỉ phát triển lớp xác suất nồng độ khi có dữ liệu hiệu chuẩn thực và đánh giá độc lập.
