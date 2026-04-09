#!/data/data/com.termux/files/usr/bin/bash

PROMPT=$(cat <<'EOF'
Read the latest pull request in the active repository.

Check the newest supervisor PR comment or review comment.

If there is an [INSTRUCTION], implement it.
If [STATUS] is COMPLETE, stop.
If [STATUS] is HUMAN_REQUIRED, stop.
If no new instruction exists, do nothing.

Work only from the latest repository and PR state.
EOF
)

echo "=== STARTING CODEX ==="
echo "$PROMPT"

# Hier später den echten Codex-CLI-Befehl einsetzen.
# Beispiel:
# codex exec "$PROMPT"

sleep 2
echo "=== CODEX PLACEHOLDER FINISHED ==="
