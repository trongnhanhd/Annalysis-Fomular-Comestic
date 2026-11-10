# FRONTEND SPEC · V2.3

## Trải nghiệm R&D hằng ngày

**Tổng quan → Phân tích INCI → Đọc kết quả & bằng chứng → Lưu sản phẩm → Công thức giả thuyết → Lưu phiên bản.**

Hệ thống có sáu khu vực được chọn qua sidebar; URL có `?tab=` để lưu trạng thái điều hướng. Thiết kế tối ưu màn hình desktop phân tích song song; màn hình nhỏ chuyển một cột, sidebar ẩn trong menu và bảng dài cho phép cuộn ngang bên trong.

## Thiết kế

- Background `#f6f8f8`, Sidebar navy `#132f3a`, Teal `#0b8d82`, trắng `#fff`.
- Trạng thái: xanh lá = khả thi/đã duyệt; vàng = cảnh báo/chưa kiểm duyệt; đỏ = mâu thuẫn/lỗi; xanh dương = nguồn/công thức tham chiếu.
- Font UI `Inter` hoặc system fallback, tiêu đề `DM Sans` hoặc system fallback.
- Giao diện hoàn toàn tiếng Việt, chuẩn `%`, ngày `dd/mm/yyyy` và phân tách thập phân Việt Nam khi hiển thị.

## Trạng thái dữ liệu

| Loại | Có trong V2.3 | Ý nghĩa |
| --- | --- | --- |
| Khoảng khả thi | Có | Cận dưới/trên cho từng nguyên liệu, giải từ LP |
| Nồng độ công bố chính xác | Có | Khóa ràng buộc khi là INCI tinh khiết trong thành phẩm và có nguồn |
| Công bố xấp xỉ | Có | Chú thích; không tự ép thành bằng đúng |
| Nguồn nghiên cứu | Có | Đối chiếu riêng, không thay ràng buộc cứng |
| Giới hạn pháp lý | Có, catalog hạn chế | Chỉ dùng nếu thị trường, chức năng, loại sản phẩm khớp |
| Nồng độ có xác suất cao | Chưa | Luôn hiển thị "Chưa có" nếu `estimated_pct=null` |

## Endpoint frontend sử dụng

Frontend chỉ gọi BFF `/api/bff/` với session cookie httpOnly. BFF chuyển tiếp tới backend có thể có khóa `WORKSPACE_API_KEY` (server-side only):

- GET `v2/catalog/research`, `v2/catalog/regulatory`.
- POST `v2/analyze` (body `AnalysisRequest` hiện hữu).
- GET/POST `workspace/products`.
- POST `workspace/products/{id}/analyses`; GET danh sách lần phân tích.
- GET/POST `workspace/research`; POST `workspace/research/{id}/review`.
- GET/POST `workspace/products/{id}/formulas`.

Màn hình có thể khởi động thiếu DB catalog hoặc DB workspace, nhưng phải cảnh báo dịch vụ chưa kết nối. Không dùng số liệu mock thay cho câu trả lời của API.

## Cải tiến đã có

- Nhập nhiều hoạt chất công bố, trường nguồn; giao diện loại đơn vị %, ppm, mg/g, exact/approximate.
- Nhập CN trace (≤0,1%) riêng; chặn tên INCI trùng.
- Lưu bản nháp nhập liệu trong `localStorage` trên thiết bị người dùng (không lưu mã truy cập, khóa server).
- Bảng bằng chứng mở rộng theo nguyên liệu và đối chiếu tổ hợp bảo quản.
- Xuất JSON đầy đủ input/result hoặc CSV dữ liệu khoảng min–max.
- Tìm kiếm sản phẩm và nghiên cứu; lọc pháp lý theo thị trường; lưu công thức đủ 100%.
- Giữ lịch sử không ghi đè; người dùng vẫn phải xem xét dữ liệu với chuyên gia.

## Chưa có

Chạy build Next.js trong môi trường tạo gói; migration production, nhiều người dùng/RBAC, upload Excel/PDF, nhập COA, ước lượng Bayesian, kết nối ChatGPT MCP qua HTTPS thật. Các giới hạn này phải được nghiệm thu riêng trong các bước sau.
