# Cosmetic R&D Intelligence V2.2 — Web App + MCP

Ứng dụng nghiên cứu mỹ phẩm **độc lập**, tiếng Việt, tiếp tục trực tiếp từ **Concentration Inference Engine V2.1**. Có frontend Next.js, backend FastAPI/LP, thư viện nghiên cứu và công thức trong PostgreSQL, MCP tools cho Codex/ChatGPT khi có quyền kết nối.

> **KHOA HỌC:** Kết quả min–max là **miền khả thi** từ ràng buộc nhãn INCI, không phải hàm lượng thực. `estimated_pct = null` (chưa có mô hình thống kê được kiểm định). Nồng độ nghiên cứu không tự biến thành giới hạn pháp lý hoặc % hiệu quả tối ưu. Catalog nghiên cứu/pháp lý chỉ là các bản ghi tuyển chọn V2.1, **không bao phủ đủ sáu thị trường**.

## 1. Chạy toàn bộ qua Docker Compose (khuyến nghị)

Yêu cầu Docker + Docker Compose, cổng localhost 3000/8000 trống, Internet lúc build để cài npm và Python packages.

```bash
cp .env.example .env
# SỬA POSTGRES_PASSWORD, WORKSPACE_API_KEY, WEB_ACCESS_TOKEN, MCP_BEARER_TOKEN trong .env
# Chỉ dùng bản ví dụ nguyên trạng trên máy thử nội bộ, tuyệt đối không đưa Internet.
docker compose up --build -d
```

- **Web App:** http://localhost:3000/login, đăng nhập bằng `WEB_ACCESS_TOKEN` trong `.env`.
- **FastAPI:** http://localhost:8000/docs — thư viện `/api/workspace/*` yêu cầu header `X-API-Key: $WORKSPACE_API_KEY`.
- **PostgreSQL:** chạy nội bộ trong mạng Docker, có volume `cosmetic_pgdata`.
- Dừng hệ thống: `docker compose down` (giữ data). **KHÔNG** `docker compose down -v` nếu cần giữ dữ liệu.

MCP HTTP tùy chọn:

```bash
docker compose --profile mcp up --build -d
# Dùng MCP client hỗ trợ Streamable HTTP, kết nối http://127.0.0.1:8001/mcp
# Header Authorization: Bearer <MCP_BEARER_TOKEN>
```

