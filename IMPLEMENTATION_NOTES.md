# Implementation Notes

The current repository already has the beginnings of a polling trigger:

- `pinger.py` detects supervisor comments and new commits
- `codex_trigger.py` converts a comment into a prompt
- `listener.py` can start a local Codex runner

To evolve this into a real orchestrator, the next code changes should be:

1. teach `pinger.py` to read and deduplicate `task_id` and `result_id`
2. move from comment-only triggering to task-file triggering
3. add a reporter step that writes `orchestrator/reports/latest-result.json`
4. optionally read GitHub Actions check state before asking the supervisor for another task
5. replace `run_codex.sh` placeholder with the real Codex invocation

Suggested event sources:

- new commit on orchestration branch
- update to `orchestrator/tasks/current-task.json`
- update to `orchestrator/reports/latest-result.json`
- workflow completion event
