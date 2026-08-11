# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: ChatLatencyP95Breach
- Severity: P1
- SLI/SLO liên quan: `latency_p95_ms` — objective 3000ms, target 99.5% (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: p95 của `response_sent.latency_ms` > 3000ms, duy trì 5 phút liên tục
- Ảnh hưởng tới người dùng: người dùng chờ quá lâu, client timeout, tỉ lệ bỏ ngang hội thoại tăng
- Ba bước kiểm tra đầu tiên:
  1. Panel Latency: xác nhận p95 tăng thật hay chỉ một outlier; đối chiếu panel Traffic xem có phải do tải tăng
  2. Mở Langfuse, lọc trace theo `latency > 3000ms`, xem waterfall để tìm span chiếm nhiều thời gian nhất (retrieval hay generation)
  3. Lấy `correlation_id` của trace chậm, grep trong `data/logs.jsonl` để xác nhận `feature`, `model` và `tokens_in` của request đó
- Mitigation tạm thời: giảm số document retrieve, hoặc rollback prompt về label `production` nếu version mới làm tăng context
- Owner: vai trò Dashboard, SLO & Alert

## Alert 2

- Tên: ChatErrorRateBreach
- Severity: P1
- SLI/SLO liên quan: `error_rate_pct` — objective 2%, target 99.0% (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: `count(request_failed) / count(request_received) * 100` > 2%, duy trì 5 phút
- Ảnh hưởng tới người dùng: request trả 500, người dùng không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Panel Errors: xem breakdown theo `error_type` để biết lỗi tập trung ở loại nào
  2. Mở trace của request lỗi trong Langfuse, xác định span nào raise exception
  3. Grep `event=="request_failed"` trong `data/logs.jsonl`, đọc `payload.detail` và `correlation_id` để lấy bằng chứng cụ thể
- Mitigation tạm thời: tắt incident/feature flag đang gây lỗi (`python scripts/inject_incident.py --scenario <name> --disable`), hoặc trả fallback response cho feature bị ảnh hưởng
- Owner: vai trò Incident, Report & Demo

## Alert 3

- Tên: ChatQualityDrop
- Severity: P2
- SLI/SLO liên quan: `quality_score_avg` — objective 0.75, target 95.0% (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: trung bình `response_sent.quality_score` < 0.75, duy trì 15 phút
- Ảnh hưởng tới người dùng: câu trả lời rỗng, lạc đề hoặc bị redact quá tay — hệ thống vẫn 200 nên không alert nào khác bắt được
- Ba bước kiểm tra đầu tiên:
  1. Panel Quality: xác nhận mức giảm; đối chiếu thời điểm giảm với lần đổi `prompt_label` gần nhất
  2. Trong Langfuse, so sánh trace của `prompt_version` cũ và mới trên cùng input để loại trừ nguyên nhân prompt
  3. Kiểm tra `doc_count` trong metadata của generation: `doc_count == 0` nghĩa là retrieval trả rỗng, không phải lỗi prompt
- Mitigation tạm thời: rollback `prompt_label=production` về version trước; nếu do retrieval thì nới điều kiện lọc document
- Owner: vai trò Tracing & Prompt Version

## Nguyên tắc chung

- Cả ba alert đều symptom-based: đo cái người dùng cảm nhận (chậm, lỗi, câu trả lời tệ), không alert vào chỉ số nội bộ như CPU hay số lần gọi hàm.
- Mọi điều tra phải đi theo luồng Metrics → Traces → Logs và dẫn lại `correlation_id` hoặc trace ID cụ thể.
