import faiss
import numpy as np
import pickle
import time
import torch
from sentence_transformers import SentenceTransformer

class MedicalSearchEngine:
    def __init__(self):
        print("⏳ Đang khởi tạo bộ máy tìm kiếm...")
        
        # 1. Load Model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer('BAAI/bge-m3', device=device)
        
        # 2. Load FAISS Indexes
        self.index_icd10 = faiss.read_index("icd10.index")
        self.index_rxnorm = faiss.read_index("rxnorm.index")
        
        # 3. Load Metadata Dictionaries
        with open("icd10_metadata.pkl", "rb") as f:
            self.meta_icd10 = pickle.load(f)
            
        with open("rxnorm_metadata.pkl", "rb") as f:
            self.meta_rxnorm = pickle.load(f)
            
        print("✅ Hệ thống đã sẵn sàng!\n" + "-"*50)

    def search(self, query, db_type='icd10', top_k=5):
        """
        Thực hiện tìm kiếm vector.
        - query: Câu truy vấn (Ví dụ: "bệnh ỉa chảy tả", "thuốc trị huyết áp amlodipine")
        - db_type: 'icd10' hoặc 'rxnorm'
        - top_k: Số lượng kết quả muốn lấy
        """
        # Chọn đúng CSDL
        if db_type == 'icd10':
            index = self.index_icd10
            meta = self.meta_icd10
        else:
            index = self.index_rxnorm
            meta = self.meta_rxnorm

        start_time = time.time()
        
        # BƯỚC QUAN TRỌNG: Encode câu query. 
        # Bắt buộc phải có normalize_embeddings=True để đồng bộ với thuật toán IndexFlatIP.
        query_vector = self.model.encode(
            [query], 
            normalize_embeddings=True
        )
        query_vector = np.array(query_vector).astype('float32')

        # Thực thi tìm kiếm trong FAISS
        # D: Mảng chứa điểm số (Score/Distance), I: Mảng chứa ID
        scores, indices = index.search(query_vector, k=top_k)
        
        search_time = time.time() - start_time

        # In kết quả
        print(f"🔍 Kết quả cho: '{query}' (Tìm trong: {db_type.upper()})")
        print(f"⏱️ Thời gian phản hồi: {search_time:.4f}s")
        print(f"{'Mã (Code)':<15} | {'Điểm Tương Đồng (Score)'}")
        print("-" * 50)
        
        for i in range(top_k):
            faiss_id = indices[0][i]
            score = scores[0][i]
            
            # Lấy mã thực tế từ Metadata Dict
            medical_code = meta.get(faiss_id, "Unknown")
            
            # Vì ta dùng Inner Product với vector chuẩn hóa, Score chính là Cosine Similarity.
            # Điểm càng gần 1.0 thì ngữ nghĩa càng giống nhau.
            print(f"{medical_code:<15} | {score:.4f}")
        print("\n")

