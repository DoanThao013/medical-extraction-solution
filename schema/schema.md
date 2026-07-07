# Đặc Tả Output

## Mục tiêu

Output của mỗi văn bản đầu vào là một JSON array.

Mỗi phần tử trong mảng biểu diễn đúng một khái niệm y tế được phát hiện trong văn bản.

Mỗi khái niệm bao gồm 5 trường:

- text
- position
- type
- assertions
- candidates

Output :

```json
[
  {
    "text": "...",
    "position": [10, 20],
    "type": "TRIỆU_CHỨNG",  
    "assertions": [],
    "candidates": []
  }
]
```

type phải nhận đúng một trong năm giá trị sau: CHẨN_ĐOÁN, TRIỆU_CHỨNG, TÊN_XÉT_NGHIỆM, KẾT_QUẢ_XÉT_NGHIỆM, THUỐC

## Cấu trúc top-level

- Kiểu dữ liệu: `array`
- Mỗi phần tử trong mảng là một entity object.
- Mỗi entity trong văn bản phải được biểu diễn bằng đúng một object.
- Không gom nhiều entity vào cùng một object.

Ví dụ đúng:

```json
[
  {
    "text": "ho",
    "position": [31, 33],
    "type": "TRIỆU_CHỨNG",
    "assertions": [],
    "candidates": []
  },
  {
    "text": "sốt",
    "position": [36, 39],
    "type": "TRIỆU_CHỨNG",
    "assertions": [],
    "candidates": []
  }
]
```

Ví dụ sai:

```json
[
  {
    "text": "ho sốt",
    "position": [31, 39],
    "type": "TRIỆU_CHỨNG",
    "assertions": [],
    "candidates": []
  }
]
```

## Entity Object

Mỗi entity object có đúng 5 field:

```json
{
  "text": "...",
  "position": [start, end],
  "type": "TRIỆU_CHỨNG",
  "assertions": [],
  "candidates": []
}
```

### `text`

- Mục đích: Chuỗi thực thể được trích xuất từ văn bản.
- Kiểu dữ liệu: `string`
- Bắt buộc: Có
- Ràng buộc:
  - Không được rỗng.
  - Phải là đúng surface text của entity trong văn bản nguồn.
- Ví dụ:
  - `"ho đờm xanh"`
  - `"Chlorpheniramine"`
  - `"WBC"`
  - `"14.3"`

### `position`

- Mục đích: Vị trí xuất hiện của entity trong văn bản nguồn.
- Kiểu dữ liệu: `array` gồm đúng 2 phần tử số nguyên.
- Bắt buộc: Có
- Ràng buộc:
  - Dạng: `[start, end]`
  - Là character offset.
  - Là 0-based offset.
  - `start` và `end` phải là số nguyên không âm.
  - `start <= end`
  - BTC mô tả theo ký tự từ `0 -> n-1`.
- Ví dụ:

```json
"position": [31, 42]
```

### `type`

- Mục đích: Loại entity theo taxonomy của BTC.
- Kiểu dữ liệu: `string`
- Bắt buộc: Có
- Allowed values:
  - `TRIỆU_CHỨNG`
  - `TÊN_XÉT_NGHIỆM`
  - `KẾT_QUẢ_XÉT_NGHIỆM`
  - `CHẨN_ĐOÁN`
  - `THUỐC`
- Ví dụ:
  - `"TRIỆU_CHỨNG"`
  - `"THUỐC"`

### `assertions`

- Mục đích: Danh sách assertion áp dụng cho entity.
- Kiểu dữ liệu: `array` của `string`
- Bắt buộc: Có
- Allowed values:
  - `isNegated`
  - `isHistorical`
  - `isFamily`
- Ràng buộc:
  - Chỉ áp dụng cho 3 loại:
    - `TRIỆU_CHỨNG`
    - `CHẨN_ĐOÁN`
    - `THUỐC`
  - Với `TÊN_XÉT_NGHIỆM` và `KẾT_QUẢ_XÉT_NGHIỆM`, `assertions` phải là mảng rỗng.
  - Không dùng giá trị tự do như `nghi ngờ`, `bình thường`, `được kê`, `được chỉ định`.
- Ví dụ đúng:

```json
"assertions": ["isHistorical"]
```

Ví dụ đúng khác:

```json
"assertions": []
```

Ví dụ sai:

```json
"assertions": ["bình thường"]
```

### `candidates`

