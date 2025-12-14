## Kế hoạch tổng thể (đã cập nhật theo bối cảnh: dùng Gemini/OpenAI; RAGFlow đã chạy; bổ sung Giai đoạn 0 môi trường Python)

### Mục tiêu tổng quát

Xây dựng hệ thống **deep research pháp lý–chính sách** theo nguyên tắc: **RAGFlow cung cấp bằng chứng (evidence), AutoGen điều phối lập luận–phản biện–tổng hợp**, bắt buộc **trích dẫn nguồn**, kiểm soát **hiệu lực** và **phân cấp văn bản**.

---

## Giai đoạn 0 – Chuẩn hóa môi trường Python và cách cài đặt (bắt buộc, ưu tiên cao)

**Mục tiêu:** môi trường tái lập 100%, không “vỡ dependency”, chạy giống nhau giữa dev/CI.

**Việc thực hiện**

* Chốt chuẩn **Python 3.11.x** cho toàn repo.
* Chốt một cơ chế quản lý phụ thuộc: **Poetry** *hoặc* **pip-tools** (khuyến nghị chọn 1 và áp dụng thống nhất).
* Tạo artifact môi trường trong repo:

  * `.python-version`
  * `pyproject.toml + poetry.lock` *hoặc* `requirements.in + requirements.lock.txt`
  * `scripts/setup_venv.ps1|sh`, `Makefile` (`make setup/test/run`)
  * `.env.example` (OPENAI/GEMINI keys; RAGFlow base url; timeout)
* Smoke test tối thiểu: import libs + gọi thử endpoint RAGFlow (health/retrieval ping).

**Đầu ra nghiệm thu**

* Dev mới clone repo → chạy 1–2 lệnh → chạy được `tests/smoke_test.py` thành công.

---

## Giai đoạn 1 – Khóa “contract truy xuất” từ RAGFlow (evidence pack) (1 tuần)

**Mục tiêu:** RAGFlow đã chạy; việc cần làm là chuẩn hóa **đầu ra bằng chứng** để AutoGen dùng được cho deep research.

**Việc thực hiện**

* Viết `ragflow_client.py` + `ragflow_retriever_tool.py` (HTTP client + tool).
* Chuẩn hóa schema:

  * `EvidenceItem`: quote + metadata (văn bản, cơ quan, hiệu lực, điều/khoản/điểm, trang/anchor)
  * `EvidencePack`: gói bằng chứng cho từng sub-question
* Mapping metadata của RAGFlow → schema chuẩn (làm rõ trường nào có/không có).
* Bổ sung `effective_date_checker.py` (đánh dấu hết hiệu lực/không rõ hiệu lực).

**Đầu ra nghiệm thu**

* Tool `retrieve_legal_documents()` trả về **>= 5 evidence items** có đủ trường tối thiểu để trích dẫn.

---

## Giai đoạn 2 – Xây AutoGen core (Planner – Retriever – Analyzer) (1 tuần)

**Mục tiêu:** tạo báo cáo nháp có cấu trúc, **chỉ dựa trên evidence**.

**Thiết kế agent**

* **Planner Agent:** phân rã theo 4 mục: *Điều kiện – Hồ sơ – Thẩm quyền – Thời gian xử lý*, sinh sub-questions và filter.
* **Retriever Agent:** chỉ gọi tool RAGFlow để lấy evidence pack.
* **Analyzer Agent:** viết nháp, mỗi ý chính bắt buộc gắn `evidence_id`.

**Đầu ra nghiệm thu**

* Báo cáo nháp đúng 4 mục; **mỗi bullet có trích dẫn**.

---

## Giai đoạn 3 – Bổ sung Critic loop (để “deep” thật sự) (1–2 tuần)

**Mục tiêu:** tự động phản biện và bắt quay vòng truy xuất khi thiếu căn cứ/sai hiệu lực/sai phân cấp.

**Critic Agent kiểm tra bắt buộc**

* Citation coverage (không có nguồn → reject)
* Kiểm tra hiệu lực theo `as_of_date`
* Kiểm tra phân cấp văn bản (Luật/NQ QH > NĐ > TT > QĐ > CV)
* Mâu thuẫn nguồn (phải nêu và xử lý)
* Suy diễn vượt chứng cứ (reject)

**Cơ chế**

* Fail → tạo “missing_queries/new_filters” → Planner refine → Retriever chạy lại → Analyzer viết lại.

**Đầu ra nghiệm thu**

* Với bộ test, hệ thống tự lặp 1–2 vòng để đạt “pass”.

---

## Giai đoạn 4 – Synthesizer & chuẩn hóa đầu ra hành chính (1 tuần)

**Mục tiêu:** báo cáo dùng được ngay trong hồ sơ, thống nhất trích dẫn.

**Việc thực hiện**

* Synthesizer Agent chuẩn hóa:

  * Văn phong hành chính, cấu trúc rõ
  * Mẫu trích dẫn chuẩn (VB–Điều/Khoản/Điểm–Cơ quan–Ngày ban hành–Hiệu lực)
  * “Danh mục văn bản sử dụng” cuối báo cáo
* `citation_formatter.py` thống nhất format.

**Đầu ra nghiệm thu**

* Báo cáo có thể dùng trực tiếp trong Word; trích dẫn nhất quán; không có đoạn “nhận định chung” thiếu nguồn.

---

## Giai đoạn 5 – QA/Benchmark và tiêu chí nghiệm thu (1 tuần)

**Mục tiêu:** đo được chất lượng, tránh “nông” như các deep-research framework mặc định.

**Việc thực hiện**

* Bộ 20 câu hỏi test (pháp lý–đất đai–đầu tư–thủ tục).
* Tự động chấm:

  * Citation coverage ≥ 95%
  * Không dùng văn bản hết hiệu lực làm căn cứ chính
  * Có xử lý mâu thuẫn nguồn
  * Bám đủ 4 mục đầu ra
* Xuất “audit log” (plan, evidence, critic findings, final).

**Đầu ra nghiệm thu**

* Báo cáo QA batch; dashboard đơn giản (CSV/JSON) cho đội quản trị.

---

## Phân công khuyến nghị (để làm nhanh)

* **Dev (Python):** Giai đoạn 0–2 (env + tool + orchestration core)
* **Chuyên gia pháp lý/chính sách:** định nghĩa rule Critic + mẫu trích dẫn
* **QA:** bộ câu hỏi test + tiêu chí pass/fail

---

Nếu anh muốn, tôi sẽ viết ngay **mẫu “Giai đoạn 0” đầy đủ** (Makefile + scripts Windows/Linux + lựa chọn Poetry hoặc pip-tools + bộ requirements tối thiểu cho OpenAI/Gemini + requests + pydantic + pytest), để đội triển khai copy vào repo dùng ngay.
