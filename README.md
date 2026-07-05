# Medical Extraction Solution

## 1. Tổng quan

Dự án giải bài toán trích xuất thông tin y khoa từ văn bản tự do, gồm 4 module chính:
- NER: nhận diện 5 loại thực thể
- Entity Linking: ánh xạ CHẨN_ĐOÁN vào ICD-10 và THUỐC vào RxNorm
- Assertion Classification: xác định isNegated, isFamily, isHistorical
- Relation/Ontological Reasoning: suy luận quan hệ giữa các khái niệm

Output cuối cùng là 100 file JSON theo đúng format BTC, đóng gói thành output.zip.

## 2. Cấu trúc thư mục

Cây thư mục mục tiêu:

```text
medical-extraction-solution/
├── config/
│   ├── project.yaml
│   ├── ner.yaml
│   ├── linking.yaml
│   └── assertion.yaml
├── data/
│   ├── input/                 # input test BTC (1.txt ... 100.txt)
│   ├── train/                 # dữ liệu train nội bộ
│   ├── dev/                   # dữ liệu dev nội bộ
│   ├── icd10/
│   │   └── icd10_mapping.csv
│   └── rxnorm/
│       └── rxnorm_mapping.csv
├── models/
│   ├── ner_model/
│   │   └── best_model.pt
│   └── embeddings/
│       ├── icd10.index
│       └── rxnorm.index
├── notebooks/
│   └── eda.ipynb
├── output/
│   ├── 1.json
│   ├── 2.json
│   ├── ...
│   └── 100.json
├── reports/
│   ├── eda_report.md
│   ├── error_analysis.md
│   └── submission_log.md
├── scripts/
│   ├── run_pipeline.py
│   ├── build_index.py
│   ├── validate_output.py
│   └── zip_submission.py
├── src/
│   ├── ner/
│   │   ├── model.py
│   │   ├── train.py
│   │   └── infer.py
│   ├── entity_linking/
│   │   ├── candidate_gen.py
│   │   └── rerank.py
│   ├── assertions/
│   │   └── classify.py
│   ├── relations/
│   │   └── infer_relation.py
│   └── pipeline.py
├── requirements.txt
└── README.md
```

Lưu ý:
- Hiện tại workspace đang ở giai đoạn khởi tạo. Các thư mục cấp cao đã có sẵn, một số file code sẽ được bổ sung theo tiến độ.

## 3. Ý nghĩa từng thư mục

| Thư mục | Ý nghĩa | Thành phần chính |
|---|---|---|
| `config` | Chứa toàn bộ tham số chạy, model path, ngưỡng score, top-k candidates; giúp thay đổi cấu hình mà không cần sửa code. | `project.yaml`, `ner.yaml`, `linking.yaml`, `assertion.yaml` |
| `data` | Chứa dữ liệu đầu vào, dữ liệu huấn luyện/đánh giá nội bộ và dữ liệu mapping phục vụ entity linking. | `input/`, `train/`, `dev/`, `icd10/`, `rxnorm/` |
| `models` | Lưu model NER đã huấn luyện và vector index cho ICD-10, RxNorm; tránh phụ thuộc máy cụ thể. | `ner_model/`, `embeddings/` |
| `src` | Chứa logic nghiệp vụ chính theo module; `pipeline.py` là điểm vào xử lý end-to-end. | `ner/`, `entity_linking/`, `assertions/`, `relations/`, `pipeline.py` |
| `scripts` | Chứa script thao tác vận hành: build index, infer 100 file, validate output, zip nộp bài. | `build_index.py`, `run_pipeline.py`, `validate_output.py`, `zip_submission.py` |
| `output` | Chứa kết quả JSON để nộp BTC, yêu cầu đúng tên từ 1.json đến 100.json. | `1.json` ... `100.json` |
| `reports` | Chứa tài liệu EDA, phân tích lỗi, lịch sử nộp bài để phục vụ giải trình và cải tiến mô hình. | `eda_report.md`, `error_analysis.md`, `submission_log.md` |

## 4. Quy ước output theo schema BTC

Mỗi object trong file JSON gồm các trường:
- text
- type
- assertions
- position
- candidates

Quy tắc quan trọng:
- candidates chỉ áp dụng cho CHẨN_ĐOÁN và THUỐC.
- assertions là danh sách, có thể rỗng.
- position là [start, end] theo ký tự, tính từ 0.

## 5. Quy trình chạy dự án

### Bước 1: Cài đặt môi trường
- Tạo môi trường Python 3.10+.
- Cài dependency từ requirements.txt.

### Bước 2: Chuẩn bị dữ liệu
- Đặt 100 file input vào data/input.
- Kiểm tra dữ liệu mapping ICD-10 và RxNorm trong data/icd10 và data/rxnorm.

### Bước 3: Build index
- Chạy script build_index.py để tạo icd10.index và rxnorm.index.

### Bước 4: Chạy pipeline
- Chạy run_pipeline.py để sinh output/1.json ... output/100.json.

### Bước 5: Validate và đóng gói
- Chạy validate_output.py để kiểm tra schema.
- Chạy zip_submission.py để tạo output.zip.

## 6. Checklist dựng lại

- [ ] Có requirements.txt
- [ ] Có README.md hướng dẫn đầy đủ
- [ ] Có model weights trong models
- [ ] Có mapping ICD-10 và RxNorm
- [ ] Chạy được infer end-to-end
- [ ] Tạo được output.zip đúng cấu trúc
- [ ] Không sử dụng API ngoài cho model nộp bài

## 7. Ranh giới và cam kết tuân thủ

- Giải pháp nộp bài sử dụng self-host model theo ràng buộc BTC.
- Không hardcode output theo input test.
- Ưu tiên tính tái lập: clone repo, cài đặt, chạy lại, cho kết quả hợp lệ.


Cập nhật lần cuối: 2026-07-05
Người phụ trách: Team Medical Extraction