# AGENTS.md

Phạm vi: code ở gốc repo là **V2.2**. Bỏ qua `cosmetic_rd_webapp_v24/` trừ khi người dùng yêu cầu rõ ràng (đây là bản V2.3 frontend-first riêng, có Makefile/compose/backend riêng).

## Cấu trúc

- `backend/`: FastAPI (`main.py`), workspace CRUD (`workspace_api.py`, `workspace_db.py`), MCP (`mcp_server.py` STDIO, `mcp_gateway.py` HTTP + bearer).
- `backend/engine.py`, `backend/evidence_catalog.py`, `backend/data/*.json`: solver và catalog V2.1. **Đóng băng** (xem bên dưới).
- `backend/regulatory_check.py` + `backend/data/regulatory_rules.json` (bản sao của `regulatory_rules.json` ở gốc repo, 163 quy tắc, EU/US/VN/ASEAN; không có KR/CN): kiểm tra sơ bộ giới hạn, endpoint `POST /api/v2/regulatory/check`. Không phải phê duyệt pháp lý; không có bản ghi khớp = NEEDS_LEGAL_REVIEW, không phải được phép. Không dùng để ghi đè `regulatory_catalog.json`.
- `frontend/`: Next.js 16 / React 19, UI tiếng Việt. Mọi gọi API từ trình duyệt đi qua `app/api/bff/[...path]/route.ts`, route này chỉ proxy `v2/*` và `workspace/*`.
- `docs/ARCHITECTURE.md`, `docs/QA_REPORT.md`, `CODEX_TASK.md`: tài liệu nghiệp vụ và handoff. Đọc `CODEX_TASK.md` trước khi làm việc lớn.
- Không có git repo, CI, lint/formatter config, `opencode.json`, hay file instruction nào khác (CLAUDE.md, `.cursor/`, copilot).

## Lệnh

Makefile dùng recipe kiểu sh; trên Windows (PowerShell) `make` có thể không có, khi đó chạy trực tiếp các lệnh dưới đây.

- Backend test toàn bộ: `cd backend && python -m pytest -q`
- Một file / một test: `cd backend && python -m pytest -q tests/test_workspace.py::test_protected_workspace`
- Chạy API: `cd backend && uvicorn main:app --reload --port 8000`
- Chạy web: `cd frontend && npm run dev`
- Typecheck / build web: `cd frontend && npm run typecheck` và `npm run build`
- MCP STDIO: `cd backend && python mcp_server.py`
- Docker: `docker compose up --build -d`, `docker compose --profile mcp up --build -d`, `docker compose down`

Thứ tự khi xác minh frontend: `npm install` → `npm run typecheck` → `npm run build`.

## Gotchas

- **Test phải chạy từ `backend/`** (import trực tiếp `main`, `workspace_db`).
- Fixture `TestClient(app)` kích hoạt lifespan → `initialize_database()` dùng engine toàn cục theo `DATABASE_URL` (mặc định `sqlite:///./cosmetic_rd_local.db`). Đã kiểm chứng: chạy pytest có và không đặt `DATABASE_URL` đều không đổi mtime của `cosmetic_rd_local.db` (bảng đã tồn tại). Vẫn nên dùng DB tạm nếu schema thay đổi.
- `python` trên PATH là stub của Microsoft Store, không chạy được. Dùng venv riêng (đã tạo ở `%LOCALAPPDATA%\Temp\opencode\venv`, cài `backend/requirements.txt`) hoặc `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`. Python 3.12 chưa có pytest/fastapi cài sẵn.
- Schema dùng `Base.metadata.create_all`; **chưa có Alembic**. Đổi schema trên DB đã có dữ liệu sẽ không tự migrate.
- `docker compose down -v` xóa volume `cosmetic_pgdata`. Chỉ dùng khi chắc chắn.
- `cosmetic_rd_local.db` đã có trong thư mục (bị `.gitignore` theo `*.db`). Không commit, không coi là dữ liệu chuẩn.
- Biến môi trường: backend đọc `DATABASE_URL`, `WORKSPACE_API_KEY`, `MCP_BEARER_TOKEN`. Frontend đọc `WEB_ACCESS_TOKEN`, `INTERNAL_API_URL`, `WORKSPACE_API_KEY`, `FORCE_SECURE_COOKIES`. Dev web cần `frontend/.env.local`. `.env` và `.env.local` đã gitignore.
- `FORCE_SECURE_COOKIES=1` chỉ khi phục vụ qua HTTPS.
- Cổng 3000 có thể bị tiến trình Node `server.mjs` không liên quan giữ (đã gặp khi chạy `next start`; không phải của repo này). Khi đó dùng cổng khác (ví dụ `npx next start --port 3100`) và không tự tắt tiến trình đó.
- `WORKSPACE_API_KEY` và `MCP_BEARER_TOKEN` không được xuất hiện trong code client/bundle.
- Kiểm thử trình duyệt (công cụ browser): gọi `tabs.focus` trước khi click/screenshot, nếu không sẽ lỗi `UnknownVizError` hoặc "needs a visible tab". Accessibility snapshot không liệt kê ô nhập của form Phân tích INCI; điền bằng `evaluate` với native value setter + sự kiện `input`, rồi `click()` nút.

