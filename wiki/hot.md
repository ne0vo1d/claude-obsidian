---
type: meta
title: "Hot Cache"
updated: 2026-07-05T20:55:00
tags:
  - meta
  - hot-cache
status: evergreen
related:
  - "[[index]]"
  - "[[log]]"
  - "[[Wiki Map]]"
  - "[[getting-started]]"
---

# Recent Context

Navigation: [[index]] | [[log]] | [[overview]]

## Last Updated

**2026-07-05: hot cache reconciled after ~7 weeks of drift.** The previous entry stopped at v1.7.1 (2026-05-17, local/unpushed). Since then the project shipped all the way to **v1.9.2 public** and beyond. This session also began work on a personal fork.

## Release history since v1.7.1

- **v1.7.2** — audit closure follow-up.
- **v1.8.0 / v1.8.1 / v1.8.2** — methodology modes (LYT / PARA / Zettelkasten / Generic) landed as the `wiki-mode` skill (`.vault-meta/mode.json`, `scripts/wiki-mode.py`); pre-push audit closure at v1.8.2.
- **v1.9.0** (2026-05-18) — the 10-principle thinking framework shipped as the `/think` skill; every other skill got a "How to think" appendix. First-public-release prep (repo hygiene, README SSS+ rewrite).
- **v1.9.1** (2026-05-18) — v1.9.0 audit hardening (atomic chunk writes, hook pathspec blast-radius fix, stale-lock reaper, IPv6 case-pattern quoting, single-tenant threat model).
- **v1.9.2** (2026-05-27) — contextual-prefix prompt-cache hardening + path-handling robustness. Then **promoted to public canonical** (`00213b7`) with an SEO pass; social preview card added (`cb93ff6`, current HEAD).

## This session (2026-07-05)

- **Forked** the repo to `ne0vo1d/claude-obsidian`. Remotes rewired: `origin` → fork, `upstream` → AgriciDaniel. `gh` authenticated as `ne0vo1d`; git credential helper configured.
- **Environment fixed**: Homebrew Python 3.14 + Bash 5.3 + `flock` now win PATH via a new `~/.zprofile` (`brew shellenv`). Satisfies the 3.10+/4.0+ prereqs.
- **Obsidian CLI transport enabled**: Obsidian 1.12.7's bundled `obsidian-cli` symlinked to `~/.local/bin`; CLI toggle enabled in-app; `transport.json` now `preferred: cli`, verified end-to-end (read/search/create/append/property).
- **CLI-syntax fix** (branch `fix/obsidian-cli-syntax`, **PR #1 into fork `main`, open — NOT yet merged**): corrected the documented CLI recipes across 7 skill files + `transport-fallback.md` from the broken positional form (`obsidian-cli read "$VAULT" "$NOTE"`) to the real named-param syntax (`read path=…`, `search query=…`, `create … overwrite`; no stdin; auto-targets active vault). Verifier pass: HOLD-FIX-FIRST → all findings closed. Commit `3d76b75`.

## Active threads

- **PR #1** open on the fork — decide merge strategy (squash recommended).
- On `main` the skill docs still show the old positional syntax until PR #1 merges.
- Fork will keep evolving; `git fetch upstream` pulls in AgriciDaniel changes.
