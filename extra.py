import requests
import json

url = "https://api.oxapay.com/merchants/allowedCoins"
data = {
    'merchant': 'Z699KV-HVW8CT-P2HN9C-3EG0PE'
}
response = requests.post(url, data=json.dumps(data))
result = response.json()
print(result)