- Mục đích: Danh sách candidate mapping để chuẩn hóa cho entity.
- Kiểu dữ liệu: `array` của `string`
- Bắt buộc: Có
- Ràng buộc:
  - Chỉ áp dụng cho:
    - `CHẨN_ĐOÁN`: candidate là mã ICD
    - `THUỐC`: candidate là mã RxNorm
  - Với các type khác, `candidates` phải là mảng rỗng.
  - Không chứa object dạng `{ "code": ..., "description": ... }`
  - Chỉ chứa string code.
- Ví dụ đúng cho chẩn đoán:

```json
"candidates": ["K21.0", "K21.9"]
```

- Ví dụ đúng cho thuốc:

```json
"candidates": ["360047"]
```

- Ví dụ đúng cho triệu chứng:

```json
"candidates": []
```

## Giải thích theo từng loại entity

### `TRIỆU_CHỨNG`

- Mục đích: Biểu diễn một triệu chứng hoặc dấu hiệu lâm sàng.
- `assertions`: được phép dùng.
- `candidates`: phải rỗng.
- Ví dụ:

```json
{
  "text": "ho đờm xanh",
  "position": [31, 42],
  "type": "TRIỆU_CHỨNG",
  "assertions": [],
  "candidates": []
}
```

### `CHẨN_ĐOÁN`

- Mục đích: Biểu diễn một chẩn đoán.
- `assertions`: được phép dùng.
- `candidates`: là danh sách mã ICD dạng string.
- Ví dụ:

```json
{
  "text": "trào ngược dạ dày",
  "position": [80, 96],
  "type": "CHẨN_ĐOÁN",
  "assertions": [],
  "candidates": ["K21.0", "K21.9"]
}
```

### `THUỐC`

- Mục đích: Biểu diễn một tên thuốc.
- `assertions`: được phép dùng.
- `candidates`: là danh sách mã RxNorm dạng string.
- Ví dụ:

```json
{
  "text": "Chlorpheniramine",
  "position": [120, 136],
  "type": "THUỐC",
  "assertions": ["isHistorical"],
  "candidates": ["360047"]
}
```

### `TÊN_XÉT_NGHIỆM`

- Mục đích: Biểu diễn tên xét nghiệm hoặc tên chỉ số xét nghiệm.
- `assertions`: phải rỗng.
- `candidates`: phải rỗng.
- Ví dụ:

```json
{
  "text": "WBC",
  "position": [150, 152],
  "type": "TÊN_XÉT_NGHIỆM",
  "assertions": [],
  "candidates": []
}
```

### `KẾT_QUẢ_XÉT_NGHIỆM`

- Mục đích: Biểu diễn giá trị hoặc kết quả của xét nghiệm.
- `assertions`: phải rỗng.
- `candidates`: phải rỗng.
- Ví dụ:

```json
{
  "text": "14.3",
  "position": [156, 159],
  "type": "KẾT_QUẢ_XÉT_NGHIỆM",
  "assertions": [],
  "candidates": []
}
```

## VD Output hoàn chỉnh
```json
[
  {
    "text":"ho đờm xanh",
    "position":[31,42],
    "type":"TRIỆU_CHỨNG",
    "assertions":[],
    "candidates":[]
  },
  {
    "text":"trào ngược dạ dày",
    "position":[80,95],
    "type":"CHẨN_ĐOÁN",
    "assertions":[],
    "candidates":[
      "K21.0",
      "K21.9"
    ]
  }
]
```

## Business Rules

1. Output top-level là một mảng entity, không phải object phân nhóm.
2. Một entity tương ứng đúng một object.
3. `text` phải là chuỗi gốc được nhìn thấy trong văn bản.
4. `position` là character offset 0-based, theo dạng `[start, end]`.
5. `type` chỉ được lấy từ 5 giá trị enum do BTC quy định.
6. `assertions` chỉ được lấy từ 3 giá trị enum do BTC quy định.
7. `assertions` chỉ áp dụng cho `TRIỆU_CHỨNG`, `CHẨN_ĐOÁN`, `THUỐC`.
8. Với `TÊN_XÉT_NGHIỆM` và `KẾT_QUẢ_XÉT_NGHIỆM`, `assertions` phải là `[]`.
9. `candidates` chỉ chứa string code, không chứa object.
10. `candidates` chỉ áp dụng cho `CHẨN_ĐOÁN` và `THUỐC`.
11. Với `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, `candidates` phải là `[]`.
12. `CHẨN_ĐOÁN` dùng candidate ICD.
13. `THUỐC` dùng candidate RxNorm.
14. `TÊN_XÉT_NGHIỆM` và `KẾT_QUẢ_XÉT_NGHIỆM` là hai entity khác nhau.
