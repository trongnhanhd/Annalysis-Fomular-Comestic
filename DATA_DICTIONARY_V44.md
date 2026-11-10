# Từ điển thuật toán V4.4

| Trường | Ý nghĩa | Đơn vị/loại |
|---|---|---|
| items[].item_id | Mã duy nhất của nguyên liệu được cân | string |
| items[].group_code | Nhóm chính không chồng lặp để cộng % | group key |
| items[].percent_bounds.min/max | Cận lượng nguyên liệu thương mại cân vào mẻ | % thành phẩm |
| items[].prior_percent | Trọng số/giá trị mong muốn khi chọn nghiệm minh họa, không phải dữ liệu đo | % thành phẩm |
| composition.complete | Đã mô hình hóa toàn bộ khối lượng grade hay chưa | boolean |
| composition.status | verified/supplier_range/user_assumption/unknown | nhãn nguồn |
| components[].fraction_min/max | Tỷ phần INCI trong grade nguồn | 0..1 |
| claims[].basis | raw_material/finished_inci | claim basis |
| ambiguous_claims[] | Danh sách các cách diễn giải cần so sánh | scenarios |
| template_mode | advisory hoặc strict | ràng buộc tham khảo |
| group_limits[] | Ràng buộc hoặc mục tiêu theo nhóm do người dùng nhập | % thành phẩm |
| label_inci_order[] | Thứ tự nhãn INCI, kiểm tra sau nghiệm | danh sách INCI |
| label_order_known_above_one[] | Chỉ nhóm >1% khi người dùng xác nhận; mới được đưa vào LP | danh sách INCI |
| result.status | FEASIBLE / INFEASIBLE / INSUFFICIENT_DATA_OR_SELECTION | trạng thái solver |
| result.groups[].feasible_interval_percent | Khoảng min–max tối ưu với cùng bộ constraint | [% thấp,% cao] |
| result.inci_known_contributions[] | Lượng INCI đã mô hình hóa, chưa chắc là tổng cuối nếu có unknown premix | % thành phẩm |
| unresolved_composition_percent_example | Khối lượng premix còn chưa phân rã | % thành phẩm |
| scientific_screening | Đánh giá V4.3 từ nghiệm minh họa, không phải kết quả lab | object |

Lưu ý: % thành phẩm theo khối lượng được phân biệt với tỷ phần grade. Ví dụ 8% grade chứa 30% PAD tạo 2,4% PAD, không phải 8% PAD. Dải `%` từ ảnh ứng dụng Oganic có provenance `reference_screenshot_not_legal_limit`.
