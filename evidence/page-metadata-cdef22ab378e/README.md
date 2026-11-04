# Evidence: favicon, meta description and social-card tags (#24)

- Baseline: `main` @ `63531db`
- Changed revision: `agent/add-page-metadata-cdef22ab378e` @ `cc8feb7`

Captured from the real page served over HTTP from a local checkout of each revision, in
Chrome 143.0.7499.192 (playwright, `channel=chrome`, headed, Xvfb; the same browser build,
window size, viewport, colour scheme and default two-task state for both sides of each pair).

| File | What it shows |
| --- | --- |
| `01-tab-favicon-before-after.png` | Chrome tab strip, two tabs, 4x zoom. Before: generic page icon. After: the blue inline SVG icon in both tabs. |
| `02-favicon-zoom.png` | The 16x16 tab icon slot at 16x zoom, before and after. |
| `03-share-preview.png` | Link-preview card drawn from the tags each revision's `<head>` actually parses to. Before: bare URL, no description. After: title, description and icon. |
| `04-page-unchanged.png` | Full page render, both revisions. Byte-identical — the edit is head-only. |

## Measured results

- Headed Chrome, server-side request log: `GET /favicon.ico` → **404** on the baseline;
  **no favicon request at all** after the change (the browser uses the declared `data:` URI).
  The live GitHub Pages site also answers `/favicon.ico` with 404 today.
- Parsed `<head>` after the change adds: `meta[name=description]`, `og:type`, `og:title`,
  `og:description`, `og:url`, `twitter:card`, `twitter:title`, `twitter:description`, and one
  `link[rel=icon]` whose href is a `data:image/svg+xml` URI. The pre-existing `viewport` tag
  from #41 is untouched.
- Tab-strip diff is confined to the two 16x16 favicon slots (bbox `x 58-311, y 22-37`);
  nothing else in the tab band changes.
- Full-page renders at 1280x760: 0 differing pixels, identical md5.
- CI's local asset regex only matches `href`/`src` values without `:` and therefore ignores the
  `data:` URI; the repository CI steps (file existence, HTML structure/assets, `node --check`,
  CSS brace balance, typo check) all pass locally.
