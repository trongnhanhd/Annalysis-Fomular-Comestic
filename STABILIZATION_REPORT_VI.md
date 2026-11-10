# FORMULA INTELLIGENCE — BÁO CÁO SỬA LỖI P0 V4.5.2-R1

**Ngày rà soát:** 10/11/2026  
**Phạm vi:** Ổn định V4.5.2 hiện có, không phát triển V4.6, không gộp vào SkinSim/ComesticLab.  
**Đầu vào:** `Formula_Intelligence_Integrated_V4_5_2` (bản nguồn đã bàn giao).  
**Đầu ra:** Một bản sửa lỗi độc lập; bản gốc không thay đổi.

## Kết quả có bằng chứng

| Gate | Trạng thái | Bằng chứng | Việc còn thiếu |
|---|---|---|---|
| A — Next.js build | **Chưa đạt** | 10 tệp TypeScript/TSX được kiểm tra cú pháp, không có parse error | `npm run build` trả `next: not found`, npm registry không phân giải DNS nên không tải được dependency; chưa có lockfile và chưa E2E trình duyệt |
| B — API | **Một phần** | 89/89 pytest đạt; 11 assert frontend model đạt; FastAPI OpenAPI 22 đường dẫn, không còn duplicate `/docs`/`openapi.json`; TestClient xác nhận luồng DoE/candidate/batch | Chưa có contract/browser E2E thật, phiên bản hóa hợp đồng rộng hơn và quản lý lỗi đầy đủ |
| C — Dữ liệu thực nghiệm | **Một phần** | SQLite lưu candidate DoE immutable, liên kết batch với candidate SHA, khối lượng cân, mã lô, SOP; các bản cũ có trạng thái `UNLINKED_LEGACY` | PostgreSQL chưa có máy chủ để thử; migration `002_v452_traceability.sql` chỉ mới viết, chưa áp dụng; dữ liệu cũ cần đối soát trước backfill |
| D — An toàn vận hành | **Chưa đạt** | Ứng dụng chỉ hỗ trợ local demo | Chưa auth/RBAC, backup/restore, quyền nghiên cứu, CSRF/anti-abuse; không đưa lên Internet |
| E — Khoa học/pháp lý | **Chưa đạt** | Dữ liệu mô phỏng phân biệt demo và số đo | Chưa xác minh 190 INCI/grade, premix, và giới hạn pháp lý toàn diện 6 thị trường |

## Thay đổi mã nguồn đã kiểm thử

1. `batch_provenance_v452.py`: Khóa candidate DoE từ đúng snapshot nghiên cứu. Nếu user truyền `doe_design`, server **tính lại** kết quả; không tin bảng % do frontend gửi thẳng.
2. `experimental_repository_v45.py`: SQLite thêm bảng `doe_candidates`, `batch_provenance`; khóa không cho UPDATE/DELETE. Mẻ mới có thể ghi `candidate_id`, `actual_weights_g`, `raw_material_lots`, `process.procedure_ref`, `weighed_by`. Các mẻ cũ vẫn đọc được nhưng bị gắn `UNLINKED_LEGACY`.
3. `experimental_repository_postgres_v451.py`, `migrations/002_v452_traceability.sql`: Thiết kế cùng hợp đồng dữ liệu cho PostgreSQL. **Chưa chạy trên PostgreSQL thật.** `ping()` yêu cầu đủ schema 001+002.
4. `api_v45.py`: Thêm `GET /api/v4.5/studies/{id}/candidates`. Các endpoint hiện có được giữ nguyên.
5. `api_v44.py`: Bỏ đăng ký trùng route tài liệu FastAPI; dùng một schema OpenAPI cho app.
6. `frontend/components/BatchTraceabilityEditor.tsx` và `/experiments`: Cho chọn phương án DoE, nhập khối lượng cân **thực** và số lô trong bảng. Không tự điền khối lượng theo mô phỏng. Giao diện có mã nhưng chưa được build Next.js.
7. `test_traceability_v452.py`: Thêm 8 bài kiểm thử, gồm candidate snapshot, duy trì dữ liệu, bất biến, mã lô, lệch bảng cân, HTTP contract và OpenAPI.

## Trạng thái khoa học và truy vết

- `FEASIBLE`: Có nghiệm toán học, không suy ra sản phẩm an toàn/ổn định/pháp lý.
- `LINKED_MATCHED`: Khối lượng người dùng nhập khớp tỷ lệ mục tiêu trong sai số 0,1 điểm phần trăm, **không xác minh sự trung thực của thao tác cân**.
- `LINKED_DEVIATED`: Độ lệch lớn hơn 0,1 điểm phần trăm; không được âm thầm coi là đúng phương án.
- `UNLINKED_LEGACY`: Mẻ cũ thiếu liên kết công thức và bảng cân; phải rà soát thủ công.
- `traceability.review_readiness`: `INCOMPLETE`, `DEVIATION_REVIEW_REQUIRED` hoặc `COMPLETE`; tách khỏi `status` của số đo để tương thích API cũ.
- `eligible_for_model_training=false` và `approved_for_manufacturing=false` trong báo cáo hiện tại. Chưa có máy học được nghiệm thu.

## Cách chạy kiểm thử trên máy phát triển

```bash
cd Formula_Intelligence_V452_Stabilization_R1
python -m pip install -r requirements.txt
python -m pytest -q
node frontend/tests/test_form_model.cjs
```

Đối với Next.js cần **có kết nối mạng** để cài dependencies. Chưa có lockfile nên làm tại máy phát triển có npm registry, xác minh phiên bản, tạo lockfile rồi kiểm thử:

```bash
cd frontend
npm install
npm run build
npm run dev
```

Đối với PostgreSQL dùng một DB thử riêng có tên kết thúc bằng `_test`, backup dữ liệu trước khi di chuyển; áp dụng `001_v451_init.sql`, sau đó `002_v452_traceability.sql`, và chạy:

```bash
pip install -r requirements-postgres.txt
TEST_POSTGRES_URL='postgresql+psycopg://.../formula_rd_test' python scripts/verify_postgres_v452.py
```

Script đã có cơ chế từ chối DB tên không kết thúc `_test`. Nếu cấu hình test URL vắng mặt, script báo `SKIPPED`, không phải `PASS`.

**Quan trọng:** Docker init scripts chỉ chạy khi volume database mới. Không xóa volume cũ để ép migration. Quản lý migration hiện chưa có Alembic; chưa phải quy trình triển khai production.

## Điều kiện trước khi nghiệm thu V4.5.2

- [ ] Cài dependency thành công, có `package-lock.json` xác định phiên bản, `npm run build` đạt, kiểm thử thao tác 3 trang trình duyệt.
- [ ] Test API qua Next rewrite `/backend`, bao gồm thất bại mạng, lỗi đầu vào, đăng tải chậm.
- [ ] PostgreSQL `_test`: migration + truy vấn study/candidate/batch/measurement + trigger bất biến + backup và restore.
- [ ] Đối soát các mẻ cũ, không gắn tự động candidate dựa trên những dữ liệu chưa xác nhận.
- [ ] Tăng cường auth, quyền R&D/QC/Admin, audit truy cập, lưu bí mật và sao lưu trước khi chạy nội bộ nhiều người.
- [ ] Rà soát độc lập nguồn khoa học và quy định pháp lý; chưa cho phép kết luận đủ điều kiện lưu hành/sản xuất.

**Quyết định:** Giữ trạng thái **prototype nội bộ**. Không phát triển V4.6 cho đến khi các gate P0 được xác minh trong môi trường có Next.js và PostgreSQL thực.
