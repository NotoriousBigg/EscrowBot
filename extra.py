import requests
import json

url = 'https://api.oxapay.com/merchants/request/whitelabel'
data = {
    'merchant': 'Z699KV-HVW8CT-P2HN9C-3EG0PE',
    'amount': 100,
    'currency': 'LTC',
    'payCurrency': 'LTC',
    'network': 'bep20',
    'lifeTime': 90,
    'feePaidByPayer': 1,
    'underPaidCover': 10,
    'callbackUrl': 'https://example.com/callback',
    'description': 'Order #12345',
    'orderId': '12345',
    'email': 'payer@example.com'
}


url3 = "https://api.oxapay.com/api/networks"
datia = {
    'merchant': 'Z699KV-HVW8CT-P2HN9C-3EG0PE'
}
response1 = requests.post(url3, data=json.dumps(datia))
result0 = response1.json()
print(result0)
ur0l = "https://api.oxapay.com/merchants/allowedCoins"

response = requests.post(ur0l, data=json.dumps(data))
result9 = response.json()
print(result9)

response = requests.post(url, data=json.dumps(data))
result = response.json()
print(result)
