"""Tạo prompt day13-chat v1/v2 trên Langfuse theo docs/PROMPT_VERSIONING.md.

Chạy: python scripts/setup_prompts.py
Cần LANGFUSE_* trong .env. Script idempotent: chạy lại sẽ tạo version mới, không ghi đè.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from langfuse import get_client  # noqa: E402

from app.cli import configure_utf8_stdio  # noqa: E402

NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")

# v1 — baseline. Giữ đúng ba biến bắt buộc của prompt contract.
V1 = (
    "You are the Day 13 lab assistant.\n"
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}"
)

# v2 — candidate. Thay đổi nhỏ về format và độ dài, KHÔNG đổi ba biến.
V2 = (
    "You are the Day 13 lab assistant. Answer in at most 3 sentences.\n"
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}\n"
    "Cite the doc you used."
)


def main() -> None:
    configure_utf8_stdio()
    client = get_client()
    if not client.auth_check():
        print("Lỗi: không xác thực được với Langfuse. Kiểm tra LANGFUSE_* trong .env.")
        sys.exit(1)

    v1 = client.create_prompt(name=NAME, type="text", prompt=V1, labels=["baseline", "production"])
    print(f"v{v1.version} labels={v1.labels} <- baseline + production")

    v2 = client.create_prompt(name=NAME, type="text", prompt=V2, labels=["candidate"])
    print(f"v{v2.version} labels={v2.labels} <- candidate")

    print(f"\nPrompt '{NAME}' sẵn sàng. Đổi LANGFUSE_PROMPT_LABEL để chọn version khi chạy app.")


if __name__ == "__main__":
    main()
