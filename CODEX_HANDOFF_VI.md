# Bàn giao Codex — Formula Intelligence V4.3

Bạn đang tiếp tục phần mềm độc lập **Cosmetic Formula R&D**; giữ nguyên FastAPI, Next.js, PostgreSQL đang có, không gộp dự án khác.

1. Đọc `README.md`, `IMPLEMENTATION_GUIDE_VI.md`, V4.1/V4.2 dependency, các CSV mới và `scientific_engine_v43.py`.
2. Không ghi đè bảng cũ; bổ sung migration từ `schema_v43_postgres.sql` sau khi đối chiếu schema thực tế và bổ sung audit/transaction/permission.
3. Tạo API tra cứu theo `INCI / trade grade / supplier / group / type / source`. Chỉ áp các thông số có `grade_id` trùng khớp, đơn vị và điều kiện hợp lệ.
4. Dùng danh mục nguồn để thêm DOI, phiên bản TDS/SDS, lot COA, trạng thái QA. Không đánh dấu 190 INCI là đã chứng thực.
5. Trong giao diện, người nghiên cứu chọn grade và thấy nguồn, điều kiện, % khuyến nghị và giới hạn còn thiếu. Ở bảng % nguyên liệu, phân biệt `raw_material_percent`, `final_inci_percent`, `claim_percent`, `unresolved_component_percent`.
6. Các review ở cấp khoa học không đồng nghĩa `legal_pass` hoặc `manufacturing_approval`.
7. Giữ API v4.2 hoặc viết adapter tương thích; tránh breaking change và test regression.
8. Chạy `python -m pytest -q test_engine.py test_scientific_v43.py`, chạy `npm install && npm run build`, tự sửa lỗi nếu có quyền truy cập registry. Nếu không có quyền, báo rõ chưa chạy được build frontend.
9. Tích hợp vào thư viện 33 loại sản phẩm × 32 nhóm, ưu tiên lip balm, serum nước, cream O/W; bổ sung từng grade có source, không điền giá trị rỗng bằng số phỏng đoán.
10. Tạo báo cáo `coverage` và `review_queue`: nguyên liệu nào thiếu TDS/COA, dữ liệu pháp lý thị trường nào chưa có, nguyên liệu đa INCI nào chưa phân rã được.

**Definition of Done:** Kiểm thử qua, API có schema OpenAPI, có truy dấu nguồn, cảnh báo có điều kiện, có thể nhập công thức minh họa 100% và thấy kết quả cùng bằng chứng. Không phê duyệt sản xuất từ kết quả mô phỏng.
