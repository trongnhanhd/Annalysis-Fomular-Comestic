# QA FRONTEND · V2.3

**Tình trạng:** frontend mã nguồn đã triển khai; bản xem trước tĩnh hoạt động; chưa nghiệm thu build Next.js thật.

| Hạng mục | Kết quả | Bằng chứng |
| --- | --- | --- |
| Backend gốc | PASS — 38/38 bài test | `cd backend && pytest -q` |
| Hợp đồng API frontend | PASS — 6/6 | `python scripts/frontend_contract_smoke.py` |
| Kiểm tra syntax TS/TSX | PASS ở lớp cú pháp | TypeScript `transpileModule` cục bộ; không thay cho typecheck |
| Bố cục desktop | PASS trên bản xem trước tĩnh | `preview/frontend_v23_preview.png` |
| Bố cục điện thoại 390px | PASS trên bản xem trước tĩnh | `preview/frontend_v23_mobile.png` — không tràn ngang toàn trang |
| Mở rộng bằng chứng nguồn | PASS trên bản xem trước tĩnh | `preview/frontend_v23_evidence.png` |
| Next.js typecheck | CHƯA CHẠY | Thiếu React/Next dependencies trong môi trường |
| Next.js production build | CHƯA CHẠY | Thiếu React/Next dependencies trong môi trường |
| PostgreSQL kết nối thật | CHƯA CHẠY | Không có Docker/PostgreSQL trong môi trường |
| MCP handshake | NGOÀI PHẠM VI | Giữ nguyên mã MCP V2.2 |

**Lưu ý:** `preview/index.html` là minh họa bằng HTML/CSS dùng chung palette và dữ liệu trả về từ solver. Không phải ảnh chụp Next.js đang chạy. Không coi phép kiểm trên preview là kiểm thử end-to-end của Next.js.

## Cần kiểm thử ở máy phát triển

1. `npm install && npm run typecheck && npm run build`.
2. Bật backend + PostgreSQL, thử đăng nhập và phân tích thực, lưu và truy xuất.
3. Tạo e2e Playwright với fixtures, kiểm tra lỗi mạng, dấu vết khoa học và khóa API.
4. Chạy axe accessibility, responsive 390/768/1440 và kiểm tra download CSV/JSON.
