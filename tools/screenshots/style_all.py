#!/usr/bin/env python3
"""Style every raw/<page-slug>/<shot-name>.png into styled/<page-slug>/<shot-name>.png.

Per shot, the optional <shot-name>.highlights.json is applied and the optional
<shot-name>.meta.json ({"preset": "..."}) selects the background preset.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

import style


def sidecar(png, suffix):
    path = png.with_name(png.stem + suffix)
    return path if path.exists() else None


def read_preset(meta_path):
    if not meta_path:
        return "default"
    with open(meta_path, encoding="utf-8") as f:
        preset = json.load(f).get("preset", "default")
    if preset not in style.PADDING:
        raise ValueError(f"{meta_path}: unknown preset {preset!r}")
    return preset


def is_up_to_date(output, inputs):
    if not output.exists():
        return False
    newest_input = max(path.stat().st_mtime for path in inputs)
    return output.stat().st_mtime > newest_input


def style_tree(raw_dir, styled_dir, scale, force):
    # A change to the styling code invalidates every output, like a changed input.
    style_source = Path(style.__file__)
    done = skipped = 0
    for png in sorted(raw_dir.rglob("*.png")):
        highlights_path = sidecar(png, ".highlights.json")
        meta_path = sidecar(png, ".meta.json")
        output = styled_dir / png.relative_to(raw_dir)
        inputs = [p for p in (png, highlights_path, meta_path, style_source) if p]
        if not force and is_up_to_date(output, inputs):
            skipped += 1
            continue

        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(png) as image:
            result = style.style_screenshot(
                image, style.load_highlights(highlights_path), read_preset(meta_path), scale
            )
        result.save(output, "PNG", optimize=True)
        print(f"styled {output}")
        done += 1
    print(f"{done} styled, {skipped} up to date")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Style a tree of raw screenshots.")
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("styled_dir", type=Path)
    parser.add_argument("--scale", type=float, default=2, help="device pixel ratio of the inputs (default 2)")
    parser.add_argument("--force", action="store_true", help="restyle even when outputs are up to date")
    args = parser.parse_args(argv)
    if not args.raw_dir.is_dir():
        parser.error(f"{args.raw_dir} is not a directory")
    style_tree(args.raw_dir, args.styled_dir, args.scale, args.force)


if __name__ == "__main__":
    sys.exit(main())
