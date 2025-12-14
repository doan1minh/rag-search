# Hướng Dẫn Sử Dụng Hệ Thống Nghiên Cứu Pháp Luật

## Giới Thiệu
Đây là hệ thống hỗ trợ tra cứu và phân tích văn bản pháp luật Việt Nam tự động. Bạn chỉ cần đặt câu hỏi, hệ thống sẽ tìm kiếm và tổng hợp thông tin pháp lý liên quan.

---

## Cách Chạy Chương Trình

### Bước 1: Mở Terminal (Command Prompt)
1. Nhấn **Windows + R** trên bàn phím
2. Gõ `cmd` và nhấn **Enter**
3. Một cửa sổ màu đen sẽ xuất hiện

### Bước 2: Di chuyển đến thư mục dự án
Gõ lệnh sau và nhấn **Enter**:
```
cd C:\Users\dvmin\Desktop\AI\RagResearch
```

### Bước 3: Kích hoạt môi trường
Gõ lệnh sau và nhấn **Enter**:
```
.\ragResearchGen\Scripts\activate
```
> Bạn sẽ thấy `(ragResearchGen)` xuất hiện ở đầu dòng

### Bước 4: Chạy chương trình
Gõ lệnh sau và nhấn **Enter**:
```
python -m src.main
```

### Bước 5: Đợi kết quả
- Chương trình sẽ tự động xử lý
- Kết quả sẽ hiển thị trên màn hình
- Thời gian chạy khoảng 1-2 phút

---

## Cách Thay Đổi Câu Hỏi

Để thay đổi câu hỏi pháp lý, bạn cần chỉnh sửa file `src/main.py`:

1. Mở file `C:\Users\dvmin\Desktop\AI\RagResearch\src\main.py`
2. Tìm dòng có nội dung:
   ```
   query = "Khoáng sản nhóm III"
   ```
3. Thay đổi nội dung trong dấu ngoặc kép thành câu hỏi của bạn
4. Lưu file (Ctrl + S)
5. Chạy lại chương trình theo Bước 4

### Ví dụ các câu hỏi:
- `"Quy định về thu hồi đất vì mục đích an ninh quốc phòng"`
- `"Thời gian làm việc và nghỉ ngơi theo Bộ luật Lao động"`
- `"Điều kiện thành lập công ty TNHH một thành viên"`

---

## Các Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|-------------|----------------|
| `'python' is not recognized` | Chưa cài Python | Liên hệ bộ phận IT để cài đặt |
| `429 Too Many Requests` | Gọi API quá nhiều | Đợi 1 phút rồi thử lại |
| `Connection error` | Mất mạng | Kiểm tra kết nối internet |

---

## Liên Hệ Hỗ Trợ
Nếu gặp vấn đề, vui lòng liên hệ bộ phận IT hoặc người quản lý dự án.
