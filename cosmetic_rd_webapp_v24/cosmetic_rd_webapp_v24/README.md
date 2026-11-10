# Cosmetic R&D Intelligence V2.3 — Frontend-first

Bản nâng cấp **frontend Next.js tiếng Việt** từ nền tảng V2.2. Giữ nguyên lõi phân tích V2.1, nguồn nghiên cứu và API FastAPI; PostgreSQL và MCP có sẵn trong gói, nhưng **phạm vi phát triển lần này chỉ là frontend và hợp đồng kết nối API**.

## Các khu vực giao diện

| Khu vực | Tính năng |
| --- | --- |
| Tổng quan | Số hồ sơ thực, nguồn tuyển chọn, trạng thái kết nối, bước nghiên cứu |
| Phân tích INCI | Tên/loại sản phẩm, 6 thị trường, thứ tự nhãn, CN trace group, nhiều % công bố có nguồn, đơn vị %, ppm, mg/g |
| Kết quả | Min–max LP, nguồn nghiên cứu theo nguyên liệu, đối chiếu tổ hợp bảo quản, lý do ràng buộc, xuất CSV/JSON |
| Sản phẩm | Tìm tên, thương hiệu, INCI; lọc theo thị trường, mở lịch sử |
| Nghiên cứu | Tài liệu tuyển chọn, nhập tài liệu nội bộ dạng nháp, kiểm duyệt thủ công |
| Pháp lý | 6 thị trường, lọc theo INCI/chức năng, cảnh báo dữ liệu chưa đầy đủ |
| Công thức | Sửa phần trăm giả thuyết, kiểm tổng 100%, lưu phiên bản mới không ghi đè |

### Nguyên tắc khoa học
- `min_pct`/`max_pct` là **khoảng khả thi LP**, không phải hàm lượng định lượng của sản phẩm.
- `estimated_pct` luôn hiển thị "Chưa có" nếu bộ giải chưa có dữ liệu hiệu chuẩn. Không kết hợp các cận độc lập thành một công thức cụ thể.
- Nồng độ công bố chính xác được khóa chỉ khi là **INCI tinh khiết trong thành phẩm**, có nguồn. Nồng độ xấp xỉ được chú thích, không tự coi là ràng buộc bằng.
- Dữ liệu nghiên cứu *không tự tham gia* ràng buộc cứng; kho pháp lý hiện có **1 bản ghi EU mẫu**, không chứng minh tính tuân thủ cho các thị trường khác.
- Các giá trị trình bày ở `preview/` sử dụng **dữ liệu ví dụ** chạy qua backend V2.1, không phải sản phẩm thương mại đã kiểm nghiệm.

## Cài nhanh toàn bộ stack bằng Docker

Yêu cầu: Docker Desktop/Engine, Docker Compose, máy có Internet để tải Docker images và npm/Python packages.

```bash
cp .env.example .env
# MỞ .env VÀ ĐỔI MỌI KHÓA / MẬT KHẨU MẪU
# WEB_ACCESS_TOKEN, POSTGRES_PASSWORD, WORKSPACE_API_KEY, MCP_BEARER_TOKEN

docker compose up --build -d
```

Truy cập `http://localhost:3000/login`, đăng nhập bằng biến `WEB_ACCESS_TOKEN`. Backend Swagger tại `http://localhost:8000/docs`. PostgreSQL chạy nội bộ. MCP tùy chọn bằng `docker compose --profile mcp up --build -d` — kết nối có xác thực chỉ sau khi đã cấu hình.

> Không đưa trực tiếp các port nội bộ hoặc khóa trong `.env` lên Internet. Dịch vụ nội bộ dùng token đơn giản của V2.2, chưa thay cho SSO/RBAC mức sản xuất.

## Chạy frontend riêng trong khi phát triển

Ở cửa sổ terminal 1:

```bash
cd backend
python -m pip install -r requirements.txt
# DATABASE_URL mặc định SQLite để thử cục bộ
# Đặt WORKSPACE_API_KEY khớp khóa của frontend (tùy môi trường)
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Ở cửa sổ terminal 2:

```bash
cd frontend
cp .env.example .env.local
# WEB_ACCESS_TOKEN=<mật khẩu dùng thử>; INTERNAL_API_URL=http://127.0.0.1:8000
# WORKSPACE_API_KEY phải trùng WORKSPACE_API_KEY của backend, nếu có
npm install
npm run typecheck
npm run dev
```

Web App: `http://localhost:3000` → `/login`. Khi thay đổi frontend, Next.js tự tải lại trang trong `npm run dev`. `npm run build` dùng cho kiểm thử sản xuất.

## Bản xem trước nhanh — không cần cài Next.js

Mở `preview/index.html` trong trình duyệt để xem giao diện tĩnh, hoặc xem `preview/frontend_v23_preview.png`. Đây **chỉ là bản xem trước HTML/CSS** cùng phong cách thiết kế với Next.js, không phải ứng dụng đang kết nối API. Các thao tác phân tích thực phải sử dụng Next.js + FastAPI.

## Kiểm thử đã thực hiện trong môi trường tạo gói

- `pytest` backend gốc: **38/38** đạt.
- `python scripts/frontend_contract_smoke.py`: **6/6** hợp đồng API đạt (catalog, % công bố, ppm, vi lượng Trung Quốc, auth).
- Các `.ts`/`.tsx`: kiểm tra cú pháp bằng TypeScript compiler (`transpileModule`) đạt; **chưa phải typecheck đầy đủ**.
- Kiểm tra bố cục và tương tác **bản xem trước tĩnh** với Chromium/Playwright: đủ sáu dòng kết quả mẫu, mở được bằng chứng, kích thước 390px không tràn trang.
- **Chưa nghiệm thu `npm install`, `npm run typecheck`, `npm run build`, Web Next.js thật, PostgreSQL thật hoặc MCP thực tế** trong môi trường này do thiếu các package Node cần thiết và không truy cập registry. Cần thực hiện ở môi trường phát triển hoặc CI có Internet trước khi dùng chính thức.

## Tiếp tục với Codex

Đọc `CODEX_TASK.md` và `docs/FRONTEND_SPEC.md`. Bắt đầu bằng cài packages, typecheck/build và kiểm thử trình duyệt thực tế; sau đó xử lý lỗi thật và hoàn thiện UX. Không thay thế các catalog khoa học bằng số liệu chưa xác minh. Các tệp `backend/engine.py`, `backend/data/*.json` được giữ nguyên.
