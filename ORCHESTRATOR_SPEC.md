# Loop Orchestrator MVP

This repository defines a GitHub-mediated orchestration loop between:

- `Supervisor`: plans and evaluates work at the repository level
- `Executor`: Codex implements code changes and returns structured results
- `GitHub`: shared state bus and event surface

The loop is:

1. Supervisor inspects the latest repository state.
2. Supervisor decides whether the global goal is complete.
3. If not complete, Supervisor writes a new task payload.
4. A trigger starts Codex.
5. Codex reads the latest task payload, changes code, runs checks, and writes a result payload.
6. Supervisor inspects the result payload, git state, and CI status.
7. Supervisor either closes the goal or emits the next task.

## Design Goal

The system must not depend on free-form chat interpretation alone. Each loop iteration should be auditable through:

- a persisted task
- a persisted result
- repository diffs
- command/test output
- optional CI status

## Repository Layout

Recommended layout:

```text
orchestrator/
  state/
    goal.json
    loop_state.json
  tasks/
    current-task.json
    archive/
  reports/
    latest-result.json
    archive/
  prompts/
    supervisor_system.md
    codex_executor_prompt.md
  schemas/
    task.schema.json
    result.schema.json
```

## Roles

### Supervisor

Responsibilities:

- inspect repo, PR, reports, and CI
- decide whether the global goal is complete
- generate the next smallest useful task
- stop the loop when the goal is satisfied or human input is required

The Supervisor should not emit vague work items like "make it better". It must generate bounded tasks with acceptance criteria.

### Executor

Codex is the executor. It should:

- read the latest task
- inspect the repo
- implement the requested change
- run the most relevant checks
- return a structured result
- push changes and expose enough evidence for evaluation

### GitHub

GitHub acts as the shared transport:

- task storage
- result storage
- branch / PR diff history
- CI / check status
- event source through webhook, polling, or Actions

## State Model

The loop should use explicit statuses.

Global loop statuses:

- `idle`
- `task_ready`
- `executor_running`
- `awaiting_evaluation`
- `goal_complete`
- `human_required`
- `error`

Task statuses:

- `open`
- `in_progress`
- `success`
- `partial_success`
- `blocked`
- `failed`
- `cancelled`

## Recommended Trigger Strategy

Robust order of preference:

1. GitHub webhook on push, PR comment, and workflow completion
2. GitHub Actions calling a lightweight orchestrator endpoint
3. Polling fallback with deduplication

Polling alone is acceptable for an MVP, but it must deduplicate by `task_id`, `result_id`, and commit SHA.

## Task Lifecycle

1. Supervisor writes `orchestrator/tasks/current-task.json`
2. Orchestrator detects a new `task_id`
3. Orchestrator starts Codex with the task payload
4. Codex writes `orchestrator/reports/latest-result.json`
5. Codex commits and pushes code plus report
6. CI runs if configured
7. Supervisor evaluates:
   - latest result payload
   - latest commit(s)
   - CI status
   - remaining open issues
8. Supervisor either:
   - marks global goal complete
   - emits a new task
   - requests human input

## Evaluation Gates

The Supervisor should not mark the task complete based only on prose. It should verify at least:

- relevant files changed
- relevant command/test output exists
- target failure no longer reproduces
- no new blocking regressions were introduced
- CI status is acceptable if CI exists

## Practical Guidance For The "Stability" Goal

The global goal "make Isaac stable" must be decomposed into measurable gates, for example:

- application starts without crash
- core module smoke test passes
- unit test suite passes or known failing tests are reduced with explicit tracking
- no unhandled exceptions in core flows
- logs do not show repeated fatal errors
- build / lint / type checks pass where applicable

Without concrete gates, the Supervisor cannot end the loop reliably.
