import sys
sys.path.append('../..')
from wbfAPI.base import exceptions
from wbfAPI.base import wss
from wbfAPI.base import rest
from wbfAPI.base import transform
import threading
import json
import datetime
import urllib
from urllib.request import Request, urlopen
from hashlib import sha256
import hmac
import time
import numpy as np
# import os
# os.environ['http_proxy'] = 'http://127.0.0.1:1080'
# os.environ['https_proxy'] = 'https://127.0.0.1:1080'


class _params():

    def __init__(self):
        """该类只放参数
        """
        self.exc = 'binanceSpot'

        self.restUrl = 'https://api.binance.com'
        self.acctWssUrl = 'wss://stream.binance.com:9443/ws'
        self.wssUrl = 'wss://stream.binance.com:9443/ws'

        self.restPaths = {
            'transfer': 'POST /sapi/v1/futures/transfer',
            'getAccount': 'GET /api/v3/account',
            'getBalance': 'GET /api/v3/account',
            'getContract': 'GET /api/v3/exchangeInfo',
            'getPosition': '',
            'getFee': 'GET /sapi/v1/asset/tradeFee',
            'getTick': 'GET /api/v3/trades',
            'getDepth': 'GET /api/v3/depth',
            'getKline': 'GET /api/v3/klines',
            'getFundingRate': '',
            'getMarket': 'GET /api/v3/ticker/price',
            'makeOrder': 'POST /api/v3/order',
            'makeOrders': '',
            'cancelOrder': 'DELETE /api/v3/order',
            'cancelAll': 'DELETE /api/v3/openOrders',
            'queryOrder': 'GET /api/v3/order',
            'getOpenOrders': 'GET /api/v3/openOrders',
            'getDeals': 'GET /api/v3/myTrades',
            'getIncreDepth': 'GET /api/v1/depth',
            'getListenKey': 'POST /api/v3/userDataStream',
            'refreshListenKey': 'PUT /api/v3/userDataStream',
            'queryReferral': 'GET /sapi/v1/apiReferral/ifNewUser',
            'universalTransfer': "POST /sapi/v1/sub-account/universalTransfer",
            "accountSummary": "GET /sapi/v2/sub-account/futures/account",
        }

        self.wssPaths = {
            'tick': {'params': ['<symbol>@trade'], 'method': 'SUBSCRIBE', 'id': 1},
            'depth': {'params': ['<symbol>@depth20@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'increDepthFlow': {'params': ['<symbol>@depth@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'kline': {'params': ['<symbol>@kline_<period>'], 'method': 'SUBSCRIBE', 'id': 1},
            'market': {'params': ['!bookTicker'], 'method': 'SUBSCRIBE', 'id': 1},
            'bidAsk': {'params': ['<symbol>@bookTicker'], 'method': 'SUBSCRIBE', 'id': 1},

            'orders': '',
            'deals': '',
            'balance': '',
            'position': '',
        }

        self.klinePeriods = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '2h': '2h',
            '4h': '4h',
            '6h': '6h',
            '8h': '8h',
            '12h': '12h',
            '1d': '1d',
            '3d': '3d',
            '1w': '1w',
            '1M': '1M',
        }
        self.reverseKlinePeriods = {v: k for k, v in self.klinePeriods.items()}

        self.statusDict = {
            'NEW': 'submit',
            'PARTIALLY_FILLED': 'partial-filled',
            'FILLED': 'filled',
            'CANCELED': 'cancel',
            'REJECTED': 'rejected',
            'EXPIRED': 'expired',
        }

        self.legalCurrency = [
            'USDT', 'USD', 'BTC', 'ETH', 'BUSD'
        ]

    def getSymbol(self, symbol):
        return symbol.replace('/', '').upper()

    def accountWsSymbol(self, symbol):
        for lc in self.legalCurrency:
            if lc in symbol[-4:]:
                symbol = f"{symbol.split(lc)[0]}/{lc}".lower()
        return symbol

    def getPeriod(self, key):
        return key

    def getRestPath(self, key):
        if key not in self.restPaths \
                or self.restPaths[key] == '':
            exceptions.raisePathError(self.exc, key)
        return self.restPaths[key]

    def getWssPath(self, **kwargs):
        """拿wss订阅字段

        Args:
            *args: topic/symbol/....

        Returns:
            TYPE: Description
        """
        key = kwargs['topic']
        if 'symbol' in kwargs:
            kwargs['symbol'] = self.getSymbol(kwargs['symbol'])
        if 'period' in kwargs:
            kwargs['period'] = self.getPeriod(kwargs['period'])

        if key not in self.wssPaths \
                or self.wssPaths[key] == '':
            exceptions.raisePathError(self.exc, key)
        req = self.wssPaths[key].copy()
        key = list(req.keys())[0]
        for k, v in kwargs.items():
            req[key] = [req[key][0].replace(f"<{k}>", v.lower())]
        return json.dumps(req)


class AccountRest(rest.Rest):

    def init(self):
        self._params = _params()

    def sign(self, content):
        """签名

        Args:
            content (TYPE): Description
        """
        sign = hmac.new(
            self.privateKey.encode('utf-8'), content.encode('utf-8'), digestmod=sha256
        ).hexdigest()

        return sign

    def request(self, path, params={}, body={}, timeout=5, isSign=True):
        """http request function

        Args:
            path (TYPE): request url
            params (dict, optional): in url
            body (dict, optional): in request body
            timeout (int, optional): request timeout(s)
        """
        method, path = path.split(' ')
        if not isSign:
            req = params
        else:
            req = {
                'recvWindow': 3000,
                'timestamp': int(time.time()*1000),
            }
            req.update(params)
            sign = urllib.parse.urlencode(req)
            req['signature'] = self.sign(sign)
        req = urllib.parse.urlencode(req)
        url = f"{self._params.restUrl}{path}?{req}"
        # print(url)

        headers = {
            'X-MBX-APIKEY': self.publicKey,
        }
        res = self.httpRequest(method, url, headers, body, timeout)
        return res

    def accountSummary(self):
        # typeDic = {
        #     'spot-usdtSwap': 1,
        #     'usdtSwap-spot': 2,
        #     'spot-coinSwap': 3,
        #     'coinSwap-spot': 4,
        # }
        params = {
            'email': "longv01_virtual@r0jmakcinoemail.com", # 4.58654773
            # 'email': "longv02_virtual@vk72dz41noemail.com", # 60.67060561
            # 'email': "longv03_virtual@rw5qp8wznoemail.com", # 2.46918273
            # 'email': "longv04_virtual@ue7wkmzpnoemail.com",  # 83.17294949
            "futuresType": 2
            # 'amount': amount,
            # 'type': typeDic.get(type, None)
        }
        # # print(params)
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path,params=params)
        print(data)
        if 'tranId' in data:
            status = 'success'
        else:
            status = 'failed'
        data = transform.normalizeTick(status=status, data=data)
        return data

    def universalTransfer(self, toEmail, asset, amount, toType='SPOT'):
        # typeDic = {
        #     'spot-usdtSwap': 1,  4.58654773
        #     'usdtSwap-spot': 2,
        #     'spot-coinSwap': 3,
        #     'coinSwap-spot': 4,
        # }
        params = {
            'toEmail': toEmail,
            # "futuresType": 2
            "toAccountType": toType,
            "fromAccountType": "SPOT",
            'asset': asset.upper(),
            'amount': amount,
            # 'type': typeDic.get(type, None)
        }
        # # print(params)
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path,params=params)
        print(data)
        if 'tranId' in data:
            status = 'success'
        else:
            status = 'failed'
        data = transform.normalizeTick(status=status, data=data)
        return data

    def transfer(self, amount, currency, type='spot-usdtSwap'):
        typeDic = {
            'spot-usdtSwap': 1,
            'usdtSwap-spot': 2,
            'spot-coinSwap': 3,
            'coinSwap-spot': 4,
        }
        params = {
            'asset': currency.upper(),
            'amount': amount,
            'type': typeDic.get(type, None)
        }
        # print(params)
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        if 'tranId' in data:
            status = 'success'
        else:
            status = 'failed'
        data = transform.normalizeTick(status=status, data=data)
        return data

    def getAccount(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data
    
    def getContract(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, isSign=False)['symbols']
        data = [i for i in data if i['symbol'].endswith('USDT')]
        # data = [i for i in data if i['symbol']=='ETHUSDT']
        data = {self._params.accountWsSymbol(i['symbol']): float([j for j in i['filters'] if j['filterType']=='LOT_SIZE'][0]['minQty']) for i in data}
        data = transform.normalizeTick(data=data)
        return data
    
    def queryReferral(self):
        params = {
            'apiAgentCode': 'VDEJXT9H',
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data      

    def getBalance(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        #print(data)
        # ---------------------------------
        print('谢克胜-------------------------->',data)
        data = data['balances']
        data = [{
            'symbol': d['asset'].lower(),
            'balance': float(d['free']) + float(d['locked']),
            'available': float(d['free']),
            'frozen': float(d['locked']),
        } for d in data if float(d['free']) != 0.]
        data = transform.normalizeBalance(data=data)
        return data

    def getPosition(self, symbol='all'):
        data = transform.normalizeBalance(data=[])
        return data

    def getFee(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data

    def getTick(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'limit': 10,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # ---------------------------------
        data = [[
            d['time'],
            float(d['price']),
            float(d['qty']),
            -1 if d['isBuyerMaker'] else 1,
        ] for d in data]
        data = transform.normalizeTick(data=data)
        return data

    def getDepth(self, symbol, type=1000):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'limit': type,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # ---------------------------------
        timestamp = int(time.time()*1000)
        bids = np.array(data['bids']).astype('float').tolist()
        asks = np.array(data['asks']).astype('float').tolist()
        data = [timestamp, bids, asks, timestamp]
        data = transform.normalizeDepth(data=data)
        return data

    def getKline(self, symbol, period, count=100):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'interval': period,
            'limit': count,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # ---------------------------------
        data = [[
            d[0],
            float(d[1]),
            float(d[2]),
            float(d[3]),
            float(d[4]),
            float(d[5]),
            float(d[7]),
        ] for d in data]
        data = transform.normalizeKline(data=data)
        return data

    def getMarket(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, isSign=False)
        # print(data)
        data = {self._params.accountWsSymbol(d['symbol']): float(d['price']) for d in data if '/' in self._params.accountWsSymbol(d['symbol'])}
        data = transform.normalizeTick(data=data)
        return data

    def makeOrder(self, symbol, vol, price=None, orderType='buy-limit',
                  offset='open', postOnly=False, clientOrderId=None, timeInForce='GTC'): 
        side, orderType = orderType.split('-')
        if postOnly:
            orderType = 'LIMIT_MAKER'
        params = {
            'symbol': self._params.getSymbol(symbol),
            'side': side.upper(),
            'quantity': vol,
            'price': price,
            'type': orderType.upper(),
            'timeInForce': timeInForce,
            'newClientOrderId': 'x-VDEJXT9Hreferral',  # 返佣
        }
        # print(params)
        if clientOrderId is not None:
            params['newClientOrderId'] = clientOrderId
        if postOnly:
            del params['timeInForce']
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        if 'code' in data:
            status = 'failed'
            data = {
                'code': -1,
                'info': data,
            }
        else:
            status = 'success'
            data = {
                'ts': data['transactTime'],
                'orderId': data['orderId'],
                'code': 0,
                'info': 'success',
            }
        data = transform.normalizeMakeOrder(status=status, data=data)
        return data

    # def makeOrders(self, symbol, vol, price, orderType='buy-limit',
    #                offset='open', postOnly=False, clientOrderId=None):
    #     if isinstance(orderType, str):  # 买卖List
    #         orderType = [orderType]*len(vol)
    #     if postOnly:
    #         orderType = [f"{ot}-maker" for ot in orderType]
    #     if clientOrderId is None:
    #         clientOrderId = [None]*len(vol)
    #     body = [{
    #         'account-id': self.acctId,
    #         'symbol': self._params.getSymbol(symbol),
    #         'amount': str(vol[i]),
    #         'price': str(price[i]),
    #         'type': orderType[i],
    #         'clientOrderId': clientOrderId[i],
    #     } for i in range(len(vol))]
    #     path = self._params.getRestPath(sys._getframe().f_code.co_name)
    #     data = self.request(path, body=body)
    #     return data

    def cancelOrder(self, symbol, orderId):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'orderId': int(orderId),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        if 'status' in data \
                and data['status'] == 'CANCELED':
            status = 'success'
            data = {
                'orderId': data['orderId'],
                'code': 0,
                'info': 'success',
            }
        else:
            status = 'failed'
            data = {
                'code': -1,
                'orderId': orderId,
                'info': data,
            }
        data = transform.normalizeCancelOrder(status=status, data=data)
        return data

    def cancelAll(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        if 'code' in data \
                and data['code'] == -2011:
            status = 'success'
            data = {
                'code': 0,
                'info': data,
            }
        elif np.array([d['status'] == 'CANCELED' for d in data]).all():
            status = 'success'
            data = {
                'code': 0,
                'info': 'success',
            }
        else:
            status = 'failed'
            data = {
                'code': -1,
                'info': data,
            }
        data = transform.normalizeCancelAll(status=status, data=data)
        return data

    def queryOrder(self, symbol, orderId):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'orderId': int(orderId),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        if 'code' in data:
            status = 'failed'
            data = {
                'symbol': symbol,
                'orderId': orderId,
                'info': data,
            }
        else:
            status = 'success'
            data = {
                'ts': data['time'],
                'symbol': symbol,
                'orderId': data['orderId'],
                'clientOrderId': data['clientOrderId'],
                'price': float(data['price']),
                'vol': float(data['origQty']),
                'matchVol': float(data['executedQty']),
                'amt': float(data['price']) * float(data['origQty']),
                'side': 'buy' if data['side'] == 'BUY' else 'sell' if data['side'] == 'SELL' else None,
                'type': 'limit' if 'LIMIT' in data['type'] else 'market',
                'postOnly': True if 'MAKER' in data['type'] else False,
                'status': self._params.statusDict[data['status']],
                'info': 'success',
            }
        data = transform.normalizeQueryOrder(status=status, data=data)
        return data

    def getOpenOrders(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        data = [{
            'ts': d['time'],
            'symbol': symbol,
            'orderId': d['orderId'],
            'clientOrderId': d['clientOrderId'],
            'price': float(d['price']),
            'vol': float(d['origQty']),
            'matchVol': float(d['executedQty']),
            'amt': float(d['price']) * float(d['origQty']),
            'side': 'buy' if d['side'] == 'BUY' else 'sell' if d['side'] == 'SELL' else None,
            'type': 'limit' if 'LIMIT' in d['type'] else 'market',
            'postOnly': True if 'MAKER' in d['type'] else False,
            'status': self._params.statusDict[d['status']] if d['status'] in self._params.statusDict else d['status'],
        } for d in data]
        data = transform.normalizeOpenOrders(data=data)
        return data

    def getDeals(self, symbol, count=100):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'limit': count,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        data = [{
            'ts': d['time'],
            'symbol': symbol,
            'myOrderId': d['orderId'],
            'tradeId': d['id'],
            'price': float(d['price']),
            'vol': float(d['qty']),
            'amt': float(d['price']) * float(d['qty']),
            'fee': d['commission'],
            'feeAsset': d['commissionAsset'].lower(),
            'side': 'buy' if d['isBuyer'] else 'sell',
            'role': 'maker' if d['isMaker'] else 'taker',
        } for d in data]
        data = transform.normalizeDeals(data=data)
        return data


class AccountWss(AccountRest, wss.websocketApp):

    def __init__(self, publicKey, privateKey, rspFunc, restartGap=0):
        self.publicKey = publicKey
        self.privateKey = privateKey
        self._params = _params()
        self.rspFunc = rspFunc
        self.author()  # 鉴权
        self.start(restartGap=restartGap)
        ping = threading.Thread(target=self.ping)
        ping.start()

    def getListenKey(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, isSign=False)
        return data

    def refreshListenKey(self):
        params = {
            'listenKey': self.listenKey,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        return data

    def init(self):
        pass

    def ping(self):
        while 1:
            time.sleep(60)
            try:
                self.refreshListenKey()
            except:
                pass

    def author(self):
        self.listenKey = self.getListenKey()['listenKey']
        self.wssUrl = f"{self._params.acctWssUrl}/{self.listenKey}"

    def openRsp(self):
        print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Connected =====")

    def messageRsp(self, message):
        data = json.loads(message)
        # ---------------------------------
        if data['e'] == "outboundAccountPosition":  # balance
            status = 'balance'
            data = [{
                'symbol': d['a'].lower(),
                'balance': float(d['f']) + float(d['l']),
                'available': float(d['f']),
                'frozen': float(d['l']),
            } for d in data['B']]
            data = transform.normalizeBalance(status=status, data=data)

        elif data['e'] == 'executionReport' and data['x'] == 'TRADE':  # deals
            status = 'orders'
            orders = {
                'ts': data['E'],
                'symbol': self._params.accountWsSymbol(data['s']),
                'orderId': data['i'],
                'clientOrderId': data['c'],
                'price': float(data['p']),
                'matchPrice': float(data['L']),
                'vol': float(data['q']),
                'matchVol': float(data['z']),
                'amt': float(data['p']) * float(data['q']),
                'matchAmt': float(data['Z']),
                'fee': float(data['n']),
                'feeAsset': data['N'].lower() if data['N'] else None,
                'side': data['S'].lower(),
                'type': data['o'].lower(),
                'status': self._params.statusDict.get(data['X'], data['X']),
                'info': 'success',
            }
            orders = transform.normalizeQueryOrder(status=status, data=orders)
            self.rspFunc(orders)

            status = 'deals'
            deals = [{
                'ts': data['T'],
                'symbol': self._params.accountWsSymbol(data['s']),
                'myOrderId': data['i'],
                'clientOrderId': data['c'],
                'tradeId': data['t'],
                'side': data['S'].lower(),
                'type': data['o'].lower(),
                'price': float(data['L']),
                'vol': float(data['l']),
                'amt': float(data['Y']),
                'fee': float(data['n']),
                'feeAsset': data['N'].lower(),
                'role': 'maker' if data['m'] else 'taker',
                'status': self._params.statusDict[data['X']],
            }]
            deals = transform.normalizeDeals(status=status, data=deals)
            self.rspFunc(deals)
            return


        elif data['e'] == 'executionReport' and data['x'] != 'TRADE':  # orders
            status = 'orders'
            data = {
                'ts': data['E'],
                'symbol': self._params.accountWsSymbol(data['s']),
                'orderId': data['i'],
                'clientOrderId': data['c'],
                'price': float(data['p']),
                'matchPrice': float(data['L']),
                'vol': float(data['q']),
                'matchVol': float(data['z']),
                'amt': float(data['p']) * float(data['q']),
                'matchAmt': float(data['Z']),
                'fee': float(data['n']),
                'feeAsset': data['N'].lower() if data['N'] else None,
                'side': data['S'].lower(),
                'type': data['o'].lower(),
                'status': self._params.statusDict[data['x']],
                'info': 'success',
            }
            data = transform.normalizeQueryOrder(status=status, data=data)

        else:
            return

        self.rspFunc(data)

    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Closed!! =====")


class DataWss(AccountWss):

    def __init__(self, symbol, publicKey='RxVDiWnRkyHbrbMnsRZl5zaXjCcO1oPBGmXxxbi3LPkxN4UaNhlrXIIBoKRTeQIs', rspFunc=None, topics=['tick', 'depth']):
        self._params = _params()
        self.publicKey = publicKey
        self.wssUrl = self._params.wssUrl
        self.symbol = symbol
        self.topics = topics
        self.increDepthStamp = 0
        self.increDepthFlag = True
        self.rspFunc = rspFunc
        # if rspFunc is not None:
        #     self.messageRsp = rspFunc
        # self.start()
        self.start(ping_interval=5, ping_timeout=3)

    def init(self):
        # self.subscribe(topic='tick', symbol=self.symbol)
        # self.subscribe(topic='depth', symbol=self.symbol, type='step0')
        if isinstance(self.symbol, list):
            for s in self.symbol:
                [self.subscribe(topic=topic, symbol=s, type='step0') for topic in self.topics]
        else:
            [self.subscribe(topic=topic, symbol=self.symbol, type='step0') for topic in self.topics]
        # self.subscribe(topic='increDepthFlow', symbol=self.symbol)
        # self.subscribe(topic='kline', symbol=self.symbol, period='1m')
        pass

    def getIncreDepth(self):
        params = {
            'symbol': self._params.getSymbol(self.symbol),
            'limit': 1000,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        return data

    def openRsp(self):
        print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Connected =====")
        self.init()

    def messageRsp(self, message):
        rsp = json.loads(message)
        #print(rsp)

        if self.rspFunc is not None: # 自定义Func
            self.rspFunc(rsp)
            return

        timestamp = int(time.time()*1000)
        # print(rsp, '\n')
        if 'e' in rsp:
            if rsp['e'] == 'trade':  # tick
                data = [[rsp['T'], float(rsp['p']), float(rsp['q']), 1 if not rsp['m'] else -1]]
                info = f"_wssData_{self.symbol}_tick"
                setattr(self, info, [timestamp, data])
                # print(info)
                # print(data)

            elif 'kline' in rsp['e']:  # kline
                data = rsp['k']
                period = self._params.reverseKlinePeriods[data['i']]
                data = [[data['t'], float(data['o']), float(data['h']), float(data['l']), float(data['c']), float(data['v']), float(data['q'])]]
                info = f"_wssData_{self.symbol}_kline_{period}"
                setattr(self, info, [timestamp, data])
                # print(data, info)

            elif 'depthUpdate' in rsp['e']:  # 增量深度流
                if rsp['U'] > self.increDepthStamp + 1:  # 未接上
                    time.sleep(1)  # 防止限频
                    increDepth = self.getIncreDepth()
                    self.oriDepth = {
                        'bids': {float(l[0]): float(l[1]) for l in increDepth['bids']},
                        'asks': {float(l[0]): float(l[1]) for l in increDepth['asks']}
                    }
                    self.increDepthStamp = increDepth['lastUpdateId']
                    # print(increDepth)
                    self.firstFollow = False
                    return  # 跳出

                elif rsp['U'] <= self.increDepthStamp + 1 \
                        and rsp['u'] >= self.increDepthStamp + 1 \
                        and not self.firstFollow:  # 第一次接上
                    self.firstFollow = True
                    # print('接上')

                elif rsp['U'] == self.increDepthStamp + 1 \
                        and self.firstFollow:  # 接上
                    # print('续上')
                    pass

                else:
                    return  # 跳出

                if 'b' in rsp and len(rsp['b']) != 0:
                    bids = {float(l[0]): float(l[1]) for l in rsp['b']}
                    for k, v in bids.items():
                        if v == 0.:
                            if k in self.oriDepth['bids']:
                                del self.oriDepth['bids'][k]
                        else:
                            self.oriDepth['bids'][k] = v
                if 'a' in rsp and len(rsp['a']) != 0:
                    asks = {float(l[0]): float(l[1]) for l in rsp['a']}
                    for k, v in asks.items():
                        if v == 0.:
                            if k in self.oriDepth['asks']:
                                del self.oriDepth['asks'][k]
                        else:
                            self.oriDepth['asks'][k] = v

                self.increDepthStamp = rsp['u']
                bids = [[i[0], i[1]] for i in sorted(self.oriDepth['bids'].items(), key=lambda d: d[0], reverse=True)]
                asks = [[i[0], i[1]] for i in sorted(self.oriDepth['asks'].items(), key=lambda d: d[0])]
                data = [rsp['E'], bids, asks, timestamp]
                info = f"_wssData_{self.symbol}_increDepth"
                setattr(self, info, [timestamp, data])
                # print(info)
                # print(data[1][0],data[2][0])

        elif 'lastUpdateId' in rsp:  # 深度
            bids = np.array(rsp['bids']).astype('float').tolist()
            asks = np.array(rsp['asks']).astype('float').tolist()
            data = [timestamp, bids, asks, timestamp]
            info = f"_wssData_{self.symbol}_depth"
            setattr(self, info, [timestamp, data])
            #print(data[1][0],data[2][0])

    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Closed!! =====")


if __name__ == '__main__':
    publicKey = "VbSjGinSrj7H5ShfCBWSMybZvUXZ3DyUUHbJuol4frKHqX5PSznu8toNKqmHWl4M"
    privateKey = "B4QYXbJHok0Hh8njyLbJzNTptyFl1cCJ4xDC4NZSacIhdtXl04FWjaBv1OUiA0NH"
    #publicKey = 'RKyJDEqJoEHFkJaNWQMIjEZHqmltkmWj49PHhsnD2n5ZRyuat7SNMfE5QCzb698h'
    #privateKey = 'BxZgDHeJzrSKY3bcDjsHIP0phFCxQNLntYaRQKkJW5nHAub9Zqwql71u61p8WFDy'
    publicKey = 'csnfGALBPk9A6edvqVPmfMuZCNUjNu8Q283vRKDdfJtRnIdZOzH47gU7ZOR44kIP'
    privateKey = 'dkVC1tFA3BON8z76iHP5bhekTMTu2BX7mApWjQeMbB7yQJ2zqVbKjKJZxUOdeycX'
    publicKey,privateKey = 'ZNyFoy4DLFXw4vXAGEbW36OUU8chxXfQsE7EpW3SkhyqcUyejBGSZoClUK0KKKWj', 'pzxxkabA1DiSnYIJPptVbQfdokMvhXcThz6lWzGxVhC5EQSF0HQyT33vM2IyyNp9'
    task = AccountRest(publicKey, privateKey)
    # print([i for i in task.getBalance()['data'] if i['balance']>0])
    # data = [i for i in task.getBalance()['data'] if i['balance']>0]
    # print(task.transfer(100, 'usdt', 'spot-usdtSwap'))
    # print(task.queryReferral())
    # print(task.getFee())
    # task.accountSummary()
    #task.universalTransfer(toEmail='guxiaoyan_virtual@6emrb0p7managedsub.com', asset='usdt', amount=1)
    #print(task.getBalance())
    # print(task.getBalance())
    # print(task.getAccount())
    # print(task.getContract())
    # data = task.getBalance()['data']
    # print(task.getMarket())['data']
    # print(data)
    # print([i for i in data if i['balance']!=0.])
    # print(task.getPosition('doge/usdt'))
    # print(task.getFee('btc/usdt'))
    # print(task.getTick('btc/usdt'))
    print(task.getDepth('theta/usdt', type=5))
    # print(task.getKline('btc/usdt', '1d', count=1000))
    # print(task.getFundingRate('btc/usdt'))
    # print(task.cancelAll('btc/usdt'))
    # print(task.makeOrder('egld/usdt', 3.2469, price=128, orderType='sell-limit'))
    # print(task.makeOrders('btc/usdt', 1, 8000, postOnly=True))
    # print(task.cancelOrder('btc/usdt', 3285830730))
    # print(task.queryOrder('btc/usdt',3285830730))
    # time.sleep(5)
    # print(task.getOpenOrders('btc/usdt'))
    # data = task.getDeals('eos/usdt')['data']
    # print(data[0]['tradeId'], data[-1]['tradeId'])

    '''--------------------------------------------------'''
    # dic = {}
    def rspFunc(content):
        #data = json.loads(content)
        print(content)
    #     if 's' in data:
    #         symbol = task._params.accountWsSymbol(data['s'])
    #         if '/' in symbol:
    #             dic[symbol] = (float(data['b']) + float(data['a'])) / 2
    # task = AccountWss(publicKey, privateKey, rspFunc)

    '''--------------------------------------------------'''
    #print(time.time())
    #task = DataWss(['btc/usdt'], topics=['depth'])  #, rspFunc=rspFunc)
    # while 1:
    #     print(len(dic))
    #     time.sleep(5)
    # task.subscribe(topic='market')
    # print(task.getIncreDepth())
