#!/data/data/com.termux/files/usr/bin/bash

if [ "${PINGER_TRIGGER_SOURCE:-}" = "task_file" ]; then
PROMPT=$(cat <<EOF
Read the latest pull request in the active repository.

Check the task payload in orchestrator/tasks/current-task.json.

Trigger source: ${PINGER_TRIGGER_SOURCE:-unknown}
Task id: ${PINGER_TASK_ID:-}
Task title: ${PINGER_TASK_TITLE:-}
Task goal: ${PINGER_TASK_GOAL:-}

Work only from the latest repository and task state.
Use all available tools and verification steps required to complete the task.
Take as much time as needed for careful implementation and validation.
Write the result to orchestrator/reports/latest-result.json when finished.
EOF
)
else
PROMPT=$(cat <<'EOF'
Read the latest pull request in the active repository.

Check the newest supervisor PR comment or review comment.

If there is an [INSTRUCTION], implement it.
If [STATUS] is COMPLETE, stop.
If [STATUS] is HUMAN_REQUIRED, stop.
If no new instruction exists, do nothing.

Work only from the latest repository and PR state.
Use all available tools and verification steps needed.
EOF
)
fi

echo "=== STARTING CODEX ==="
echo "$PROMPT"

# Hier später den echten Codex-CLI-Befehl einsetzen.
# Beispiel:
# codex exec "$PROMPT"

sleep 2
echo "=== CODEX PLACEHOLDER FINISHED ==="
