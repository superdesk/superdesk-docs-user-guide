#!/usr/bin/env python3
"""Turn a raw UI screenshot into a documentation image.

The screenshot gets optional highlights, rounded corners and a soft drop
shadow, and is placed on a subtle gradient background. Sizes below are in
1x (CSS) pixels and get multiplied by --scale, the device pixel ratio the
screenshot was captured at.
"""

import argparse
import json
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ACCENT = (224, 69, 63)  # #e0453f
GRADIENT = ((0xEE, 0xF1, 0xF5), (0xDF, 0xE5, 0xEC))  # top-left -> bottom-right
PADDING = {"default": 48, "dialog": 72, "wide": 32}

CORNER_RADIUS = 12
SHADOW_OFFSET = 10
SHADOW_BLUR = 14
SHADOW_OPACITY = 0.35
# A tight, faint shadow that separates white UI edges from the light background.
CONTACT_SHADOW_BLUR = 1.5
CONTACT_SHADOW_OPACITY = 0.14

OUTLINE_WIDTH = 3
OUTLINE_GAP = 6
OUTLINE_RADIUS = 8
BADGE_RADIUS = 14
BADGE_RING = 2
BADGE_FONT_SIZE = 15

# Pillow's drawing primitives are not anti-aliased, so shapes are drawn this
# many times larger and downsampled.
SUPERSAMPLE = 4

FONT_CANDIDATES = [
    ("/System/Library/Fonts/Helvetica.ttc", 1),  # index 1 is Helvetica Bold
    ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0),
    ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 0),
]


def load_font(size):
    for path, index in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def load_highlights(path):
    if not path:
        return []
    with open(path, encoding="utf-8") as f:
        highlights = json.load(f)
    if not isinstance(highlights, list):
        raise ValueError(f"{path}: expected a JSON array of highlights")
    return highlights


def draw_supersampled(canvas, bounds, paint):
    """Run paint(draw, transform) on an enlarged overlay covering bounds, then
    downsample it and composite it onto canvas (RGBA) for smooth edges."""
    left, top, right, bottom = (round(v) for v in bounds)
    left, top = max(left, 0), max(top, 0)
    right, bottom = min(right, canvas.width), min(bottom, canvas.height)
    if right <= left or bottom <= top:
        return
    size = ((right - left) * SUPERSAMPLE, (bottom - top) * SUPERSAMPLE)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))

    def transform(*values):
        # Even positions are x, odd positions are y.
        return [(v - (left if i % 2 == 0 else top)) * SUPERSAMPLE for i, v in enumerate(values)]

    paint(ImageDraw.Draw(overlay), transform)
    overlay = overlay.resize((right - left, bottom - top), Image.LANCZOS)
    canvas.alpha_composite(overlay, (left, top))


def draw_outline(canvas, box, s):
    x, y, w, h = box
    width = OUTLINE_WIDTH * s
    # Pillow strokes inward from the rectangle, so the stroke is added to the gap.
    grow = (OUTLINE_GAP + OUTLINE_WIDTH) * s
    rect = (x - grow, y - grow, x + w + grow, y + h + grow)

    def paint(draw, t):
        draw.rounded_rectangle(
            t(*rect),
            radius=(OUTLINE_RADIUS + OUTLINE_GAP + OUTLINE_WIDTH) * s * SUPERSAMPLE,
            outline=ACCENT,
            width=round(width * SUPERSAMPLE),
        )

    draw_supersampled(canvas, (rect[0] - 2, rect[1] - 2, rect[2] + 2, rect[3] + 2), paint)


