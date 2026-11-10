# CODEX IMPLEMENTATION HANDOFF — Cosmetic R&D V2.2 → V2.3

## Trạng thái xác minh

- V2.2 đã tạo Next.js UI, FastAPI endpoints mở rộng, PostgreSQL qua Docker Compose, schema SQLAlchemy, thư viện sản phẩm / nghiên cứu / công thức và MCP Python SDK stdio + HTTP tùy chọn.
- **38/38 kiểm thử backend đạt** (31 bài V2.1 + 5 bài workspace + 1 bài mock MCP logic + 1 bài gateway bearer giả lập), sử dụng SQLite cách ly qua FastAPI TestClient.
- **9 tệp TypeScript/TSX đã parse** bằng TypeScript global, không thấy lỗi cú pháp; **chưa `npm install`, `npm run build` hoặc kiểm thử trình duyệt Next.js** trong môi trường đóng gói vì registry mạng không truy cập được.
- `mcp` SDK và `psycopg` chưa cài trong môi trường đóng gói; **chưa kiểm thử kết nối MCP thực tế hoặc PostgreSQL trực tiếp**. Docker Compose chưa chạy vì máy build thiếu Docker.

## Bước 1 — Môi trường & phép thử E2E

1. Copy `.env.example` → `.env`, tạo password + API key riêng đủ mạnh; không commit secrets.
2. `docker compose up --build`, kiểm tra `http://localhost:3000/login`, `http://localhost:8000/docs`.
3. `docker compose --profile mcp up --build -d` nếu cần MCP HTTP. Test token sai phải 401, token đúng kết nối `.../mcp` bằng MCP Inspector/SDK client.
4. `cd frontend && npm install && npm run typecheck && npm run build` và sửa lỗi build nếu có; xác minh flow phân tích, lưu sản phẩm, tạo nghiên cứu nháp, kiểm duyệt và lưu công thức.
5. Test route `/api/bff/*` chặn người chưa đăng nhập. Kiểm tra độ an toàn web khi đưa Internet, không coi shared password là đăng nhập production.
6. Chạy PostgreSQL integration tests trong container; thử khởi động mới và restart giữ dữ liệu trên volume.

## Bước 2 — Hạ tầng dữ liệu chuẩn

- Thêm Alembic migration + kiểm thử nâng cấp dữ liệu. Bổ sung index/unique constraint `product_id + version`, xử lý concurrent writes.
- OIDC/SAML, người dùng/nhóm quyền, audit log, file evidence attachment, quota và sao lưu.
- Chuẩn hóa `Ingredient`, `Product`, `ProductVersion`, `Source`, `Evidence`, `LegalRequirement` thay vì cho người dùng tự nhập tên INCI tự do quá lâu.
- Quy định trạng thái `draft → reviewed → published` với phê duyệt độc lập. Reviewed chưa đồng nghĩa cho phép làm constraint.

## Bước 3 — Dữ liệu nghiên cứu và luật

- Duy trì kho V2.1 bất biến. Mỗi bản ghi mới phải chứa DOI/PMID/URL, ngày xuất bản, phiên bản nguồn, nguyên liệu và dạng nền, phương pháp, % đo/hiệu quả, điều kiện thử, phạm vi áp dụng.
- Mở rộng catalog luật 6 thị trường theo **market × product_type × intended_use × active-equivalent unit × valid_from/valid_to**; kiểm tra nguồn gốc và ngày hiệu lực, không suy từ khoảng INCI.
- Cần bao phủ qua kiểm định thủ công; không coi *no record* là *permitted*.
- Tập hợp công thức tham chiếu có định lượng được phép sử dụng trước khi phát triển posterior/prior.

## Bước 4 — MCP và bảo mật production

- Xác nhận SDK v2 dùng `MCPServer` (đã cập nhật từ FastMCP v1), và `streamable_http_app(json_response=True, stateless_http=True)` cùng `session_manager.run()` trên bản cài thực tế.
- Kiểm thử Codex STDIO qua `python mcp_server.py` và remote Streamable HTTP qua `/mcp`; kiểm tra HTTPS hoặc tunnel, allowlist Host/Origin, OAuth/Bearer tương thích với ChatGPT.
- Chỉ mở write tools sau khi có xác thực theo người dùng, phân quyền, xác nhận ghi, chống CSRF/audit và cơ chế rollback.
- Không bao giờ đưa `WORKSPACE_API_KEY` / `MCP_BEARER_TOKEN` vào bundle client.

## Quy tắc bất biến khi Codex sửa

- **Không sửa `backend/engine.py` hoặc dataset V2.1** nếu không có test mới xác nhận tác động và người chủ dự án chấp nhận.
- Không biến % nghiên cứu thành % bắt buộc, % tối ưu hoặc giá trị `estimated_pct` giả tạo.
- Không tự mô tả hệ bảo quản trong nghiên cứu như đã đạt challenge test của sản phẩm đang phân tích.
- Giao diện tiếng Việt tự nhiên, số/ngày định dạng Việt Nam.
- Báo cáo chính xác tình trạng test; không tuyên bố PostgreSQL/MCP/Next build pass khi chưa chạy.

## Definition of Done V2.3

- Python pytest + Postgres integration pass, `npm run typecheck` + `npm run build` pass.
- E2E: login → analyze → save → library → create reviewed citation → formula V1/V2 → export JSON.
- MCP stdio + HTTP authenticated tested qua client thực; public HTTPS/tunnel chỉ khi có cấu hình bảo mật.
- Migration, backup/restore, tài liệu mô hình pháp lý, phiên bản nguồn và audit được kiểm tra.
