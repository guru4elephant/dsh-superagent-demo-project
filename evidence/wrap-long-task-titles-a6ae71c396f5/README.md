# Evidence — long task titles wrap inside the list item

Issue: [#20](https://github.com/guru4elephant/dsh-superagent-demo-project/issues/20)

The change is one CSS declaration, `overflow-wrap: anywhere` on `.task-list li`.
An unbroken title wider than the item could not break at all, so the item — and
the document — grew to the title's full width and the page scrolled horizontally.

| scenario | baseline `main` @ `6fb944c` | changed `agent/wrap-long-task-titles-a6ae71c396f5` @ `7209d83` |
| --- | --- | --- |
| 500-char unbroken title, 375px viewport | scrollWidth 5189px, horizontal scroll **yes**, item overflows its box | scrollWidth 375px, **no** horizontal scroll, item 512px tall / 22 line boxes |
| 500-char unbroken title, 1280px viewport | scrollWidth 5189px, horizontal scroll **yes** | scrollWidth 1280px, **no** horizontal scroll, item 248px tall / 10 line boxes |
| 200-char unbroken title, 375 / 1280px | 2157px, horizontal scroll **yes** | 375px / 1280px, **no** horizontal scroll, 10 / 5 line boxes |
| 400-char URL, 375 / 1280px | 3829px, horizontal scroll **yes** | 375px / 1280px, **no** horizontal scroll, 17 / 8 line boxes |
| normal short titles | 1 line, panel 327px / 606px | pixel-identical captures at both viewports |

Scenario on both sides: `localStorage` is cleared, the title(s) are submitted
through the real form, then metrics are read and the viewport is captured.
Mobile captures are 375×812, desktop captures 1280×800, light theme, no hover or
focus state. The dark theme was measured as well and gives the same numbers
(see `results.json`), because the fix is a line-breaking property rather than a
colour.

## Files

- `raw/baseline-*.png`, `raw/after-*.png` — the same scenario at both revisions
- `comparison-*.png` — labelled side-by-side sheets with the measured
  `scrollWidth` vs viewport width under each capture
- `results.json` — raw script output: document/panel widths, per-item scroll and
  client widths, line-box counts, computed `overflow-wrap`, and the short-title
  pixel-diff bounding box per viewport and theme
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

- Horizontal scroll is measured (`document.documentElement.scrollWidth >
  clientWidth`), not inferred from the CSS.
- The baseline run is the negative control: the same probe reports
  `overflow-wrap: normal` and a 5189px document there.
- Line counts come from `Range.getClientRects()`, so they are line boxes actually
  laid out, not an estimate from string length.
- The short-title scenario is captured on both revisions; the pixel diff is `null`
  (no differing pixels) at both viewports, confirming normal titles still render
  exactly as before.
