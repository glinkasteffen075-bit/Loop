from __future__ import annotations

import os
from pathlib import Path

OUT = Path("codex_trigger_requests.log")


def main() -> None:
    repo = os.getenv("PINGER_REPO_FULL_NAME", "")
    pr_number = os.getenv("PINGER_PR_NUMBER", "")
    trigger_source = os.getenv("PINGER_TRIGGER_SOURCE", "unknown")
    task_id = os.getenv("PINGER_TASK_ID", "")
    task_title = os.getenv("PINGER_TASK_TITLE", "")
    task_goal = os.getenv("PINGER_TASK_GOAL", "")
    task_json = os.getenv("PINGER_TASK_JSON", "")
    comment_id = os.getenv("PINGER_COMMENT_ID", "")
    comment_body = os.getenv("PINGER_COMMENT_BODY", "")

    if trigger_source == "task_file":
        prompt = f"""Read the latest pull request in repository {repo}.

Check the task payload in `orchestrator/tasks/current-task.json` on PR #{pr_number}.

Trigger source: {trigger_source}
Task id: {task_id}
Task title: {task_title}
Task goal: {task_goal}

Work only from the latest repository and task state.
Use all available tools and verification steps needed to complete the task.
Take as much time as needed for careful execution.
When finished, write a structured result to `orchestrator/reports/latest-result.json`.

Task payload:
{task_json}
"""
    else:
        prompt = f"""Read the latest pull request in repository {repo}.

Check the newest supervisor comment on PR #{pr_number}.
Supervisor comment id: {comment_id}

If there is an [INSTRUCTION], implement it.
If [STATUS] is COMPLETE, stop.
If no new instruction exists, do nothing.

Work only from the latest repository and PR state.
Use all available tools and verification steps needed.

Supervisor comment:
{comment_body}
"""

    print(prompt)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(prompt + "\n" + ("-" * 80) + "\n")


if __name__ == "__main__":
    main()
