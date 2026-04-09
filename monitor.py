#!/usr/bin/env python3
"""Terminal monitor dashboard for autonomous AI coding system."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List

STATE_FILE = "state.json"
EVENTS_FILE = "events.log"
REFRESH_SECONDS = 1
MAX_WIDTH = 140

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

STATUS_COLORS = {
    "CODEX_RUNNING": BLUE,
    "WAITING_FOR_CHATGPT": YELLOW,
    "REVIEW_PENDING": YELLOW,
    "COMPLETE": GREEN,
    "ERROR": RED,
    "HUMAN_REQUIRED": MAGENTA,
}


def truncate(value: Any, width: int) -> str:
    text = "" if value is None else str(value)
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 3:
        return "." * width
    return text[: width - 3] + "..."


def safe_get(data: Dict[str, Any], key: str, default: str = "NO DATA") -> Any:
    value = data.get(key)
    if value is None or value == "":
        return default
    return value


def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"_error": "Malformed state.json", "status": "ERROR"}
        return data
    except FileNotFoundError:
        return {"_error": "state.json missing", "status": "NO DATA"}
    except json.JSONDecodeError:
        return {"_error": "state.json invalid JSON", "status": "ERROR"}
    except OSError as exc:
        return {"_error": f"state.json read error: {exc}", "status": "ERROR"}


def load_events() -> List[str]:
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
        return lines
    except FileNotFoundError:
        return ["NO DATA"]
    except OSError as exc:
        return [f"ERROR reading events.log: {exc}"]


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, WHITE)


def flow_active_node(state: Dict[str, Any]) -> str:
    status = str(safe_get(state, "status", ""))
    waiting_for = str(safe_get(state, "waiting_for", "")).upper()

    if status == "CODEX_RUNNING":
        return "CODEX"
    if status == "WAITING_FOR_CHATGPT":
        return "CHATGPT"
    if status in {"REVIEW_PENDING", "COMPLETE"}:
        return "GITHUB"
    if status in {"ERROR", "HUMAN_REQUIRED"}:
        return "REVIEW"
    if "CHATGPT" in waiting_for:
        return "CHATGPT"
    if "CODEX" in waiting_for:
        return "CODEX"
    return "TRIGGER"


def render_header(state: Dict[str, Any], width: int = MAX_WIDTH) -> str:
    mission = truncate(safe_get(state, "mission"), 36)
    iteration = truncate(safe_get(state, "iteration"), 4)
    status = str(safe_get(state, "status"))
    phase = truncate(safe_get(state, "phase"), 12)
    repo = truncate(safe_get(state, "repo"), 52)
    pr_number = safe_get(state, "pr_number")

    pr_display = f"#{pr_number}" if str(pr_number) != "NO DATA" else "NO DATA"
    color = status_color(status)

    line1 = f"MISSION: {mission:<36} ITERATION: {iteration}"
    line2 = f"STATUS: {color}{status}{RESET:<0} PHASE: {phase}"
    line3 = f"REPO: {repo:<52} PR: {pr_display}"

    return "\n".join(
        [
            f"{BOLD}{line1[:width]}{RESET}",
            f"{BOLD}{line2[:width]}{RESET}",
            f"{BOLD}{line3[:width]}{RESET}",
        ]
    )


def render_flow(state: Dict[str, Any], width: int = MAX_WIDTH) -> str:
    active = flow_active_node(state)
    nodes = ["DU", "CHATGPT", "TRIGGER", "CODEX", "GITHUB", "REVIEW"]

    styled: List[str] = []
    for node in nodes:
        if node == active:
            styled.append(f"{BLUE}[ {node} ]{RESET}")
        else:
            styled.append(f"( {node} )")

    flow = " -> ".join(styled)
    return f"{BOLD}SYSTEM FLOW{RESET}\n{flow[:width]}"


def render_panels(state: Dict[str, Any], width: int = MAX_WIDTH) -> str:
    col_width = max(30, (width - 6) // 2)

    sup_lines = [
        f"{BOLD}{CYAN}SUPERVISOR PANEL{RESET}",
        f"last_chatgpt_trigger_at : {truncate(safe_get(state, 'last_chatgpt_trigger_at'), col_width - 27)}",
        f"last_instruction_summary: {truncate(safe_get(state, 'last_instruction_summary'), col_width - 27)}",
        f"last_supervisor_status  : {truncate(safe_get(state, 'last_supervisor_status'), col_width - 27)}",
        f"waiting_for            : {truncate(safe_get(state, 'waiting_for'), col_width - 27)}",
    ]

    codex_status = str(safe_get(state, "codex_status"))
    codex_color = status_color(codex_status)
    codex_lines = [
        f"{BOLD}{CYAN}CODEX PANEL{RESET}",
        f"codex_status         : {codex_color}{truncate(codex_status, col_width - 25)}{RESET}",
        f"codex_started_at     : {truncate(safe_get(state, 'codex_started_at'), col_width - 25)}",
        f"codex_runtime_seconds: {truncate(safe_get(state, 'codex_runtime_seconds'), col_width - 25)}",
        f"codex_current_action : {truncate(safe_get(state, 'codex_current_action'), col_width - 25)}",
        f"codex_last_output    : {truncate(safe_get(state, 'codex_last_output'), col_width - 25)}",
    ]

    branch = truncate(safe_get(state, "branch"), col_width - 17)
    last_commit = truncate(safe_get(state, "last_commit"), col_width - 17)

    changed_files = state.get("changed_files")
    if isinstance(changed_files, list):
        files = [str(item) for item in changed_files][:5]
        changed_count = len(changed_files)
    else:
        files = []
        changed_count = 0 if changed_files in (None, "", "NO DATA") else 1

    gh_lines = [
        f"{BOLD}{CYAN}GITHUB PANEL{RESET}",
        f"branch              : {branch}",
        f"last_commit         : {last_commit}",
        f"changed_files_count : {changed_count}",
        "changed_files       :",
    ]
    if files:
        gh_lines.extend([f"  - {truncate(name, col_width - 6)}" for name in files])
    else:
        gh_lines.append("  - NO DATA")

    left = sup_lines + [""] + codex_lines
    right = gh_lines

    row_count = max(len(left), len(right))
    left.extend([""] * (row_count - len(left)))
    right.extend([""] * (row_count - len(right)))

    merged = []
    divider = f" {DIM}|{RESET} "
    for l, r in zip(left, right):
        merged.append(f"{l:<{col_width}}{divider}{r:<{col_width}}")

    return "\n".join(merged)


def render_log(events: List[str], width: int = MAX_WIDTH) -> str:
    recent = events[-10:] if events else ["NO DATA"]
    lines = [f"{BOLD}EVENT LOG (last 10){RESET}"]
    for entry in recent:
        rendered = truncate(entry if entry else "NO DATA", width - 4)
        lines.append(f"  {rendered}")
    return "\n".join(lines)


def build_screen(state: Dict[str, Any], events: List[str], width: int, height: int) -> str:
    sections = [
        render_header(state, width),
        "",
        render_flow(state, width),
        "",
        render_panels(state, width),
        "",
        render_log(events, width),
    ]

    if state.get("_error"):
        sections.append("")
        sections.append(f"{RED}{BOLD}DATA WARNING:{RESET} {state['_error']}")

    content = "\n".join(sections)
    lines = content.splitlines()
    if len(lines) < height:
        lines.extend([""] * (height - len(lines)))
    return "\n".join(lines[:height])


def main_loop() -> None:
    sys.stdout.write("\033[2J\033[?25l")
    sys.stdout.flush()
    try:
        while True:
            try:
                term_size = os.get_terminal_size()
                width = max(80, min(term_size.columns, MAX_WIDTH))
                height = max(24, term_size.lines)
            except OSError:
                width = 120
                height = 40

            state = load_state()
            events = load_events()
            screen = build_screen(state, events, width, height)

            sys.stdout.write("\033[H")
            sys.stdout.write(screen)
            sys.stdout.flush()
            time.sleep(REFRESH_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main_loop()
