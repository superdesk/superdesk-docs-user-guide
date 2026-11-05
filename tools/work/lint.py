#!/usr/bin/env python3
"""Lint the user guide pages.

Checks every page under superdesk-user-guide/ plus the landing README: GitBook
blocks are balanced, relative links and anchors resolve, SUMMARY.md targets
exist, no em-dashes, no links to the retired docs site. With --strict (the PR
gate) it also requires every referenced image to exist and refuses pages that
still carry VERIFY, SCREENSHOT PENDING or other HTML comments, and it runs
sync_indexes.py --check.

Usage: python3 lint.py <docs-repo-root> [--strict] [page.md ...]
When pages are given, only those are linted (paths relative to the repo root);
SUMMARY.md and the index check always run.
"""
import glob
import os
import re
import subprocess
import sys

BLOCKS = [("stepper", "endstepper"), ("step", "endstep"), ("hint", "endhint"), ("tabs", "endtabs"), ("tab", "endtab")]


def slug(h):
    h = h.strip().lower()
    h = re.sub(r"[^\w\s-]", "", h)
    return re.sub(r"\s+", "-", h).strip("-")


def headings(path):
    return set(slug(m) for m in re.findall(r"^#{1,6}\s+(.+?)\s*$", open(path, encoding="utf-8").read(), re.M))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    # --skip-index-check: for a PR that adds pages but leaves the landing page for a later PR.
    skip_index = "--skip-index-check" in sys.argv
    # --pending-root=<dir>: a checkout of the full working branch; links whose
    # target is missing here but present there are listed as pending, not broken.
    pending_root = next((os.path.abspath(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--pending-root=")), None)
    pending = []
    root = os.path.abspath(args[0]) if args else os.getcwd()
    if args[1:]:
        pages = args[1:]
    else:
        found = glob.glob(os.path.join(root, "superdesk-user-guide", "**", "*.md"), recursive=True)
        pages = sorted(os.path.relpath(p, root) for p in found) + ["README.md"]
    problems = []

    for page in pages:
        full = os.path.join(root, page)
        text = open(full, encoding="utf-8").read()
        d = os.path.dirname(full)
        for a, b in BLOCKS:
            o = len(re.findall(r"\{%%\s*%s\b(?!\w)" % a, text))
            c = len(re.findall(r"\{%%\s*%s\b" % b, text))
            if o != c:
                problems.append(f"{page}: {a} opened {o} times, closed {c}")
        for link, anchor in set(re.findall(r"\]\(((?:\.\./|\./)?[^)#\s]+\.md)(#[^)]*)?\)", text)):
            target = os.path.normpath(os.path.join(d, link))
            if not os.path.exists(target):
                # A page that exists on the full working branch but is not in this
                # checkout yet is a cross-link to a later PR, not a broken link.
                if pending_root and os.path.exists(os.path.join(pending_root, os.path.relpath(target, root))):
                    pending.append(f"{page}: pending link {link}")
                else:
                    problems.append(f"{page}: broken link {link}")
            elif anchor and anchor[1:] not in headings(target):
                # The anchor may exist in the branch version of a page a later PR rewrites.
                branch_target = pending_root and os.path.join(pending_root, os.path.relpath(target, root))
                if branch_target and os.path.exists(branch_target) and anchor[1:] in headings(branch_target):
                    pending.append(f"{page}: pending anchor {link}{anchor}")
                else:
                    problems.append(f"{page}: missing anchor {link}{anchor}")
        own = headings(full)
        for anchor in set(re.findall(r"\]\((#[^)]+)\)", text)):
            if anchor[1:] not in own:
                problems.append(f"{page}: missing anchor {anchor}")
        for src in re.findall(r'<img src="([^"]+)"', text) + re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
            # GitBook wraps paths with spaces in angle brackets: ![](<../a b.png>)
            src = src.strip("<>")
            if src.startswith("http") or src.startswith("data:"):
                continue
            if strict and not os.path.exists(os.path.normpath(os.path.join(d, src))):
                problems.append(f"{page}: image missing {src}")
        if "—" in text:
            problems.append(f"{page}: em-dash")
        if "superdesk.github.io" in text:
            problems.append(f"{page}: link to the retired docs site")
        if strict:
            for c in re.findall(r"<!--(.*?)-->", text, re.S):
                problems.append(f"{page}: HTML comment left in page: {c.strip()[:60]}")

    for link in re.findall(r"\]\(([^)]+\.md)\)", open(os.path.join(root, "SUMMARY.md"), encoding="utf-8").read()):
        if not os.path.exists(os.path.join(root, link)):
            problems.append(f"SUMMARY.md: missing page {link}")

    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, os.path.join(here, "sync_indexes.py"), root, "--check"], capture_output=True, text=True)
    if r.returncode and not skip_index:
        problems.append("indexes out of date with SUMMARY.md (run sync_indexes.py): " + r.stdout.strip().replace("\n", "; "))

    for p in pending:
        print(p)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s) in {len(pages)} page(s)" + (f", {len(pending)} pending link(s)" if pending else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
