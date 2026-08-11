# Đỗ Tú Anh — Incident, Report & Demo

## Việc của bạn
Điều tra challenge (`submission/evidence/06-challenge-investigation.txt`) và tổng hợp
`submission/REPORT.md`.

## Nên commit SAU CÙNG
Ba bạn còn lại nên commit trước, vì `REPORT.md` dẫn tới file evidence và trace ID của cả
nhóm. Không bắt buộc về mặt kỹ thuật (không đụng file nhau) nhưng hợp lý hơn khi trình bày.

## Trước khi commit — đọc và hiểu
- `submission/evidence/06-challenge-investigation.txt` — đọc từ mục 1 đến 7: triệu chứng
  metrics nào phát hiện ra sự cố? Trace nào khoanh vùng? Log nào chứng minh root cause?
- Mục 4 của file đó có một phát hiện phụ đáng chú ý: độ trễ client đo được gấp ~5 lần độ trễ
  server ghi lại. Hiểu vì sao (`async def` + `time.sleep()` chặn event loop) vì đây là câu
  hỏi hay bị hỏi khi demo.
- `submission/REPORT.md` mục 6 tóm tắt lại cùng nội dung, ngắn hơn — dùng cái này khi trình
  bày miệng.

## Bước làm

1. Copy `submission/REPORT.md` vào `Day13-K4-Observability/submission/REPORT.md` (ghi đè).
2. Copy `submission/evidence/06-challenge-investigation.txt` vào
   `Day13-K4-Observability/submission/evidence/`.
3. **Điền nốt các mục còn `[ĐIỀN]` trong REPORT.md** trước khi commit:
   - Cột "Commit/PR" và "Điều đã học" ở mục 7, cho từng thành viên (mỗi người tự viết phần
     của mình rồi bạn tổng hợp — đừng tự viết thay).
   - "Commit SHA cuối" ở mục 1 — điền sau khi CẢ 4 commit đã lên xong, chạy
     `git log --oneline -1` lấy SHA mới nhất rồi cập nhật lại, commit thêm một lần nữa.
4. Chạy:

```bash
git config user.name "Đỗ Tú Anh"
git config user.email "<email-truong-cua-ban>@vinuni.edu.vn"
git pull
git add submission/REPORT.md submission/evidence/06-challenge-investigation.txt
git commit -m "docs(report): điều tra challenge và tổng hợp báo cáo"
git push
```

## Tự kiểm tra trước khi nộp (README + SUBMISSION.md yêu cầu)

```bash
python -m pytest -q
python scripts/validate_logs.py
git status --short
```

`git status --short` phải sạch (không còn gì chưa commit) trước khi nộp URL repo.

## Khi bị hỏi (demo cuối buổi — luồng Metrics → Traces → Logs → Root cause)
- Đọc thuộc luồng 3 bước: metrics nào tăng bất thường → trace nào mở ra để khoanh vùng →
  log line nào (kèm correlation_id) chứng minh root cause.
- Root cause là gì, fix action và preventive measure là gì — trả lời không cần nhìn giấy.
