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

        self.restUrl = 'https://dapi.binance.com'
        self.acctWssUrl = 'wss://dstream.binance.com/ws'
        self.wssUrl = 'wss://dstream.binance.com/ws'

        self.restPaths = {
            'getContract': 'GET /dapi/v1/exchangeInfo',
            'getAccount': 'GET /dapi/v1/account',
            'getBalance': 'GET /dapi/v1/balance',
            'getPosition': 'GET /dapi/v1/positionRisk',
            'getFee': 'GET /dapi/v1/commissionRate',
            'getNewPrice': 'GET /dapi/v1/ticker/price',
            'getTick': 'GET /dapi/v1/trades',
            'getDepth': 'GET /dapi/v1/depth',
            'getKline': 'GET /dapi/v1/klines',
            'getFundingRate': 'GET /dapi/v1/premiumIndex',  # 最新现货指数价格和Mark Price
            'getClearPrice': 'GET /dapi/v1/premiumIndex',   # 最新现货指数价格和Mark Price
            'setLever': 'POST /dapi/v1/leverage',
            'makeOrder': 'POST /dapi/v1/order',
            'makeOrders': 'POST /dapi/v1/batchOrders',
            'cancelOrder': 'DELETE /dapi/v1/order',
            'cancelOrders': 'DELETE /dapi/v1/batchOrders',
            'cancelAll': 'DELETE /dapi/v1/allOpenOrders',
            'queryOrder': 'GET /dapi/v1/order',
            'getOpenOrders': 'GET /dapi/v1/openOrders',
            'getDeals': 'GET /dapi/v1/userTrades',
            'getIncreDepth': 'GET /dapi/v1/depth',
            'getListenKey': 'POST /dapi/v1/listenKey',
            'refreshListenKey': 'PUT /dapi/v1/listenKey',
            'getExchangeInfo': 'GET /dapi/v1/exchangeInfo',
            'getOpenInterestHist': 'GET /futures/data/openInterestHist',
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

        # 币本位合约币种
        self.contactSize = {}
        coin = ['BTC','ETH','DOT','ADA','LINK','BNB','XRP','LTC','BCH']
        for i in coin:
            if i == 'BTC':
                self.contactSize[i] = 100
            else:
                self.contactSize[i] = 10

        self.legalCurrency = [
            'USDT', 'USD', 'BTC', 'ETH',
        ]

    def getSymbol(self, symbol):
        symbol = symbol.replace('/', '', 1).upper()
        symbol = symbol.replace('/', '_').upper()
        return symbol

    def accountWsSymbol(self, symbol):
        target, postfix = symbol.split('_')
        for lc in self.legalCurrency:
            if lc in target[-4:]:
                symbol = f"{symbol.split(lc)[0]}/{lc}/{postfix}".lower() if postfix!='PERP' else f"{symbol.split(lc)[0]}/{lc}".lower()
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

    def getContract(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        data = data['symbols']
        data = {self._params.accountWsSymbol(d['symbol']): d['contractSize'] for d in data}
        data = transform.normalizeTick(data=data)
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

    def getOpenInterestHist(self, pair='btc/usd', contractType='CURRENT_QUARTER', period='1d'):
        params = {
            'pair': pair.replace('/', '').upper(),
            'contractType': contractType,
            'period': period,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        #print(data)
        return data
    
    def getExchangeInfo(self):
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path)
        return data

    def getNewPrice(self, symbol):
        params = {
            'pair': symbol, #self._params.getSymbol(symbol),
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        return data

    def getPosition(self, symbol=None):
        if symbol is not None:
            if symbol == 'all':
                params = {}
            else:
                symbol2 = self._params.getSymbol(symbol).split('_')[0]
                symbol3 = self._params.getSymbol(symbol)
                params = {
                    'pair': symbol2,
                }
        else:
            params = {}
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
        # print(data)
        # ---------------------------------
        if len(data) > 0 and ((symbol is None) or (symbol!='all')):
            data = [{
                'symbol': symbol,
                'pos': float(d['positionAmt']),
                'posSide': 1 if d['positionSide'] == 'LONG' else -1 if d['positionSide'] == 'SHORT' else None,
                'openPrice': float(d['entryPrice']),
                'openAmt': float(d['positionAmt']) * float(d['entryPrice']),
                'liquidationPrice': float(d['liquidationPrice']),
                'unrealProfitLoss': float(d['unRealizedProfit']),
                'lever': float(d['leverage']),
                'positionSide': d['positionSide'],
            } for d in data if d['symbol'] == symbol3]
        elif len(data) > 0 and ((not symbol) or (symbol=='all')):
            data = [{
                'symbol': self._params.accountWsSymbol(d['symbol']),
                'pos': float(d['positionAmt']),
                'posSide': 1 if d['positionSide'] == 'LONG' else -1 if d['positionSide'] == 'SHORT' else None,
                'openPrice': float(d['entryPrice']),
                'openAmt': float(d['positionAmt']) * float(d['entryPrice']),
                'liquidationPrice': float(d['liquidationPrice']),
                'unrealProfitLoss': float(d['unRealizedProfit']),
                'lever': float(d['leverage']),
                'positionSide': d['positionSide'],
            } for d in data if float(d['positionAmt'])!=0.]
        else:
            data = [{
                'symbol': symbol,
                'pos': 0.,
            }]
        data = transform.normalizePosition(data=data)
        return data

    #def getFee(self, symbol):
    #    path = self._params.getRestPath(sys._getframe().f_code.co_name)
    #    data = self.request(path)
    #    return data
    def getFee(self, symbol):
        params = {
            'symbol': "BTCUSD_PERP",
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path,params=params)
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
        data = data[0]
        # print(data)
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

    def setLever(self, symbol):
        params = {
            'symbol': self._params.getSymbol(symbol),
            'leverage': 10,
        }
        path = self._params.getRestPath(sys._getframe().f_code.co_name)
        data = self.request(path, params=params)
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
        coin = symbol.split('/')[0].upper()
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
                'amt': float(data['origQty'])*self._params.contactSize[coin],
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
        coin = symbol.split('/')[0].upper()
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
            'amt': float(d['qty'])*self._params.contactSize[coin],
            'fee': d['commission'],
            'feeAsset': d['commissionAsset'].lower(),
            'side': 'buy' if d['buyer'] else 'sell',
            'role': 'maker' if d['maker'] else 'taker',
        } for d in data]
        data = transform.normalizeDeals(data=data)
        return data


class AccountWss(AccountRest, wss.websocketApp):

    def __init__(self, publicKey, privateKey, rspFunc, symbol=None, restartGap=0):
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
            print(f"exchange持仓:{position}")
            self.rspFunc(position)
            return

        elif data['e'] == 'ORDER_TRADE_UPDATE':  # deals
            #print(f"原始信息:{data}")
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
            coin = d['s'].split('USD_')[0]
            # print('原始成交信息：',d)
            orders = {
                'ts': data['E'],
                'symbol': self._params.accountWsSymbol(d['s']),
                'orderId': d['i'],
                'clientOrderId': d['c'],
                'price': float(d['p']),
                'matchPrice': float(d['ap']),
                'vol': float(d['q']),
                'matchVol': float(d['z']),
                'amt': float(d['q'])*self._params.contactSize[coin],
                'fee': float(d['n']) if d['X'] in ['FILLED','PARTIALLY_FILLED'] else 0,
                'feeAsset': d['N'].lower() if d['X'] in ['FILLED','PARTIALLY_FILLED'] else None,
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

    def __init__(self, symbol, publicKey='VrHFaOlXmIf1fQaKFgoyd2xKeX8FsAQ1TEtpUeiXwsIpzZFeZFuz0CXndcY4WGkU', rspFunc=None, topics=['tick', 'depth']):
        self._params = _params()
        self.publicKey = publicKey
        self.wssUrl = self._params.wssUrl
        self.symbol = symbol
        self.increDepthStamp = 0
        self.increDepthFlag = True
        self.topics = topics
        # self.start(ping_interval=5, ping_timeout=3)
        if rspFunc is not None:
            self.messageRsp = rspFunc
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
                # print('depth',info,  data)

            elif 'kline' in rsp['e']:  # kline
                data = rsp['k']
                period = self._params.reverseKlinePeriods[data['i']]
                data = [[data['t'], float(data['o']), float(data['h']), float(data['l']), float(data['c']), float(data['v']), float(data['q'])]]
                info = f"_wssData_{self.symbol}_kline_{period}"
                setattr(self, info, [timestamp, data])
                # print(data)

            elif 'markPrice' in rsp['e']:   # 标记价格
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
                        'bids': {b[0]: b[1] for b in increDepth.get('bids', [[]])[:5]},
                        'asks': {a[0]: a[1] for a in increDepth.get('asks', [[]])[:5]},
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
                    if b[1] != '0':
                        self.oriDepth['bids'][b[0]] = b[1]
                    else:
                        if b[0] in self.oriDepth['bids']:
                            del self.oriDepth['bids'][b[0]]
                
                for a in rsp.get('a', []):
                    if a[1] != '0':
                        self.oriDepth['asks'][a[0]] = a[1]
                    else:
                        if a[0] in self.oriDepth['asks']:
                            del self.oriDepth['asks'][a[0]]
                
                self.oriDepth['bids'] = dict(sorted(self.oriDepth['bids'].items(), key=lambda d: float(d[0]), reverse=True)[:5])
                self.oriDepth['asks'] = dict(sorted(self.oriDepth['asks'].items(), key=lambda d: float(d[0]))[:5])
                self.lastu = rsp['u']
                data = [rsp['E'], [[float(k), float(v)] for k, v in self.oriDepth['bids'].items()], [[float(k), float(v)] for k, v in self.oriDepth['asks'].items()], timestamp]
                info = f"_wssData_{self.symbol}_increDepth"
                setattr(self, info, [timestamp, data])
                print(data)

    def closeRsp(self, isRestart):
        if isRestart:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Reconnecting =====")
        else:
            print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} {self._params.exc} Websocket Closed!! =====")


if __name__ == '__main__':
    publicKey = '8rwgWj5UwWd99DgXdXKHg0cOxbskTSgIdqILJXWD0P5ioO4qa1beRUbMU5eJqooD'
    privateKey = 'O3kx53IuP5EYZdZ79YFuGaM7GWTPgH3HQghnFo0C2zcnvGVQk0ateUtXdjXLEadQ'
    publicKey,privateKey ='t6wVyKXuA2jxv1EGG6tzOYsTgUDhpR31tTegpY0vBYQEyu9m64onp77YMbSDcgmp', '1x3U6Vx6YHKmZZzq643LoqW1vhfceZLYPMRF1FheHhZ52QyXHcJgKCvKOdQA7aQG'
    publicKey,privateKey = 'ZNyFoy4DLFXw4vXAGEbW36OUU8chxXfQsE7EpW3SkhyqcUyejBGSZoClUK0KKKWj', 'pzxxkabA1DiSnYIJPptVbQfdokMvhXcThz6lWzGxVhC5EQSF0HQyT33vM2IyyNp9'
    task = AccountRest(publicKey, privateKey)
    #task.getExchangeInfo()
    # print(task.getContract())
    # print(task.getAccount())
    print(task.getBalance())
    # print(task.getPosition('all')) # 改动较大
    print(task.getFee('eth_usd_220624'))
    # print(task.getTick('eth_usd_210625'))
    # print(task.getDepth('eth_usd_210625'))
    # print(task.getKline('eth_usd_210625', '1m', count=100))
    # print(task.getFundingRate('eth_usd_210625'))
    # print(task.getClearPrice('eth_usd_210625'))
    symbol = "eth/usd/220624"
    print(task.setLever(symbol))
    symbol = "eth/usd/220930"
    print(task.setLever(symbol))
    # print(task.makeOrder('eth_usd_210625', 1, price=2900, orderType='sell-limit', clientOrderId='diy',))
    # print(task.makeOrder('eth_usd_210625', 1, orderType='sell-market', clientOrderId='diy'))
    # print(task.makeOrder('fil/usdt', 746, price=43.25, postOnly=False, orderType='sell-limit'))
    # print(task.cancelAll('eth_usd_210625'))
    # postOnly订单没下成功，也会返回orderID和success
    # print(task.makeOrders('eth_usd_210625', [3, 3, 3, 2, 3], [2301, 2405, 2407, 2521, 2900], postOnly=True, orderType='buy-limit'))
    # print(task.cancelOrders('eth_usd_210625', [1294883570, 1294883574, 1294883573, 1294883572, 1294883571]))
    # print(task.queryOrder('eth_usd_210625',1294001531))
    # print(task.cancelOrder('eth_usd_210625', 1293259387))
    # print(task.getOpenOrders('eth_usd_210625'))
    #data = task.getDeals('eth/usd/220624')
    #print(data)
    # data = task.getPosition()
    # print(data)
    # for i in data['data']:
    #     if i['symbol'] == 'eth_usd_210625':
    #         print(i)
    
    '''--------------------------------------------------'''
    # def rspFunc(content):
    #     rsp = json.loads(content)
    #     print(rsp)
    # task = AccountWss(publicKey, privateKey, rspFunc, restartGap=10)
    # while 1:
    #     time.sleep(5)
    #     # task.restart()
    #     print(len(threading.enumerate()))
    # time.sleep(5)
    # print(task.makeOrder('eth_usd_210625', 0.001, price=10000, postOnly=False, orderType='buy-limit'))
    # print(task.cancelAll('eth_usd_210625'))

    '''--------------------------------------------------'''
    # task = DataWss('btc/usd/210924', topics=['increDepthFlow'])
    
