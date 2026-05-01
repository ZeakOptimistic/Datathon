# Project Onboarding Report

## 1. Mục tiêu của repo này là gì?

Repo này là workspace để xử lý toàn bộ **Datathon 2026 - Round 1**. Bài thi có 3 phần:

1. **Phần 1 - MCQ**
   - Trả lời 10 câu trắc nghiệm dựa trên dữ liệu CSV được cung cấp.

2. **Phần 2 - EDA / Data Storytelling**
   - Tạo chart, tìm insight, viết narrative đủ rõ để người chấm theo dõi được logic phân tích.

3. **Phần 3 - Forecasting**
   - Dự báo `Revenue` và `COGS` cho các ngày trong `sample_submission.csv`.

Mục tiêu của repo hiện tại không chỉ là “có code”, mà là:

- Có **script chạy lại được**
- Có **output đã sinh sẵn**
- Có **một phương án submit Part 3 dùng được ngay**
- Có **report EDA đọc được ngay**

---

## 2. Trạng thái hiện tại của project

### Phần 1 - MCQ

Đã solve xong và có file kết quả:

- `outputs/mcq_answers.md`

Đáp án hiện tại:

- `Q1 C`
- `Q2 D`
- `Q3 B`
- `Q4 C`
- `Q5 C`
- `Q6 A`
- `Q7 C`
- `Q8 A`
- `Q9 A`
- `Q10 C`

### Phần 2 - EDA

Đã có:

- bảng tổng hợp trung gian trong `outputs/eda/`
- chart PNG trong `outputs/eda_report/`
- report markdown trong `outputs/eda_report/eda_report.md`

Đây là trạng thái “đủ để follow, chỉnh sửa và đưa vào deck / notebook”.

### Phần 3 - Forecasting

Đã có:

- baseline model
- benchmark giữa baseline, lag model, và blend model
- benchmark riêng giữa baseline và improved model
- improved seasonal + weekday + `COGS/Revenue` ratio model
- file submit tốt nhất hiện tại

File submit nên ưu tiên dùng:

- `outputs/submission_best.csv`
- `outputs/submission_improved.csv`
- `outputs/submission_public_912428.csv` là backup của bản đã đạt public score `912428.76513`

File fallback đơn giản hơn:

- `outputs/submission_baseline.csv`

Kết luận hiện tại:

- bản public score `912428.76513` đã được giữ lại ở `outputs/submission_public_912428.csv`
- `submission_best.csv` hiện đã được revert về đúng bản public score `912428.76513`

---

## 3. Nếu mới vào repo, nên đọc theo thứ tự nào?

Để không bị overwhelmed, đọc theo đúng thứ tự này:

1. `README.md`
   - File entrypoint cho GitHub: mục tiêu repo, layout, command chính và file nộp Kaggle.

2. `PROJECT_ONBOARDING_REPORT.md`
   - File này. Mục tiêu là hiểu big picture trước.

3. `datathon-2026-round1-de-thi-vong-1.md`
   - Hiểu đề bài gốc, rubric, và yêu cầu từng phần.

4. `ROUND1_CODE_GUIDE.md`
   - Hiểu cách chạy script và output nào được sinh ra từ đâu.

5. `outputs/mcq_answers.md`
   - Nếu chỉ cần biết trạng thái Phần 1.

6. `outputs/eda_report/eda_report.md`
   - Nếu chỉ cần follow Phần 2 nhanh.

7. `outputs/forecast_benchmark.md`
   - Nếu chỉ cần biết Part 3 hiện model nào đang được chọn.

8. `scripts/`
   - Chỉ đọc khi muốn debug, rerun, hoặc cải thiện model/report.

Nói ngắn gọn:

- Muốn hiểu project: đọc `report -> đề -> guide`
- Muốn nộp nhanh: đọc `mcq_answers -> eda_report -> submission_best.csv`
- Muốn improve: đọc `scripts/`

---

## 4. File nào là quan trọng nhất?

### Nhóm “đọc để hiểu nhanh”

- `README.md`
- `PROJECT_ONBOARDING_REPORT.md`
- `datathon-2026-round1-de-thi-vong-1.md`
- `ROUND1_CODE_GUIDE.md`
- `docs/DATA.md`
- `docs/SUBMISSION_NOTES.md`

### Nhóm “deliverable hiện tại”

- `outputs/mcq_answers.md`
- `outputs/eda_report/eda_report.md`
- `outputs/submission_best.csv`
- `outputs/forecast_benchmark.md`

### Nhóm “code gốc”

- `scripts/solve_mcq.py`
- `scripts/build_eda_report.py`
- `scripts/forecast_baseline.py`
- `scripts/forecast_benchmark.py`
- `scripts/forecast_blend.py`

---

## 5. File nào có thể bỏ qua lúc đầu?

Người mới vào repo **không cần đọc ngay** những file này:

- `Đề thi Vòng 1.pdf`
  - Vì đã có bản markdown dễ đọc hơn.

- `page1.png`
  - Chỉ là file phụ sinh ra trong quá trình đọc PDF.

- `outputs/eda_report_debug/`
  - Đây là output debug, không phải deliverable chính.

- `scripts/make_eda_tables.py`
  - Hữu ích, nhưng chưa cần đọc nếu chỉ muốn hiểu toàn cục.

- toàn bộ `dataset/*.csv`
  - Dữ liệu rất lớn. Chỉ nên mở khi cần verify logic hoặc làm feature engineering thêm.

- `scripts/__pycache__/`
  - Bỏ qua hoàn toàn.

---

## 6. Map thư mục ngắn gọn

### `dataset/`

