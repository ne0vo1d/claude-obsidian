---
type: meta
title: "Lint Report 2026-07-05"
created: 2026-07-05
updated: 2026-07-05
tags: [meta, lint]
status: developing
---

# Lint Report: 2026-07-05

First lint since 2026-04-24 (~10 weeks). Scanner false positives verified and excluded: `[[Wiki Map]]`, `[[claude-obsidian-presentation]]`, `[[dashboard.base]]` resolve to existing `.canvas`/`.base` files; `[[Foo]]`/`[[notes/Foo]]` are documentation examples in [[DragonScale Memory]] prose.

## Summary

- Pages scanned: 49
- Issues found: 40 (11 ghost notes, 6 orphans, 13 true dead-link targets, 7 frontmatter gaps, 3 address errors) + 29 empty sections (informational)
- Auto-fixed: 0 (report-first policy)
- Needs review: see tiers below
- Semantic tiling: **skipped — ollama not reachable (exit 10)**
- Naming conventions: clean
- Address counter: consistent (peek=3, no drift, no collisions, address-map clean)

## Ghost Notes (hand-written / unintegrated) — 11

Detected by `scripts/wiki-adopt.py` (PR #2 branch). Issue flags: unregistered (u), no_frontmatter (f), orphan (o).

- [[fold-k3-from-2026-04-23-to-2026-04-24-n8]] — u, o
- [[2026-04-10-backlink-empire-session]] — u, o
- [[2026-04-24-v1.6.0-release-session]] — u
- [[boundary-frontier-2026-04-24]] — u
- [[claude-obsidian-v1.2.0-release-session]] — u
- [[claude-obsidian-v1.4-release-session]] — u
- [[full-audit-and-system-setup-session]] — u
- [[retrieval-benchmark-v1.7]] — u, o
- [[tiling-report-2026-04-24]] — u, f, o
- [[methodology-modes]] — u, o
- [[transport-fallback]] — u, o

Root cause cluster: session/release notes were filed into `wiki/meta/` without index registration, and `wiki/references/` pages are linked from `skills/` via markdown paths (invisible to the wiki graph). Suggest: adopt all 11 — register in [[index]] (new "Session Archive" and "References" sections), add inbound links, complete frontmatter.

## Orphan Pages — 6 (subset of ghosts above)

All six orphans are also ghosts; adopting them resolves both findings. [[transport-fallback]] and [[methodology-modes]] are the highest-value targets — they are canonical reference docs that six skills depend on, yet unreachable from the wiki graph.

## Dead Links — 13 targets (17 instances)

Dead targets below are quoted in backticks so this report does not itself add live dead links to the graph.

**Rename mismatch (highest confidence fix):**
- `[[How does the LLM Wiki pattern work?]]` ×4 (in [[Persistent Wiki Artifact]], [[Source-First Synthesis]], [[Query-Time Retrieval]], [[log]]) — the page exists as `How does the LLM Wiki pattern work.md` (no `?`, stripped at file creation). Fix: retarget links with alias.

**Missing pages referenced from session notes** (create stub or unlink):
- `[[Claude Canvas]]`, `[[Claude Obsidian]]`, `[[Karpathy LLM Wiki Pattern]]`, `[[Rankenstein]]` — all in [[2026-04-10-backlink-empire-session]]
- `[[E-commerce SEO]]` ×2 — in [[Claude SEO]] and [[2026-04-14-claude-seo-v190-session]]
- `[[AI Marketing Hub Cover Images Canvas]]` — in [[overview]]; no such canvas exists
- `[[Three laws of motion]]` — in [[Persistent Wiki Artifact]] (analogy link)
- `[[wikilinks]]` — in [[cherry-picks]]

**Repo-file references using wikilink syntax** (should be markdown links or stubs):
- `[[mcp-setup]]`, `[[wiki-cli]]` — in [[transport-fallback]]
- `[[wiki-mode]]`, `[[methodology-modes-guide]]` — in [[methodology-modes]]
- `[[wiki-fold]]`, `[[fold-template]]` — in [[fold-k3-from-2026-04-23-to-2026-04-24-n8]]
These point at `skills/`/`docs/`/`_templates/` files outside the wiki graph. Suggest: convert to plain-text or relative markdown links.

## Frontmatter Gaps — 7 pages

- [[2026-04-15-release-report-session]]: missing created
- [[2026-04-15-slides-and-release-session]]: missing created
- [[boundary-frontier-2026-04-24]]: missing created
- [[retrieval-benchmark-v1.7]]: missing created, tags
- [[tiling-report-2026-04-24]]: missing type, status, created, updated, tags (no frontmatter at all)
- [[methodology-modes]]: missing created, updated
- [[transport-fallback]]: missing created, tags

## Address Validation (DragonScale M2)

- Counter state: peek=3; highest observed c-000001; c-000002 reserved-unassigned (known, per [[hot]] 2026-04-24)
- Post-rollout pages checked: 4 (1 passing, 3 errors)
- Legacy pages pending backfill: 29 (informational, expected)
- Address-map consistency: clean

### Errors
- [[Persistent Wiki Artifact]]: missing address. Created 2026-04-24 (post-rollout).
- [[Query-Time Retrieval]]: missing address. Created 2026-04-24 (post-rollout).
- [[Source-First Synthesis]]: missing address. Created 2026-04-24 (post-rollout).

Root cause: all three were filed by the v1.6 M4 autoresearch run. Sub-agents correctly did not call `allocate-address.sh`, but the orchestrator backfill step never ran — a real gap in the M4 flow, not just missing metadata.

## Empty Sections — 29 (informational)

Mostly trailing `## Related`/navigation headings and template scaffolding in session notes and entity stubs; densest in [[cherry-picks]] (4) and [[2026-04-24-v1.6.0-release-session]] (4). Low priority; fill or prune opportunistically.

## Semantic Tiling

Skipped: ollama not reachable (exit 10). Start ollama and re-run `./scripts/tiling-check.py --report` to check for near-duplicate pages.

## Stale Claims

None flagged this run. [[hot]] was fully reconciled against git history earlier today (v1.7.1 → v1.9.2 drift closed), which was the largest stale-claim surface.
