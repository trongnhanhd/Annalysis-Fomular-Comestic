# COSMETIC REGULATORY R&D • Data seed v0.1.0

**Ngày chốt:** 09/11/2026. **Trạng thái:** BỘ DỮ LIỆU HẠT GIỐNG CÓ NGUỒN, **CHƯA** LÀ BẢNG PHÁP LÝ ĐẦY ĐỦ ĐỂ CÔNG BỐ HOẶC PHÊ DUYỆT SẢN PHẨM.

## Quy mô
- 62 định danh nguyên liệu / nhóm hóa chất.
- 163 quy tắc đã nhập với URL văn bản nguồn và phạm vi sử dụng.
- 255 cặp nguyên liệu - thị trường **chưa thể kết luận**, không tự gán phần trăm.
- 6 phạm vi: EU, US, VN, ASEAN, KR, CN. Các mức KR/CN hiện chưa được nhập theo từng chất vì cần trích nguyên văn phụ lục hiện hành.

## File
- `cosmetic_regulatory_rd_2026.xlsx` — các bảng lọc, xem và QA.
- `regulatory_rules.json` — dữ liệu JSON hợp nhất có schema mềm; các trường trên từng quy tắc.
- `regulatory_rules.csv` — bảng phẳng (UTF-8 BOM; Excel đọc tiếng Việt).
- `coverage_matrix.csv` — độ bao phủ 6 thị trường cho mỗi INCI.
- `unverified_market_pairs.csv` — hàng đợi chuyên gia pháp chế xác minh.
- `check_formula.py` — phép kiểm tra thử tối đa, mặc định an toàn: trả NEEDS_LEGAL_REVIEW nếu chưa đủ điều kiện.

## Hướng dẫn so sánh
1. Tách bạch **mỹ phẩm thông thường** và **OTC sunscreen drug** tại Mỹ. Không chuyển quy tắc M020 thành quy tắc mỹ phẩm.
2. Chỉ so sánh cùng `market`, `product_scope`, `purpose`, `concentration_basis`, thời điểm hiệu lực và nhóm nguyên liệu hợp lệ.
3. `max_pct_w_w = null` KHÔNG CÓ NGHĨA 0%, có thể là cấm, chưa xác minh hoặc không có mức %; xem `rule_type`.
4. `% muối` khác `% theo acid`; retinol ester cần quy về retinol equivalents; hỗn hợp có tổng ngưỡng phải cộng lại.
5. Một rule MAX không xác nhận nồng độ đó an toàn, hiệu quả, GMP đạt hay đủ để công bố. Giới hạn pháp lý đôi khi khác nồng độ tối ưu R&D.
6. Ở VN, dùng văn bản DAV địa phương, không tự coi mọi cập nhật ASEAN áp dụng tức thì tại Việt Nam.
7. KR/CN: `PENDING_VERIFICATION` cho toàn bộ nguyên liệu trong phiên bản seed; KHÔNG giả định phần trăm EU giống KR/CN.

## Lệnh kiểm tra ví dụ
```
python check_formula.py --market VN --category all_cosmetics --purpose preservative --inci Phenoxyethanol --pct 1.2
python check_formula.py --market VN --category leave_on --purpose preservative --inci 'Sodium Benzoate' --pct 0.6
python check_formula.py --market KR --category all_cosmetics --purpose preservative --inci Phenoxyethanol --pct 0.8
```

**Lưu ý:** kiểm tra chỉ là *pre-screen* theo quy tắc rõ ràng; các trường hợp hít vào, trẻ em, phối hợp, chất màu, chỉ tiêu vết và giấy phép hoạt chất cần chuyên gia duyệt.

## Nâng cấp cần thiết trước khi đưa vào sản xuất
- Bổ sung đầy đủ phụ lục II/III/IV/V/VI/VII theo từng thị trường (hàng nghìn entry) + ánh xạ INCI/CAS đồng nghĩa có kiểm soát.
- Trích nguyên văn Hàn Quốc (MFDS 2026-19) và Trung Quốc (NMPA hiện hành cùng sửa đổi).
- Quản lý bitemporal versioning: effective_from/to, discovered_at, supersedes_id, reviewer, legal sign-off, confidence, document checksum.
- Bộ chuyển đổi đơn vị/formal equivalence + quy tắc giới hạn tổng nhóm theo công thức.
- Kiểm tra từng quốc gia ASEAN nếu xuất khẩu thực tế vì thực thi và hướng dẫn địa phương khác nhau.
