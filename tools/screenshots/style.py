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
# Least space between two neighbouring outlines. Controls closer than twice the
# outline's reach get outlines that grow less on their facing sides.
OUTLINE_SEPARATION = 4
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


def draw_outline(canvas, box, s, grow=None):
    """grow: how far the outline reaches outside box on each side, in 1x pixels
    as (left, top, right, bottom). Left out, it is the gap plus the stroke."""
    x, y, w, h = box
    width = OUTLINE_WIDTH * s
    # Pillow strokes inward from the rectangle, so the stroke is added to the gap.
    reach = OUTLINE_GAP + OUTLINE_WIDTH
    left, top, right, bottom = (g * s for g in (grow or (reach,) * 4))
    rect = (x - left, y - top, x + w + right, y + h + bottom)
    radius = (OUTLINE_RADIUS + min(reach, left / s, top / s, right / s, bottom / s)) * s

    def paint(draw, t):
        draw.rounded_rectangle(
            t(*rect),
            radius=radius * SUPERSAMPLE,
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
    # fully inside the image.
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


def outline_reach(boxes, s, warn=lambda message: None):
    """Per-outline reach (left, top, right, bottom) in 1x pixels. Two outlines
    whose controls are closer than twice the default reach would overlap, so both
    grow less towards each other and keep OUTLINE_SEPARATION between them. When
    even that leaves no room for the stroke, the outlines stay as they are and a
    warning says so: the manifest should box the group as one, or use a badge."""
    reach = OUTLINE_GAP + OUTLINE_WIDTH
    grows = [[reach] * 4 for _ in boxes]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a == b:
                continue
            # Positive gaps in 1x pixels along each axis; negative means overlap.
            gap_x = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2])) / s
            gap_y = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3])) / s
            gap = max(gap_x, gap_y)
            if gap >= 2 * reach + OUTLINE_SEPARATION:
                continue
            if gap < 0:
                warn(f"outlines {i + 1} and {j + 1} overlap; box the group as one or use a badge")
                continue
            # Index of the facing side on a and on b: 0 left, 1 top, 2 right, 3 bottom.
            if gap_x >= gap_y:
                a_side, b_side = (2, 0) if b[0] >= a[0] + a[2] else (0, 2)
            else:
                a_side, b_side = (3, 1) if b[1] >= a[1] + a[3] else (1, 3)
            each = (gap - OUTLINE_SEPARATION) / 2
            if each < OUTLINE_WIDTH:
                warn(f"outlines {i + 1} and {j + 1} have no room between them; box the group as one or use a badge")
                continue
            grows[i][a_side] = min(grows[i][a_side], each)
            grows[j][b_side] = min(grows[j][b_side], each)
    return grows


def draw_highlights(image, highlights, s, origin=(0, 0), warn=lambda message: None):
    """Draw highlights on image. Boxes are in screenshot pixels; origin is where
    the screenshot's top-left corner sits on image."""
    ox, oy = origin
    outlines = [item for item in highlights if item.get("style", "outline") == "outline"]
    grows = outline_reach([tuple(item["box"]) for item in outlines], s, warn)
    for item in highlights:
        x, y, w, h = item["box"]
        box, kind = (x + ox, y + oy, w, h), item.get("style", "outline")
        center = item.get("center")
        if center is not None:
            center = (center[0] + ox, center[1] + oy)
        if kind == "badge":
            draw_badge(image, box, item.get("label"), s, center)
        elif kind == "outline":
            draw_outline(image, box, s, grows[outlines.index(item)])
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


def style_screenshot(image, highlights=(), preset="default", scale=2, warn=lambda message: None):
    s = scale
    shot = image.convert("RGBA")

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

    # Highlights go on last, in canvas space: an outline around an element that
    # touches the screenshot's edge extends into the padding. Drawn on the
    # screenshot itself it would be cut off at that edge and by the rounded corners.
    canvas = canvas.convert("RGBA")
    draw_highlights(canvas, highlights, s, position, warn)
    return canvas.convert("RGB")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Style a raw screenshot for the user guide.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--highlights", help="JSON file with highlight boxes in input pixel space")
    parser.add_argument("--preset", choices=sorted(PADDING), default="default")
    parser.add_argument("--scale", type=float, default=2, help="device pixel ratio of the input (default 2)")
    args = parser.parse_args(argv)

    with Image.open(args.input) as image:
        result = style_screenshot(
            image,
            load_highlights(args.highlights),
            args.preset,
            args.scale,
            warn=lambda message: print(f"warning: {message}", file=sys.stderr),
        )
    result.save(args.output, "PNG", optimize=True)


if __name__ == "__main__":
    sys.exit(main())
