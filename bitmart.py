import hashlib
import hmac
import json
import time
import urllib.parse

import requests


class Bitmart:

    def __init__(self, api_key, secret_key, memo):
        """Constructor"""
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__memo = memo
        self.__access_token = ''
        self.precision = {}
        self.base_min_size = {}
        self.__load_precision()

    def __create_sha256_signature(self, message):
        return hmac.new(self.__secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

    def __get_access_token(self):
        url = "https://openapi.bitmart.com/v2/authentication"
        message = self.__api_key + ':' + self.__secret_key + ':' + self.__memo
        data = {"grant_type": "client_credentials", "client_id": self.__api_key,
                "client_secret": self.__create_sha256_signature(message)}
        response = requests.post(url, data=data)
        print(response.content)
        accessToken = response.json()['access_token']
        self.__access_token = accessToken
        return accessToken

    def __get(self, request_path):
        if self.__access_token == '':
            self.__get_access_token()
        headers = {"X-BM-TIMESTAMP": str(int(time.time() * 1000)),
                   "X-BM-AUTHORIZATION": "Bearer {}".format(self.__access_token)}
        response = requests.get(request_path, headers=headers)
        if 'Unauthorized' in response.text:
            print('Unauthorized')
            self.__get_access_token()
            headers = {"X-BM-TIMESTAMP": str(int(time.time() * 1000)),
                       "X-BM-AUTHORIZATION": "Bearer {}".format(self.__access_token)}
            response = requests.get(request_path, headers=headers)
        return response.json()

    def __post(self, request_path, params):
        if self.__access_token == '':
            self.__get_access_token()
        data = {}
        for key in sorted(params.keys()):
            data.update({key: params[key]})
        url = urllib.parse.urlencode(data)
        sign = self.__create_sha256_signature(url)
        headers = {"X-BM-TIMESTAMP": str(int(time.time() * 1000)),
                   "X-BM-AUTHORIZATION": "Bearer {}".format(self.__access_token),
                   "X-BM-SIGNATURE": sign,
                   "Content-Type": "application/json"}

        response = requests.post(request_path, data=json.dumps(params), headers=headers)
        return response.json()

    def __delete(self, request_path, entrust_id):
        if self.__access_token == '':
            self.__get_access_token()
        sign = self.__create_sha256_signature('entrust_id={}'.format(entrust_id))
        headers = {"X-BM-TIMESTAMP": str(int(time.time() * 1000)),
                   "X-BM-AUTHORIZATION": "Bearer {}".format(self.__access_token),
                   "X-BM-SIGNATURE": sign}

        response = requests.delete(request_path, headers=headers)
        return response.json()

    def __delete2(self, request_path):
        if self.__access_token == '':
            self.__get_access_token()
        headers = {"X-BM-TIMESTAMP": str(int(time.time() * 1000)),
                   "X-BM-AUTHORIZATION": "Bearer {}".format(self.__access_token)}

        response = requests.delete(request_path, headers=headers)
        return response.json()

    # Public Endpoints

    def ping(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/ping').json()

    def time(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/time').json()

    def steps(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/steps').json()

    def currencies(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/currencies').json()

    def symbols(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/symbols').json()

    def symbols_details(self):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/symbols_details').json()

    def ticker(self, symbol):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/ticker?symbol={}'.format(symbol)).json()

    def kline(self, symbol, step, time_from, time_to):
        return requests.request("GET",
                                'https://openapi.bitmart.com/v2/symbols/{}/kline?step={}&from={}&to={}'.format(symbol,
                                                                                                               step,
                                                                                                               time_from,
                                                                                                               time_to)).json()

    def orderbook(self, symbol, precision):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/symbols/{}/orders?precision={}'.format(symbol,
                                                                                                              precision)).json()

    def trades(self, symbol):
        return requests.request("GET", 'https://openapi.bitmart.com/v2/symbols/BMX_ETH/trades'.format(symbol)).json()

    # Authenticated Endpoints

    def wallet(self):
        return self.__get('https://openapi.bitmart.com/v2/wallet')

    def place_order(self, symbol, amount, price, side):
        params = {"symbol": symbol, "amount": amount, "price": price, "side": side}
        return self.__post('https://openapi.bitmart.com/v2/orders', params)

    def cancel_order(self, order_id):
        return self.__delete('https://openapi.bitmart.com/v2/orders/{}'.format(order_id), order_id)

    def cancel_all_order(self, symbol, side):
        return self.__delete2('https://openapi.bitmart.com/v2/orders?symbol={}&side={}'.format(symbol, side))

    def list_orders(self, symbol, status, offset, limit):
        return self.__get('https://openapi.bitmart.com/v2/orders?symbol={}&status={}&offset={}&limit={}'.format(symbol,
                                                                                                                status,
                                                                                                                offset,
                                                                                                                limit))

    def order_details(self, order_id):
        return self.__get('https://openapi.bitmart.com/v2/orders/{}'.format(order_id))

    # Service

    def __load_precision(self):
        r = self.symbols_details()
        for x in r:
            self.precision.update({x['id']: x['price_max_precision']})

