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
        self.exc = 'binanceUsdtSwap'

        self.restUrl = 'https://fapi.binance.com'
        self.acctWssUrl = 'wss://fstream.binance.com/ws'
        self.wssUrl = 'wss://fstream.binance.com/ws'

        self.restPaths = {
            'getContract': 'GET /fapi/v1/exchangeInfo',
            'getAccount': 'GET /fapi/v2/account',
            'getBalance': 'GET /fapi/v2/balance',
            'getPosition': 'GET /fapi/v2/positionRisk',
            'getFee': 'GET /fapi/v1/commissionRate',
            'getNewPrice': 'GET /fapi/v1/ticker/price',
            'getInfo': 'GET /fapi/v1/ticker/24hr',
            'getTick': 'GET /fapi/v1/trades',
            'getDepth': 'GET /fapi/v1/depth',
            'getKline': 'GET /fapi/v1/klines',
            'getFundingRate': 'GET /fapi/v1/premiumIndex',
            'getClearPrice': 'GET /fapi/v1/premiumIndex',
            'makeOrder': 'POST /fapi/v1/order',
            'makeOrders': 'POST /fapi/v1/batchOrders',
            'cancelOrder': 'DELETE /fapi/v1/order',
            'cancelAll': 'DELETE /fapi/v1/allOpenOrders',
            'queryOrder': 'GET /fapi/v1/order',
            'getOpenOrders': 'GET /fapi/v1/openOrders',
            'getDeals': 'GET /fapi/v1/userTrades',
            'getForceOrders': 'GET /fapi/v1/forceOrders',
            'getIncreDepth': 'GET /fapi/v1/depth',
            'getListenKey': 'POST /fapi/v1/listenKey',
            'refreshListenKey': 'PUT /fapi/v1/listenKey',
            'updateLeverage': 'POST /fapi/v1/leverage',
            'getMarketRate': 'GET /fapi/v1/premiumIndex',
            'getHisTrans': "POST /fapi/v1/positionSide/dual",
            'setLever': 'POST /fapi/v1/leverage',
        }

        self.wssPaths = {
            'tick': {'params': ['<symbol>@aggTrade'], 'method': 'SUBSCRIBE', 'id': 1},
            'depth': {'params': ['<symbol>@depth20@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'increDepthFlow': {'params': ['<symbol>@depth@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'kline': {'params': ['<symbol>@kline_<period>'], 'method': 'SUBSCRIBE', 'id': 1},
            'clearPrice': {'params': ['<symbol>@markPrice@1s'], 'method': 'SUBSCRIBE', 'id': 1},
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
            'USDT', 'USD', 'BTC', 'ETH',
        ]

    def getSymbol(self, symbol):
        return symbol.replace('/', '').upper()

    def accountWsSymbol(self, symbol):
        for lc in self.legalCurrency:
            if lc in symbol:
                symbol = f"{symbol.split(lc)[0]}/{lc}".lower()
                break
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

        headers = {
            'X-MBX-APIKEY': self.publicKey,
        }
        # print(url)
        res = self.httpRequest(method, url, headers, body, timeout)
        return res

    def getContract(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)['symbols']
        #print(data)
        # data = {d['symbol'].split('USDT')[0].lower()+'/usdt': d['quantityPrecision'] for d in data if d['contractType']=='PERPETUAL'}
        #data = {d['symbol'].split('USDT')[0].lower()+'/usdt': 1 for d in data if d['contractType']=='PERPETUAL'}
        data = [[d['symbol'], d['filters'][0]['tickSize'], d['filters'][1]['stepSize']]for d in data if d['contractType']=='PERPETUAL']
        # print(data.keys())
        #data = transform.normalizeDepth(data=data)
        return data   

    def getMarketRate(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, isSign=False)
        data = {self._params.accountWsSymbol(i['symbol'].split('_')[0]): float(i['lastFundingRate']) for i in data if i['lastFundingRate']!=''}
        data = transform.normalizeTick(data=data)
        return data

    def getAccount(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data
    
    def getHisTrans(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data

    def getInfo(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data      

    def getBalance(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        #print(data)
        # ---------------------------------
        data = [{
            'symbol': d['asset'].lower(),
            'balance': float(d['balance']),
            'available': float(d['availableBalance']),
            'frozen': float(d['balance']) - float(d['availableBalance']),
        } for d in data]
        data = transform.normalizeBalance(data=data)
        return data

    def getNewPrice(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data

    def updateLeverage(self, symbol, leverage=3):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'leverage': leverage,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data
    
    def getForceOrders(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data
        
    def getPosition(self, symbol):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        # print(data)
        if symbol != 'all':
            tempSymbol = self._params.getSymbol(symbol)
            data = [d for d in data if d['symbol']==tempSymbol]
        # ---------------------------------
            if len(data) > 0:
                data = [{
                    'symbol': symbol,
                    'pos': float(d['positionAmt']),
                    'posSide': 1 if d['positionSide'] == 'LONG' else -1 if d['positionSide'] == 'SHORT' else None,
                    'openPrice': float(d['entryPrice']),
                    'openAmt': float(d['positionAmt']) * float(d['entryPrice']),
                    'liquidationPrice': float(d['liquidationPrice']),
                    'unrealProfitLoss': float(d['unRealizedProfit']),
                    'lever': float(d['leverage']),
                } for d in data]
            else:
                data = [{
                    'symbol': symbol,
                    'pos': 0.,
                }]
        else:
            data = [{
                'symbol': self._params.accountWsSymbol(d['symbol']),
                    'pos': float(d['positionAmt']),
                    'posSide': 1 if d['positionSide'] == 'LONG' else -1 if d['positionSide'] == 'SHORT' else None,
                    'openPrice': float(d['entryPrice']),
                    'openAmt': float(d['positionAmt']) * float(d['entryPrice']),
                    'liquidationPrice': float(d['liquidationPrice']),
                    'unrealProfitLoss': float(d['unRealizedProfit']),
                    'lever': float(d['leverage']),
                } for d in data if float(d['positionAmt'])!=0.]
        data = transform.normalizePosition(data=data)
        return data

    def getFee(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
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
        data = [data['E'], bids, asks, timestamp]
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
            float(d[0]),
            float(d[1]),
            float(d[2]),
            float(d[3]),
            float(d[4]),
            float(d[5]),
            float(d[7]),
        ] for d in data]
        data = transform.normalizeKline(data=data)
        return data

    def getFundingRate(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # ---------------------------------
        timestamp = int(time.time()*1000)
        data = [
            data['time'],
            float(data['lastFundingRate']),
            np.nan,
            timestamp,
        ]
        data = transform.normalizeFundingRate(data=data)
        return data

    def getClearPrice(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # ---------------------------------
        timestamp = int(time.time()*1000)
        data = [
            data['time'],
            float(data['indexPrice']),
            np.nan,
            timestamp
        ]
        data = transform.normalizeClearPrice(data=data)
        return data

    def makeOrder(self, symbol, vol, price=0, orderType='buy-limit',
                  offset='open', postOnly=False, clientOrderId=None, timeInForce='GTC'):
        side, orderType = orderType.split('-')
        timeInForce = 'GTX' if postOnly else timeInForce
        params = {
            'symbol': self._params.getSymbol(symbol),
            'side': side.upper(),
            'quantity': vol,
            'price': price,
            'type': orderType.upper(),
            'reduceOnly': False if offset == 'open' else True if offset == 'close' else None,
            'timeInForce': timeInForce,
            'newClientOrderId': clientOrderId,
        }
        if clientOrderId is None:
            del params['newClientOrderId']
        if orderType == 'market':
            del params['timeInForce']
            del params['price']
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
                'orderId': data['orderId'],
                'code': 0,
                'info': 'success',
            }

        data = transform.normalizeMakeOrder(status=status, data=data)
        return data

    def makeOrders(self, symbol, vol, price, orderType='buy-limit',
                   offset='open', postOnly=False, clientOrderId=None, timeInForce='GTC'):
        if isinstance(orderType, str):  # 买卖List
            orderType = [orderType]*len(vol)
        orderType = [o.split('-') for o in orderType]
        if clientOrderId is None:
            clientOrderId = [None]*len(vol)
        reduceOnly = False if offset == 'open' else True if offset == 'close' else None
        timeInForce = 'GTX' if postOnly else timeInForce
        batchOrders = [{
            'symbol': self._params.getSymbol(symbol),
            'side': orderType[i][0].upper(),
            'quantity': str(vol[i]),
            'price': str(price[i]),
            'type': orderType[i][1].upper(),
            # 'reduceOnly': reduceOnly,
            'timeInForce': timeInForce,
            # 'newClientOrderId': clientOrderId[i],
        } for i in range(len(vol))]
        params = {
            'batchOrders': json.dumps(batchOrders)
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # ---------------------------------
        status = 'success'
        data = [{
            'orderId': int(d['orderId']),
            'code': 0,
            'info': 'success',
        } if 'orderId' in d else {
            'code': -1,
            'info': d,
        } for d in data]
        data = transform.normalizeMakeOrders(status=status, data=data)
        return data

    def cancelOrder(self, symbol, orderId):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'orderId': orderId,
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
        elif data.get('code', 0) == -2011:
            status = 'success'
            data = {
                'orderId': orderId,
                'code': 0,
                'info': data['msg'],
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
                and data['code'] == 200:
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
            'orderId': orderId,
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
                'matchPrice': float(data['avgPrice']),
                'vol': float(data['origQty']),
                'matchVol': float(data['executedQty']),
                'amt': float(data['price']) * float(data['origQty']),
                'side': data['side'].lower(),
                'offset': 'close' if data['reduceOnly'] else 'open',
                'type': data['type'].lower(),
                'postOnly': True if data['timeInForce'] == 'GTX' else False,
                'status': self._params.statusDict[data['status']] if data['status'] in self._params.statusDict else data['status'],
                'info': 'success',
            }
        data = transform.normalizeQueryOrder(status=status, data=data)
        return data

    def getOpenOrders(self, symbol):
        print(symbol)
        params = {
            'symbol': self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        print(data)
        print(1111)
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
            'side': d['side'].lower(),
            'offset': 'close' if d['reduceOnly'] else 'open',
            'type': d['type'].lower(),
            'postOnly': True if d['timeInForce'] == 'GTX' else False,
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
            'side': 'buy' if d['buyer'] else 'sell',
            'role': 'maker' if d['maker'] else 'taker',
        } for d in data]
        data = transform.normalizeDeals(data=data)
        return data

    def setLever(self, symbol, leverage=3):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'leverage': leverage,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data

class AccountWss(AccountRest, wss.websocketApp):

    def __init__(self, publicKey, privateKey, rspFunc, restartGap=0):
        self.publicKey = publicKey
        self.privateKey = privateKey
        self._params = _params()
        self.rspFunc = rspFunc
        self.author()  # 鉴权
        self.start(restartGap=8)
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

    def ping(self):
        while 1:
            time.sleep(60)
            try:
                self.refreshListenKey()
            except:
                pass

    def init(self):
        pass

    def author(self):
        self.listenKey = self.getListenKey()['listenKey']
        self.wssUrl = f"{self._params.acctWssUrl}/{self.listenKey}"

    def openRsp(self):
        print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Connected =====")

    def messageRsp(self, message):
        data = json.loads(message)
        # ---------------------------------
        if data['e'] == 'ACCOUNT_UPDATE':  # balance and position
            status = 'balance'
            balance = [{
                'symbol': d['a'].lower(),
                'balance': float(d['wb']),
                'available': float(d['cw']),
                'frozen': float(d['wb']) - float(d['cw']),
                'initMargin': float(d['wb']) - float(d['cw']),
            } for d in data['a']['B']]
            balance = transform.normalizeBalance(status=status, data=balance)
            self.rspFunc(balance)

            status = 'position'
            position = [{
                'symbol': self._params.accountWsSymbol(d['s']),
                'pos': float(d['pa']),
                'posSide': 1 if ['ps'] == 'LONG' else -1 if ['ps'] == 'SHORT' else None,
                'openPrice': float(d['ep']),
                'unrealProfitLoss': float(d['up']),
                'closeProfitLoss': float(d['cr']),
            } for d in data['a']['P']]
            position = transform.normalizePosition(status=status, data=position)
            self.rspFunc(position)
            return

        elif data['e'] == 'ORDER_TRADE_UPDATE':  # deals
            if data['o']['x'] == 'TRADE':
                status = 'deals'
                d = data['o']
                deals = [{
                    'ts': d['T'],
                    'symbol': self._params.accountWsSymbol(d['s']),
                    'myOrderId': d['i'],
                    'clientOrderId': d['c'],
                    'tradeId': d['t'],
                    'side': d['S'].lower(),
                    'type': d['o'].lower(),
                    'offset': 'close' if d['R'] else 'open',
                    'price': float(d['L']),
                    'vol': float(d['l']),
                    'fee': float(d['n']),
                    'feeAsset': d['N'].lower(),
                    'role': 'maker' if d['m'] else 'taker',
                    'status': self._params.statusDict[d['X']],
                }]
                deals = transform.normalizeDeals(status=status, data=deals)
                self.rspFunc(deals) 

            status = 'orders'
            d = data['o']
            orders = {
                'ts': data['E'],
                'symbol': self._params.accountWsSymbol(d['s']),
                'orderId': d['i'],
                'clientOrderId': d['c'],
                'price': float(d['p']),
                'matchPrice': float(d['ap']),
                'vol': float(d['q']),
                'matchVol': float(d['z']),
                'amt': float(d['p']) * float(d['q']),
                'side': d['S'].lower(),
                'type': d['o'].lower(),
                'status': self._params.statusDict[d['X']],
                'info': 'success',
            }
            orders = transform.normalizeQueryOrder(status=status, data=orders)
            self.rspFunc(orders)
            return

        else:
            return

        self.rspFunc(data)

    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Account Websocket Closed!! =====")


class DataWss(AccountWss):

    def __init__(self, symbol, publicKey='8xPSsNUylQUZEs81IWC3H28iLfY2lGbhH8aOMlLPlB9BEs2eEcXoraLBsx73rjsj', rspFunc=None, topics=['tick', 'depth']):
        self._params = _params()
        self.publicKey = publicKey
        self.wssUrl = self._params.wssUrl
        self.symbol = symbol
        self.increDepthStamp = 0
        self.increDepthFlag = True
        # self.start(ping_interval=5, ping_timeout=3)
        # if rspFunc is not None:
        #     self.messageRsp = rspFunc
        self.rspFunc = rspFunc
        self.topics = topics
        self.start()

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
        # self.subscribe(topic='clearPrice', symbol=self.symbol)
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
        # if self._messageRsp is not None:
        #     self._messageRsp(message)
        #     return
        rsp = json.loads(message)

        if self.rspFunc is not None: # 自定义Func
            self.rspFunc(rsp)
            return

        timestamp = int(time.time()*1000)
        # print(rsp, '\n')
        if 'e' in rsp:
            if rsp['e'] == 'aggTrade':  # tick
                data = [[rsp['T'], float(rsp['p']), float(rsp['q']), 1 if not rsp['m'] else -1]]
                info = f"_wssData_{self.symbol}_tick"
                setattr(self, info, [timestamp, data])
                # print(info)
                # print(data)

            elif rsp['e'] == 'depthUpdate' \
                    and len(rsp['b']) == 20 \
                    and len(rsp['a']) == 20:
                bids = np.array(rsp['b']).astype('float').tolist()
                asks = np.array(rsp['a']).astype('float').tolist()
                data = [rsp['E'], bids, asks, timestamp]
                info = f"_wssData_{self.symbol}_depth"
                setattr(self, info, [timestamp, data])
                # print(data[1][0], data[2][0])
                # print(info,data)
            elif 'kline' in rsp['e']:  # kline
                data = rsp['k']
                period = self._params.reverseKlinePeriods[data['i']]
                data = [[data['t'], float(data['o']), float(data['h']), float(data['l']), float(data['c']), float(data['v']), float(data['q'])]]
                info = f"_wssData_{self.symbol}_kline_{period}"
                setattr(self, info, [timestamp, data])
                # print(data, info)

            elif 'markPrice' in rsp['e']:
                # print(rsp)
                data1 = [rsp['E'], float(rsp['i']), float(rsp['p']), timestamp]
                data2 = [rsp['E'], float(rsp['r']), np.nan, timestamp]
                info1 = f"_wssData_{self.symbol}_clearPrice"
                info2 = f"_wssData_{self.symbol}_fundingRate"
                setattr(self, info1, [timestamp, data1])
                setattr(self, info2, [timestamp, data2])
                # print(data1, info1)
                # print(data2, info2)

            elif 'depthUpdate' in rsp.get('e', 0):  # 增量深度流
                if rsp['pu'] > getattr(self, 'lastu', 0):  # 未接上
                    increDepth = self.getIncreDepth()
                    # print(increDepth)
                    self.oriDepth = {
                        'bids': {float(b[0]): float(b[1]) for b in increDepth.get('bids', [[]])[:5]},
                        'asks': {float(a[0]): float(a[1]) for a in increDepth.get('asks', [[]])[:5]},
                    }
                    self.lastu = increDepth['lastUpdateId']
                    self.firstFollow = False
                    return
                elif rsp['U']<=self.lastu and rsp['u']>=self.lastu and not self.firstFollow:  # 第一次接上
                    self.firstFollow = True
                    # print('第一次接上')
                elif rsp['pu']==self.lastu and self.firstFollow:
                    # print('接上')
                    pass
                else:
                    return
                
                for b in rsp.get('b', []):
                    if float(b[1]) != 0.:
                        self.oriDepth['bids'][float(b[0])] = float(b[1])
                    else:
                        if float(b[0]) in self.oriDepth['bids']:
                            del self.oriDepth['bids'][float(b[0])]
                
                for a in rsp.get('a', []):
                    if float(a[1]) != 0.:
                        self.oriDepth['asks'][float(a[0])] = float(a[1])
                    else:
                        if float(a[0]) in self.oriDepth['asks']:
                            del self.oriDepth['asks'][float(a[0])]
                
                self.oriDepth['bids'] = dict(sorted(self.oriDepth['bids'].items(), key=lambda d: d[0], reverse=True)[:5])
                self.oriDepth['asks'] = dict(sorted(self.oriDepth['asks'].items(), key=lambda d: d[0])[:5])
                self.lastu = rsp['u']
                # print(self.oriDepth)
                data = [rsp['E'], [[k, v] for k, v in self.oriDepth['bids'].items()], [[k, v] for k, v in self.oriDepth['asks'].items()], timestamp]
                info = f"_wssData_{self.symbol}_increDepth"
                setattr(self, info, [timestamp, data])
                #print(data)


    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Closed!! =====")


if __name__ == '__main__':
    publicKey = 'j7157yZZp6SAOCXGjZf2ZVm21XiUr7Fbk3GuiMOMP5VQxTQigue1Wolqq4W9aoYE'
    privateKey = 't1Z3aOLkBrBpSoI7RCvaOyp0tlJ3GGMabpMFfdyTo8O8atY4OrNqi5kMKtQmuA4r'

    #publicKey = 'TT5xCssUK5y14o0Qwgc7cpPpZiRbo5vRyBKmerarpBxj07GpgMXGF9z9gER5OaST'
    #privateKey = 'oxCCyXVD5azX1pDr6DAQlRlnwwc4Ot5EiQcs39RgHuBK1aoyhJYqAD1lisZKolNt'
    
    publicKey, privateKey = '6QPbozcODQLsCtQMEIgPTJAfZOaqCDKeHJwi1bTAc6krlZlwhuYq4imrMk859FIn','y4l7mj4UcOcLqQMGesohHHZexPyZI6vzxi28FfuWr9zAAxSrDXPwUn4MxAhYCppY'

    task = AccountRest(publicKey, privateKey)
    # data = task.getInfo()
    # data = {d['symbol']: float(d['quoteVolume']) for d in data}
    # print(sorted(list(zip(data.values(), data.keys())))[::-1])
    # print(data['BTCUSDT'])
    # print(task.getAccount())
    # print(task.getBalance())
    # print(task.getContract())
    # print(task.getMarketRate())
    print(task.getPosition('axs/usdt'))
    print(task.setLever('axs/usdt'))
    # print(task.getFee('btc/usdt'))
    # print(task.getTick('btc/usdt'))
    # print(task.getDepth('/usdt', type=20))
    # print(task.getKline('btc/usdt', '1m', count=100))
    # print(task.getFundingRate('btc/usdt'))
    # print(task.getClearPrice('btc/usdt'))
    # print(task.cancelAll('btc/usdt'))
    # print(task.makeOrder('eos/usdt', vol=12.6, orderType='buy-market', clientOrderId='diy', offset='close'))
    # print(task.makeOrder('eos/usdt', 8.5, orderType='sell-market', clientOrderId='diy'))
    # print(task.makeOrder('fil/usdt', 746, price=43.25, postOnly=False, orderType='sell-limit'))
    # print(task.makeOrders('eos/usdt', [1, 2, 2, 2, 1], [2, 2.1, 2.2, 2.3, 10], postOnly=True, orderType='buy-limit'))
    # print(task.cancelOrder('btc/usdt', 7768526829))
    # print(task.queryOrder('eos/usdt',9809286976))
    # print(task.getOpenOrders('trx/usdt'))
    # print(task.getDeals('btc/usdt')['data'])
    # print(data[0]['tradeId'], data[-1]['tradeId'])
    # print(task.getDeals('fil/usdt', count=40)['data'][0])
    # data = task.getDeals('btc/usdt', count=20)['data']
    # print(data)
    # print(np.nansum([i['vol'] for i in data if i['ts']>=1610380800000]))
    # print(len(data))
    # vol = 0
    # fee = 0
    # data = task.getDeals('btc/usdt', count=250)['data']
    # print(data)
    # for i in data:
    #     vol += i['vol']
    #     fee += float(i['fee'])
    # print(vol, fee)
    '''--------------------------------------------------'''
    #def rspFunc(content):
        # print(content) 
        #pass
    # task = AccountWss(publicKey, privateKey, rspFunc, restartGap=10)
    # while 1:
    #     time.sleep(5)
    #     # task.restart()
    #     print(len(threading.enumerate()))
    # time.sleep(5)
    # print(task.makeOrder('btc/usdt', 0.001, price=10000, postOnly=False, orderType='buy-limit'))
    # print(task.cancelAll('btc/usdt'))

    '''--------------------------------------------------'''
    #task = DataWss('eth/usdt', topics=['depth'])#, rspFunc=rspFunc)
