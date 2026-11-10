# Giao việc cho Codex — V4.4 Formula Group & Concentration Optimizer

## Mục tiêu

Tích hợp module trong gói này vào **Web App R&D mỹ phẩm độc lập hiện có** (Next.js + FastAPI + PostgreSQL). Không tạo sản phẩm Mountain Lab SkinSim, không gộp phần mềm khác, không xóa các API cũ. Giữ giao diện hoàn toàn tiếng Việt.

## Trình tự thực hiện

1. Đọc `README_V44.md`, `optimizer_v44.py`, `examples/*.json`, `schema_v44_postgres.sql`, file kế thừa `ingredient_catalog_v4_1.json` và API hiện có.
2. Xác định đường dẫn repo/backend/frontend đang dùng; phát triển theo migration additive, tránh tạo database trùng. Áp dụng schema sau khi review mapping bảng và có backup.
3. Tích hợp `POST /api/v4.4/optimize` và `POST /api/v4.4/compare-claims`; đặt validation Pydantic có độ dài và kiểu dữ liệu chặt chẽ. Phân quyền, audit, rate limit theo hệ thống sẵn có.
4. Gắn 33 `Product Type`, nhóm chức năng và khoảng % tham khảo. Mặc định `template_mode=advisory`. Chỉ áp `strict` khi người dùng chủ động chọn.
5. Sử dụng `x_j` cho % nguyên liệu cân, `z_ij` cho INCI đóng góp sau phân rã. Premix không rõ tỷ phần phải có biến **unresolved**; không được tự phân bổ theo thứ tự nhãn.
6. Đối với claim thiếu `basis`, yêu cầu đánh dấu/so sánh giả thuyết. `8% PAD grade` và `8% PAD INCI` không phải một điều kiện.
7. Thêm route frontend `/optimizer` vào navigation chính, hoàn thiện việc nhập/chọn nguyên liệu từ PostgreSQL, trang so sánh nghiệm, danh sách cảnh báo và xuất báo cáo JSON/Excel.
8. Nối `scientific_bridge_v44` vào workflow R&D. Không tự tuyên bố sản phẩm ổn định, bảo quản đạt hoặc tuân thủ pháp lý.
9. Viết integration test database/API, frontend e2e (Playwright), test build, smoke test trên môi trường cài Next.js.
10. Hoàn thành báo cáo: mã nguồn thay đổi, số test chạy thực tế, log build, migration, việc còn thiếu và những giả định chưa có nguồn.

## Trạng thái trước khi bàn giao

- Python optimizer và API runnable, kiểm thử hồi quy thành công (xem `TEST_RESULTS_V44.txt`).
- Next.js đã có mã route demo mới nhưng **chưa build trong môi trường này** vì thiếu dependency `next`. Không tuyên bố frontend production-ready.
- API vẫn dùng dữ liệu CSV/JSON file V4.x; PostgreSQL migration mới là hướng dẫn, chưa được áp dụng vào database thực.

## Điều kiện nghiệm thu

- Mọi nghiệm có tổng % nguyên liệu cân = 100 trong sai số số học.
- Khi grade chỉ có danh sách INCI định tính, không báo % cuối cùng đã xác minh.
- Khi hai ràng buộc mâu thuẫn, trả `INFEASIBLE` và gợi ý xung đột, không bịa nghiệm.
- Kết quả các nhóm chính không cộng trùng `Lipid Base` với thành phần con.
- Khoảng tham chiếu khoa học và giới hạn pháp lý hiển thị bằng badge/tên rõ ràng, không được dùng lẫn.
- Mọi kết quả mặc định `approved_for_manufacturing=false`.

## Prompt để sao chép vào Codex

Đọc toàn bộ gói Formula_Intelligence_V4_4. Tích hợp optimizer vào repo Web App R&D mỹ phẩm độc lập hiện có mà không làm mất tính năng V4.3, dùng PostgreSQL migration có kiểm soát, FastAPI endpoints và route Next.js /optimizer tiếng Việt. Bổ sung chọn nguyên liệu/grade, phân rã premix theo COA hoặc khoảng chứng cứ, ràng buộc nhóm, tính min/max khả thi với SciPy HiGHS, so sánh claim raw-material và finished-INCI, xuất JSON/Excel có audit trail. Giữ mọi dữ liệu chưa xác minh ở trạng thái REVIEW_REQUIRED; không đưa kết luận pháp lý hoặc phê duyệt sản xuất. Chạy kiểm thử backend/frontend/e2e và cung cấp log thật, không thay thế dữ liệu khoa học chưa xác minh.
