import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / ".deps"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT.parent / ".browsers"))

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    errors = []
    page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.wait_for_function("document.body.dataset.ready === 'true'")
    page.wait_for_timeout(300)

    assert page.locator("#inquiry-empty").is_hidden()
    assert page.locator("#inquiry-result").is_visible()
    assert page.locator("#lead-score").inner_text() == "65"
    assert page.locator("#inquiry-text").input_value().startswith("Subject: Inquiry")

    page.select_option("#market-select", "VN")
    page.wait_for_timeout(100)
    assert page.locator("#price-currency").inner_text() == "₫"
    assert "₫" in page.locator("#price-input").input_value() or float(page.locator("#price-input").input_value()) > 100000
    page.select_option("#product-select", "portable_power")
    page.click("#analyze-btn")
    page.wait_for_function("document.querySelector('#report-title').textContent.includes('越南')", timeout=10000)
    page.wait_for_timeout(500)
    assert "越南" in page.locator("#report-title").inner_text()
    assert page.locator("#verdict-note").inner_text()
    assert page.locator("#pipeline .pipeline-step.done").count() == 5

    page.select_option("#market-select", "DE")
    page.select_option("#product-select", "led_outdoor")
    page.wait_for_timeout(100)
    page.click("#analyze-btn")
    page.wait_for_function("document.querySelector('#report-title').textContent.includes('德国')", timeout=10000)
    page.wait_for_timeout(300)
    page.locator("#trace-toggle").click()
    assert page.locator("#trace").is_visible()
    assert page.locator("#trace .trace-step").count() == 5

    page.click("#sample-btn")
    page.wait_for_timeout(500)
    assert page.locator("#lead-score").inner_text() == "65"

    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("desktop overflow:", overflow)
    print("errors:", errors)
    assert overflow <= 1
    assert not errors

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    mobile.goto("http://127.0.0.1:8000", wait_until="networkidle")
    mobile.wait_for_function("document.body.dataset.ready === 'true'")
    mobile.wait_for_timeout(300)
    print("mobile overflow:", mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth"))
    assert mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 1
    mobile.click("#menu-btn")
    assert mobile.locator("#sidebar").evaluate("el => el.classList.contains('open')")
    mobile.wait_for_timeout(350)
    mobile.screenshot(path=str(ROOT / "screenshots" / "app_mobile_menu.png"), full_page=False)
    mobile.mouse.click(350, 300)
    mobile.wait_for_timeout(350)
    assert mobile.locator("#sidebar").evaluate("el => !el.classList.contains('open')")
    mobile.screenshot(path=str(ROOT / "screenshots" / "app_mobile.png"), full_page=False)
    browser.close()
print("UI checks passed")
