# Chuẩn hóa ICD-10

## Mục tiêu
- Tải danh mục ICD-10 từ nguồn công khai.
- Làm sạch và chuẩn hóa dữ liệu để dùng cho pipeline.
- Chưa thực hiện mapping synonym ở bước này.

## Nguồn sử dụng
- URL tải: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2027/icd10cm-code-descriptions-2027.zip
- File dùng trong zip: icd10cm-code-descriptions-2027/icd10cm-codes-2027.txt

## Done
- Viết script: scripts/prepare_icd10_catalog.py.
- Chuẩn hóa mã ICD về dạng có dấu chấm.
- Chuẩn hóa tên bệnh EN (unicode, khoảng trắng).
- Khử trùng lặp theo mã.
- Xuất catalog CSV và metadata JSON.

## Cách chuẩn hóa ICD-10
1. Tải file zip từ nguồn CDC FTP đã chốt.
2. Đọc file mã bệnh gốc: icd10cm-codes-2027.txt.
3. Tách từng dòng thành code và disease_name_en.
4. Chuẩn hóa code về định dạng chuẩn có dấu chấm (ví dụ A010 -> A01.0).
5. Chuẩn hóa text tên bệnh (chuẩn unicode, xóa khoảng trắng thừa).
6. Khử trùng lặp theo code, giữ bản ghi đầu tiên theo thứ tự nguồn.
7. Xuất kết quả ra CSV chuẩn và lưu metadata JSON để truy vết.

## Output
- data/icd10/icd10_catalog_normalized.csv
  - Cột: code, disease_name_vi, disease_name_en
  - Số dòng: 74879
- data/icd10/icd10_catalog_normalized.meta.json

## Phạm vi hiện tại
- Đã xong: tải + chuẩn hóa catalog ICD-10.
- Chưa làm: mapping synonym và bổ sung đầy đủ tên bệnh tiếng Việt.
