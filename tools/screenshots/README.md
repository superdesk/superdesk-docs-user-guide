# Screenshot styling

Turns raw UI screenshots into documentation images: the screenshot gets optional highlights, rounded corners and a soft drop shadow, and sits on a subtle grey-blue gradient. Only Python 3 and Pillow are needed.

Screenshots are expected at 2x device pixel ratio. All sizes (padding, corner radius, shadow, highlight strokes) are defined in 1x pixels and multiplied by `--scale`, so the output keeps the input's pixel density and stays crisp on retina screens.

## `style.py`: one image

```
python3 style.py <input.png> <output.png> [--highlights highlights.json] [--preset default|wide|dialog] [--scale 2]
```

## `style_all.py`: a whole tree

```
python3 style_all.py <raw-dir> <styled-dir> [--force] [--scale 2]
```

Mirrors `raw/<page-slug>/<shot-name>.png` to `styled/<page-slug>/<shot-name>.png`. Next to each shot, two optional files are picked up:

- `<shot-name>.highlights.json`: highlights, format below.
- `<shot-name>.meta.json`: `{"preset": "dialog"}`.

Outputs newer than their inputs (the PNG, its two JSON files and `style.py` itself) are skipped unless `--force` is given.

## Presets

All presets use the same background gradient; they only differ in padding (1x pixels).

| Preset | Padding | Use for |
| --- | --- | --- |
| `default` | 48 | most shots |
| `dialog` | 72 | small dialogs and popovers |
| `wide` | 32 | full-width shots |

## Highlights

A JSON array; coordinates are in the input image's pixels (2x space for 2x captures). An empty array draws nothing.

```json
[
  {"box": [1160, 140, 200, 60], "label": null, "style": "outline"},
  {"box": [1160, 140, 200, 60], "label": "1", "style": "badge"},
  {"box": [1400, 140, 60, 60], "label": "2", "style": "badge", "center": [1430, 96]}
]
```

- `outline`: a red rounded rectangle around `box`, with a small gap so it does not touch the element.
- `badge`: a red numbered circle on the top-left corner of `box`. Pair it with an `outline` on the same box to get a numbered callout, or use it alone to mark an area. Badges are kept inside the screenshot when the box touches its edge.
- `center` (badges only, optional): `[x, y]` in the same pixel space as `box`. When present the badge is centred there instead of on the box corner, so it can sit outside a small control (above or below it) without covering it. `box` still names the element the badge refers to. Without `center` the behaviour is unchanged.

## Example

```
python3 style.py raw/monitoring/overview.png styled/monitoring/overview.png --highlights raw/monitoring/overview.highlights.json --preset wide
```
