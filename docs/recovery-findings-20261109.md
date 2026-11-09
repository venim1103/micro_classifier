# Recovery Findings and Handoff

2026-11-09. Documentation-only note; no new crash diagnosis or source validation.

## Confirmed Findings

- Recovery records describe truncated review/test tails, including exact prefixes
  of committed files. Missing tails were recovered while preserving local edits.
  Local backups remain under `.git/recovery-20261109-PmbQpU/`; they are not pushed.
- Editor reads sometimes showed pre-migration text while terminal reads showed
  the written layout. Reconcile or reload stale buffers before saving; do not
  overwrite recovered files with an old buffer. This is not a proven cause.
- Historical records and repeated handoffs had accumulated in large root files.
  Commit `1956786` split them into linked chapters and archives, retaining failed
  checks, spent budgets, evidence limits and historical sections. Link rebasing
  preserved existing reference-definition behavior rather than hiding conflicts.
- Current on-disk roots are 111 lines for [DESIGN.md][design] and 709 lines for
  [REVIEW.md][review]. At WIP `5465393`, [sim/diagnostics.py][source] has 14,153
  lines and [tests/test_sim.py][tests] has 22,683. No source split was attempted
  for this note.

## What Remains Unproven

- The chat window, document size, caches and OOM are possible explanations, not
  established causes. Recorded current-container OOM counters were zero; those
  counters cannot exclude a previous container or host/editor failure.
- Earlier observations reported 21 MiB workspace storage, 65 MiB user cache and
  328 GiB free disk. These are historical observations, not current measurements
  or evidence of a cache leak. No cache purge was justified or performed.
- Smaller document roots reduce routine reading, but do not prove crashes fixed.

## Resume Safely

- Read [AGENTS.md][agents], this note and [the last verified source checkpoint][gate].
  Follow only relevant chapter links; avoid whole archives and giant diffs/logs.
  Keep new checkpoint notes short and archive whole sections without dropping
  failures, limits or spent run ledgers.
- Emergency WIP `5465393` is pushed and explicitly unverified. It adds optional
  native ToF selection retention in `record_native_tof_source(include_selection=...)`
  and `test_native_tof_selection_retention`. Inspect that increment before running
  focused checks; retain its existing finite limits and count interrupted attempts.
- Verify worktree, processes, file completeness and available tools after restart.
  Preserve damaged versions before repair; never infer an interrupted gate passed.
- All qualification/admission flags remain false. No command, physical bounds,
  clock qualification, studies, dependency changes or hardware work are authorized
  by matching records or this handoff. This note does not resume implementation.

[agents]: ../AGENTS.md
[design]: ../DESIGN.md
[review]: ../REVIEW.md
[source]: ../sim/diagnostics.py
[tests]: ../tests/test_sim.py
[gate]: ../REVIEW.md#225-bounded-native-tof-selection-intake-2026-11-09