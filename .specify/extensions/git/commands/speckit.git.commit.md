---
description: "Commit changes using the project's atomic commit standard"
---

# Commit Changes

Commit outstanding changes following the project's atomic commit convention.
This command is invoked as an optional hook after Spec Kit commands complete.

## Commit Convention

Each commit message follows this format:

```
<type> <scope> <emoji>: <short description in English>
```

Scope is optional. When omitted: `<type> <emoji>: <description>`

### Commit Types

| Type      | Emoji | Description                                                              |
|-----------|-------|--------------------------------------------------------------------------|
| feat      | ✨    | New functionality (model, function, script, API, etc.)                   |
| fix       | 🐛    | Bug fixes in code or logic                                               |
| data      | 🗃️    | Data changes (cleanup, update, source change)                            |
| eda       | 📊    | Exploratory data analysis                                                |
| model     | 🤖    | Model changes (training, evaluation, improvements)                       |
| test      | ✅    | Addition or modification of tests                                        |
| docs      | 📝    | Documentation (README, notebooks, explanatory comments)                  |
| viz       | 📈    | New or adjusted visualizations                                           |
| refactor  | ♻️    | Code refactoring without changing functionality                          |
| chore     | ⚒️    | Minor tasks, configuration, maintenance                                  |
| env       | 📦    | Environment or dependency changes                                        |
| ci        | ⚙️    | CI/CD or automation changes                                              |
| schema    | 🗂️    | DB schema changes (tables, migrations, columns, constraints)             |
| pipeline  | 🛤️    | Data pipeline changes (ETL/ELT, DAGs, orchestration)                    |
| ops       | 🔧    | Operational or deployment changes                                        |
| style     | 🎨    | Style and formatting adjustments (linting, typing, code formatting)      |
| deps      | 📥    | External dependency changes (install, update, remove)                    |
| sec       | 🔒    | Security-related changes                                                 |
| perf      | ⚡    | Performance optimization                                                 |

## Execution

### Step 1 — Inspect the working tree

Run in parallel:
- `git status` — list all modified, staged, and untracked files
- `git diff` — show unstaged changes
- `git diff --staged` — show staged changes
- `git log --oneline -5` — understand recent commit context

### Step 2 — Check for changes

If there are no changes to commit, inform the user and stop. Do not create
empty commits.

### Step 3 — Group into atomic commits

Analyze the diff and group related changes into the smallest meaningful units.
Each commit must represent a single logical change. Do not mix unrelated
concerns (e.g., a spec file addition and a config change are separate commits).

For each group, determine the appropriate type, emoji, scope, and a concise
English description (imperative mood, max 72 chars).

### Step 4 — Present proposed commits for approval

Show the user a numbered list:

```
Proposed commits:

1. docs specs 📝: add main dashboard specification
   Files: specs/001-main-dashboard/spec.md, .specify/feature.json

2. chore specify ⚒️: add requirements checklist for main dashboard
   Files: specs/001-main-dashboard/checklists/requirements.md
```

Then ask:
> **Do these commits look good?** You can approve as-is, suggest changes
> (e.g., "merge 1 and 2", "change type of 1 to feat"), or cancel.

### Step 5 — Apply feedback if needed

Adjust the list based on user feedback, show the updated list, and ask for
confirmation again. Repeat until approved.

### Step 6 — Execute upon approval

For each commit:
1. Stage only the relevant files: `git add <files>`
2. Create the commit using a HEREDOC to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
type(scope): emoji description

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

3. Confirm each commit succeeded before moving to the next.

### Step 7 — Summary

```
Done! 2 commits created:
  abc1234 docs(specs): 📝 add main dashboard specification
  def5678 chore(specify): ⚒️ add requirements checklist for main dashboard
```

## Rules

- **Never skip approval** — always show proposed commits and wait for confirmation
- **Atomic commits** — one logical change per commit
- **English only** — all commit messages must be in English
- **Imperative mood** — "add", "fix", "update" not "added", "fixed", "updated"
- **Never use `--no-verify`** — if a hook fails, fix the underlying issue
- **Never amend published commits**

## Graceful Degradation

- If Git is not available or not a repository: skip with a warning
- If no changes to commit: inform the user and stop
