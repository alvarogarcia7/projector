---
id: PROJ-1
title: Cache the execution result
status: In Progress
assignee: []
created_date: '2026-03-25 10:32'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
uv run python3 -m projector.cli project add projector
uv run python3 -m projector.cli worktree add projector    eW688AmPx6UdoD4VCa7Fe
uv run python3 -m projector.cli runner    -p projector -w eW688AmPx6UdoD4VCa7Fe    sleep 10 # takes 10 seconds
uv run python3 -m projector.cli runner    -p projector -w eW688AmPx6UdoD4VCa7Fe    sleep 10 # takes 0 seconds
uv run python3 -m projector.cli runner    -p projector -w eW688AmPx6UdoD4VCa7Fe -B sleep 10 # takes 10 seconds again
<!-- SECTION:FINAL_SUMMARY:END -->