Chứa dữ liệu gốc của bài thi:

- master tables
- transaction tables
- analytical tables
- operational tables

### `scripts/`

Chứa toàn bộ code chính:

- `solve_mcq.py`
  - Tính 10 câu trắc nghiệm từ CSV thật

- `build_eda_report.py`
  - Sinh chart + report markdown cho Part 2

- `forecast_baseline.py`
  - Baseline forecasting đơn giản, dễ giải thích

- `forecast_benchmark.py`
  - So sánh baseline, lag model, blend model

- `forecast_blend.py`
  - Sinh candidate blend cũ để so sánh

- `forecast_improved.py`
  - Sinh file submit tốt nhất hiện tại bằng seasonal + weekday + ratio model

### `outputs/`

Chứa toàn bộ kết quả đã sinh:

- `mcq_answers.md`
- `eda/`
- `eda_report/`
- `forecast_benchmark.md`
- `forecast_improved_benchmark.md`
- `submission_baseline.csv`
- `submission_blend.csv`
- `submission_improved.csv`
- `submission_public_912428.csv`
- `submission_best.csv`

---

## 7. Hiện tại từng phần đang được solve như thế nào?

### Phần 1

Logic:

- đọc trực tiếp CSV
- tính metric theo yêu cầu đề
- map giá trị sang đáp án A/B/C/D

Mục tiêu của phần này là **tính reproducible**, không trả lời thủ công.

### Phần 2

Logic:

- tổng hợp một số góc nhìn lớn:
  - seasonality doanh thu
  - category revenue vs margin
  - returns by reason / size
  - region + acquisition
  - traffic + inventory imbalance

Output:

- chart PNG để đưa vào deck
- markdown report để người mới đọc được câu chuyện

### Phần 3

Hiện có 4 nhánh:

1. `baseline`
   - seasonal-growth
   - đơn giản, dễ giải thích, chạy nhanh

2. `lag model`
   - thêm lag / rolling / calendar / seasonal features
   - dùng để benchmark

3. `blend`
   - blend giữa baseline và lag model
   - candidate cũ, vẫn giữ để so sánh

4. `improved_seasonal_dow_ratio`
   - thêm hiệu chỉnh weekday lên seasonal pattern
   - forecast annual level gần hơn với regime 2021-2022
   - dự báo `COGS` qua seasonal `COGS/Revenue` ratio
   - đây là file submit nên dùng hiện tại

---

## 8. Tại sao Part 3 lại chọn improved seasonal-dow-ratio?

Vì benchmark hiện tại cho thấy:

- baseline cũ under-forecast annual level trong `2021` và `2022`
- weekday adjustment cải thiện pattern ngày trong tuần
- public score `912428.76513` cho thấy hướng improved tốt hơn bản trước

Kết luận thực dụng:

- nếu cần file nộp ngay: dùng `outputs/submission_best.csv`
- `outputs/submission_public_912428.csv` là backup cùng nội dung với bản đang nộp
- nếu cần lời giải đơn giản, dễ explain hơn: dùng `outputs/submission_baseline.csv`

---

## 9. Có caveat nào quan trọng không?

Có 2 caveat nên biết:

### Caveat 1 - Câu Q7 trong MCQ

Đề mô tả theo kiểu dùng `sales_train.csv`, nhưng file `sales.csv` không có cột `region`.

Vì vậy lời giải MCQ cho Q7 đang dùng:

- `orders.zip`
- join `geography.region`
- revenue từ transaction tables

Điểm tốt là:

- tính theo `order_items`
- hoặc tính theo `payments`

đều cho cùng top region, nên đáp án vẫn ổn định.

### Caveat 2 - Report EDA là bản nền tốt, chưa phải deck cuối cùng

`outputs/eda_report/eda_report.md` đủ để người khác follow logic, nhưng vẫn nên chỉnh wording / bố cục nếu dùng để nộp chính thức hoặc thuyết trình.

---

## 10. Muốn rerun toàn bộ project thì làm gì?

Nếu chỉ cần sinh lại toàn bộ output chính:

```powershell
uv run --with pandas python scripts/solve_mcq.py
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
uv run --with pandas --with numpy python scripts/forecast_improved.py
```

Nếu muốn xem benchmark Part 3:

```powershell
uv run --with pandas --with scikit-learn python scripts/forecast_benchmark.py
```

---

## 11. Recommended path cho từng kiểu người đọc

### Nếu chỉ muốn nộp bài nhanh

Xem:

- `outputs/mcq_answers.md`
- `outputs/eda_report/eda_report.md`
- `outputs/submission_best.csv`

### Nếu muốn review chất lượng bài

Xem:

- `outputs/forecast_benchmark.md`
- `outputs/forecast_improved_benchmark.md`
- `outputs/eda_report/`
- `ROUND1_CODE_GUIDE.md`

### Nếu muốn cải thiện thêm

Bắt đầu từ:

- `scripts/forecast_blend.py`
- `scripts/forecast_improved.py`
- `scripts/forecast_benchmark.py`
- `scripts/build_eda_report.py`

---

## 12. Tóm tắt 1 đoạn

Repo này đã ở trạng thái **có thể follow và có thể dùng**:

- Phần 1 đã có đáp án
- Phần 2 đã có report + chart
- Phần 3 đã có file submit tốt nhất hiện tại

Nếu là người mới mở repo, đừng bắt đầu từ raw data. Hãy bắt đầu từ:

1. `README.md`
2. file report này
3. file đề markdown
4. output đã sinh
5. rồi mới quay lại scripts nếu cần cải thiện

Đó là cách nhanh nhất để hiểu toàn bộ project mà không bị ngợp.
