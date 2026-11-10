# Hướng dẫn kỹ thuật V4.3 — Scientific Knowledge Graph

## 1. Phân cấp dữ liệu

`Product Type → Functional Group → Candidate INCI → Supplier Grade → Observed Property + Test Conditions → Evidence Source → Scenario-specific R&D Warning`.

Tên INCI là danh mục chung. `supplier_grade_reference_v43` là hàng hóa cụ thể có thể mang nhiều INCI. `scientific_property_observations_v43` là một **quan sát** có khoảng giá trị, đơn vị, điều kiện áp dụng, nguồn và trạng thái, không phải giới hạn công thức phổ quát.

## 2. Kiểm tra % theo nhóm

- `x_j` là tỷ lệ vật liệu thương mại cân vào mẻ (% w/w).
- `a_ij` là tỷ phần INCI i trong vật liệu j **chỉ khi nguồn định lượng được chứng thực**.
- `y_i = Σ_j a_ij × x_j` nếu tỷ phần đã xác minh.
- `G_k = Σ_i b_ik × y_i` hoặc tính theo vật liệu đầu vào khi chọn chế độ nhóm raw material, không cộng cả hai chế độ.
- Trường hợp premix chưa có tỷ phần `a_ij`: không đưa vào tính y_i, thay bằng `unresolved_component_fraction`; tổng vật liệu cân vẫn tính đủ 100%.

## 3. Độ ưu tiên nguồn

1. COA của lô nguyên liệu và thử nghiệm phòng lab cho quy trình thật.
2. TDS/SDS chính thức, có phiên bản và đúng grade.
3. Tài liệu kỹ thuật từ website chính thức của nhà cung cấp.
4. Tài liệu nghiên cứu có mô tả phương pháp và điều kiện.
5. Mẫu công thức thương mại tham khảo.
6. Dải người dùng cung cấp hoặc giả định mô phỏng.

Các cấp chứng cứ là *thứ tự ưu tiên triển khai*, không phải hệ số tin cậy cố định. Khi hai nguồn khác nhau, điều kiện phải được so sánh trước khi giải quyết xung đột.

## 4. Ví dụ phân tích 

`Lip Balm`: 10% KahlWax 8109 + 5% KahlWax 2039L; công đoạn làm chảy hoàn toàn ở 60°C. Hệ thống cảnh báo 60°C thấp hơn khoảng nóng chảy 61–66°C và 68–73°C của hai grade. Không được coi cảnh báo này là lỗi an toàn hoặc lệnh buộc nhiệt độ cụ thể, vì hỗn hợp có thể làm thay đổi hành vi pha.

`KahlBase 4074`: Nhà cung cấp có danh sách tên cấu tử và dải dùng trong lipstick, nhưng tỷ phần từng cấu tử chưa được chứng minh. Không phân bổ phần trăm từ tên danh sách.

## 5. Các bảng dữ liệu

- `fi_v43_sources`
- `fi_v43_supplier_grades`
- `fi_v43_grade_observations`
- `fi_v43_grade_components_qualitative`
- `fi_v43_review_events`

Dùng ID bền vững, không ghi đè nguồn cũ và lưu revision của TDS/SDS. Một source có thể bị thay đổi mà không làm mất dữ liệu lịch sử.

## 6. Yêu cầu R&D trước khi dùng để phê duyệt sản xuất

Xác thực danh pháp INCI; COA/assay grade; lô nguyên liệu; độ tan trong nền thực; pH; tương tác điện giải; ổn định nhiệt/lạnh; độ nhớt; độ bền vi sinh; an toàn thành phẩm; công bố chức năng và pháp lý thị trường. Không tự động ký duyệt từ bất kỳ warning score nào.