def draw_badge(canvas, box, label, s, center=None):
    x, y = box[0], box[1]
    radius, ring = BADGE_RADIUS * s, BADGE_RING * s
    outer = radius + ring
    # By default the badge sits on the top-left corner of an outline drawn around
    # the same box. An explicit centre (input pixels) places it anywhere, for
    # example outside a control so it does not cover it. Either way it is kept
    # fully inside the screenshot so the frame does not clip it.
    if center is not None:
        cx, cy = center
    else:
        corner = (OUTLINE_GAP + OUTLINE_WIDTH / 2) * s
        cx, cy = x - corner, y - corner
    cx = min(max(cx, outer), canvas.width - outer)
    cy = min(max(cy, outer), canvas.height - outer)

    def paint(draw, t):
        draw.ellipse(t(cx - outer, cy - outer, cx + outer, cy + outer), fill=(255, 255, 255))
        draw.ellipse(t(cx - radius, cy - radius, cx + radius, cy + radius), fill=ACCENT)

    draw_supersampled(canvas, (cx - outer - 2, cy - outer - 2, cx + outer + 2, cy + outer + 2), paint)

    if label is None or str(label) == "":
        return
    # Text is drawn at final size: FreeType anti-aliases glyphs on its own.
    text = str(label)
    font = load_font(round(BADGE_FONT_SIZE * s))
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (left + right) / 2, cy - (top + bottom) / 2), text, font=font, fill=(255, 255, 255))


def draw_highlights(image, highlights, s):
    for item in highlights:
        box, kind = item["box"], item.get("style", "outline")
        if kind == "badge":
            draw_badge(image, box, item.get("label"), s, item.get("center"))
        elif kind == "outline":
            draw_outline(image, box, s)
        else:
            raise ValueError(f"unknown highlight style {kind!r}")


def rounded_mask(size, radius):
    big = Image.new("L", (size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, big.width - 1, big.height - 1), radius=radius * SUPERSAMPLE, fill=255
    )
    return big.resize(size, Image.LANCZOS)


def gradient_background(size):
    ramp = Image.linear_gradient("L")  # 256x256, black at the top
    vertical = ramp.resize(size, Image.BILINEAR)
    horizontal = ramp.transpose(Image.Transpose.ROTATE_90).resize(size, Image.BILINEAR)
    diagonal = ImageChops.add(horizontal, vertical, scale=2.0)
    start = Image.new("RGB", size, GRADIENT[0])
    end = Image.new("RGB", size, GRADIENT[1])
    return Image.composite(end, start, diagonal)


def shadow_layer(canvas_size, mask, position, offset, blur, opacity):
    layer = Image.new("L", canvas_size, 0)
    layer.paste(mask.point(lambda v: round(v * opacity)), (position[0], position[1] + round(offset)))
    return layer.filter(ImageFilter.GaussianBlur(blur))


def style_screenshot(image, highlights=(), preset="default", scale=2):
    s = scale
    shot = image.convert("RGBA")
    draw_highlights(shot, highlights, s)

    mask = rounded_mask(shot.size, CORNER_RADIUS * s)
    shot.putalpha(ImageChops.multiply(shot.getchannel("A"), mask))

    pad = round(PADDING[preset] * s)
    canvas_size = (shot.width + 2 * pad, shot.height + 2 * pad)
    canvas = gradient_background(canvas_size)

    position = (pad, pad)
    for offset, blur, opacity in (
        (SHADOW_OFFSET * s, SHADOW_BLUR * s, SHADOW_OPACITY),
        (0.5 * s, CONTACT_SHADOW_BLUR * s, CONTACT_SHADOW_OPACITY),
    ):
        shadow = shadow_layer(canvas_size, mask, position, offset, blur, opacity)
        canvas = Image.composite(Image.new("RGB", canvas_size, (20, 28, 40)), canvas, shadow)

    canvas.paste(shot, position, shot)
    return canvas


def main(argv=None):
    parser = argparse.ArgumentParser(description="Style a raw screenshot for the user guide.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--highlights", help="JSON file with highlight boxes in input pixel space")
    parser.add_argument("--preset", choices=sorted(PADDING), default="default")
    parser.add_argument("--scale", type=float, default=2, help="device pixel ratio of the input (default 2)")
    args = parser.parse_args(argv)

    with Image.open(args.input) as image:
        result = style_screenshot(image, load_highlights(args.highlights), args.preset, args.scale)
    result.save(args.output, "PNG", optimize=True)


if __name__ == "__main__":
    sys.exit(main())
