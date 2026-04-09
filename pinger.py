from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# @add-package requests
import requests


STATE_FILE = Path("pinger_state.json")
EVENTS_FILE = Path("pinger_events.log")

# Pflicht:
# export GITHUB_TOKEN=...
# export REPO_FULL_NAME=owner/repo
# export PR_NUMBER=12
#
# Optional:
# export POLL_INTERVAL_SECONDS=15
# export SUPERVISOR_GITHUB_LOGIN=dein-github-name
# export CODEX_TRIGGER_COMMAND='python codex_trigger.py'
# export CODEX_COMMIT_AUTHOR_HINT='codex'


@dataclass
class Config:
    github_token: str
    repo_full_name: str
    pr_number: int
    poll_interval_seconds: int = 15
    supervisor_github_login: str | None = None
    codex_trigger_command: str | None = None
    codex_commit_author_hint: str = "codex"


def load_config() -> Config:
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("REPO_FULL_NAME")
    pr_number = os.getenv("PR_NUMBER")

    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    if not repo:
        raise RuntimeError("Missing REPO_FULL_NAME")
    if not pr_number:
        raise RuntimeError("Missing PR_NUMBER")

    return Config(
        github_token=token,
        repo_full_name=repo,
        pr_number=int(pr_number),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "15")),
        supervisor_github_login=os.getenv("SUPERVISOR_GITHUB_LOGIN"),
        codex_trigger_command=os.getenv("CODEX_TRIGGER_COMMAND"),
        codex_commit_author_hint=os.getenv("CODEX_COMMIT_AUTHOR_HINT", "codex"),
    )


def log_event(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "last_supervisor_comment_id": None,
            "last_commit_sha": None,
            "status": "IDLE",
        }
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_issue_comments(cfg: Config) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{cfg.repo_full_name}/issues/{cfg.pr_number}/comments"
    response = requests.get(url, headers=github_headers(cfg.github_token), timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_review_comments(cfg: Config) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{cfg.repo_full_name}/pulls/{cfg.pr_number}/comments"
    response = requests.get(url, headers=github_headers(cfg.github_token), timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_pr(cfg: Config) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{cfg.repo_full_name}/pulls/{cfg.pr_number}"
    response = requests.get(url, headers=github_headers(cfg.github_token), timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_pr_commits(cfg: Config) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{cfg.repo_full_name}/pulls/{cfg.pr_number}/commits"
    response = requests.get(url, headers=github_headers(cfg.github_token), timeout=30)
    response.raise_for_status()
    return response.json()


def is_supervisor_comment(comment: dict[str, Any], cfg: Config) -> bool:
    body = comment.get("body", "") or ""
    user_login = (comment.get("user") or {}).get("login")

    if cfg.supervisor_github_login:
        return user_login == cfg.supervisor_github_login

    return "[INSTRUCTION]" in body or "[STATUS]" in body


def extract_status(comment_body: str) -> str | None:
    upper = comment_body.upper()
    if "[STATUS]" not in upper:
        return None
    if "COMPLETE" in upper:
        return "COMPLETE"
    if "HUMAN_REQUIRED" in upper:
        return "HUMAN_REQUIRED"
    if "CONTINUE" in upper:
        return "CONTINUE"
    return None


def latest_supervisor_comment(cfg: Config) -> dict[str, Any] | None:
    combined = fetch_issue_comments(cfg) + fetch_review_comments(cfg)
    combined.sort(key=lambda c: c.get("id", 0))

    supervisor_comments = [c for c in combined if is_supervisor_comment(c, cfg)]
    if not supervisor_comments:
        return None

    return supervisor_comments[-1]


def latest_commit(cfg: Config) -> dict[str, Any] | None:
    commits = fetch_pr_commits(cfg)
    if not commits:
        return None
    return commits[-1]


def trigger_codex(cfg: Config, comment: dict[str, Any]) -> None:
    if not cfg.codex_trigger_command:
        log_event("No CODEX_TRIGGER_COMMAND configured. Skipping Codex trigger.")
        return

    env = os.environ.copy()
    env["PINGER_REPO_FULL_NAME"] = cfg.repo_full_name
    env["PINGER_PR_NUMBER"] = str(cfg.pr_number)
    env["PINGER_COMMENT_ID"] = str(comment.get("id"))
    env["PINGER_COMMENT_BODY"] = comment.get("body", "") or ""

    log_event(f"Triggering Codex via: {cfg.codex_trigger_command}")
    subprocess.run(cfg.codex_trigger_command, shell=True, check=False, env=env)


def main() -> None:
    cfg = load_config()
    state = load_state()

    log_event(
        f"Started pinger for {cfg.repo_full_name} PR #{cfg.pr_number} "
        f"(poll every {cfg.poll_interval_seconds}s)"
    )

    while True:
        try:
            pr = fetch_pr(cfg)
            pr_state = pr.get("state", "").upper()
            if pr_state == "CLOSED":
                log_event("PR is closed. Stopping pinger.")
                state["status"] = "STOPPED_PR_CLOSED"
                save_state(state)
                break

            supervisor_comment = latest_supervisor_comment(cfg)
            if supervisor_comment:
                comment_id = supervisor_comment.get("id")
                comment_body = supervisor_comment.get("body", "") or ""
                status = extract_status(comment_body)

                if comment_id != state.get("last_supervisor_comment_id"):
                    state["last_supervisor_comment_id"] = comment_id
                    log_event(f"New supervisor comment detected: id={comment_id}")

                    if status == "COMPLETE":
                        state["status"] = "COMPLETE"
                        save_state(state)
                        log_event("Supervisor marked task COMPLETE. Stopping pinger.")
                        break

                    if status == "HUMAN_REQUIRED":
                        state["status"] = "HUMAN_REQUIRED"
                        save_state(state)
                        log_event("Supervisor marked HUMAN_REQUIRED. Stopping pinger.")
                        break

                    if status in ("CONTINUE", None):
                        state["status"] = "TRIGGERING_CODEX"
                        save_state(state)
                        trigger_codex(cfg, supervisor_comment)
                        state["status"] = "WAITING_FOR_CODEX_OUTPUT"
                        save_state(state)

            commit = latest_commit(cfg)
            if commit:
                sha = commit.get("sha")
                if sha and sha != state.get("last_commit_sha"):
                    state["last_commit_sha"] = sha
                    author_login = ((commit.get("author") or {}).get("login")) or ""
                    commit_message = (commit.get("commit") or {}).get("message", "")

                    log_event(
                        f"New PR commit detected: sha={sha[:8]} "
                        f"author={author_login or 'unknown'} "
                        f"message={commit_message.splitlines()[0] if commit_message else ''}"
                    )

                    if cfg.codex_commit_author_hint.lower() in author_login.lower():
                        state["status"] = "REVIEW_NEEDED"
                    else:
                        state["status"] = "PR_UPDATED"

                    save_state(state)

        except KeyboardInterrupt:
            log_event("Interrupted by user.")
            raise
        except Exception as exc:
            state["status"] = "ERROR"
            save_state(state)
            log_event(f"ERROR: {exc}")

        time.sleep(cfg.poll_interval_seconds)


if __name__ == "__main__":
    main()