Cổng chỉ bind loopback. ChatGPT web không truy cập localhost trực tiếp: cần HTTPS/tunnel + cơ chế xác thực phù hợp, và quyền tài khoản/workspace tương ứng. Tham khảo [hướng dẫn OpenAI kết nối MCP](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt), [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp) và [Python MCP SDK](https://py.sdk.modelcontextprotocol.io/).

## 2. Chạy dev không có Docker

Yêu cầu Python 3.11+, Node.js 22+, PostgreSQL nếu muốn dữ liệu chung. Có thể chạy với SQLite để thử API local.

**Terminal A:**

```bash
cd backend
python -m venv .venv
# kích hoạt virtualenv theo hệ điều hành
pip install -r requirements.txt
# DATABASE_URL mặc định SQLite ./cosmetic_rd_local.db
# Thiết lập WORKSPACE_API_KEY nếu kết nối cùng frontend
uvicorn main:app --reload --port 8000
```

**Terminal B:**

```bash
cd frontend
cp .env.example .env.local    # Nếu đã tạo; xem biến mẫu ở thư mục gốc.
npm install
npm run dev
```

> `frontend/.env.local` phải có `WEB_ACCESS_TOKEN`, `INTERNAL_API_URL=http://127.0.0.1:8000` và cùng `WORKSPACE_API_KEY` với backend. Trong bản ZIP có `frontend/.env.example` để copy. Trên Windows dùng lệnh copy tương ứng.

**MCP Codex STDIO** (cần `pip install -r requirements-mcp.txt` trong backend):

```bash
cd backend
python mcp_server.py
```

Có thể cấu hình trong Codex CLI bằng lệnh tương ứng: 

```bash
codex mcp add cosmetic-rd -- python /DUONG_DAN_TUYET_DOI/cosmetic_rd_app_mcp_v22/backend/mcp_server.py
```

Dùng biến `DATABASE_URL` của cùng PostgreSQL để MCP đọc đúng dữ liệu của App. Nếu dùng SQLite, cả backend và MCP phải trỏ cùng tệp bằng đường dẫn tuyệt đối. Các công cụ MCP hiện là **chỉ đọc hoặc phân tích không ghi**.

## 3. Luồng sử dụng thực tế

1. Mở **Phân tích INCI**, dán danh sách INCI theo đúng thứ tự, chọn EU/US/KR/CN/VN/ASEAN và loại sản phẩm.
2. Nếu có % INCI tinh khiết **đã xác minh**, nhập tên + % + nguồn; nếu chỉ là “5% complex” thì để trống và dùng phần premix nâng cao của API.
3. Chạy LP, xem miền % khả thi và bằng chứng tham chiếu. Pháp lý chỉ được áp khi người dùng xác nhận giới hạn phù hợp.
4. Nhấn **Lưu sản phẩm + phân tích** để lưu snapshot đầu vào/đầu ra cùng phiên bản catalog.
5. Vào **Nghiên cứu khoa học** để thêm tài liệu ở trạng thái nháp, kiểm duyệt thủ công. Kể cả đã duyệt, dữ liệu này **không tự thay đổi LP**.
6. Vào **Công thức giả thuyết** để lưu nhiều phiên bản tổng 100%; phải kiểm nghiệm thực tế trước khi ứng dụng sản xuất.

## 4. API, MCP, bảo mật

- API gốc V2.1: `/api/v2/analyze`, `/api/v2/catalog`, `/api/v2/catalog/research`, `/api/v2/catalog/regulatory`, `/api/v2/catalog/preservation`, `/api/v2/rules`.
- API mới: xem [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Swagger tự sinh ở `/docs`.
- MCP công cụ: `analyze_inci`, `analyze_confirmed_ingredient_percentage`, `search_curated_research`, `compare_regulatory_references`, `search_preservation_systems`, `list_research_products`, `get_saved_product`, `list_saved_analyses`, `search_workspace_research`.
- Web App BFF thực hiện xác thực cookie HttpOnly (khi đưa qua HTTPS phải đặt `FORCE_SECURE_COOKIES=1`) và thêm khóa API backend ở server. MVP dùng **mã truy cập dùng chung**, chưa hỗ trợ nhiều người dùng, OAuth, phân quyền vai trò hoặc audit-grade identity. Không dùng làm hệ thống production public trước khi nâng bảo mật.
- Không gắn tài liệu nghiên cứu chưa xác minh vào constraint. Không dùng output phần mềm để chứng nhận hợp pháp, an toàn, hiệu lực hay đạt challenge test.

## 5. Kiểm thử và phạm vi đã xác minh

**Đã xác minh trong môi trường tạo mã nguồn:**

```bash
cd backend
python -m pytest -q
# 38/38 passed (31 bài cũ, 5 bài workspace, 1 bài mock MCP logic và 1 bài gateway auth giả lập) với SQLite test DB cách ly
```

- FastAPI TestClient kiểm thử tạo sản phẩm, lưu phân tích, kiểm duyệt nghiên cứu, formula version và API key.
- TypeScript transpile kiểm tra cú pháp TS/TSX (9 tệp) đã đạt.
- Đã kiểm tra Python compile cho MCP gateway; **chưa thể import/run MCP SDK trực tiếp** vì môi trường không truy cập registry gói.

**Chưa xác minh tại môi trường đóng gói:** `npm install`, `npm run typecheck`, `npm run build`, trình duyệt Next.js, PostgreSQL live, Docker Compose live và MCP client handshake. Những bước này được hướng dẫn chính xác trong [CODEX_TASK.md](CODEX_TASK.md). Không tuyên bố chúng đã pass.

## 6. Cấu trúc dự án

```text
cosmetic_rd_app_mcp_v22/
├── frontend/                    # Next.js 16, React 19, hoàn toàn tiếng Việt
│   ├── app/                    # login, dashboard, BFF route
│   ├── components/             # phân tích, thư viện, nghiên cứu, pháp lý, công thức
│   ├── lib/                    # auth, types
│   └── Dockerfile
├── backend/                     # FastAPI + solver V2.1 nguyên vẹn
│   ├── engine.py, evidence_catalog.py, data/
│   ├── workspace_api.py        # CRUD API mới
│   ├── workspace_db.py         # SQLAlchemy schema
│   ├── mcp_server.py           # STDIO tools
│   ├── mcp_gateway.py          # Streamable HTTP + bearer
│   ├── tests/                  # V2.1 tests + tests tích hợp mới
│   └── Dockerfile
├── docs/ARCHITECTURE.md
├── CODEX_TASK.md
├── compose.yaml
└── .env.example
```

## 7. Tài liệu công nghệ tham khảo

- [Next.js App Router](https://nextjs.org/docs/app)
- [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/)
- [OpenAI MCP connection](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/)

**Tiếp theo:** xem [CODEX_TASK.md](CODEX_TASK.md) để Codex hoàn tất build/E2E với registry mạng và Docker, sau đó mới phát triển V2.3.
