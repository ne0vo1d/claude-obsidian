#!/usr/bin/env python3
"""wiki-adopt.py — ghost-note detector for hand-written vault pages.

Notes added directly in Obsidian (not via Claude's ingest/save flows) are
invisible to the wiki's navigation layer: they're absent from index.md, often
lack frontmatter, and have no inbound wikilinks. This script finds them so
they can be adopted (frontmatter added, links woven, index registered).

A page is a GHOST when any of these hold:

  unregistered   — not wikilinked from wiki/index.md or any */_index.md
  no_frontmatter — file does not start with a YAML frontmatter block
  orphan         — zero inbound wikilinks from any other wiki page

Consumed by:
  - hooks/hooks.json SessionStart  (--quiet one-line summary)
  - skills/wiki-lint/SKILL.md      (§Adopt workflow drives the full report)

CLI:
  wiki-adopt.py scan [--format text|json] [--quiet] [--vault PATH]

  --format text  human-readable report grouped by page (default)
  --format json  machine-readable, for skills to parse
  --quiet        print a single summary line ONLY when ghosts exist; else
                 nothing. Always exits 0. Safe for hooks.
  --vault PATH   vault root override (default: repo root above scripts/)

Known heuristic limitation: pages in different folders sharing a basename
(wiki/concepts/Foo.md and wiki/sources/Foo.md) share the bare-stem link key
"Foo", so a [[Foo]] link anywhere marks BOTH as registered/linked even though
Obsidian resolves it to one. Duplicate basenames are against this vault's
conventions ("filenames are unique"), so the false-negative is accepted
rather than re-implementing Obsidian's resolver.

Exit codes:
  0 — success (including "no ghosts")
  2 — usage error
  3 — vault root has no wiki/ folder
"""

import argparse
import json
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent

# Navigation/meta files that are never "ghosts" themselves. Mirrors the
# canonical exclusion list in skills/wiki-ingest/SKILL.md §Never ingest.
EXCLUDE_NAMES = {
    "index.md", "log.md", "hot.md", "overview.md", "getting-started.md",
    "dashboard.md", "Wiki Map.md",
}

# [[Target]], [[Target|alias]], [[Target#heading]] — capture the target.
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


def wiki_pages(wiki_dir):
    """All .md pages under wiki/, sorted for deterministic output."""
    return sorted(p for p in wiki_dir.rglob("*.md"))


def link_targets(text):
    """Set of wikilink targets in text, stripped of whitespace."""
    return {m.strip() for m in WIKILINK_RE.findall(text)}


def page_keys(page, wiki_dir):
    """Names under which a page can be wikilinked.

    Obsidian resolves [[Name]] by unique filename, and also accepts
    path-style links like [[concepts/_index]]. Match either.
    """
    rel = page.relative_to(wiki_dir).with_suffix("")
    return {page.stem, str(rel)}


def has_frontmatter(text):
    return text.startswith("---\n") or text.startswith("---\r\n")


def scan(vault_root):
    wiki_dir = vault_root / "wiki"
    if not wiki_dir.is_dir():
        print(f"ERR: no wiki/ folder under {vault_root}", file=sys.stderr)
        sys.exit(3)

    pages = wiki_pages(wiki_dir)
    texts = {}
    for p in pages:
        try:
            texts[p] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            texts[p] = ""

    # Registration surface: index.md + every */_index.md
    index_files = [p for p in pages if p.name == "index.md" and p.parent == wiki_dir]
    index_files += [p for p in pages if p.name == "_index.md"]
    registered = set()
    for idx in index_files:
        registered |= link_targets(texts[idx])

    # Inbound-link map: target name -> set of pages that link to it.
    # Parsed once per page; orphan check below is then a set lookup.
    linkers_of = {}
    targets_by_page = {p: link_targets(texts[p]) for p in pages}
    for p, targets in targets_by_page.items():
        for t in targets:
            linkers_of.setdefault(t, set()).add(p)

    ghosts = []
    for p in pages:
        if p.name in EXCLUDE_NAMES or p.name == "_index.md":
            continue
        keys = page_keys(p, wiki_dir)
        issues = []
        if not keys & registered:
            issues.append("unregistered")
        if not has_frontmatter(texts[p]):
            issues.append("no_frontmatter")
        # Orphan: no page OTHER than itself links to it.
        inbound_pages = set()
        for k in keys:
            inbound_pages |= linkers_of.get(k, set())
        if not inbound_pages - {p}:
            issues.append("orphan")
        if issues:
            ghosts.append({
                "path": str(p.relative_to(vault_root)),
                "issues": issues,
            })
    return ghosts


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wiki-adopt.py", add_help=True)
    ap.add_argument("command", choices=["scan"], nargs="?", default="scan")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--vault", default=str(VAULT_ROOT))
    args = ap.parse_args(argv)

    ghosts = scan(Path(args.vault).resolve())

    if args.quiet:
        if ghosts:
            names = ", ".join(g["path"] for g in ghosts[:3])
            more = f" (+{len(ghosts) - 3} more)" if len(ghosts) > 3 else ""
            print(
                f"GHOST_NOTES: {len(ghosts)} wiki page(s) not integrated "
                f"({names}{more}). Run 'lint the wiki' to adopt them."
            )
        return 0

    if args.format == "json":
        print(json.dumps({"ghost_count": len(ghosts), "ghosts": ghosts}, indent=2))
        return 0

    if not ghosts:
        print("No ghost notes. Every wiki page is registered, frontmattered, and linked.")
        return 0
    print(f"{len(ghosts)} ghost note(s):\n")
    for g in ghosts:
        print(f"  {g['path']}")
        for issue in g["issues"]:
            print(f"    - {issue}")
    print("\nAdopt via the wiki-lint skill: add frontmatter, weave inbound links, register in index.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