if __name__ == "__main__":
    # Khởi tạo engine
    engine = MedicalSearchEngine()
    
    print("\n" + "="*50)
    print("🧪 BẮT ĐẦU CHẠY 30 TESTCASE TỪ DỮ LIỆU THỰC TẾ")
    print("="*50 + "\n")

    # =====================================================================
    # NHÓM 1: KIỂM THỬ TÊN THUỐC (RXNORM)
    # Mục đích: Test khả năng nhận diện thuốc khi bị kẹp giữa hàm lượng, 
    # đường dùng (po, iv), tần suất (bid, qhs) và từ viết tắt.
    # =====================================================================
    print("💊 NHÓM 1: TEST TÊN THUỐC (RXNORM)")
    
    # Từ File 1.txt
    engine.search(query="metoprolol 25mg po bid", db_type='rxnorm', top_k=3)
    engine.search(query="aspirin 325mg x 1", db_type='rxnorm', top_k=3)
    
    # Từ File 100.txt
    engine.search(query="Laxis 20mg tiêm tĩnh mạch", db_type='rxnorm', top_k=3)
    engine.search(query="nitroglycerin đặt dưới lưỡi", db_type='rxnorm', top_k=3)
    
    # Từ File 33.txt
    engine.search(query="vancomycin 1 gram", db_type='rxnorm', top_k=3)
    engine.search(query="albuterolipratropium nebulizer", db_type='rxnorm', top_k=3)
    
    # Từ File 37.txt (Cách ghi chú liều dùng tiếng Việt)
    engine.search(query="Torsemide: uống 1 viên/ngày", db_type='rxnorm', top_k=3)
    engine.search(query="Insulin glargine: theo đơn 100 đơn vị x 2 lần/ngày", db_type='rxnorm', top_k=3)
    
    # Từ File 44.txt
    engine.search(query="10mg iv diltiazem", db_type='rxnorm', top_k=3)
    engine.search(query="8mg morphine", db_type='rxnorm', top_k=3)
    
    # Từ File 73.txt
    engine.search(query="atorvastatin 80mg daily", db_type='rxnorm', top_k=3)
    engine.search(query="ranexa 500mg daily", db_type='rxnorm', top_k=3)
    
    # Từ File Bài toán (Quy chuẩn output mẫu)
    engine.search(query="metoprolol succinate xl 50 mg po daily", db_type='rxnorm', top_k=3)
    engine.search(query="clonazepam 1.5 mg po qhs", db_type='rxnorm', top_k=3)
    engine.search(query="nystatin oral suspension 5 ml po qid:prn", db_type='rxnorm', top_k=3)


    # =====================================================================
    # NHÓM 2: KIỂM THỬ CHẨN ĐOÁN & BỆNH LÝ CHÍNH QUY (ICD-10)
    # Mục đích: Test các thuật ngữ y khoa chuẩn, tên bệnh phức tạp, 
    # có sự pha trộn giữa tiếng Việt và tiếng Anh.
    # =====================================================================
    print("\n🏥 NHÓM 2: TEST CHẨN ĐOÁN / BỆNH LÝ CHÍNH QUY (ICD-10)")
    
    # Từ File 100.txt, 11.txt, 14.txt
    engine.search(query="cường cận giáp nguyên phát", db_type='icd10', top_k=3)
    engine.search(query="cơn đau thắt ngực ổn định", db_type='icd10', top_k=3)
    engine.search(query="xơ gan mất bù có tăng áp lực tĩnh mạch cửa", db_type='icd10', top_k=3)
    engine.search(query="Bệnh động mạch vành mạn tính có thiếu máu cơ tim", db_type='icd10', top_k=3)
    
    # Từ File 15.txt, 18.txt, 20.txt
    engine.search(query="xuất huyết nội sọ không do chấn thương", db_type='icd10', top_k=3)
    engine.search(query="bóc tách động mạch chủ Stanford loại B", db_type='icd10', top_k=3)
    engine.search(query="gãy cổ xương đùi di lệch", db_type='icd10', top_k=3)
    
    # Từ File 30.txt, 35.txt, 72.txt
    engine.search(query="Bệnh bạch cầu dòng tủy mãn tính", db_type='icd10', top_k=3)
    engine.search(query="Giả gout", db_type='icd10', top_k=3)
    engine.search(query="u ác của đầu tuỵ mới được chẩn đoán", db_type='icd10', top_k=3)


    # =====================================================================
    # NHÓM 3: KIỂM THỬ TRIỆU CHỨNG / MÔ TẢ LÂM SÀNG DÂN DÃ (ICD-10)
    # Mục đích: Test sức mạnh của Model Embedding trong việc hiểu ngữ nghĩa 
    # của các câu văn dài, chứa cụm từ mô tả của bệnh nhân thay vì tên bệnh.
    # =====================================================================
    print("\n🤒 NHÓM 3: TEST TRIỆU CHỨNG & MÔ TẢ LÂM SÀNG PHỨC TẠP (ICD-10)")
    
    # Từ File 10.txt
    engine.search(query="đôi khi đi ngoài ra máu", db_type='icd10', top_k=3)
    
    # Từ File 12.txt
    engine.search(query="ho ra máu cỡ đồng xu x3 đêm qua", db_type='icd10', top_k=3)
    
    # Từ File 13.txt
    engine.search(query="có dịch giống mủ có màu vàng chảy ra từ tổn thương", db_type='icd10', top_k=3)
    
    # Từ File 51.txt
    engine.search(query="vài tuần tiêu chảy bùng nổ", db_type='icd10', top_k=3)
    
    # Từ File 75.txt
    engine.search(query="đau ngực trái dữ dội lan xuống cánh tay trái", db_type='icd10', top_k=3)