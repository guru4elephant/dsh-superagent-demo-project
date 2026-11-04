# Evidence — long task titles wrap inside the list item

Issue: [#20](https://github.com/guru4elephant/dsh-superagent-demo-project/issues/20)

The change is a single CSS declaration, `overflow-wrap: anywhere` on
`.task-list li`. An unbroken title longer than the item could previously not
break at all, so the item — and the whole document — grew to the title's full
width and the page scrolled horizontally.

| | baseline `main` @ `6fb944c` | changed `agent/wrap-long-task-titles-a6ae71c396f5` @ `7209d83` |
| --- | --- | --- |
| 500-char unbroken title, 375px viewport | document scrollWidth 5189px, horizontal scroll **yes**, item overflows its box | document scrollWidth 375px, horizontal scroll **no**, item 512px tall / 22 line boxes |
| 200-char unbroken title, 375px viewport | 2157px, horizontal scroll **yes** | 375px, horizontal scroll **no**, 248px tall / 10 line boxes |
| 400-char URL, 375px viewport | 3829px, horizontal scroll **yes** | 375px, horizontal scroll **no**, 402px tall / 17 line boxes |
| 500-char unbroken title, 1280px viewport | 5189px, horizontal scroll **yes** | 1280px, horizontal scroll **no**, 248px tall / 10 line boxes |
| normal short titles | seeded, 1 line, panel 327px / 606px | pixel-identical to baseline at both viewports |
| `.panel` width | 327px (mobile) / 606px (desktop) | unchanged |

Scenario on both sides: the page is loaded with `localStorage` cleared, the
title(s) are submitted through the real form, then metrics are read and the
viewport is captured. Mobile captures are 375×812, desktop captures 1280×800,
light theme (the host browser's `prefers-color-scheme` is light), no hover or
focus state.

## Files

- `raw/baseline-*.png` / `raw/after-*.png` — the same scenario at both revisions
- `comparison-*.png` — labelled side-by-side sheets with the measured
  `scrollWidth` vs viewport width under each capture
- `results.json` — raw script output: document and panel widths, per-item
  scroll/client width, line-box counts, computed `overflow-wrap`, pixel-diff
  bounding box for the short-title scenario
- `verify.py` — the script that produced all of the above

## Reproducing

From a checkout of this branch (or the PR head):

```bash
git worktree add /tmp/task-board-before 6fb944c
python3 evidence/wrap-long-task-titles-a6ae71c396f5/verify.py /tmp/task-board-before
```

Without the baseline argument the script records the after side only. It writes
captures and `results.json` to a fresh temporary directory and prints the path.
It needs `playwright`, Pillow and a Chrome/Chromium install.

## Notes on the check

- Horizontal scroll is the measured fact (`document.documentElement.scrollWidth
  > clientWidth`), not an inspection of the CSS.
- The baseline run doubles as a negative control: the same probe finds
  `overflow-wrap: normal` and a 5189px document there.
- The short-title scenario is captured and measured on both revisions; the pixel
  diff is `null` (no differing pixels), confirming normal titles still render
  exactly as before.
- Line counts come from `Range.getClientRects()`, so they are line boxes actually
  laid out, not a guess from string length.
