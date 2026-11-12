#!/usr/bin/env python3
"""Regenerate the hand-kept page lists from SUMMARY.md.

SUMMARY.md is the one source of truth for which pages exist. Two other places
repeat that list and drift when a page is added: the "In this section" list on
every section README, and the "Browse by topic" list on the landing README.
This script rewrites both from SUMMARY.md. With --check it only reports whether
anything would change and exits 1 if so, which is what the PR gate uses.

Usage: python3 sync_indexes.py <docs-repo-root> [--check]
"""
import os
import re
import sys

IN_SECTION_RE = re.compile(r"^#{2,4} In this section\s*$", re.M)
BROWSE = "### Browse by topic"
BROWSE_END = "### Additional resources"


def parse_summary(root):
    """Return the tree as nested dicts: {title, path, children}."""
    tree = []
    stack = [(-1, {"children": tree})]
    for line in open(os.path.join(root, "SUMMARY.md"), encoding="utf-8"):
        m = re.match(r"^(\s*)\* \[(.+?)\]\((.+?)\)\s*$", line)
        if not m:
            continue
        depth = len(m.group(1)) // 2
        node = {"title": m.group(2).replace("\\\\-", "-").replace("\\-", "-"), "path": m.group(3), "children": []}
        while stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1]["children"].append(node)
        stack.append((depth, node))
    return tree[0]["children"] if tree and tree[0]["path"] == "README.md" else tree


def rel(from_path, to_path):
    return os.path.relpath(to_path, os.path.dirname(from_path)).replace(os.sep, "/")


def bullets(nodes, from_path, indent=0):
    out = []
    for n in nodes:
        out.append("  " * indent + f"* [{n['title']}]({rel(from_path, n['path'])})")
        out.extend(bullets(n["children"], from_path, indent + 1))
    return out


def replace_block(text, start_marker, end_markers, body):
    if isinstance(start_marker, str):
        start = text.find(start_marker)
        body_start = start + len(start_marker)
    else:
        m = start_marker.search(text)
        start = m.start() if m else -1
        body_start = m.end() if m else -1
    if start < 0:
        return None
    end = len(text)
    for em in end_markers:
        i = text.find(em, body_start)
        if i >= 0:
            end = min(end, i)
    return text[:body_start] + "\n\n" + "\n".join(body) + "\n\n" + text[end:]


def section_readme_body(node):
    return bullets(node["children"], node["path"])


def landing_body(tree):
    out = []
    for n in tree:
        out.append(f"#### {n['title']}")
        out.append("")
        if n["children"]:
            out.extend(bullets(n["children"], "README.md"))
        else:
            out.append(f"* [{n['title']}]({n['path']})")
        out.append("")
    return out[:-1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    root = args[0] if args else "."
    tree = parse_summary(root)
    changed = []

    def write(path, new):
        full = os.path.join(root, path)
        old = open(full, encoding="utf-8").read()
        if new is None:
            print(f"warning: marker not found in {path}")
            return
        new = re.sub(r"\n{3,}", "\n\n", new).rstrip("\n") + "\n"
        if new != old:
            changed.append(path)
            if not check:
                open(full, "w", encoding="utf-8").write(new)

    for n in tree:
        if n["children"] and n["path"].endswith("README.md"):
            text = open(os.path.join(root, n["path"]), encoding="utf-8").read()
            write(n["path"], replace_block(text, IN_SECTION_RE, ["\n### ", "\n## "], section_readme_body(n)))
    text = open(os.path.join(root, "README.md"), encoding="utf-8").read()
    write("README.md", replace_block(text, BROWSE, [BROWSE_END], landing_body(tree)))

    for p in changed:
        print(("would update " if check else "updated ") + p)
    if not changed:
        print("indexes match SUMMARY.md")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
