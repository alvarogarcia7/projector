---
id: PROJ-1.1
title: Caching both for runner and for checks
status: To Do
assignee: []
created_date: '2026-05-15 14:43'
updated_date: '2026-05-15 14:46'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. In .projector/ create a .projectorignore, that lists files/folders that do not "pollute" the directory.

When a file/folder is ignored, even if its changed, its status is not "modified" for projector.

2. The `check` subcommand should also be cached, same as `run`. Check PROJ-1 (in backlog/)
<!-- SECTION:DESCRIPTION:END -->
