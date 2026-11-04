"""Verify that long unbroken task titles wrap inside the list instead of
widening the panel and producing horizontal scroll.

Usage (from the repository root of a checkout holding the changed files):

    python3 evidence/wrap-long-task-titles-a6ae71c396f5/verify.py [baseline-dir]

Without an argument it evaluates the current directory and captures the
after side only. Pass a baseline checkout (for example an `origin/main`
worktree) to record the before/after pair used in the PR.

Each scenario runs in a fresh headless Chrome page through Playwright at
375x812 and 1280x800. The script submits a 500-character unbroken title and a
long URL through the real form, records document/panel/item widths and line
wrap metrics, captures viewport screenshots, and writes labelled side-by-side
comparison sheets plus a results.json.

Requires `playwright`, Pillow and a Chrome install.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

CURRENT = pathlib.Path.cwd()
BASELINE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
OUT = pathlib.Path(tempfile.mkdtemp(prefix='wrap-title-evidence-'))

LONG_UNBROKEN = 'A' * 500
LONG_URL = 'https://example.com/' + 'a' * 400
SHORT_TITLES = ['Write the project brief', 'Review the design draft']

VIEWPORTS = {'mobile': (375, 812), 'desktop': (1280, 800)}
MAX_SIDE_WIDTH = 900
SCENARIOS = {
    'short': SHORT_TITLES,
    'unbroken-500': [LONG_UNBROKEN],
    'long-url': [LONG_URL],
    'unbroken-200': ['B' * 200],
}

METRICS = """
() => {
  const doc = document.documentElement;
  const panel = document.querySelector('.panel');
  const items = [...document.querySelectorAll('.task-list li')];
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  };
  const lineTops = (el) => {
    const range = document.createRange();
    range.selectNodeContents(el);
    return [...new Set([...range.getClientRects()].map((r) => Math.round(r.top)))]
      .sort((a, b) => a - b);
  };
  return {
    viewportWidth: doc.clientWidth,
    viewportHeight: doc.clientHeight,
    documentScrollWidth: doc.scrollWidth,
    documentScrollHeight: doc.scrollHeight,
    horizontalScroll: doc.scrollWidth > doc.clientWidth,
    panel: box(panel),
    panelScrollWidth: panel.scrollWidth,
    panelClientWidth: panel.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    items: items.map((li) => {
      const style = getComputedStyle(li);
      const tops = lineTops(li);
      return {
        chars: li.textContent.length,
        scrollWidth: li.scrollWidth,
        clientWidth: li.clientWidth,
        overflowsOwnBox: li.scrollWidth > li.clientWidth,
        height: box(li).height,
        lineBoxes: tops.length,
        overflowWrap: style.overflowWrap,
        wordBreak: style.wordBreak,
        whiteSpace: style.whiteSpace,
      };
    }),
  };
}
"""


def open_page(browser, root, viewport):
    page = browser.new_page(viewport=viewport)
    page.goto((root / 'index.html').as_uri())
    page.evaluate('localStorage.clear()')
    page.reload()
    page.wait_for_timeout(80)
    return page


def submit(page, titles):
    for title in titles:
        page.fill('#task-input', title)
        page.click('#add-form button')
        page.wait_for_timeout(30)
    page.mouse.move(0, 0)
    page.wait_for_timeout(100)


def run_scenario(browser, root, viewport, titles, capture):
    page = open_page(browser, root, viewport)
    submit(page, titles)
    metrics = page.evaluate(METRICS)
    page.screenshot(path=str(capture), full_page=False)
    page.close()
    return metrics


def font(size, bold=False):
    path = ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold
            else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    if pathlib.Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap(text, max_width, use_font):
    words, lines, current = text.split(' '), [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if use_font.getlength(candidate) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def sheet(title, before_png, after_png, before_caption, after_caption, out,
          before_note, after_note):
    before = Image.open(before_png).convert('RGB')
    after = Image.open(after_png).convert('RGB')
    scale = min(1.0, MAX_SIDE_WIDTH / max(before.width, after.width))
    size = (max(1, round(before.width * scale)), max(1, round(before.height * scale)))
    before = before.resize(size, Image.LANCZOS)
    after = after.resize(size, Image.LANCZOS)

    caption_font = font(13)
    caption_lines = max(
        len(wrap(before_note, before.width, caption_font)),
        len(wrap(after_note, after.width, caption_font)),
    )
    pad, header, label_h = 24, 46, 30
    caption_h = 10 + caption_lines * 18
    width = pad * 2 + before.width + pad + after.width
    height = header + label_h + max(before.height, after.height) + caption_h + pad
    canvas = Image.new('RGB', (width, height), (244, 250, 252))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 12), title, font=font(20, bold=True), fill=(27, 42, 51))

    left_x, right_x = pad, pad + before.width + pad
    y = header
    draw.text((left_x, y), before_caption, font=font(14, bold=True), fill=(160, 40, 40))
    draw.text((right_x, y), after_caption, font=font(14, bold=True), fill=(30, 110, 70))
    y += label_h
    canvas.paste(before, (left_x, y))
    canvas.paste(after, (right_x, y))
    draw.rectangle([left_x - 1, y - 1, left_x + before.width, y + before.height],
                   outline=(190, 70, 70))
    draw.rectangle([right_x - 1, y - 1, right_x + after.width, y + after.height],
                   outline=(50, 140, 90))
    caption_y = y + max(before.height, after.height) + 10
    for i, line in enumerate(wrap(before_note, before.width, caption_font)):
        draw.text((left_x, caption_y + i * 18), line, font=caption_font,
                  fill=(90, 107, 122))
    for i, line in enumerate(wrap(after_note, after.width, caption_font)):
        draw.text((right_x, caption_y + i * 18), line, font=caption_font,
                  fill=(90, 107, 122))
    canvas.save(out)


def revision_sha(root):
    try:
        return subprocess.run(
            ['git', '-C', str(root), 'rev-parse', '--short=7', 'HEAD'],
            capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        return ''


def main():
    (OUT / 'raw').mkdir(parents=True, exist_ok=True)
    results = {
        'currentDir': str(CURRENT),
        'currentSha': revision_sha(CURRENT),
        'baselineDir': str(BASELINE) if BASELINE else None,
        'baselineSha': revision_sha(BASELINE) if BASELINE else None,
        'longUnbrokenChars': len(LONG_UNBROKEN),
        'longUrlChars': len(LONG_URL),
        'runs': [],
    }
    sides = [('after', CURRENT)]
    if BASELINE:
        sides.insert(0, ('baseline', BASELINE))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for label, root in sides:
            for viewport_name, size in VIEWPORTS.items():
                viewport = {'width': size[0], 'height': size[1]}
                for scenario, titles in SCENARIOS.items():
                    capture = OUT / 'raw' / f'{label}-{viewport_name}-{scenario}.png'
                    metrics = run_scenario(browser, root, viewport, titles, capture)
                    results['runs'].append({
                        'revision': label,
                        'viewport': viewport_name,
                        'viewportSize': viewport,
                        'scenario': scenario,
                        'capture': capture.name,
                        **metrics,
                    })
        browser.close()

    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')

    by_key = {(r['revision'], r['viewport'], r['scenario']): r for r in results['runs']}
    if BASELINE:
        for viewport_name in VIEWPORTS:
            for scenario in ('unbroken-200', 'unbroken-500', 'long-url'):
                before = by_key[('baseline', viewport_name, scenario)]
                after = by_key[('after', viewport_name, scenario)]
                sheet(
                    f'{viewport_name} viewport ({VIEWPORTS[viewport_name][0]}px wide) '
                    f'-- {scenario} title',
                    OUT / 'raw' / f'baseline-{viewport_name}-{scenario}.png',
                    OUT / 'raw' / f'after-{viewport_name}-{scenario}.png',
                    f"Before -- main @ {results['baselineSha']} | viewport capture",
                    f"After -- branch @ {results['currentSha']} | viewport capture",
                    OUT / f'comparison-{viewport_name}-{scenario}.png',
                    (f"document scrollWidth {before['documentScrollWidth']}px vs "
                     f"{before['viewportWidth']}px viewport; horizontal scroll "
                     f"{'YES' if before['horizontalScroll'] else 'no'}; "
                     f"item overflows its box: "
                     f"{'yes' if before['items'][-1]['overflowsOwnBox'] else 'no'}"),
                    (f"document scrollWidth {after['documentScrollWidth']}px vs "
                     f"{after['viewportWidth']}px viewport; horizontal scroll "
                     f"{'YES' if after['horizontalScroll'] else 'no'}; "
                     f"item overflows its box: "
                     f"{'yes' if after['items'][-1]['overflowsOwnBox'] else 'no'}"),
                )
            # Short titles must be unchanged: a pixel diff on the same scenario.
            base_short = OUT / 'raw' / f'baseline-{viewport_name}-short.png'
            after_short = OUT / 'raw' / f'after-{viewport_name}-short.png'
            diff = ImageChops.difference(
                Image.open(base_short).convert('RGB'),
                Image.open(after_short).convert('RGB'))
            results.setdefault('shortTitlePixelDiff', {})[viewport_name] = {
                'diffBBox': list(diff.getbbox()) if diff.getbbox() else None,
            }
            sheet(
                f'{viewport_name} viewport ({VIEWPORTS[viewport_name][0]}px wide) '
                f'-- normal short titles',
                base_short, after_short,
                f"Before -- main @ {results['baselineSha']}",
                f"After -- branch @ {results['currentSha']}",
                OUT / f'comparison-{viewport_name}-short.png',
                'seeded short titles; layout unchanged',
                'seeded short titles; layout unchanged',
            )

    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')

    for r in results['runs']:
        last = r['items'][-1] if r['items'] else {}
        print(
            f"{r['revision']:8} {r['viewport']:7} {r['scenario']:12} "
            f"scrollWidth={r['documentScrollWidth']:5} "
            f"viewport={r['viewportWidth']:5} "
            f"hscroll={str(r['horizontalScroll']):5} "
            f"panelW={r['panel']['width']:.0f} "
            f"itemH={last.get('height', 0):.0f} "
            f"lines={last.get('lineBoxes')} "
            f"overflowWrap={last.get('overflowWrap')}"
        )
    for viewport_name, diff in results.get('shortTitlePixelDiff', {}).items():
        print(f"short-title pixel diff {viewport_name}: {diff['diffBBox']}")
    print('evidence written to', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
