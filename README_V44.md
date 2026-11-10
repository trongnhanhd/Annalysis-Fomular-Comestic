# Formula Intelligence V4.4 — Intelligent Formula Group & Concentration Optimizer

Phiên bản V4.4 là **bản mẫu backend chạy được và giao diện Next.js bổ sung** cho phần mềm Web App R&D mỹ phẩm độc lập. V4.4 được xây **trên nguồn V4.3**, giữ dữ liệu V4.1 (33 mẫu sản phẩm, 32 nhóm, 190 INCI ứng viên) và lớp khoa học V4.2/V4.3. Không tự sửa dữ liệu khoa học đã xác minh.

## Chức năng mới

1. Tính % nguyên liệu *cân vào mẻ* (raw-material composition), tổng đúng 100%.
2. Phân rã nguyên liệu thương mại thành INCI theo khoảng tỷ phần đã nhập (`fraction_min`, `fraction_max`). Nếu thiếu dữ liệu, giữ khối lượng **UNRESOLVED**, không tự phân chia.
3. Tính phần trăm từng nhóm chức năng từ các nguyên liệu cân, mỗi vật liệu được tính **một lần**.
4. Kiểm tra nghiệm khả thi bằng `scipy.optimize.linprog` và tính **min/max khả thi toàn cục** cho mỗi nguyên liệu, nhóm và INCI đã mô hình hóa.
5. Chọn nghiệm minh họa bằng tối ưu L1 có trọng số theo mục tiêu do người dùng nhập. Mục tiêu trống dùng phân bố đều tổng hợp, **không phải bằng chứng**.
6. So sánh nhiều cách hiểu claim, ví dụ 8% *dung dịch thương mại* và 8% *PAD trong thành phẩm*.
7. Cho phép nhóm từ ảnh Oganic ở chế độ `advisory` (cảnh báo) hoặc `strict` (ràng buộc cứng do người dùng chọn).
8. Sàng lọc rủi ro bằng V4.3 trên nghiệm minh họa theo yêu cầu; không thay thế phòng thử nghiệm.

## Kiến trúc và đơn vị

Đặt `x_j` là **% khối lượng nguyên liệu thương mại cân vào mẻ**, `z_ij` là **% INCI i do nguyên liệu j đóng góp**:

- `Σ_j x_j = 100`
- `fraction_min_ij × x_j ≤ z_ij ≤ fraction_max_ij × x_j`
- `Σ_i z_ij + z_unresolved_j = x_j`
- `G_k = Σ_{j thuộc nhóm chính k} x_j`
- Khi có claim `finished_inci`, áp `Σ_j z_ij = claim_percent` **chỉ khi không còn thành phần premix chưa được giải**.

Tất cả `%` đều theo khối lượng thành phẩm. `0.30` ở `fraction_min` tương ứng **30% trong grade**, không phải 0,30% thành phẩm.

## Chạy nhanh

```bash
python -m pip install -r requirements.txt
python -m pytest -q test_engine.py test_scientific_v43.py test_optimizer_v44.py test_scientific_bridge_v44.py
python cli_v44.py examples/lip_balm_optimizer_v44.json
python cli_v44.py examples/pad_claim_ambiguity_v44.json --compare
uvicorn api_v44:app --host 127.0.0.1 --port 8000
```

API:

- `GET /health/v4.4`
- `GET /api/v4.4/templates` — 33 mẫu sản phẩm
- `GET /api/v4.4/groups?product_id=1` — nhóm và dải % từ ảnh
- `POST /api/v4.4/optimize` — một kịch bản
- `POST /api/v4.4/compare-claims` — kịch bản khác cơ sở claim
- Các endpoint `/api/v4.3/*` vẫn có trong app V4.4.

Ví dụ:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v4.4/compare-claims \
  -H 'Content-Type: application/json' \
  --data-binary @examples/pad_claim_ambiguity_v44.json
```

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run build
npm run dev
```

Mở `http://localhost:3000/optimizer` (trang `/` cũ của V4.3 vẫn được giữ). **Build frontend chưa xác nhận** trong môi trường hiện tại do chưa cài gói `next` (`sh: next: not found`). Chạy `npm install` và `npm run build` tại máy có kết nối npm registry.

## Giới hạn minh bạch

- Khoảng từ `Oganic.zip` chỉ là **dữ liệu giao diện tham khảo**, có thể sai hoặc không đầy đủ. `strict` nghĩa là người dùng chọn áp làm hard constraint, **không phải luật**.
- `grade.composition.status='user_assumption'` không phải COA. Giao diện minh họa có **30% PAD và 70% Aqua hoàn toàn giả định** để chỉ ra khác biệt hai cách hiểu claim.
- Khi còn cấu tử premix chưa biết, INCI được trả dưới nhãn **known contributions only**; không thể khẳng định tổng INCI cuối cùng.
- Thứ tự nhãn INCI chỉ được kiểm tra sơ bộ sau khi tìm nghiệm; các khoảng min/max **không tự động chịu ràng buộc toàn bộ thứ tự nhãn**, trừ khi người dùng xác nhận rõ nhóm INCI >1% trong `label_order_known_above_one`.
- Đếm số lượng nguyên liệu là số **nguyên liệu đã chọn và có lượng dương**, không phải số cấu tử INCI phát sinh từ premix.
- Việc gỡ từng constraint để giải thích vô nghiệm chỉ gợi ý lỗi; không phải minimal unsatisfiable core.
- Không đánh giá pháp lý 6 thị trường, thử độ ổn định, hiệu quả bảo quản, an toàn thành phẩm, tiêu chuẩn Organic hoặc công bố lưu hành.
- `approved_for_manufacturing = false` trong mọi kết quả.

## Cấu trúc quan trọng

- `optimizer_v44.py`: LP concentration engine + scenario alternatives
- `api_v44.py`: REST API, giữ đường dẫn V4.3
- `scientific_bridge_v44.py`: đọc kết quả ví dụ để sàng lọc V4.3
- `test_optimizer_v44.py`, `test_scientific_bridge_v44.py`: bài kiểm thử V4.4
- `examples/*.json`: kịch bản đầu vào và kết quả mẫu
- `frontend/app/optimizer/`: giao diện Next.js tiếng Việt
- `schema_v44_postgres.sql`: schema đề xuất; không thực hiện migration tự động
- `Concentration_Optimizer_V4_4_Results.xlsx`: đối chiếu kịch bản và bảng tỷ trọng nhóm có công thức Excel
- `CODEX_HANDOFF_V44.md`: hướng dẫn tích hợp dự án thật
