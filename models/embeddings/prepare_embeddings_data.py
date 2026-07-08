import pandas as pd
import os

def process_icd10_data(input_path, output_path):
    print("Đang xử lý dữ liệu ICD-10...")
    # 1. Đọc dữ liệu
    df = pd.read_csv(input_path)
    
    # 2. Xử lý missing data (NaN -> chuỗi rỗng)
    df = df.fillna('')
    
    # 3. Chuẩn hóa cột synonym: Thay thế '|' bằng ', '
    # Dùng regex=False để hiểu '|' là ký tự bình thường, không phải toán tử OR trong regex
    df['synonym'] = df['synonym'].str.replace('|', ', ', regex=False)
    
    # 4. Áp dụng Template
    def apply_icd10_template(row):
        # Lọc bỏ các khoảng trắng thừa nếu có cột bị trống hoàn toàn
        vi = row['tên bệnh VI'].strip()
        en = row['tên bệnh EN'].strip()
        syn = row['synonym'].strip()
        return f"Chẩn đoán: {vi}. Tên tiếng Anh: {en}. Các cách gọi khác: {syn}"
    
    df['text_to_embed'] = df.apply(apply_icd10_template, axis=1)
    
    # 5. Lưu lại để kiểm tra hoặc pass thẳng vào bước encode
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ Hoàn thành ICD-10. Dữ liệu mẫu dòng 1:\n{df['text_to_embed'].iloc[1]}\n")
    return df

def process_rxnorm_data(input_path, output_path):
    print("Đang xử lý dữ liệu RxNorm...")
    # 1. Đọc dữ liệu
    df = pd.read_csv(input_path)
    
    # 2. Xử lý missing data
    df = df.fillna('')
    
    # 3. Chuẩn hóa cột synonyms: Thay thế '|' bằng ', '
    df['synonyms'] = df['synonyms'].str.replace('|', ', ', regex=False)
    
    # 4. Áp dụng Template
    def apply_rxnorm_template(row):
        name = row['name'].strip()
        syn = row['synonyms'].strip()
        return f"Thuốc: {name}. Tên thương mại và đồng nghĩa: {syn}"
    
    df['text_to_embed'] = df.apply(apply_rxnorm_template, axis=1)
    
    # 5. Lưu lại
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ Hoàn thành RxNorm. Dữ liệu mẫu dòng 0:\n{df['text_to_embed'].iloc[0]}\n")
    return df

if __name__ == "__main__":

    ICD10_INPUT = "data\\icd10\\icd10_mapping.csv"
    ICD10_OUTPUT = "icd10_prepared_for_embed.csv"
    
    RXNORM_INPUT = "data\\rxnorm\\rxnorm_mapping.csv"
    RXNORM_OUTPUT = "rxnorm_prepared_for_embed.csv"
    
    # Chạy xử lý
    if os.path.exists(ICD10_INPUT):
        df_icd10 = process_icd10_data(ICD10_INPUT, ICD10_OUTPUT)
    else:
        print(f"❌ Không tìm thấy file {ICD10_INPUT}")
        
    if os.path.exists(RXNORM_INPUT):
        df_rxnorm = process_rxnorm_data(RXNORM_INPUT, RXNORM_OUTPUT)
    else:
        print(f"❌ Không tìm thấy file {RXNORM_INPUT}")