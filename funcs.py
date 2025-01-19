import re
import json
import requests
import random
import string
from config import MERCHANT_KEY


# Func To verify USDT Address
def verify_address(address):
    if isinstance(address, str):
        pattern = r"^0x[a-fA-F0-9]{40}$"
        return bool(re.match(pattern, address))
    return False


# to generate code for deep linking of the bot
def generate_linking_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


# To create A static address
def create_random_address():
    url = "https://api.oxapay.com/merchants/request/staticaddress"
    data = {
        'merchant': f'{MERCHANT_KEY}',
        'currency': 'LTC',
    }
    r = requests.post(url, data=json.dumps(data))
    data = r.json()
    address = data['address']
    if r.status_code != 200:
        return False
    return address


# to destroy static address after some time
def destroy_random_address(address):
    url = "https://api.oxapay.com/merchants/revoke/staticaddress"
    data = {
        'merchant': f'{MERCHANT_KEY}',
        'address': f'{address}'
    }
    r = requests.post(url, data=json.dumps(data))

    if r.status_code != 200:
        return False
    return True


# To check payment status
def check_payment_status(pay_id):
    url = 'https://api.oxapay.com/merchants/inquiry'
    data = {
        'merchant': f'{MERCHANT_KEY}',
        'trackId': f'{pay_id}'
    }
    response = requests.post(url, data=json.dumps(data))

    if response.status_code != 200:
        return False
    if response.status_code == 200:
        result = response.json()
        status = result['result']
        resp = result['status']
        return status, resp


# Generating a payment request

def generate_payment_request(amount):
    url = 'https://api.oxapay.com/merchants/request/whitelabel'
    data = {
        'merchant': f'{MERCHANT_KEY}',
        'amount': f'{amount}',
        'payCurrency': 'LTC',
        'currency': 'LTC'
    }
    response = requests.post(url, data=json.dumps(data))
    if response.status_code != 200:
        return False
    if response.status_code == 200:
        result = response.json()
        status = result['result']

        qrcode = result['QRCode']
        track_id = result['trackId']
        address = result['address']

        return status, address, qrcode, track_id


# For paying funds to seller/buyer
def create_payout_to_seller(address, amount):
    url = "https://api.oxapay.com/api/send"
    data = {
        'key': f'{MERCHANT_KEY}',
        'address': f'{address}',
        'amount': f'{amount}',
        'currency': 'LTC',
    }
    response = requests.post(url, data=json.dumps(data))

    if response.status_code != 200:
        return False
    if response.status_code == 200:
        data = response.json()
        track_id = data['trackId']
        result = data['status']
        status = data['result']
        return status, track_id, result


# For checking payout status

def check_payout_status(pay_id):
    url = 'https://api.oxapay.com/api/inquiry'
    data = {
        'key': 'YOUR_PAYOUT_API_KEY',
        'trackId': f'{pay_id}'
    }
    response = requests.post(url, data=json.dumps(data))
    if response.status_code != 200:
        return False
    if response.status_code == 200:
        result = response.json()
        status = result['result']
        resp = result['status']
        return status, resp


# YA KUTAFUTA ZA KAHAWA
def calculate_total_deposit(amount):
    total_fee_percentage = 0.006  # 0.6%
    total_deposit = float(amount) / (1 - total_fee_percentage)
    return round(total_deposit, 2)
