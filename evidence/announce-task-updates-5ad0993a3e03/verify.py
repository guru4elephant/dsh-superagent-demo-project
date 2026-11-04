"""Verify that task additions are announced to assistive technology.

Usage (from the repository root of a checkout holding the changed files):

    python3 evidence/announce-task-updates-5ad0993a3e03/verify.py [baseline-dir]

Without an argument it evaluates the current directory and captures evidence
only. Pass a baseline checkout (for example an `origin/main` worktree) to record
the before/after pair used in the PR.

Each page runs in headless Chrome through Playwright; the script records every
mutation of the status region and dumps the relevant parts of Chrome's
accessibility tree. Requires `playwright` plus a Chrome install.
"""
import json
import pathlib
import sys
import tempfile

from playwright.sync_api import sync_playwright

REPO = pathlib.Path.cwd()
BASELINE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
OUT = pathlib.Path(tempfile.mkdtemp(prefix='announce-evidence-'))

# Track every mutation of the candidate live region, so the evidence reflects
# what assistive technology actually receives.
PROBE = """
() => {
  window.__announcements = [];
  const status = document.getElementById('status');
  if (!status) return { hasRegion: false };
  new MutationObserver(() => window.__announcements.push({
    text: status.textContent, at: performance.now(),
  })).observe(status, { childList: true, characterData: true, subtree: true });
  return { hasRegion: true, role: status.getAttribute('role'),
           ariaLive: status.getAttribute('aria-live') };
}
"""

ADD_TASK = """
async (title) => {
  const input = document.getElementById('task-input');
  input.value = title;
  document.getElementById('add-form').dispatchEvent(
    new Event('submit', { bubbles: true, cancelable: true })
  );
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
}
"""


def snapshot_tree(page):
    """Return the interesting parts of Chrome's accessibility tree."""
    client = page.context.new_cdp_session(page)
    client.send('Accessibility.enable')
    nodes = []
    for node in client.send('Accessibility.getFullAXTree')['nodes']:
        role = node.get('role', {}).get('value')
        if role in ('status', 'list', 'listitem', 'paragraph', 'textbox',
                    'button', 'heading'):
            props = {}
            for prop in node.get('properties', []):
                if prop.get('name') in ('live', 'atomic', 'relevant', 'busy', 'level'):
                    props[prop['name']] = prop.get('value', {}).get('value')
            nodes.append({'role': role,
                          'name': (node.get('name') or {}).get('value'),
                          'ignored': node.get('ignored', False),
                          'properties': props})
    return nodes


def run(page, directory):
    page.goto((directory / 'index.html').as_uri())
    page.wait_for_load_state('load')
    # Same starting state on both sides: the two seeded tasks.
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_load_state('load')

    region = page.evaluate(PROBE)
    for title in ('Buy milk', 'Call the dentist', 'Ship the release notes'):
        page.evaluate(ADD_TASK, title)
    page.wait_for_timeout(300)

    status_css = None
    if page.locator('#status').count():
        status_css = page.evaluate(
            """() => {
              const el = document.getElementById('status');
              const r = el.getBoundingClientRect();
              const cs = getComputedStyle(el);
              return { width: r.width, height: r.height, position: cs.position,
                       clipPath: cs.clipPath, overflow: cs.overflow };
            }""")

    return {
        'region': region,
        'announcements': page.evaluate('() => window.__announcements'),
        'status_in_ax_tree': [n for n in snapshot_tree(page) if n['role'] == 'status'],
        'status_css': status_css,
        'list': page.evaluate(
            '() => [...document.querySelectorAll("#list li")].map(li => li.textContent)'),
    }


directories = [('after', REPO)]
if BASELINE:
    directories.insert(0, ('before', BASELINE))

results = {}
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')
    for label, directory in directories:
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        results[label] = run(page, directory)
        page.screenshot(path=str(OUT / f'{label}-desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(OUT / f'{label}-mobile.png'), full_page=True)
        page.close()
    browser.close()

(OUT / 'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
for label, data in results.items():
    print('=' * 20, label, '=' * 20)
    print('region:', json.dumps(data['region']))
    print('announcements:', json.dumps(data['announcements'], ensure_ascii=False))
    print('status role in AX tree:', json.dumps(data['status_in_ax_tree']))
    print('status CSS:', json.dumps(data['status_css']))
print(f'\ncaptures and results.json: {OUT}')
