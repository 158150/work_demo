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
# os.environ['httpproxy'] = 'http://127.0.0.1:1080'
# os.environ['https_pr_oxy'] = 'https://127.0.0.1:1080'


class _params():

    def __init__(self):
        """该类只放参数
        """
        self.exc = 'binanceUsdtSwap'

        self.restUrl = 'https://vapi.binance.com'
        self.acctWssUrl = 'wss://vstream.binance.com'
        self.wssUrl = 'wss://vstream.binance.com'

        self.restPaths = {
            'getOptionInfo': 'GET /vapi/v1/optionInfo',     # 获取当前交易对信息
            'getAccount': 'GET /fapi/v2/account',
            'getBalance': 'GET /fapi/v2/balance',
            'getPosition': 'GET /fapi/v2/positionRisk',
            'getFee': '',
            'getIndexPrice': 'GET /vapi/v1/index',          # 现货指数价格
            'getMarketPrice': 'GET /vapi/v1/mark',          # 最新标记价格
            'getTick': 'GET /fapi/v1/trades',
            'getDepth': 'GET /vapi/v1/depth',               # √
            'getKline': 'GET /vapi/v1/klines',              # √
            'getFundingRate': 'GET /fapi/v1/premiumIndex',
            'getClearPrice': 'GET /fapi/v1/premiumIndex',
            'makeOrder': 'POST /fapi/v1/order',
            'makeOrders': 'POST /fapi/v1/batchOrders',
            'cancelOrder': 'DELETE /fapi/v1/order',
            'cancelAll': 'DELETE /fapi/v1/allOpenOrders',
            'queryOrder': 'GET /fapi/v1/order',
            'getOpenOrders': 'GET /fapi/v1/openOrders',
            'getDeals': 'GET /fapi/v1/userTrades',
            'getIncreDepth': 'GET /fapi/v1/depth',
            'getListenKey': 'POST /fapi/v1/listenKey',
            'refreshListenKey': 'PUT /fapi/v1/listenKey',
        }

        self.wssPaths = {
            'tick': {'params': ['<symbol>@aggTrade'], 'method': 'SUBSCRIBE', 'id': 1},
            'depth': {'params': ['<symbol>@depth20@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'increDepthFlow': {'params': ['<symbol>@depth@100ms'], 'method': 'SUBSCRIBE', 'id': 1},
            'kline': {'params': ['<symbol>@kline_<period>'], 'method': 'SUBSCRIBE', 'id': 1},
            'clearPrice': {'params': ['<symbol>@markPrice@1s'], 'method': 'SUBSCRIBE', 'id': 1},

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
        return symbol.replace('/', '-').upper()

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
        req = self.wssPaths[key]
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

    def getOptionInfo(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data   

    def getAccount(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data

    def getBalance(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        # print(data)
        # ---------------------------------
        data = [{
            'symbol': d['asset'].lower(),
            'balance': float(d['balance']),
            'available': float(d['availableBalance']),
            'frozen': float(d['balance']) - float(d['availableBalance']),
        } for d in data]
        data = transform.normalizeBalance(data=data)
        return data

    def getIndexPrice(self, symbol):
        params = {
            'underlying': symbol.replace('/','').upper(),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data

    def getMarketPrice(self, symbol):
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

    def getDepth(self, symbol, type=100):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'limit': type,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params, isSign=False)
        # print(f"原始信息:{data}")
        # ---------------------------------
        timestamp = int(time.time()*1000)
        bids = np.array(data['data']['bids']).astype('float').tolist() if 'bids' in data['data'] else []
        asks = np.array(data['data']['asks']).astype('float').tolist() if 'asks' in data['data'] else []
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
        # print(f"原始信息:{data}")
        # ---------------------------------
        data = [[
            d['openTime'],        # ts
            float(d['open']),     # 开
            float(d['high']),     # 高
            float(d['low']),      # 低
            float(d['close']),    # 收
            float(d['volume']),   # 量
            # float(d['takerVolume']),    # 主动交易量
            # float(d['takerAmount']),    # 主动交易金额
        ] for d in data['data']]
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
        if rspFunc is not None:
            self.messageRsp = rspFunc
        self.topics = topics
        self.start()

    def init(self):
        # self.subscribe(topic='tick', symbol=self.symbol)
        # self.subscribe(topic='depth', symbol=self.symbol, type='step0')
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
        timestamp = int(time.time()*1000)
        print(rsp, '\n')
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

            elif 'depthUpdate' in rsp['e']:  # 增量深度流
                if rsp['pu'] > self.increDepthStamp:  # 未接上
                    time.sleep(1)  # 防止限频
                    increDepth = self.getIncreDepth()
                    self.oriDepth = {
                        'bids': {float(l[0]): float(l[1]) for l in increDepth['bids']},
                        'asks': {float(l[0]): float(l[1]) for l in increDepth['asks']}
                    }
                    self.increDepthStamp = increDepth['lastUpdateId']
                    self.firstFollow = False
                    return  # 跳出

                elif rsp['U'] <= self.increDepthStamp \
                        and rsp['u'] >= self.increDepthStamp \
                        and not self.firstFollow:  # 第一次接上
                    self.firstFollow = True
                    # print('接上')

                elif rsp['pu'] == self.increDepthStamp \
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
                # print(data)

    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Closed!! =====")


if __name__ == '__main__':
    publicKey = 'KrCKwCkicxsaod0MPBZ012IzBUtAYWtazDOZsFnwPqSmH8P95MNv8r7aplSRndma'
    privateKey = '3zqEyclLrxKAAoLDYFbEJi2VDhOGky5NbcU4S5rQkH8E8FC4ltmgPEXyBhpenwHg'

    task = AccountRest(publicKey, privateKey)
    # print(task.getOptionInfo())
    # print(task.getIndexPrice('btc/usdt'))
    # print(task.getAccount())
    # print(task.getBalance())
    # print(task.getPosition('all'))
    # print(task.getMarketPrice('btc/210723/26000/p'))
    print(task.getDepth('btc/20220121/40000/p', 10))
    # print(task.getKline('btc/210730/26000/p', '1d', count=10))
    # print(task.getFundingRate('btc/usdt'))
    # print(task.getClearPrice('btc/usdt'))
    # print(task.cancelAll('doge/usdt'))
    # print(task.makeOrder('etc/usdt', 0.1, orderType='sell-market', clientOrderId='diy', offset='close'))
    # print(task.makeOrder('eos/usdt', 8.5, orderType='sell-market', clientOrderId='diy'))
    # print(task.makeOrder('fil/usdt', 746, price=43.25, postOnly=False, orderType='sell-limit'))
    # print(task.makeOrders('eos/usdt', [1, 2, 2, 2, 1], [2, 2.1, 2.2, 2.3, 10], postOnly=True, orderType='buy-limit'))
    # print(task.cancelOrder('btc/usdt', 7768526829))
    # print(task.queryOrder('eos/usdt',9809286976))
    # print(task.getOpenOrders('trx/usdt'))
    # print(task.getDeals('trx/usdt')['data'][-1])
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
    # def rspFunc(content):
    #     print(content)
    # task = AccountWss(publicKey, privateKey, rspFunc, restartGap=10)
    # while 1:
    #     time.sleep(5)
    #     # task.restart()
    #     print(len(threading.enumerate()))
    # time.sleep(5)
    # print(task.makeOrder('btc/usdt', 0.001, price=10000, postOnly=False, orderType='buy-limit'))
    # print(task.cancelAll('btc/usdt'))

    '''--------------------------------------------------'''
    # task = DataWss('btc/usdt', rspFunc=rspFunc, topics=['depth'])
