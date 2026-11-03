import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / ".deps"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT.parent / ".browsers"))

from playwright.sync_api import sync_playwright
from PIL import Image

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1.5)
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.wait_for_function("document.body.dataset.ready === 'true'")
    page.wait_for_timeout(500)
    page.evaluate("""
      document.querySelector('.sidebar').style.display = 'none';
      document.querySelector('.app').style.marginLeft = '0';
      document.querySelector('.topbar').style.paddingLeft = '34px';
    """)
    page.wait_for_timeout(300)
    path = ROOT / "screenshots" / "poster_app_wide_raw.png"
    page.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": 1440, "height": 1000})
    browser.close()

raw = Image.open(path)
# 1440x1000 at 1.5x; crop to exactly 3:2-ish 1440x960 CSS for a clean card.
raw.crop((0, 0, 2160, 1440)).save(ROOT / "screenshots" / "poster_app_wide.png")
print("saved", (2160, 1440))
