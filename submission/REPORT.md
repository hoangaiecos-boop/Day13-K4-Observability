# Báo cáo Day 13 Observability

> Các dòng đánh dấu `[ĐIỀN]` cần bổ sung thủ công (thông tin nhóm, trace ID và ảnh chụp từ Langfuse/dashboard).

## 1. Thông tin nhóm

- Tên nhóm: Team CAPYBARA
- Repository URL: https://github.com/hoangaiecos-boop/Day13-K4-Observability
- Commit SHA cuối: [ĐIỀN — điền sau khi commit lần cuối]
- Thành viên và vai trò:
  - Nguyễn Tấn Hoàng (2A202601198, Leader) — Tracing & Prompt Version
  - Nguyễn Minh Hiếu (2A202601154) — Tracing & Prompt Version
  - Nguyễn Minh Đức (2A202601946) — Logging & PII
  - Trần Thanh Huyền (2A202601578) — Dashboard, SLO & Alert
  - Đỗ Tú Anh (2A202601272) — Incident, Report & Demo

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** (baseline trước khi làm: 30/100)
  - trước: `submission/evidence/01-validate-logs-baseline.txt`
  - sau: `submission/evidence/02-validate-logs-final.txt`
- Tổng số traces: **19** trên Langfuse JP (`submission/evidence/08-langfuse-traces.txt`),
  tất cả đều có `prompt_name` / `prompt_label` / `prompt_version` và `prompt_source=langfuse`
- Số PII leak còn lại: **0** (`Potential PII leaks detected: 0`)
- Link/đường dẫn dashboard: `scripts/dashboard.py` — chạy `streamlit run scripts/dashboard.py`, mở http://localhost:8501
  - Ảnh: `submission/evidence/14-dashboard-1-latency.png` … `19-dashboard-6-quality.png` (6 panel, cuộn tuần tự)

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/03-correlation-id-log.txt`
  - Middleware `app/middleware.py` sinh ID dạng `req-<8 hex>` (hoặc nhận lại từ header `x-request-id`),
    bind vào structlog contextvars và trả về qua header `x-request-id` + `x-response-time-ms`.
  - Ví dụ `req-50bd63f5` xuất hiện ở cả `request_received` và `response_sent` của cùng một request.
- Evidence PII redaction: `submission/evidence/04-pii-redacted.txt`
  - Processor `scrub_event` được đăng ký trong `app/logging_config.py` nên PII bị che TRƯỚC khi ghi file.
  - Input `student@vinuni.edu.vn`, `0987654321`, `4111 1111 1111 1111` → log chỉ còn
    `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`.
  - Bổ sung 2 pattern ngoài yêu cầu: `passport` và `address_vn` (`app/pii.py`).
- Nối log ↔ trace: mỗi trace mang tag `cid:<correlation_id>` (`app/agent.py`), lọc theo tag này
  trên Langfuse để mở đúng trace của một log line. Không đặt trong trace metadata vì public test
  `tests/test_agent_prompt_trace.py:52` khoá cứng metadata phải đúng 4 field `prompt_*`.
- Evidence trace waterfall: `submission/evidence/13-trace-waterfall.png` (trace `f5e1c300815ed0b058cec69b9dce159b`)
- Giải thích một span đáng chú ý: span retrieval (`app/mock_rag.py`) chiếm ~2.5s trong tổng 2.66s
  của các request challenge, trong khi span generation không đổi. Xem mục 6.

## 4. Prompt versioning

Bằng chứng đầy đủ: `submission/evidence/09-prompt-versioning.txt`

- Prompt name: `day13-chat` (host `https://jp.cloud.langfuse.com`, project `My Project` / `davidaiecos's Organization`)
- Version/label baseline: **v1** — labels `baseline`, `production`
- Version/label candidate: **v2** — label `candidate` — thêm giới hạn 3 câu và yêu cầu cite doc
- Trace ID của mỗi version (cùng input, session `prompt-compare`):

  | Label | Version | correlation_id | trace_id |
  |---|---|---|---|
  | `baseline` | 1 | `req-ab996fed` | `01b670aaa6a235c194bb428377db3064` |
  | `candidate` | 2 | `req-d275cf0a` | `dec9e3fea2b0f4680a6d9d449eb86640` |

