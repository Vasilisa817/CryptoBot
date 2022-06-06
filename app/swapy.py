import requests
import statistics


API_URL = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'


headers = {
    "Accept": "*/*",
    "content-type": "application/json",
    "Origin": "https://p2p.binance.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
}

sell_value = {}
buy_value = {}

def swapy_curs():    
    crypto_values = [
    {"USDT":"RUB"},
    {"BTC": "RUB"},
    {"ETH": "RUB"}
    ]
    for i in crypto_values:
        for key in i.keys():
            value1 = key
            value2 = i[key]
            data = {
                "asset": value1,
                "fiat": value2,
                "merchantCheck": True,
                "page": 1,
                "payTypes": ["Tinkoff"],
                "publisherType": "merchant",
                "rows": 1,
                "tradeType": "SELL",
                "transAmount":  "500000"
            }
            r = requests.post(API_URL, headers=headers, json=data)
            all_adv = r.json().get("data")
            c = []
            for i in all_adv:
                a=i["adv"]["price"]
                c.append(float(a))
            sell_value[key] = '{:.2f}'.format(statistics.mean(c) * 0.96)
    #print (sell_value)
    for j in crypto_values:
        for key in j.keys():
            value1 = key
            value2 = j[key]
            data = {
                "asset": value1,
                "fiat": value2,
                "merchantCheck": True,
                "page": 1,
                "payTypes": ["Tinkoff"],
                "publisherType": "merchant",
                "rows": 1,
                "tradeType": "BUY",
                "transAmount":  "500000"
            }
            r = requests.post(API_URL, headers=headers, json=data)
            all_adv = r.json().get("data")
            f = []
            for k in all_adv:
                a=k["adv"]["price"]
                f.append(float(a))
            buy_value[key] = '{:.2f}'.format(statistics.mean(f) * 1.04)
    #print (buy_value)
    return [sell_value, buy_value]
    
if __name__ == '__main__':
    swapy_curs()
