import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / ".deps"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT.parent / ".browsers"))

from playwright.sync_api import sync_playwright

OUT = ROOT / "screenshots"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1.5)
    errors = []
    page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.wait_for_function("document.body.dataset.ready === 'true'", timeout=20000)
    page.wait_for_timeout(600)
    print("title:", page.title())
    print("size:", page.evaluate("[document.body.scrollWidth, document.body.scrollHeight]"))
    print("errors:", errors)
    page.screenshot(path=str(OUT / "app_top.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 1120})
    page.screenshot(path=str(OUT / "app_full.png"), full_page=True)
    # A tighter panel shot for the poster, without browser scrollbars.
    page.locator("#report").screenshot(path=str(OUT / "report.png"))
    page.locator("#inquiry").screenshot(path=str(OUT / "inquiry.png"))
    browser.close()
print("saved", OUT)
