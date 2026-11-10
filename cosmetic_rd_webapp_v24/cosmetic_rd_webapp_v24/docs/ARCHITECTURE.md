# Kiến trúc kỹ thuật — Cosmetic R&D V2.2

## Nguyên tắc cốt lõi

- Ứng dụng độc lập, không gộp với Mountain Lab SkinSim hay MixColor.
- Backend FastAPI giữ nguyên `engine.py`, `evidence_catalog.py`, các endpoint `/api/v2/*` và dữ liệu tuyển chọn từ V2.1.
- API không bao giờ tự tuyên bố nguồn pháp lý đầy đủ, dự đoán điểm hay hiệu lực bảo quản từ INCI.
- `estimated_pct` phải tiếp tục `null` cho đến khi hoàn tất kiểm định mô hình thống kê trên tập dữ liệu có số đo thực.
- Bản ghi nghiên cứu do người dùng nhập ở bảng `research_records`, không được tự động nhập `data/evidence_catalog.json` kể cả khi đánh dấu reviewed.

## Luồng sử dụng

```
               ┌───────────── WEB APP NEXT.JS ─────────────┐
               │ đăng nhập / danh sách / phân tích / báo cáo│
               └─────────────────┬─────────────────────────┘
                                 │ BFF /api/bff/* (server-side secret)
                                 ▼
                          FASTAPI REST
                          │          │
                          ▼          ▼
                    LP V2.1 engine  Workspace repository
                          │          │
                     JSON curated    PostgreSQL
                          ▲          ▲
                          │          │
                    MCP tools read-only
                          ▲
                 Codex STDIO / ChatGPT HTTPS
```

## PostgreSQL schema

| Table | Vai trò | Ghi chú |
|---|---|---|
| `products` | tên, thương hiệu, khu vực, loại, INCI gốc | lưu nhãn đầu vào |
| `analysis_runs` | snapshot input, result, catalog_version, thời điểm | kết quả bất biến qua API |
| `research_records` | tài liệu R&D có URL, % và trạng thái kiểm duyệt | luôn tách khỏi catalog đã chọn |
| `formula_versions` | phiên bản công thức giả thuyết, tổng 100%, ghi chú | không tự khẳng định an toàn/ổn định |

Dùng SQLAlchemy ORM; PostgreSQL trong Docker Compose. SQLite hỗ trợ chạy offline/test. MVP dùng `create_all`, **chưa có Alembic migrations**; khi sản xuất phải bổ sung trước khi đổi schema.

## API mới

| Method + path | Mô tả |
|---|---|
| `GET /api/workspace/health` | kiểm tra DB |
| `GET/POST /api/workspace/products` | danh sách / tạo sản phẩm |
| `GET /api/workspace/products/{id}` | chi tiết sản phẩm |
| `POST /api/workspace/products/{id}/analyses` | giải LP từ snapshot sản phẩm + điều kiện thêm, lưu kết quả |
| `GET /api/workspace/products/{id}/analyses` | lịch sử kết quả |
| `GET /api/workspace/analyses/{id}` | kết quả và input của lần chạy |
| `GET/POST /api/workspace/research` | tra cứu/thêm bằng chứng nháp |
| `POST /api/workspace/research/{id}/review` | kiểm duyệt thủ công (không tự áp LP) |
| `GET/POST /api/workspace/products/{id}/formulas` | lịch sử và lưu phiên bản công thức giả thuyết |

Các route `/api/workspace/*` có `X-API-Key` nếu `WORKSPACE_API_KEY` được thiết lập. Web không gửi khóa cho trình duyệt; BFF server-side thêm header sau khi kiểm tra cookie đăng nhập. Đây là thiết kế nội bộ một người dùng; chưa có OAuth/OIDC, RBAC hay kiểm toán người dùng cấp tổ chức.

## MCP

`mcp_server.py`: stdio cho Codex, `mcp_gateway.py`: Streamable HTTP đi kèm bearer token (triển khai tùy chọn). Các tools hiện chỉ **đọc** hoặc tính toán không ghi DB: phân tích INCI, phân tích với % xác minh, tra cứu nghiên cứu, pháp lý, hệ bảo quản, sản phẩm và lịch sử.

ChatGPT không truy cập `http://localhost` trực tiếp qua web; dùng endpoint HTTPS có xác thực hoặc Secure MCP Tunnel theo quyền tài khoản và môi trường được hỗ trợ. Không công khai cổng 8001 khi chưa có TLS, host allowlist và kiểm thử xác thực ở triển khai đích.

## Ranh giới tin cậy

1. Lệnh từ AI / tài liệu ngoài là đầu vào chưa tin cậy; không thực hiện theo chỉ dẫn nằm trong `notes`, nội dung nghiên cứu, hoặc metadata.
2. Nguồn công bố tỷ lệ được nhập như `known_pct` là ràng buộc toán học, phải được con người kiểm chứng; nếu không, để trống.
3. Giới hạn pháp lý chỉ áp dụng theo thị trường, loại sản phẩm, mục đích, và có tùy chọn xác nhận.
4. Khi thiếu nguồn, hiển thị “Chưa đủ dữ liệu”, không tự tạo DOI, nồng độ, % hiệu quả, điểm độ tin cậy, hoặc số liệu ISO 11930.
5. Không dùng API quản lý hồ sơ để cập nhật catalog tuyển chọn. Thay đổi catalog phải qua review + version + test.
