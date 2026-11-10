# Báo cáo kiểm thử V2.2 — 09/11/2026

## Đạt trong môi trường hiện tại

| Kiểm tra | Kết quả | Phạm vi |
|---|---|---|
| Backend unit/API pytest | **38/38 PASS** | 31 bài V2.1, 5 bài workspace, 1 bài MCP business logic mô phỏng SDK, 1 bài gateway bearer giả lập |
| Live FastAPI HTTP | **PASS** | Uvicorn thật localhost; `/api/v2/catalog` có 5 nguồn, `/api/v2/analyze` khả thi, `/api/workspace/products` sai key 401, đúng key 200 |
| PostgreSQL DDL compile | **PASS** | Cả 4 bảng compile thành SQL theo dialect PostgreSQL |
| TypeScript/TSX syntax | **9/9 PASS** | TypeScript transpileModule trên nguồn Next.js; không phải `next build` hoặc typecheck đầy đủ |
| SHA-256 preservation | **PASS** | `engine.py`, `evidence_catalog.py`, 3 catalog JSON nguyên vẹn so với V2.1 |
| Python `compileall` | **PASS** | Mã Python hiện có, gồm MCP server/gateway |

## Chưa kiểm thử trong môi trường tạo mã nguồn

- Không có npm registry / Docker / psycopg / MCP Python SDK được cài đặt, nên **chưa chạy** `npm install`, `npm run build`, `npm run typecheck`, trình duyệt Next.js, PostgreSQL trực tiếp, Docker Compose hoặc MCP handshake thực.
- Tests MCP với server giả chỉ chứng minh logic tool và middleware, **không** xác nhận tương thích protocol ngoài môi trường thật.
- Cần làm E2E + HTTPS/OAuth hoặc bearer review + rate-limit + audit trước khi triển khai Internet.

## Cách nghiệm thu ở máy phát triển

```bash
cp .env.example .env
# thay tất cả secrets
docker compose up --build -d
cd backend && python -m pytest -q
cd ../frontend && npm install && npm run typecheck && npm run build
# qua web: đăng nhập → phân tích → lưu → tạo nghiên cứu → duyệt → tạo công thức
```

## Kiểm chứng dữ liệu khoa học

Chưa bổ sung bất kỳ giá trị % hay DOI/PMID mới nào vào ba catalog gốc. Dữ liệu nghiên cứu do người dùng thêm là dữ liệu độc lập, không làm thay đổi solver `estimated_pct` (vẫn `null`).