## Ranh giới khoa học (bắt buộc)

- `estimated_pct` luôn `null` cho đến khi có kiểm định mô hình trên dữ liệu đo thực.
- `min_pct`/`max_pct` là miền khả thi LP từ ràng buộc INCI, không phải hàm lượng sản phẩm.
- Bản ghi `research_records` do người dùng nhập **không** được đưa vào LP hay `evidence_catalog.json`, kể cả khi đã `reviewed`.
- Không tự tạo DOI/PMID, %, giới hạn pháp lý, điểm tin cậy, hay số liệu ISO 11930. Thiếu nguồn thì hiển thị "Chưa đủ dữ liệu".
- Không khẳng định hệ bảo quản đạt challenge test; không dùng output phần mềm để chứng nhận pháp lý hay an toàn.
- Không coi "không có bản ghi" là "được phép" (market × product_type × intended_use).

## Đóng băng

- `backend/evidence_catalog.py`, `backend/data/*.json`: không sửa nếu chưa có test mới xác nhận tác động và chủ dự án chấp nhận. Phải khớp SHA-256 với V2.1.
- `backend/engine.py`: đã thay đổi có phê duyệt (2026-11-09): thêm tham số tùy chọn `model_out` vào `_analysis` để `backend/suggest.py` đọc mô hình LP. Kết quả `analyze` không đổi (đã so sánh 6 đầu vào). SHA-256 mới: `099D0E54…53BAA`. Không mở rộng thay đổi này nếu chưa có test và phê duyệt.
- `backend/suggest.py`: `analyze_with_suggestion` được dùng trong `/api/v2/analyze` và khi lưu phân tích. Mỗi thành phần có `suggested_pct` (tổng 100%, nằm trong min–max); mục tiêu là điểm giữa khoảng, hoặc % tối ưu nếu được truyền vào `preferred` (hiện chưa có API nào truyền). `estimated_pct` vẫn `null`. Không phải ước tính hàm lượng. Kèm `explanation`: lý do từng tỷ lệ (cố định / khoảng hẹp / chưa xác định), giả định, dữ liệu cần thêm; khi không khả thi thì liệt kê nguồn mâu thuẫn bằng cách thử bỏ từng nguồn ràng buộc.
- Không thêm DOI/PMID/% mới vào ba catalog gốc.

## Trạng thái xác minh

- Đã pass (QA_REPORT, 09/11/2026): backend pytest 38/38, live FastAPI, PostgreSQL DDL compile, TS syntax transpile (9 file), `compileall`.
- **Chưa từng chạy:** `npm install`, `npm run build`, `npm run typecheck`, trình duyệt, PostgreSQL thật, Docker Compose, MCP handshake thật. Không báo cáo các mục này là pass khi chưa chạy.
- Ngôn ngữ: UI, tài liệu và thông báo người dùng bằng tiếng Việt; số/ngày theo định dạng Việt Nam.
