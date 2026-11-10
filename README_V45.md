# Formula Intelligence V4.5 — Formula Optimization & Experimental Validation

**Mức hoàn thiện:** nguyên mẫu thực thi (backend Python/FastAPI, SQLite, trang Next.js, workbook), chưa phải hệ thống LIMS/GMP/ERP dùng trong sản xuất hoặc hồ sơ phê duyệt pháp lý.

## Kế thừa V4.4

V4.5 là bản nâng cấp *trong cùng project*, không tạo sản phẩm khác: giữ `optimizer_v44.py`, bộ dữ liệu 33 loại sản phẩm/32 nhóm/190 INCI ứng viên và lớp sàng lọc V4.3. Các kết quả suy luận về % vẫn giữ trạng thái mô phỏng nếu thiếu COA, assay và nguồn định lượng.

## Tính năng mới

1. **DoE:** Tạo thí nghiệm sàng lọc 1–3 yếu tố ở hai mức, có điểm nền tham chiếu. Cân bằng sai lệch bằng nguyên liệu được chỉ định, giữ các nguyên liệu khác cố định. Từng phương án chạy lại bộ giải V4.4, phương án vô nghiệm bị loại.
2. **Study & Protocol:** Khóa snapshot công thức bằng SHA-256, gắn từng chỉ tiêu/thời điểm kiểm tra/đơn vị/method/điều kiện/mục tiêu R&D do người dùng định nghĩa.
3. **Batch:** Tạo từng mẻ thử với lot code riêng.
4. **Measurement:** Lưu số đo, mã thiết bị, người thực hiện, SOP và đường dẫn chứng cứ. Chỉnh lỗi bằng bản ghi mới trỏ đến bản ghi bị thay thế; bản cũ vẫn lưu.
5. **Assessment:** Tính độ phủ dữ liệu theo mẻ × chỉ tiêu × thời điểm, phân loại kết quả ngoài hoặc trong quy cách của người dùng, thống kê chỉ tiêu numeric theo ngày và số mẻ độc lập.
6. **Evidence firewall:** Mục `DEMO_SYNTHETIC` không được đưa vào tổng hợp đo; đo thực tế phải có evidence URI, operator, method và thiết bị. Mọi kết quả có `approved_for_manufacturing=false`.

## Kiến trúc

- `experimental_validation_v45.py`: DoE và sàng lọc số đo
- `experimental_repository_v45.py`: SQLite demo với lịch sử append-only ở cấp API; database production cần ACL/immutable audit/backup
- `api_v45.py`: FastAPI endpoints V4.5 đồng thời bảo toàn endpoint V4.4 và V4.3
- `frontend/app/experiments/`: trang giao diện tiếng Việt (demo)
- `schema_v45_postgres.sql`: blueprint PostgreSQL, **chưa áp dụng migration**
- `examples/lip_balm_study_v45.json`: ví dụ protocol **không có số đo**; ngưỡng là giả định của người dùng
- `examples/lip_balm_doe_v45.json`: ví dụ DoE 5 phương án
- `Experimental_Validation_V4_5.xlsx`: workbook theo dõi, sheet nhật ký trống, chỉ có công thức DoE mô phỏng

## Chạy backend

```bash
python -m pip install -r requirements.txt
python -m pytest -q test_engine.py test_scientific_v43.py test_optimizer_v44.py test_scientific_bridge_v44.py test_experimental_v45.py
export V45_DB_PATH=./var/experiments_v45.sqlite3
uvicorn api_v45:app --host 127.0.0.1 --port 8000
```

Gọi mẫu:

```bash
python cli_v45.py doe examples/lip_balm_doe_v45.json
python cli_v45.py new-study examples/lip_balm_study_v45.json --db ./var/experiments_v45.sqlite3
# lấy study_id trả về và dùng CLI report hoặc GET endpoint
```

## API

- `GET /health/v4.5`
- `POST /api/v4.5/design-experiments`
- `POST /api/v4.5/studies`, `GET /api/v4.5/studies`
- `GET /api/v4.5/studies/{id}`
- `POST/GET /api/v4.5/studies/{id}/batches`
- `POST/GET /api/v4.5/studies/{id}/measurements`
- `GET /api/v4.5/studies/{id}/assessment`

**Hệ thống dùng SQLite demo.** Database PostgreSQL là schema tham chiếu, chưa có repository production và không có migration vào cơ sở dữ liệu thật.

## Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run build
npm run dev
```

Truy cập `http://localhost:3000/experiments`. Trang `/optimizer` của V4.4 vẫn còn. Trong môi trường tạo gói, build Next.js thất bại vì chưa có dependency `next` (`sh: 1: next: not found`), do đó **chưa chứng minh frontend đã build/chạy trình duyệt**.

## Giới hạn khoa học và dữ liệu

- Dữ liệu Lip Balm chứa premix chưa định lượng. V4.4 chỉ chứng minh tính khả thi dựa trên giả định và ràng buộc; chưa thể thay COA, Master Formula hay đo độ cứng thực tế.
- Thiết kế DoE là toàn bộ tổ hợp 2 mức với 1–3 yếu tố và điểm nền, **không phải tối ưu phản ứng/ML/thiết kế thống kê đầy đủ có ngẫu nhiên hóa**. Cần bổ sung replicates, randomization, blocking, sample size và đánh giá sai số nếu muốn suy luận thống kê.
- `READY_FOR_RND_REVIEW` chỉ có nghĩa đủ các trường bắt buộc để đối chiếu với quy cách người dùng, **không phải chứng nhận ổn định hoặc đủ điều kiện sản xuất**.
- Báo cáo thống kê chỉ tổng hợp số liệu người dùng đánh dấu `MEASURED` có truy vết; phần mềm **chưa xác thực tính thật của chứng cứ** hoặc hiệu chuẩn thiết bị.
- ISO/TR 18811:2018 là khung phương pháp ổn định, **không tự đưa ra ngưỡng thử chuẩn**. ISO 11930:2019 liên quan đánh giá bảo vệ vi sinh. V4.5 **không** tự kết luận kết quả ISO 11930.
- Mọi dữ liệu user-defined, reference, model assumption phải được phân biệt trong schema. Không tự phê duyệt pháp lý 6 thị trường.

## Nguồn tham khảo

- ISO/TR 18811:2018: https://www.iso.org/standard/63465.html
- ISO 11930:2019: https://www.iso.org/standard/75058.html
- Nguồn V4.1–V4.4: file đính kèm và các bản trước trong gói dữ liệu
