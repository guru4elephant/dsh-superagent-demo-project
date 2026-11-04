# Evidence — task additions announced to assistive technology

Issue: [#16](https://github.com/guru4elephant/dsh-superagent-demo-project/issues/16)

The change is an `aria-live` status region, which is invisible by design, so the
page captures below are pixel-identical before and after. What changed is how the
page behaves for assistive technology, which these captures record from Chrome's
accessibility tree.

| | baseline `main` @ `47fcf86` | changed `agent/announce-task-updates-5ad0993a3e03` @ `580357e` |
| --- | --- | --- |
| status role in the accessibility tree | none | `role=status`, `live=polite`, `atomic=true`, `relevant=additions text` |
| messages received after three quick additions | none | `Added "Buy milk". 3 tasks in the list.` / `Added "Call the dentist". 4 tasks in the list.` / `Added "Ship the release notes". 5 tasks in the list.` |
| visual layout | — | unchanged: 1×1 clipped region, `clip-path: inset(50%)` |

Scenario on both sides: 1280×800, light theme, the two seeded tasks, then
"Buy milk", "Call the dentist" and "Ship the release notes" submitted in quick
succession. Mobile captures use 390×844 with the same steps.

## Files

- `before-desktop.png`, `after-desktop.png` — the same DOM state, both revisions
- `before-mobile.png`, `after-mobile.png` — same at 390×844
- `comparison-desktop.png`, `comparison-mobile.png` — labelled side-by-side sheets
  that pair each capture with the accessibility tree for that page
- `results.json` — raw script output: status-region mutations with timestamps,
  accessibility-tree nodes, computed CSS and list contents
- `verify.py` — the script that produced all of the above

## Reproducing

From a checkout that contains the changed files:

```bash
python3 evidence/announce-task-updates-5ad0993a3e03/verify.py
```

Pass a baseline checkout as the first argument to also record the before side:

```bash
git worktree add /tmp/task-board-before origin/main
python3 evidence/announce-task-updates-5ad0993a3e03/verify.py /tmp/task-board-before
```

The script writes its captures and `results.json` to a fresh temporary directory
and prints the path. It needs `playwright` and a Chrome or Chromium install.

## Notes on the check

- `verify.py` records a `MutationObserver` on the candidate status region, so the
  "messages received" column is the text assistive technology is handed, not the
  text the script assumes was set.
- The baseline run doubles as a negative control: the same probe finds no status
  region and observes no mutations there.
- The list itself is deliberately not a live region, because `render()` rebuilds
  every row on each addition and a list-level live region would replay the whole
  list on every change.
