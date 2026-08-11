# Trần Thanh Huyền — Dashboard, SLO & Alert

## Việc của bạn

Dashboard 6 panel bằng Streamlit (`scripts/dashboard.py`), 3 alert rule
(`config/alert_rules.yaml`, `docs/alerts.md`).

## Trước khi commit — đọc và hiểu code

- `scripts/dashboard.py` — mỗi panel lấy field nào từ `data/logs.jsonl`? Đối chiếu với
  `config/dashboard.yaml` (contract có sẵn, không phải file bạn tạo) để biết panel nào map
  vào field nào.
- `config/alert_rules.yaml` + `docs/alerts.md` — vì sao cả 3 alert đều "symptom-based"
  (đo latency/error/quality) chứ không alert vào chỉ số nội bộ? Đọc phần "Nguyên tắc chung"
  cuối `docs/alerts.md`.
- Alert 3 (`ChatQualityDrop`) là loại lỗi gì mà 2 alert kia không bắt được? (gợi ý: HTTP vẫn
  200 nhưng câu trả lời tệ).

## Bước làm

1. Copy `scripts/dashboard.py` vào `Day13-K4-Observability/scripts/dashboard.py`.
2. Copy `requirements-dashboard.txt` vào thư mục gốc `Day13-K4-Observability/`.
3. Copy `config/alert_rules.yaml` vào `Day13-K4-Observability/config/` (ghi đè).
4. Copy `docs/alerts.md` vào `Day13-K4-Observability/docs/` (ghi đè).
5. Copy 8 file trong `submission/evidence/` vào `Day13-K4-Observability/submission/evidence/`.
6. Chạy:

```bash
git config user.name "Trần Thanh Huyền"
git config user.email "<email-truong-cua-ban>@vinuni.edu.vn"
git pull
git add scripts/dashboard.py requirements-dashboard.txt config/alert_rules.yaml docs/alerts.md submission/evidence/05-validate-dashboard.txt submission/evidence/07-dashboard-panel-values.txt submission/evidence/14-dashboard-1-latency.png submission/evidence/15-dashboard-2-traffic.png submission/evidence/16-dashboard-3-errors.png submission/evidence/17-dashboard-4-cost.png submission/evidence/18-dashboard-5-tokens.png submission/evidence/19-dashboard-6-quality.png
git commit -m "feat(dashboard): dashboard 6 panel Streamlit và alert rules"
git push
```

## Tự kiểm tra

```bash
pip install -r requirements-dashboard.txt
python scripts/validate_dashboard.py       # phải ra HỢP LỆ: 6/6 panel
streamlit run scripts/dashboard.py         # mở http://localhost:8501, xem lại 6 panel
```

## Khi bị hỏi

- SLO của panel latency là gì, tại sao chọn P95 làm ngưỡng thay vì trung bình?
- Alert `ChatLatencyP95Breach` có threshold và thời gian duy trì bao nhiêu?
- Panel nào đang cảnh báo trong ảnh evidence (`14`–`19`) và vì sao?
