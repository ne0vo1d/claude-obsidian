#!/usr/bin/env python3
"""test_wiki_adopt.py — hermetic tests for scripts/wiki-adopt.py.

Builds a throwaway vault fixture in a temp dir and asserts ghost-note
classification: unregistered / no_frontmatter / orphan, plus the clean-page,
exclusion, alias-link, path-link, and --quiet cases. No network, no LLM.

Usage:
  python3 tests/test_wiki_adopt.py
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "wiki-adopt.py"

spec = importlib.util.spec_from_file_location("wiki_adopt", HELPER)
wa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wa)


class Fail(SystemExit):
    pass


def assert_eq(label, expected, actual):
    if expected != actual:
        raise Fail(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"OK   {label}")


def assert_true(label, cond, hint=""):
    if not cond:
        raise Fail(f"FAIL {label}{(': ' + hint) if hint else ''}")
    print(f"OK   {label}")


FM = "---\ntype: concept\n---\n\n"


def build_vault(root):
    wiki = root / "wiki"
    (wiki / "concepts").mkdir(parents=True)
    (wiki / "meta").mkdir()

    # Nav files (excluded from ghost checks themselves).
    (wiki / "index.md").write_text(
        FM + "# Index\n- [[Registered Note]]\n- [[concepts/_index]]\n"
        "- [[Aliased Note|shown as alias]]\n- [[Heading Note#section]]\n"
    )
    (wiki / "log.md").write_text(FM + "# Log\n")
    (wiki / "hot.md").write_text(FM + "# Hot\n")
    (wiki / "concepts" / "_index.md").write_text(
        FM + "# Concepts\n- [[Sub Registered]]\n"
    )

    # Clean page: registered in index.md, frontmattered, linked from another page.
    (wiki / "concepts" / "Registered Note.md").write_text(
        FM + "links to [[Sub Registered]]\n"
    )
    # Registered via _index.md + inbound link from Registered Note.
    (wiki / "concepts" / "Sub Registered.md").write_text(FM + "body\n")
    # Registered via alias-form and heading-form links; also give them inbound links.
    (wiki / "concepts" / "Aliased Note.md").write_text(FM + "see [[Heading Note]]\n")
    (wiki / "concepts" / "Heading Note.md").write_text(FM + "see [[Aliased Note]]\n")

    # GHOST 1: hand-written note — unregistered, no frontmatter, orphan.
    (wiki / "meta" / "Hand Written.md").write_text("just some thoughts\n")
    # GHOST 2: frontmattered but unregistered + orphan.
    (wiki / "concepts" / "Half Ghost.md").write_text(FM + "orphaned idea\n")
    # GHOST 3: self-link only — must still count as orphan.
    (wiki / "concepts" / "Self Linker.md").write_text(FM + "loops to [[Self Linker]]\n")
    return root


def find(ghosts, name):
    for g in ghosts:
        if g["path"].endswith(name):
            return g
    return None


with tempfile.TemporaryDirectory() as td:
    vault = build_vault(Path(td))
    ghosts = wa.scan(vault)
    by_issues = {g["path"]: g["issues"] for g in ghosts}

    assert_eq("ghost count", 3, len(ghosts))

    g1 = find(ghosts, "Hand Written.md")
    assert_true("hand-written detected", g1 is not None)
    assert_eq("hand-written issues", ["unregistered", "no_frontmatter", "orphan"], g1["issues"])

    g2 = find(ghosts, "Half Ghost.md")
    assert_true("half-ghost detected", g2 is not None)
    assert_eq("half-ghost issues", ["unregistered", "orphan"], g2["issues"])

    g3 = find(ghosts, "Self Linker.md")
    assert_true("self-link still orphan", g3 is not None and "orphan" in g3["issues"])

    assert_true("registered note clean", find(ghosts, "Registered Note.md") is None)
    assert_true("sub-index registration honored", find(ghosts, "Sub Registered.md") is None)
    assert_true("alias-form link resolves", find(ghosts, "Aliased Note.md") is None)
    assert_true("heading-form link resolves", find(ghosts, "Heading Note.md") is None)
    assert_true("nav files excluded", find(ghosts, "log.md") is None and find(ghosts, "hot.md") is None)

    # CLI: JSON output round-trips.
    out = subprocess.run(
        [sys.executable, str(HELPER), "scan", "--format", "json", "--vault", str(vault)],
        capture_output=True, text=True,
    )
    assert_eq("json exit code", 0, out.returncode)
    payload = json.loads(out.stdout)
    assert_eq("json ghost_count", 3, payload["ghost_count"])

    # CLI: --quiet prints one line when ghosts exist…
    out = subprocess.run(
        [sys.executable, str(HELPER), "scan", "--quiet", "--vault", str(vault)],
        capture_output=True, text=True,
    )
    assert_eq("quiet exit code", 0, out.returncode)
    assert_true("quiet one-liner", out.stdout.startswith("GHOST_NOTES: 3"), out.stdout)

    # …and nothing at all when the vault is clean.
    for name in ("meta/Hand Written.md", "concepts/Half Ghost.md", "concepts/Self Linker.md"):
        (vault / "wiki" / name).unlink()
    out = subprocess.run(
        [sys.executable, str(HELPER), "scan", "--quiet", "--vault", str(vault)],
        capture_output=True, text=True,
    )
    assert_eq("quiet silent when clean", "", out.stdout)

    # Missing wiki/ folder → exit 3.
    out = subprocess.run(
        [sys.executable, str(HELPER), "scan", "--vault", td + "/nonexistent"],
        capture_output=True, text=True,
    )
    assert_eq("missing wiki exit code", 3, out.returncode)

print("\nALL PASS test_wiki_adopt.py")