- Bằng chứng đổi label và rollback (`scripts/promote_prompt.py`, session `prompt-rollback`):

  | Bước | Trạng thái label | correlation_id | trace_id | prompt_version ghi trong trace |
  |---|---|---|---|---|
  | promote `production` → v2 | v1=`[baseline]`, v2=`[candidate, production, latest]` | `req-12770db7` | `a0160354a534357e2758979159537b61` | 2 |
  | rollback `production` → v1 | v1=`[baseline, production]`, v2=`[candidate, latest]` | `req-72f6712a` | `ed226edda8d41c1315a936124c82fc6c` | 1 |

  Hai trace cùng label `production` nhưng khác version → chứng minh rollback có hiệu lực thật.

- Lỗi đã gặp khi làm (đáng ghi lại): bản đầu của `scripts/promote_prompt.py` gửi
  `PATCH {"newLabels": ["production"]}`. API Langfuse **thay thế toàn bộ** label của version
  đó chứ không thêm vào, nên lệnh promote đầu tiên đã vô tình xoá mất `candidate` khỏi v2 và
  kéo theo `baseline` khỏi v1 — chi tiết ở `submission/evidence/09-prompt-versioning.txt` mục 4.
  Sửa bằng cách đọc label hiện có rồi gửi trọn bộ label mong muốn, chỉ di chuyển `production`.

