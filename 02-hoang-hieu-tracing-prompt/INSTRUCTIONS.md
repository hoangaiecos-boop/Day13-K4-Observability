# Nguyễn Tấn Hoàng + Nguyễn Minh Hiếu — Tracing & Prompt Version

## Việc của hai bạn
Gắn trace vào Langfuse (`app/agent.py`), tạo prompt v1/v2 với label (`scripts/setup_prompts.py`),
đổi label và rollback (`scripts/promote_prompt.py`). Langfuse project: JP region,
`https://jp.cloud.langfuse.com`, project "My Project" (org davidaiecos's Organization).

## Trước khi commit — đọc và hiểu code
- `app/agent.py` — tìm đoạn `langfuse_client.update_current_trace(...)` và
  `update_current_generation(...)`. Vì sao `correlation_id` được gắn vào **tag** (`cid:...`)
  chứ không phải vào `metadata` của trace? (gợi ý: đọc `tests/test_agent_prompt_trace.py`,
  test đó khoá cứng metadata phải đúng 4 field `prompt_*`.)
- `scripts/promote_prompt.py` — đọc phần `set_labels()`. Có một lỗi thật đã xảy ra khi làm
  bài: bản đầu gọi API Langfuse với `newLabels: ["production"]` và vô tình XOÁ MẤT label
  `baseline`/`candidate` của version khác, vì API đó thay thế toàn bộ label chứ không thêm
  vào. Đọc `submission/evidence/09-prompt-versioning.txt` mục 4 để hiểu rõ và giải thích
  được khi bị hỏi — đây là câu hỏi rất hợp lý cho phần B1.

## Bước làm

1. Copy `app/agent.py` vào `Day13-K4-Observability/app/agent.py` (ghi đè).
2. Copy 2 file trong `scripts/` vào `Day13-K4-Observability/scripts/`.
3. Copy 6 file trong `submission/evidence/` vào `Day13-K4-Observability/submission/evidence/`.
4. Chạy:

```bash
git config user.name "Nguyễn Tấn Hoàng"        # hoặc "Nguyễn Minh Hiếu" tuỳ ai commit
git config user.email "<email-truong-cua-ban>@vinuni.edu.vn"
git pull
git add app/agent.py scripts/setup_prompts.py scripts/promote_prompt.py submission/evidence/08-langfuse-traces.txt submission/evidence/09-prompt-versioning.txt submission/evidence/10-rollback-terminal.txt submission/evidence/11-rollback-truoc.png submission/evidence/12-rollback-sau.png submission/evidence/13-trace-waterfall.png
git commit -m "feat(tracing): gắn trace Langfuse, prompt v1/v2, label và rollback"
git push
```

Hai bạn có thể chia làm 2 commit riêng nếu muốn (ví dụ Hoàng commit `app/agent.py`,
Hiếu commit 2 script `scripts/`) — chỉ cần đổi `user.name`/`user.email` và `git add` đúng
phần trước khi commit của mỗi người.

**KHÔNG chạy lại** `python scripts/setup_prompts.py` — prompt v1/v2 đã tồn tại sẵn trên
Langfuse, chạy lại sẽ tạo thêm version thừa. Cũng không cần chạy lại `promote_prompt.py`
trừ khi bạn muốn tự tay làm lại demo rollback.

## Tự kiểm tra
Đăng nhập `https://jp.cloud.langfuse.com`, vào Prompts → `day13-chat`, xác nhận
v1 = `production, baseline`, v2 = `candidate, latest`.

## Khi bị hỏi
- Prompt version hiện tại của `production` là mấy? Làm sao biết?
- Vì sao mỗi trace có tag `cid:req-xxxxxxxx`? Dùng để làm gì khi điều tra incident?
- Kể lại lỗi label bị mất và cách đã sửa.
