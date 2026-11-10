# API sửa lỗi P0 — V4.5.2-R1

## GET /api/v4.5/studies/{study_id}/candidates
Trả về các phương án đã được máy chủ tái tính và đóng băng khi tạo nghiên cứu. Mỗi dòng có `candidate_id`, `candidate_sha256`, `composition_percent` (theo item_id), `design`.

## POST /api/v4.5/studies
Các trường cũ (`title`, `created_by`, `scenario`, `protocol`) giữ nguyên. Có thể thêm `doe_design: {scenario,variables,balance_item_id}`. `doe_design.scenario` phải chính xác bằng `scenario` đã khóa. Nếu không nhập DoE, máy chủ lưu một phương án `BASELINE` từ solver.

## POST /api/v4.5/studies/{study_id}/batches
Các trường cũ (`lot_code`, `operator`, `prepared_at`) giữ nguyên để đọc/ghi legacy. Đối với mẻ cần truy vết, gửi bổ sung:

```json
{
  "lot_code": "LAB-001",
  "operator": "Người cân",
  "candidate_id": "DOE-002",
  "actual_weights_g": {
    "beeswax": 20,
    "jojoba_oil": 30
  },
  "raw_material_lots": {
    "beeswax": "LO-001",
    "jojoba_oil": "LO-002"
  },
  "process": {"procedure_ref": "SOP-LAB-001"},
  "weighed_by": "Người cân"
}
```

**Ví dụ trên là định dạng hai nguyên liệu minh họa, không phải payload hợp lệ cho mẫu Lip Balm 6 nguyên liệu.** Trường `actual_weights_g` và `raw_material_lots` phải có đầy đủ mọi `item_id` của candidate, lấy từ GET candidates. Không tự thay cân nặng thực bằng tỷ lệ mục tiêu.

## GET /api/v4.5/studies/{study_id}/batches
Kết quả cũ được bổ sung `traceability_status`, `candidate_id`, `candidate_sha256`, `actual_weights_g`, `raw_material_lots`, `process`, `weighed_by`, `deviation_max_pp`. Mẻ cũ không có provenance dùng `UNLINKED_LEGACY`.

## GET /api/v4.5/studies/{study_id}/assessment
Thêm `traceability` với `linked_batches`, `total_batches`, `unlinked_batch_ids`, `deviated_batch_ids`, `review_readiness`. Giữ nguyên trạng thái đánh giá số đo để tránh làm hỏng client cũ; **phải kiểm tra cả `traceability.review_readiness` trước khi đánh giá khả năng dùng dữ liệu**.

Không endpoint nào của bản vá cấp phép mỹ phẩm hoặc thay thế đánh giá an toàn.
