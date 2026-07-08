import pandas as pd
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import os
import time

def check_hardware():
    """Step 3.1: Kiểm tra môi trường phần cứng"""
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        print(f"✅ Đã phát hiện GPU: {gpu_name}. ")
    else:
        device = 'cpu'
        print("⚠️ CẢNH BÁO: Không tìm thấy GPU, hệ thống sẽ chạy bằng CPU. Điều này sẽ chậm hơn đáng kể.")
    return device

def vectorize_and_save(model, csv_path, id_col, output_prefix):
    """
    Hàm lõi thực hiện đọc CSV, encode và lưu ma trận.
    - csv_path: Đường dẫn file CSV đã chuẩn bị ở Bước 2.
    - id_col: Cột định danh (code với ICD-10, rxcui với RxNorm).
    - output_prefix: Tiền tố tên file khi lưu ra (ví dụ 'icd10', 'rxnorm').
    """
    if not os.path.exists(csv_path):
        print(f"❌ Không tìm thấy file: {csv_path}")
        return

    print(f"\n🚀 ĐANG XỬ LÝ: {csv_path}")
    
    # Step 3.3: Đọc và bóc tách dữ liệu
    df = pd.read_csv(csv_path)
    
    # Rút trích List text và List ID
    texts = df['text_to_embed'].tolist()
    ids = df[id_col].tolist()
    print(f"📊 Đã tải {len(texts)} dòng dữ liệu.")

    # Step 3.4: Thực thi Encode
    print("⏳ Bắt đầu encode (có thể mất vài phút tùy cấu hình)...")
    start_time = time.time()
    
    # KÍCH HOẠT SỨC MẠNH CỦA SENTENCE-TRANSFORMERS
    # - batch_size=32: Tối ưu cho VRAM 8GB-12GB (Không bị OOM).
    # - normalize_embeddings=True: Chuẩn hóa L2, biến vector thành dạng tối ưu cho phép Dot Product (Inner Product).
    embeddings = model.encode(
        texts,
        batch_size=32, 
        normalize_embeddings=True, 
        show_progress_bar=True
    )
    
    end_time = time.time()
    print(f"⏱️ Encode hoàn tất trong {end_time - start_time:.2f} giây.")
    
    # Ép kiểu dữ liệu về float32 để tối ưu hóa lưu trữ và tính toán với FAISS sau này
    embeddings = np.array(embeddings).astype('float32')
    
    # Step 3.5: Kiểm tra Output và Lưu trữ tạm thời
    print(f"📏 Kích thước ma trận sinh ra (N, Dimensions): {embeddings.shape}")
    
    # Lưu file ma trận vectors (.npy)
    vector_file = f"{output_prefix}_vectors.npy"
    np.save(vector_file, embeddings)
    
    # Lưu file danh sách IDs (.npy) để sau này map với kết quả từ FAISS
    id_file = f"{output_prefix}_ids.npy"
    np.save(id_file, np.array(ids))
    
    print(f"💾 Đã lưu ma trận vector tại: {vector_file}")
    print(f"💾 Đã lưu danh sách ID tại: {id_file}")

if __name__ == "__main__":
    # Khai báo đường dẫn Input (Output của file Python trước đó)
    ICD10_CSV = "icd10_prepared_for_embed.csv"
    RXNORM_CSV = "rxnorm_prepared_for_embed.csv"
    
    # Thiết lập phần cứng
    device = check_hardware()
    
    # Step 3.2: Load Model BAAI/bge-m3 vào bộ nhớ
    print("\n📥 Đang tải mô hình BAAI/bge-m3 vào VRAM/RAM...")
    model = SentenceTransformer('BAAI/bge-m3', device=device)
    print("✅ Load model thành công!")
    
    # Chạy Vectorization cho ICD-10 (Định danh bằng cột 'code')
    vectorize_and_save(model, ICD10_CSV, id_col='code', output_prefix='icd10')
    
    # Chạy Vectorization cho RxNorm (Định danh bằng cột 'rxcui')
    vectorize_and_save(model, RXNORM_CSV, id_col='rxcui', output_prefix='rxnorm')
    
    print("\n🎉 BƯỚC 3 ĐÃ HOÀN TẤT! Dữ liệu đã sẵn sàng cho FAISS.")