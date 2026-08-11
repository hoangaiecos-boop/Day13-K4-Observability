"""Chuyển label `production` của prompt day13-chat sang một version cụ thể.

Dùng cho bước promote và rollback trong docs/PROMPT_VERSIONING.md.

    python scripts/promote_prompt.py 2   # promote production -> v2
    python scripts/promote_prompt.py 1   # rollback production -> v1
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from app.cli import configure_utf8_stdio  # noqa: E402

NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
AUTH = (os.getenv("LANGFUSE_PUBLIC_KEY", ""), os.getenv("LANGFUSE_SECRET_KEY", ""))


def labels_of(version: int) -> list[str]:
    r = httpx.get(f"{HOST}/api/public/v2/prompts/{NAME}", params={"version": version}, auth=AUTH, timeout=10.0)
    r.raise_for_status()
    return r.json().get("labels", [])


def set_labels(version: int, labels: list[str]) -> None:
    """PATCH newLabels THAY THẾ toàn bộ label của version, không phải thêm vào.

    Gửi thẳng ["production"] sẽ xoá mất 'baseline'/'candidate' đang gắn ở đó.
    Luôn gửi trọn bộ label mong muốn. Bỏ 'latest' vì Langfuse tự quản label này
    (luôn trỏ version mới nhất) — gửi kèm chỉ gây xung đột.
    """
    payload = sorted({l for l in labels if l != "latest"})
    r = httpx.patch(
        f"{HOST}/api/public/v2/prompts/{NAME}/versions/{version}",
        json={"newLabels": payload},
        auth=AUTH,
        timeout=10.0,
    )
    r.raise_for_status()


def main() -> None:
    configure_utf8_stdio()
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    target = int(sys.argv[1])

    before = {1: labels_of(1), 2: labels_of(2)}
    print(f"TRƯỚC:  v1 labels={before[1]} | v2 labels={before[2]}")

    # Giữ nguyên label vai trò của từng version, chỉ di chuyển 'production'.
    set_labels(target, list(before[target]) + ["production"])
    other = 2 if target == 1 else 1
    set_labels(other, [l for l in before[other] if l != "production"])

    print(f"SAU:    v1 labels={labels_of(1)} | v2 labels={labels_of(2)}")
    print(f"=> label 'production' hiện trỏ tới v{target}")


if __name__ == "__main__":
    main()
