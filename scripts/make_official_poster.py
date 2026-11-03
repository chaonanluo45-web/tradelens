import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / ".deps"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT.parent / ".browsers"))

from playwright.sync_api import sync_playwright
from PIL import Image

html = (ROOT / "poster" / "poster_official.html").resolve().as_uri()
tmp = ROOT / "poster" / "_poster_official_2x.png"
out = ROOT / "poster" / "TradeLens_poster_official.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1080, "height": 1525}, device_scale_factor=2)
    page.goto(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(400)
    page.locator(".poster").screenshot(path=str(tmp))
    browser.close()

img = Image.open(tmp).convert("RGB")
img.resize((1080, 1525), Image.Resampling.LANCZOS).save(out, optimize=True)
tmp.unlink()
print("saved", out, Image.open(out).size)