- Ảnh evidence:
  - danh sách 2 version: `submission/evidence/12-rollback-sau.png` (sidebar hiện cả #1 và #2 kèm label)
  - trace waterfall: `submission/evidence/13-trace-waterfall.png`
  - trước rollback (production ở v2): `submission/evidence/11-rollback-truoc.png`
  - sau rollback (production ở v1): `submission/evidence/12-rollback-sau.png`

Khi chưa cấu hình key, `app/prompt_management.py` dùng template local và trace metadata ghi
`prompt_source=local-fallback` thay vì giả vờ đã lấy được prompt managed. Trong bài này cả 19 trace
đều ghi `prompt_source=langfuse`, chứng minh app thực sự lấy prompt managed chứ không rơi vào fallback.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
  (`submission/evidence/05-validate-dashboard.txt`)
- Evidence dashboard:
  - giá trị 6 panel tính từ log: `submission/evidence/07-dashboard-panel-values.txt`
  - ảnh dashboard: [ĐIỀN — chụp http://localhost:8501, phải thấy tên panel, time range, đơn vị và threshold line]
- Công cụ: Streamlit đọc trực tiếp `data/logs.jsonl` (`scripts/dashboard.py`), đúng nguồn chuẩn theo
  `docs/DASHBOARD_SETUP.md`. Mỗi panel hiển thị SLO line đỏ đứt nét lấy từ `config/dashboard.yaml`.
- SLO đã chọn và lý do (`config/slo.yaml`):

  | SLI | Objective | Lý do |
  |---|---|---|
  | `latency_p95_ms` | 3000ms | Dùng P95 thay vì trung bình vì sự cố kiểu rag_slow chỉ đội đuôi phân phối: P50 đứng yên 155ms trong khi P95 vọt lên 2659ms |
  | `error_rate_pct` | 2% | Ngưỡng người dùng còn chấp nhận được khi có retry |
  | `daily_cost_usd` | 2.5 USD | Chặn cost spike do prompt phình to hoặc vòng lặp retry |
  | `quality_score_avg` | 0.75 | Bắt lỗi "trả lời tệ nhưng vẫn HTTP 200" — không alert nào khác phát hiện được |

- Alert rules và runbook: `config/alert_rules.yaml` + `docs/alerts.md`
  1. `ChatLatencyP95Breach` — P1 — p95 > 3000ms trong 5 phút
  2. `ChatErrorRateBreach` — P1 — error rate > 2% trong 5 phút
  3. `ChatQualityDrop` — P2 — mean(quality_score) < 0.75 trong 15 phút

  Cả ba đều symptom-based: đo cái người dùng cảm nhận (chậm / lỗi / trả lời tệ), không alert vào
  chỉ số nội bộ. Mỗi alert có 3 bước kiểm tra đầu tiên và mitigation tạm thời trong `docs/alerts.md`.

## 6. Điều tra challenge

Bằng chứng đầy đủ: `submission/evidence/06-challenge-investigation.txt`

- Challenge ID: `day13-k4-observability-v1` (cohort K4, incident `rag_slow`, threshold 2000ms)
- Triệu chứng từ metrics:
  - chỉ request bình thường (n=14): `p50=155ms  p95=661ms  p99=786ms`
  - gồm cả request challenge (n=19): `p50=155ms  p95=2657ms  p99=2659ms`
  - error rate 0.00% ở cả hai cửa sổ
  - P95 vượt ngưỡng challenge 2000ms nhưng P50 và error rate KHÔNG đổi → sự cố chỉ ảnh hưởng
    một nhánh request, không phải toàn hệ thống.
- Trace ID và correlation ID liên quan — 5/19 request vượt ngưỡng, **100% đều `feature=monitoring`**:

  | correlation_id | trace_id | session | latency |
  |---|---|---|---|
  | `req-2f96475e` | `6a78668cbc658b7e208f2baa918c783d` | `k4-challenge-s01` | 2656ms |
  | `req-909f8e05` | `f5e1c300815ed0b058cec69b9dce159b` | `k4-challenge-s02` | 2657ms |
  | `req-3c62c46a` | `85dff80bc3e26081c3929c347d18c92e` | `k4-challenge-s03` | 2655ms |
  | `req-4df7ebab` | `d26eb8f74e4d33e6eb95ce03519f9efa` | `k4-challenge-s04` | 2655ms |
  | `req-41513c3b` | `0f1b558c341feff17f57dc985f8226e5` | `k4-challenge-s05` | 2660ms |

  Đối chứng cùng cửa sổ: `req-72f6712a` (feature `qa`) < 1000ms.
  `tokens_in`/`tokens_out`/`cost_usd` của request chậm không cao hơn request nhanh, và cả hai nhóm
  đều dùng `prompt_version=1` → loại trừ nguyên nhân prompt phình to hoặc đổi model; chênh lệch
  nằm hoàn toàn ở `latency_ms`.
- Root cause: bước retrieval của RAG (`app/mock_rag.py:18`) chèn 2.5s blocking khi cờ
  `STATE["rag_slow"]` bật. Khuếch đại thêm bởi việc handler `chat` khai báo `async def` nhưng gọi
  `agent.run()` đồng bộ — `time.sleep()` chặn event loop nên request đồng thời phải xếp hàng:
  client đo 13.3s cho 5 request song song trong khi server log chỉ ~2.66s mỗi request.
- Fix action:
  1. Tắt cờ sự cố: `python scripts/inject_incident.py --disable` (P95 về ~155ms)
  2. Đặt timeout cho retrieval (vd 800ms) và trả fallback khi quá hạn
  3. Đẩy lời gọi blocking sang threadpool (`run_in_threadpool`) để một feature chậm không chặn feature khác
- Preventive measure:
  1. Bật `ChatLatencyP95Breach`, đồng thời thêm alert P95 theo từng `feature` — P95 toàn cục lần này
     chỉ đạt 2659ms, chưa chạm ngưỡng 3000ms nên alert toàn cục sẽ bỏ sót
  2. Thêm span riêng cho retrieval kèm attribute `retrieval_ms` và `doc_count` để khoanh vùng ngay từ trace
  3. Đưa load test có concurrency vào CI, fail build khi P95 vượt SLO

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.
Cột "Điều đã học" và "Commit/PR" do từng người tự điền — mỗi người phải giải thích được
phần của mình khi được hỏi (rubric B1/A3), nên không thể viết thay.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Minh Đức | Logging & PII — `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py` | [ĐIỀN] | [ĐIỀN] |
| Nguyễn Tấn Hoàng, Nguyễn Minh Hiếu | Tracing & Prompt Version — prompt v1/v2, label, rollback | [ĐIỀN] | [ĐIỀN] |
| Trần Thanh Huyền | Dashboard, SLO & Alert — `scripts/dashboard.py`, `config/alert_rules.yaml`, `docs/alerts.md` | [ĐIỀN] | [ĐIỀN] |
| Đỗ Tú Anh | Incident, Report & Demo — điều tra challenge, `submission/` | [ĐIỀN] | [ĐIỀN] |
