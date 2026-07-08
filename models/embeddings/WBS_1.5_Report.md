
## 1. TỔNG QUAN KIẾN TRÚC
Hệ thống sử dụng phương pháp **Dense Retrieval** (Truy xuất dựa trên Vector không gian) để giải quyết bài toán Entity Linking trong văn bản y khoa. Thay vì so khớp chuỗi (Exact Match) dễ thất bại khi sai chính tả hoặc dùng từ đồng nghĩa, toàn bộ dữ liệu y tế được nhúng (embed) vào không gian vector đa chiều.

* **Mô hình Embedding:** `BAAI/bge-m3` (Đa ngôn ngữ, < 9B tham số, xử lý tốt Anh-Việt giao thoa).
* **Vector Dimension:** 1024 chiều.
* **Công cụ Indexing:** `FAISS-CPU` (Sử dụng thuật toán Inner Product trên vector đã chuẩn hóa).
* **Phần cứng tăng tốc:** NVIDIA CUDA (tại khâu encode).

---

## 2. QUÁ TRÌNH TRIỂN KHAI CHI TIẾT (WORKFLOW)

### Bước 1: Tiền xử lý & Làm giàu ngữ nghĩa (Data Preparation)
Dữ liệu gốc dạng bảng (Tabular) từ ICD-10 và RxNorm không phù hợp để đưa trực tiếp vào mô hình ngôn ngữ. Giải pháp là thiết kế **Contextual Templates** để bọc dữ liệu, giúp mô hình hiểu rõ chức năng của từng thực thể.
* **ICD-10 Template:** `Chẩn đoán: {tên bệnh VI}. Tên tiếng Anh: {tên bệnh EN}. Các cách gọi khác: {synonyms}`
* **RxNorm Template:** `Thuốc: {name}. Tên thương mại và đồng nghĩa: {synonyms}`
* *Kết quả:* Các ký tự nhiễu như `|` được thay bằng dấu phẩy `,`. Dữ liệu được số hóa thành các chuỗi văn bản hoàn chỉnh.

### Bước 2: Chuyển đổi Vector (Vectorization)
Tiến hành chạy mô hình `BAAI/bge-m3` trên GPU để biến đổi các chuỗi văn bản thành ma trận vector.
* **Tối ưu VRAM:** Sử dụng `batch_size=32` để chống tràn bộ nhớ.
* **Chuẩn hóa L2 (L2 Normalization):** Kích hoạt `normalize_embeddings=True`. Đây là kỹ thuật cốt lõi giúp đưa tất cả các vector về cùng độ dài, cho phép hệ thống sử dụng phép nhân vô hướng (Dot Product) thay vì công thức Cosine phức tạp ở bước sau.
* *Kết quả:* Sinh ra ma trận kích thước (12219, 1024) cho ICD-10 và (48, 1024) cho RxNorm. Lưu trữ dưới định dạng `.npy`.

### Bước 3: Xây dựng Bộ chỉ mục (FAISS Indexing)
Nạp ma trận vector vào không gian tìm kiếm của Meta FAISS.
* **Thuật toán:** `IndexFlatIP` (Inner Product). Do vector đã được chuẩn hóa, Inner Product đại diện chính xác cho Cosine Similarity.
* **Metadata Mapping:** Xây dựng từ điển `.pkl` ánh xạ giữa ID của FAISS (từ 0 đến n) với mã Code chuẩn (A00.0, 1191,...).
* *Thời gian index:* Chỉ mất chưa tới 0.1 giây để nạp toàn bộ dữ liệu.

---

## 3. PHÂN TÍCH KẾT QUẢ ĐÁNH GIÁ (EVALUATION LOGS)

Hệ thống đã được kiểm thử với 30 truy vấn (queries) lấy từ dữ liệu lâm sàng thực tế, chia làm 3 nhóm chính. Thời gian phản hồi trung bình cực kỳ ấn tượng: **~0.1s / query**.

### 🟢 Nhóm 1: Tên thuốc & Y lệnh (RxNorm)
* **Đặc điểm:** Bác sĩ thường viết tắt, trộn lẫn tên thương mại, hàm lượng và đường dùng (VD: *metoprolol 25mg po bid*, *Laxis 20mg tiêm tĩnh mạch*).
* **Nhận xét:** Hệ thống xử lý xuất sắc. Mô hình không bị nhiễu bởi các thông tin định lượng (25mg, 500mg) hay đường dùng (po bid, tiêm tĩnh mạch). Điểm tương đồng (Score) duy trì ổn định ở mức **0.45 - 0.71**. 
* **Độ chính xác:** Truy xuất thành công mã RxCUI chuẩn (VD: *Laxis* map chuẩn xác về *202991 - furosemide*, *aspirin* map về *1191*).

### 🟢 Nhóm 2: Chẩn đoán & Bệnh lý chính quy (ICD-10 Formal)
* **Đặc điểm:** Các cụm từ chẩn đoán dài, lai tạp Anh-Việt hoặc sử dụng thuật ngữ y khoa chuyên sâu.
* **Nhận xét:** Đây là nhóm hệ thống đạt hiệu suất cao nhất. Điểm Score thường xuyên vượt ngưỡng **0.65 - 0.76**.
* **Độ chính xác:** Các ca khó như *"xuất huyết nội sọ không do chấn thương"* map chính xác vào nhóm I62 (Score 0.76). Mô hình hiểu rất rõ các thuật ngữ giải phẫu học và bệnh học.

### 🟡 Nhóm 3: Triệu chứng & Mô tả lâm sàng phức tạp (ICD-10 Symptoms)
* **Đặc điểm:** Text phi cấu trúc, văn phong tự do của bác sĩ, nhiều từ lóng hoặc mô tả hình tượng (VD: *ho ra máu cỡ đồng xu*, *vài tuần tiêu chảy bùng nổ*).
* **Nhận xét:** Đã bắt đầu xuất hiện thách thức. 
    * *Điểm sáng:* Mô hình map rất tốt các triệu chứng có từ khóa cận nghĩa (VD: *"đôi khi đi ngoài ra máu"* -> K92.0 Xuất huyết dạ dày ruột).
    * *Điểm cần lưu ý:* Với các mô tả có nhiều vùng giải phẫu (VD: *"đau ngực trái dữ dội lan xuống cánh tay trái"*), mô hình bị nhầm lẫn trọng số sang "cánh tay" và map vào nhóm chấn thương tay (S66.7) thay vì bệnh lý mạch vành (I20).

---
