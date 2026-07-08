import numpy as np
import faiss
import pickle
import os
import time

def build_and_save_index(vector_file, id_file, output_prefix):
    """
    Hàm thực thi 4 bước xây dựng và lưu trữ FAISS Index cùng Metadata.
    """
    print(f"\n🚀 ĐANG XỬ LÝ: {output_prefix.upper()}")
    
    if not os.path.exists(vector_file) or not os.path.exists(id_file):
        print(f"❌ Lỗi: Không tìm thấy file dữ liệu đầu vào cho {output_prefix}!")
        return

    # Step 4.1: Load dữ liệu từ Bước 3 vào bộ nhớ (RAM)
    print("⏳ Đang tải dữ liệu vào RAM...")
    vectors = np.load(vector_file)
    ids = np.load(id_file, allow_pickle=True)
    print(f"📊 Kích thước ma trận vector: {vectors.shape}")
    print(f"📊 Số lượng ID tương ứng: {len(ids)}")

    # Step 4.2: Khởi tạo FAISS Index với thuật toán Cosine Similarity
    # Vì vector đã được chuẩn hóa (normalize_embeddings=True) ở Bước 3, 
    # ta dùng IndexFlatIP (Inner Product) để đại diện cho Cosine Similarity.
    d = vectors.shape[1] # Số chiều (dimensions), ở đây là 1024
    print(f"⚙️ Đang khởi tạo FAISS Index với số chiều d={d} (IndexFlatIP)...")
    index = faiss.IndexFlatIP(d)
    
    # Nạp toàn bộ ma trận vector vào Index
    start_time = time.time()
    index.add(vectors)
    print(f"✅ Đã nạp {index.ntotal} vectors vào FAISS Index trong {time.time() - start_time:.4f} giây.")

    # Step 4.3: Xây dựng Từ điển Metadata (Mapping Dictionary)
    print("🗂️ Đang xây dựng từ điển Metadata mapping...")
    # Tạo dictionary dạng: {faiss_id: medical_code}
    # enumerate sẽ sinh ra faiss_id chạy từ 0 đến n-1
    metadata_dict = {i: str(code) for i, code in enumerate(ids)}

    # Step 4.4: Lưu trữ ra file vật lý (Export)
    index_filename = f"{output_prefix}.index"
    metadata_filename = f"{output_prefix}_metadata.pkl"

    print("💾 Đang xuất file vật lý...")
    # Lưu FAISS Index
    faiss.write_index(index, index_filename)
    
    # Lưu Metadata Dictionary bằng Pickle
    with open(metadata_filename, 'wb') as f:
        pickle.dump(metadata_dict, f)

    print(f"🎉 Hoàn thành {output_prefix.upper()}!")
    print(f"   -> File Index: {index_filename}")
    print(f"   -> File Dictionary: {metadata_filename}")


if __name__ == "__main__":
    # 1. Xử lý bộ ICD-10
    build_and_save_index(
        vector_file="icd10_vectors.npy",
        id_file="icd10_ids.npy",
        output_prefix="icd10"
    )
    
    print("-" * 50)
    
    # 2. Xử lý bộ RxNorm
    build_and_save_index(
        vector_file="rxnorm_vectors.npy",
        id_file="rxnorm_ids.npy",
        output_prefix="rxnorm"
    )
    
    print("\n✅ TOÀN BỘ BƯỚC 4 ĐÃ HOÀN TẤT. BẠN ĐÃ CÓ THỂ BẮT ĐẦU TRUY VẤN!")