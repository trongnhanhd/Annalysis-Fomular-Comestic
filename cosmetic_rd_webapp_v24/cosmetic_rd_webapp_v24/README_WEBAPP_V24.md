# Cosmetic R&D Intelligence — Web App V2.4 (chạy cục bộ)

Bản Web App mới phục vụ **trực tiếp từ FastAPI** trên `/app`, không cần npm để sử dụng hàng ngày. **Mã nguồn Next.js V2.3 gốc vẫn nằm trong `frontend/`**; không xóa, không thay thế backend, không xóa MCP Server. Bộ giải LP và các dữ liệu catalog đều giữ nguyên.

## Khởi chạy trên Windows

1. Giải nén ZIP vào một thư mục riêng.
2. Cài **Python 3.11+**, bảo đảm lệnh `python` chạy trong Terminal.
3. Chạy `start_webapp_windows.bat`, hoặc mở Terminal trong thư mục dự án và chạy:

   ```powershell
   python -m pip install -r backend/requirements.txt
   python run_webapp.py
   ```

4. Mở **http://127.0.0.1:8000/app**. Swagger API: `http://127.0.0.1:8000/docs`.
5. Dừng ứng dụng bằng `Ctrl+C` tại Terminal.

Để chạy trên macOS/Linux: `python3 -m pip install -r backend/requirements.txt && python3 run_webapp.py`.

> `run_webapp.py` chỉ lắng nghe `127.0.0.1`, không mở ra Internet. Database mặc định: `backend/cosmetic_rd_local.db` (SQLite để thử nghiệm cục bộ, được tạo khi chạy). File này không được đưa vào ZIP. Sao lưu tệp database sau khi có dữ liệu quan trọng.

## Những màn hình đã dùng được

| Màn hình | Tính năng hoạt động |
| --- | --- |
| Tổng quan | Số liệu thư viện và nguồn nghiên cứu từ API thật, sản phẩm gần đây |
| Phân tích INCI | INCI theo thứ tự, 6 thị trường, vi lượng Trung Quốc, nhiều nồng độ công bố bằng %, ppm, mg/g, giới hạn tùy chọn |
| Kết quả | LP min/max, lý do ràng buộc, bằng chứng theo nguyên liệu, tổ hợp bảo quản, cảnh báo, xuất CSV/JSON |
| Thư viện sản phẩm | Lưu sản phẩm, kết quả phân tích bất biến, xem các lần phân tích |
| Nghiên cứu khoa học | Tìm nguồn catalog tuyển chọn, lưu tài liệu nội bộ mới ở trạng thái `draft` |
| Pháp lý | 6 thị trường và những bản ghi luật thực sự có trong catalog; ghi rõ thiếu dữ liệu |
| Công thức giả thuyết | Sửa từng % w/w, kiểm tổng 100%, tạo phiên bản mới |

Dữ liệu từ nút **“Nạp dữ liệu mẫu”** là **hoàn toàn giả định** và được ghi nhãn rõ. Không dùng để chứng minh thành phần của sản phẩm thật.

## Cấu trúc

```text
backend/
  main.py                     FastAPI gốc, thêm /app và assets
  webapp/index.html           Web App, semantic HTML tiếng Việt
  webapp/app.css              Thiết kế responsive desktop/mobile
  webapp/app.js               Logic 6 màn hình, kết nối API thực
  engine.py                   Bộ giải V2.1, KHÔNG sửa
  data/*.json                 Catalog V2.1, KHÔNG sửa
  workspace_api.py            CRUD thư viện gốc V2.2
  mcp_server.py               MCP gốc V2.2
frontend/                      Next.js V2.3 giữ nguyên
run_webapp.py                 Máy chủ localhost:8000
start_webapp_windows.bat      Trình khởi chạy cho Windows
scripts/test_live_webapp.py  Kiểm thử Chromium bằng cầu nối API
screenshots/                  Ảnh kiểm thử giao diện thực tế
CODEX_TASK_WEBAPP_V24.md     Roadmap tiếp tục
```

## Kiểm thử thực hiện

- `backend` Python: `python -m pytest -q` → 40/40 đạt (38 bài gốc + 2 bài mới).
- `node --check backend/webapp/app.js` → đạt.
- HTTP thật: GET `/app`, GET `/app/assets/*`, phân tích API thực.
- Chromium / Playwright: render HTML/CSS/JS thật, chạy API backend thật thông qua **cầu nối request** bởi môi trường này chặn browser điều hướng tới localhost. Kiểm tra thao tác sáu màn hình, chạy INCI, mở nguồn, lưu sản phẩm, lưu công thức và giao diện 390px. Không được xem đây là kiểm thử trình duyệt chạy trực tiếp URL thật.
- Next.js full build và MCP handshake **chưa được nghiệm thu** trong môi trường này. Cần thực hiện trên máy có registry npm và môi trường SDK đầy đủ.

## Bảo mật và triển khai công khai

**Chỉ dành cho thử nghiệm / sử dụng trên máy cá nhân. Không triển khai công khai cấu hình này lên Internet.** Giao diện này không có đăng nhập người dùng. `WORKSPACE_API_KEY` hiện chỉ là khóa dùng chung cho thư viện và có thể nhập tại **Cài đặt kết nối** (lưu phiên trình duyệt), không phải cơ chế xác thực production. Chỉ cấu hình public sau khi có HTTPS, đăng nhập, RBAC, bảo vệ MCP, CORS/CSRF, quản lý secrets, database migration, giám sát và sao lưu.

Nếu muốn dùng Next.js production, tiếp tục từ `frontend/` và `CODEX_TASK_WEBAPP_V24.md` để tích hợp/gỡ UI thử nghiệm sau nghiệm thu, không thay backend khoa học.

## Chính sách dữ liệu nghiên cứu

- Từ INCI chỉ suy ra **miền nghiệm LP**. Không gọi đó là hàm lượng đo được, khoảng tin cậy hoặc % có xác suất cao.
- Nguồn nghiên cứu là tham khảo, **không tự động** trở thành giới hạn cứng hay xác nhận độ hiệu quả bảo quản của sản phẩm.
- Nguồn nội bộ mới chỉ lưu nháp, chưa được bộ giải dùng để suy luận.
- Catalog pháp lý hiện còn rất hạn chế, không tạo giả định rằng sáu thị trường đã tuân thủ đầy đủ.
