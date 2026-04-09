from __future__ import annotations

import os
from pathlib import Path

OUT = Path("codex_trigger_requests.log")


def main() -> None:
    repo = os.getenv("PINGER_REPO_FULL_NAME", "")
    pr_number = os.getenv("PINGER_PR_NUMBER", "")
    comment_id = os.getenv("PINGER_COMMENT_ID", "")
    comment_body = os.getenv("PINGER_COMMENT_BODY", "")

    prompt = f"""Read the latest pull request in repository {repo}.

Check the newest supervisor comment on PR #{pr_number}.
Supervisor comment id: {comment_id}

If there is an [INSTRUCTION], implement it.
If [STATUS] is COMPLETE, stop.
If no new instruction exists, do nothing.

Work only from the latest repository and PR state.

Supervisor comment:
{comment_body}
"""

    print(prompt)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(prompt + "\n" + ("-" * 80) + "\n")


if __name__ == "__main__":
    main()
