import hmac
import base64
from hashlib import sha256
import hashlib
import json
import gzip
import requests
import urllib
import time
import numpy as np
import datetime
import zmq
import websocket
import traceback
import pickle
import threading
import os
import shutil
from urllib.request import Request,urlopen
# import DataAnalysis as das
#嵌入http代理
# os.environ['http_proxy'] = 'http://127.0.0.1:1080'
# os.environ['https_proxy'] = 'https://127.0.0.1:1080'



class SDK():
    '''服务器端'''

    def __init__(self,config,port=1001,proxy=False):
        #logTool
        # self._setLog()
        if proxy:
            os.environ['http_proxy'] = 'http://127.0.0.1:1080'
            os.environ['https_proxy'] = 'https://127.0.0.1:1080'
        self.config = config
        self.port = port
        #Server
        self.huobiRestUrl = 'https://api.huobi.pro'
        self.huobiFRestUrl = 'https://api.hbdm.com'
        self.huobiSwapRestUrl = 'https://api.hbdm.com'
        # self.huobiWsUrl = 'wss://api.huobi.pro/ws/v1'
        self.binanceRestUrl = 'https://api.binance.com'
        self.binanceSwapRestUrl = 'https://fapi.binance.com'
        # self.binanceSwapRestUrl = 
        self.wbfRestUrl = 'https://intra-api.wbfutures.me'        # 正向永续
        # self.wbfRestUrl = 'https://intra-api.wbfutures.me/api2'   # 全币种
        # self.wbfRestUrl = 'https://intra-api.wbfutures.me/api3'   # 反向合约
        # self.wbfRestUrl = 'https://www.wbfutures.pro/api'
        self.bitmexPSRestUrl = 'https://www.bitmex.com'
        self.okexPSRestUrl = 'https://www.okex.com'
        self.huobiSwapDic = {'btcusd': 'BTC-USD', 'ethusd': 'ETH-USD'}
        self.wbfSymbolDic = {'btcusdt':100000, 'ethusdt':100001, 'ethusd':200002}
        self.okexSymbolDic = {'btcusdt':'BTC-USDT-SWAP','ethusdt':'ETH-USDT-SWAP'}
        self.okexKlineDic = {'1m': '60', '3m': '180', '5m': '300',
                             '15m': '900', '30m': '1800', '1h': '3600',
                             '2h': '7200', '4h': '14400', '6h': '21600',
                             '12h': '43200', '1d': '86400', '1w': '604800'}

        # self.das = das.DataAnalysis()
        # self.listen()



    '''======================================================================='''
    '''============================= Signature ==============================='''
    '''======================================================================='''
    def _signature(self,sign=None,exc='huobi',params='',body=None,):
        '''generate digital signature'''
        if exc in ['huobi', 'huobiF', 'huobiSwap']:
            secretKey = self.config[f'{exc}PrivateKey'].encode('utf-8')
            sign = sign.encode('utf-8')
            signature = base64.b64encode(hmac.new(secretKey, sign, digestmod=sha256).digest())
            return signature.decode()
        elif exc == 'binance':
            secretKey = self.config['binancePrivateKey'].encode('utf-8')
            sign = sign.encode('utf-8')
            signature = hmac.new(secretKey, sign, digestmod=sha256).hexdigest()
            return signature
        elif exc == 'binanceSwap':
            secretKey = self.config['binanceSwapPrivateKey'].encode('utf-8')
            sign = sign.encode('utf-8')
            signature = hmac.new(secretKey, sign, digestmod=sha256).hexdigest()
            return signature      
        elif exc=='wbf':
            expires = int(time.time()+5)
            sign = f"apiExpires{expires}apiKey{self.config['wbfPublicKey']}{self.config['wbfPrivateKey']}"
            m = hashlib.md5()
            m.update(sign.encode())
            signature = m.hexdigest()
            return signature,expires
        elif exc=='bitmex':
            # expires = int(time.mktime(datetime.datetime.utcnow().timetuple()))
            expires = int(time.time()+10)
            secretKey = self.config['bitmexPrivateKey'].encode('utf-8')
            sign = f'{sign}{expires}{params}'.encode('utf-8') if body is None else f'{sign}{expires}{params}{body}'.encode('utf-8')
            # print(sign)
            signature = hmac.new(secretKey, sign, digestmod=sha256).hexdigest()
            return signature,expires
        elif exc=='okexPS':
            expires = int((time.mktime(datetime.datetime.utcnow().timetuple()))*1000)
            secretKey = self.config['okexPrivateKey'].encode('utf-8')
            sign = f'{expires}{sign}'.encode('utf-8') if body is None else f'{expires}{sign}{body}'.encode('utf-8')
            signature = hmac.new(secretKey, sign, digestmod=sha256).hexdigest()
            return signature,expires



    def _getUrl(self,method,params=None,exc='huobi',body=None):
        '''generate url request'''
        if exc=='huobi':
            rqUrl = self.huobiRestUrl
            apiKey = self.config['huobiPublicKey']

            method = method.split(' ')
            req = {}
            req['AccessKeyId'] = apiKey
            req['SignatureMethod'] = 'HmacSHA256'
            req['SignatureVersion'] = '2'
            req['Timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') #generate utc timestamp
            if params is not None:
                req.update(params)
            req = sorted(req.items(),key=lambda d:d[0],reverse=False)

            sign = urllib.parse.urlencode(req)
            sign = f"{method[0]}\n{rqUrl.split('//')[-1]}\n{method[1]}\n{sign}"
            req.append(('Signature',self._signature(sign,exc=exc)))
            req = urllib.parse.urlencode(req)
            url = f'{rqUrl}{method[1]}?{req}'
            # print(url)
            
        elif exc in ['huobiF','huobiSwap']:
            rqUrl = self.huobiFRestUrl
            apiKey = self.config[f'{exc}PublicKey']

            method = method.split(' ')
            req = {}
            req['AccessKeyId'] = apiKey
            req['SignatureMethod'] = 'HmacSHA256'
            req['SignatureVersion'] = '2'
            req['Timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') #generate utc timestamp
            if params is not None:
                req.update(params)
            req = sorted(req.items(),key=lambda d:d[0],reverse=False)

            sign = urllib.parse.urlencode(req)
            sign = f"{method[0]}\n{rqUrl.split('//')[-1]}\n{method[1]}\n{sign}"
            req.append(('Signature',self._signature(sign,exc=exc)))
            req = urllib.parse.urlencode(req)
            url = f'{rqUrl}{method[1]}?{req}'

        elif exc=='binance':
            rqUrl = self.binanceRestUrl
            # apiKey = self.config['binancePublicKey']

            method = method.split(' ')
            req = {}
            if params is not None:
                req.update(params)
            req['recvWindow'] = 2000
            # req['timestamp'] = int((time.mktime(datetime.datetime.utcnow().timetuple())+time.time()%1)*1000)
            req['timestamp'] = int(time.time()*1000)
            sign = urllib.parse.urlencode(req)
            req['signature'] = self._signature(sign,exc=exc)
            req = urllib.parse.urlencode(req)
            url = f'{rqUrl}{method[1]}?{req}'

        elif exc == 'binanceSwap':
            rqUrl = self.binanceSwapRestUrl

            method = method.split(' ')
            req = {}
            if params is not None:
                req.update(params)
            req['recvWindow'] = 2000
            # req['timestamp'] = int((time.mktime(datetime.datetime.utcnow().timetuple())+time.time()%1)*1000)
            req['timestamp'] = int(time.time()*1000)
            sign = urllib.parse.urlencode(req)
            req['signature'] = self._signature(sign,exc=exc)
            req = urllib.parse.urlencode(req)
            url = f'{rqUrl}{method[1]}?{req}'

        elif exc=='wbf':
            baseRsUrl = self.wbfRestUrl
            path = method.split(' ')[1]
            req = {}
            signature,expires = self._signature(exc=exc)
            if (params is not None) and ('filter' in params):
                req = {'filter':json.dumps(params['filter'])}
            elif params is not None:
                for k in params:
                    if params[k] is not None:
                        req[k] = params[k]
            req = urllib.parse.urlencode(req)
            if req=='':
                url = f'{baseRsUrl}{path}'
            else:
                url = f'{baseRsUrl}{path}?{req}'
            # print(url)
            return url,signature,expires

        elif exc=='bitmex':
            baseRsUrl = self.bitmexPSRestUrl
            method,path = method.split(' ')
            req = {}
            if (params is not None) and ('filter' in params):
                req = {'filter':json.dumps(params['filter'])}
            elif params is not None:
                for k in params:
                    if params[k] is not None:
                        req[k] = params[k]
            req = urllib.parse.urlencode(req)
            if req=='':
                url = f'{baseRsUrl}{path}'
                sign = f'{method}{path}'
            else:
                url = f'{baseRsUrl}{path}?{req}'
                sign = f'{method}{path}?{req}'
            # print(url)
            signature,expires = self._signature(sign=sign,exc=exc,body=body)
            return url,signature,expires       

        elif exc=='okexPS':
            baseRsUrl = self.okexPSRestUrl
            method,path = method.split(' ')
            req = {}
            if params is not None:
                for k in params:
                    if params[k] is not None:
                        req[k] = params[k]
            req = urllib.parse.urlencode(req)
            url = f'{baseRsUrl}{path}' if req=='' else f'{baseRsUrl}{path}?{req}'
            sign = f'{method}{path}' if req=='' else f'{method}{path}?{req}'
            signature,expires = self._signature(sign=sign,exc=exc,body=body)
            return url,signature,expires

        return url


    def _httpReq(self,method,url=None,params=None,body=None,exc='huobi',headers=None):
        '''http request method'''
        if exc == 'huobi':
            # print(url,params)
            method = method.split(' ')
            if 'GET' in method:
                res = requests.get(url,timeout=10)
            elif 'POST' in method:
                res = requests.post(url,data=json.dumps(params),headers={'Content-Type': 'application/json'},timeout=10)
            res = res.json()
            # print(res)
            if res['status'] != 'ok':
                if res['err-code']=='order-value-min-error':
                    res['err-code']='InvalidOrder'
                elif res['err-code']=='base-record-invalid':
                    res['err-code']='OrderNotFound'
                elif res['err-code']=='not-found':
                    res['err-code']='OrderNotFound'
                elif res['err-code']=='account-frozen-balance-insufficient-error':
                    res['err-code']='InsufficientFunds'
                elif res['err-code']=='api-signature-not-valid':
                    res['err-code']='AuthenticationError'
                return {'error':res['err-code']}
                # raise Exception(f"errCode:{res['err-code']}  errMsg:{res['err-msg']}")
            try:
                return res['data'] 
            except:
                return res

        elif exc in ['huobiF','huobiSwap']:
            method = method.split(' ')
            if 'GET' in method:
                res = requests.get(url,timeout=10)
            elif 'POST' in method:
                res = requests.post(url,data=json.dumps(params),headers={'Content-Type': 'application/json'},timeout=10)
            res = res.json()
            if res['status'] == 'error':
                if res['err_msg']=='order-value-min-error':
                    res['err_msg']='InvalidOrder'
                # elif res['err-code']=='base-record-invalid':
                #     res['err-code']='OrderNotFound'
                # elif res['err-code']=='not-found':
                #     res['err-code']='OrderNotFound'
                elif res['err_msg']=='Insufficient margin available':
                    res['err_msg']='InsufficientFunds'
                # elif res['err-code']=='api-signature-not-valid':
                #     res['err-code']='AuthenticationError'
                return {'error':res['err_msg']}
                # raise Exception(f"errCode:{res['err-code']}  errMsg:{res['err-msg']}")
            # elif 'errors' in res['data']:
            #     if res['data']['errors'][0]['err_msg']=='This order doesnt exist.':
            #         res['err_msg']='OrderNotFound'
            #         return {'error':res['err_msg']}
            return res

        elif exc=='binance':
            method = method.split(' ')
            apiKey = self.config['binancePublicKey']
            if 'GET' in method:
                res = requests.get(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            elif 'POST' in method:
                res = requests.post(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            elif 'DELETE' in method:
                res = requests.delete(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            res = res.json()
            if 'error' in res:
                res['error'] = 'InsufficientFunds'
            elif 'code' in res:
                if res['code']==-1022:
                    res = {'error':'AuthenticationError'}
                elif res['code']==-2013:
                    res = {'error':'OrderNotFound'}
            return res

        elif exc=='binanceSwap':
            # print(url)
            method = method.split(' ')
            apiKey = self.config['binanceSwapPublicKey']
            # print(url)
            if 'GET' in method:
                res = requests.get(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            elif 'POST' in method:
                res = requests.post(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            elif 'DELETE' in method:
                res = requests.delete(url,headers={'X-MBX-APIKEY': apiKey},timeout=10)
            res = res.json()
            if 'error' in res:
                res['error'] = 'InsufficientFunds'
            elif 'code' in res:
                if res['code']==-1022:
                    res = {'error':'AuthenticationError'}
                elif res['code']==-2013:
                    res = {'error':'OrderNotFound'}
            return res     

        elif exc=='wbf':
            url,signature,expires = self._getUrl(method,params,exc=exc)
            # print(url)
            method = method.split(' ')[0]
            if headers is None:
                headers = {'content-type':'application/json',
                           'Accept':'application/json',
                           'apiExpires':str(expires),
                           'apiKey':self.config['wbfPublicKey'],
                           'signature':signature}
            # print(url,params,headers,method)
            # if method == 'DELETE':
            #     res = requests.delete(url,params=params,headers=headers)
            #     res = res.json()
            #     return res
            if method=='GET':
                res = requests.get(url,headers=headers,timeout=10)
            elif method=='POST':
                if body is not None:
                    # print(f'body:{body}')
                    res = requests.post(url,headers=headers,data=body,timeout=10)
                else:
                    res = requests.post(url,headers=headers,timeout=10)
            elif method=='DELETE':
                res = requests.delete(url,headers=headers,data=body,timeout=10) if body is not None else requests.delete(url,headers=headers,timeout=10)
            # print(res)
            rsp = res.json()
            return rsp

        elif exc=='bitmex':
            url,signature,expires = self._getUrl(method,params,exc=exc,body=body)
            # print(url)
            method = method.split(' ')[0]
            headers = {'content-type':'application/json',
                       'api-expires':str(expires),
                       'api-key':self.config['bitmexPublicKey'],
                       'api-signature':signature}
            if method=='GET':
                res = requests.get(url,headers=headers,timeout=10)
            elif method=='PUT':
                res = requests.put(url,headers=headers,timeout=10)
            elif method=='POST':
                if body is not None:
                    # print(f'body:{body}')
                    res = requests.post(url,headers=headers,data=body,timeout=10)
                else:
                    res = requests.post(url,headers=headers,timeout=10)
            elif method=='DELETE':
                res = requests.delete(url,headers=headers,data=body,timeout=10)
            rsp = res.json()
            return rsp

        elif exc=='okexPS':
            url,signature,expires = self._getUrl(method,params,exc=exc,body=body)
            method = method.split(' ')[0]
            headers = {'content-type':'application/json',
                       'OK-ACCESS-KEY':self.config['okexPublicKey'],
                       'OK-ACCESS-SIGN':signature,
                       'OK-ACCESS-TIMESTAMP':str(expires),
                       'OK-ACCESS-PASSPHRASE':self.config['okexPassphrase']}
            if method=='GET':
                res = requests.get(url,headers=headers,timeout=10)
            elif method=='POST':
                if body is not None:
                    res = requests.post(url,headers=headers,data=body,timeout=10)
                else:
                    res = requests.post(url,headers=headers,timeout=10)
            rsp = res.json()
            return rsp



    '''======================================================================='''
    '''============================= Spot Tools ==============================='''
    '''======================================================================='''  
    def initExchange(self,exc='huobi',accId=None):
        '''exc='huobi',accId=None'''
        '''弃用'''
        if exc=='huobi':
            try:
                if accId is None:
                    setattr(self,f"{self.config['strategyName']}{self.config['strategyId']}huobiaccId",self.getAccounts(exc='huobi')[0]['id'])
                else:
                    setattr(self,f"{self.config['strategyName']}{self.config['strategyId']}huobiaccId",str(accId))
                self._loadOrders(exc) #重读orderbook
                # self._auth(exc)
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} huobi accountId {getattr(self,f"{self.config['strategyName']}{self.config['strategyId']}huobiaccId")} Successfully==='''
            except:
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} huobi account Failed!!!==='''
                print(traceback.format_exc())
        elif exc=='binance':
            try:
                self.getAccounts(exc=exc)
                self._loadOrders(exc) #重读orderbook
                # self._auth(exc)
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Successfully!!!==='''
            except:
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Failed!!!==='''
                print(traceback.format_exc())

        elif exc=='wbf':
            try:
                self.getBalance(exc=exc)
                self._loadOrders(exc) #重读orderbook
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Successfully!!!==='''
            except:
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Failed!!!==='''
                print(traceback.format_exc())
        elif exc=='bitmex':
            try:
                self.getAccounts(exc=exc)
                self._loadOrders(exc)
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Successfully!!!==='''
            except:
                msg = f'''===Login {self.config['strategyName']}{self.config['strategyId']} {exc} account Failed!!!==='''
                print(traceback.format_exc())



        else:
            msg = {'error':'ExchangeError'}
        # print(msg)
        return msg


    def getContract(self,symbol=None,exc='wbf'):
        '''get contract info'''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryContract'
            data = self._httpReq(req,exc=exc)
        elif exc=='huobiF':
            req = 'GET /api/v1/contract_contract_info'
            info = symbol.split('_')
            symbol = info[0].upper()
            contractType = 'this_week' if info[1]=='cw' else\
                            'next_week' if info[1]=='nw' else\
                            'quarter' if info[1]=='cq' else\
                            'next_quarter' if info[1] == 'nq' else None
            params = {'symbol':symbol,'contract_type':contractType}
            url = self._getUrl(req,params=params,exc='huobiF')
            data = self._httpReq(req,url,exc='huobiF') 
        return data


    def getAccounts(self,symbol=None,exc='huobi'):
        '''
        获取账户信息
        params: exc: huobi/binance/bitmex/okex/wbf
        '''
        if exc=='huobi':
            if 'huobiAcctId' in dir(self):
                return self.huobiAcctId
            else:
                GET_ACCOUNTS = 'GET /v1/account/accounts'
                url = self._getUrl(GET_ACCOUNTS,exc=exc)
                data = self._httpReq(GET_ACCOUNTS,url,exc=exc)
                self.huobiAcctId = data
                return data
            # print(data)
            # return data
        elif exc=='binance':
            GET_ACCOUNTS = 'GET /api/v3/account'
            url = self._getUrl(GET_ACCOUNTS,exc=exc)
            data = self._httpReq(GET_ACCOUNTS,url,exc=exc)
            # return data
        elif exc=='binanceSwap':
            GET_ACCOUNTS = 'GET /fapi/v1/account'
            url = self._getUrl(GET_ACCOUNTS, exc=exc)
            data = self._httpReq(GET_ACCOUNTS, url, exc=exc)
        # elif exc=='wbf':
        #     req = 'GET /api/v1/future/user'
        #     data = self._httpReq(req,self._getUrl(req,exc=exc),exc=exc)
        elif exc=='bitmex':
            req = 'GET /api/v1/user'
            data = self._httpReq(req,exc=exc)
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_account_info'
            url = self._getUrl(req,exc='huobiF')
            # print(url)
            data = self._httpReq(req,url,exc='huobiF')

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_account_info'
            url = self._getUrl(req,exc=exc)
            params = {''}
            symbol = symbol if symbol is None else self.huobiSwapDic[symbol]
            params = {'contract_code':symbol}
            data = self._httpReq(req,url,params=params,exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getFAccounts(self,symbol=None,exc='huobi'):
        '''
        获取合约账户信息
        symbol可选参数
        '''
        if exc=='huobi':
            GET_ACCOUNTS = 'POST /api/v1/contract_account_info'
            params = {}
            if symbol is not None:
                params['symbol'] = symbol.upper()
            url = self._getUrl(GET_ACCOUNTS,exc='huobiF')
            data = self._httpReq(GET_ACCOUNTS,url,params=params,exc='huobiF')
            return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data

    def getBalance(self,currencyId=None,exc='huobi'):
        '''
        获取账户余额
        params: exc: huobi/binance/bitmex/okex/wbf
        
        '''
        if exc=='huobi':
            # try:
            accId = self.getAccounts(exc='huobi')[0]['id']
            # except:
            #     return {'error': 'initExchange Huobi Firstly'}
            GET_BALANCE = f'GET /v1/account/accounts/{accId}/balance'
            params = {'account-id':accId}
            url = self._getUrl(GET_BALANCE,params=params,exc=exc)
            data = self._httpReq(GET_BALANCE,url,exc=exc)
            # return data  

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_account_position_info'
            params = {'contract_code':self.huobiSwapDic[currencyId]}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='binance':
            data = self.getAccounts(exc='binance')['balances']
        elif exc=='wbf':
            req = 'GET /api/v1/future/margin'
            data = self._httpReq(req,exc=exc)
            if currencyId is not None:
                data['data'] = [i for i in data['data'] if i['currencyId']==currencyId]
            data['data'] = [{}] if data['data']==[] else data['data']
        elif exc=='bitmex':
            req = 'GET /api/v1/user/margin'
            data = self._httpReq(req,exc=exc)
        elif exc=='huobiF':
            data = self.getAccounts(exc=exc)['data']
            # GET_BALANCE = 'POST /api/v1/contract_position_info'
            # params = {}
            # # if symbol is not None:
            # #     params['symbol'] = symbol.upper()
            # url = self._getUrl(GET_BALANCE,exc='huobiF')
            # data = self._httpReq(GET_BALANCE,url,params=params,exc='huobiF')
            # return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getFBalance(self,symbol=None,exc='huobi'):
        '''
        获取合约账户余额
        symbol可选参数
        '''
        if exc=='huobi':
            GET_BALANCE = 'POST /api/v1/contract_position_info'
            params = {}
            if symbol is not None:
                params['symbol'] = symbol.upper()
            url = self._getUrl(GET_BALANCE,exc='huobiF')
            data = self._httpReq(GET_BALANCE,url,params=params,exc='huobiF')
            return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getPosition(self,symbol=None,contractId=None,exc='wbf'):
        '''获取仓位信息'''
        if exc=='wbf':
            req = 'GET /api/v1/future/position'
            data = self._httpReq(req,exc=exc)
            if data['data']==[]:
                return data
            else:
                if contractId is not None:
                    data['data'] = [i for i in data['data'] if i['contractId']==contractId]
            return data 
        elif exc=='binanceSwap':
            GET_ACCOUNTS = 'GET /fapi/v1/positionRisk'
            url = self._getUrl(GET_ACCOUNTS, exc=exc)
            data = self._httpReq(GET_ACCOUNTS, url, exc=exc)
        elif exc=='bitmex':
            req = 'GET /api/v1/position'
            data = self._httpReq(req,params={'filter':{'symbol':symbol.upper()}},exc=exc)
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_position_info'
            url = self._getUrl(req,exc='huobiF')
            data = self._httpReq(req,url,exc='huobiF') 
        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_position_info'
            symbol = symbol if symbol is None else self.huobiSwapDic[symbol]
            params = {'contract_code':symbol}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getMargin(self,varietyId,contractId,exc='wbf'):
        '''获取保证金梯度
        varietyId 品种Id
        contractId 合约Id
        '''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryVarietyMargin'
            data = self._httpReq(req,params={'filter':{'varietyId':varietyId,
                                             'contractId':contractId}},exc=exc)
        return data


    def getFFee(self,symbol=None,exc='huobi'):
        '''get futures transaction fee'''
        if exc=='huobi':
            GET_FEE = 'POST /api/v1/contract_fee'
            params = {}
            if symbol is not None:
                params['symbol'] = symbol.upper()
            url = self._getUrl(GET_FEE,exc='huobiF')
            data = self._httpReq(GET_FEE,url,params=params,exc='huobiF')
            return data


    def makeOrder(self,symbol,amount,orderType='buy-market',price=None,offset='open',leverRate=1,source=None,clientId=None,stopPrice=None,operator=None,timeInForce='GTC',exc='huobi'):
        '''
        params: symbol
                amount: represents vol if not market-price order
                orderType: buy-market/sell-market/buy-limit/sell-limit/buy-ioc/sell-ioc/buy-limit-maker/
                      sell-limit-maker/buy-stop-limit/sell-stop-limit
                price: limit order price
                source: spot-api/margin-api/super-margin-api
                clientId: diy-orderID less than 64bytes
                stopPrice: stop order price
                operater: gte represents >= / lte represents <=
                exc: exchange name
        '''
        prefix = f"{self.config['strategyName']}{self.config['strategyId']}{exc}Orders"
        if exc=='huobi':
            # try:
            accId = self.getAccounts(exc='huobi')[0]['id']
            # except:
            #     return {'error': 'initExchange Huobi Firstly'}
            MAKE_ORDER = 'POST /v1/order/orders/place'
            params = {'account-id':accId, 'symbol':symbol, 'type':orderType, 'amount':amount}
            extraKey = ['price','source','client-order-id','stop-price','operator']
            extra = [price,source,clientId,stopPrice,operator]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(MAKE_ORDER,exc=exc)
            # t1 = time.time()
            data = self._httpReq(MAKE_ORDER,url,params=params,exc=exc)
            # data = {'data':'12345'}
            # if 'data' in data:
            #     temp = getattr(self,prefix)
            #     temp.append([data['data'],price,amount])
            #     setattr(self,prefix,temp)
            #     self._recordOrders(temp,exc)
            # t2 = time.time()
            # print(f'请求耗时{t2-t1}')
            # return data
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_order'
            info = symbol.split('_')
            symbol = info[0].upper()
            direction,order_price_type = orderType.split('-')
            contract_type = 'this_week' if info[1]=='cw' else\
                            'next_week' if info[1]=='nw' else\
                            'quarter' if info[1]=='cq' else\
                            'next_quarter' if info[1] == 'nq' else None
            params = {'symbol':symbol, 'contract_type':contract_type, 'client_order_id':clientId,
                      'price':price, 'direction':direction, 'order_price_type':order_price_type,
                      'offset':offset, 'lever_rate':leverRate, 'volume':amount}
            # print(params)
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_order'
            direction,order_price_type = orderType.split('-')
            order_price_type = 'opponent' if order_price_type=='market' else order_price_type
            params = {'contract_code':self.huobiSwapDic[symbol],'client_order_id':clientId,'price':price,
                      'volume':amount,'direction':direction,'offset':offset,'lever_rate':leverRate,
                      'order_price_type':order_price_type}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='binance':
            #现只支持市价单和限价单
            MAKE_ORDER = 'POST /api/v3/order'
            orderInfo = orderType.split('-')
            params = {'symbol':symbol.upper(),'side':orderInfo[0],'type':orderInfo[1].upper(),'quantity':amount}
            extraKey = ['timeInForce','price']
            extra = [timeInForce,price]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(MAKE_ORDER,params=params,exc=exc)
            data = self._httpReq(MAKE_ORDER,url,exc=exc)
            # data = {'orderId':12345,'clientOrderId':'12487692'}
            # if 'orderId' in data:
            #     temp = getattr(self,prefix)
            #     temp.append([data['orderId'],price,amount])
            #     setattr(self,prefix,temp)
            #     self._recordOrders(temp,exc)
            # return data
        elif exc=='binanceSwap':
            # 现只支持市价单和限价单
            MAKE_ORDER = 'POST /fapi/v1/order'
            orderInfo = orderType.split('-')
            params = {'symbol':symbol.upper(),'side':orderInfo[0].upper(),'type':orderInfo[1].upper(),'quantity':amount}
            extraKey = ['timeInForce','price']
            extra = [timeInForce,price]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(MAKE_ORDER,params=params,exc=exc)
            data = self._httpReq(MAKE_ORDER,url,exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def makeFOrder(self,symbol,amount,offset='open',leverRate=10,orderType='buy-limit',price=None,clientId=None,stopPrice=None,timeInForce=None,exc='binance'):
        #contractType:this_week,next_week,quarter
        #same to makeOrder for futures
        prefix = f"{self.config['strategyName']}{self.config['strategyId']}{exc}Orders"
        if exc=='binance':
            MAKE_ORDER = 'POST /fapi/v1/order'
            orderInfo = orderType.split('-')
            params = {'symbol':symbol.upper(),'side':orderInfo[0].upper(),'type':orderInfo[1].upper(),'quantity':amount}
            extraKey = ['timeInForce','price']
            extra = [timeInForce,price]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(MAKE_ORDER,params=params,exc='binanceSwap')
            data = self._httpReq(MAKE_ORDER,url,exc='binanceSwap')
            if 'orderId' in data:
                temp = getattr(self,prefix)
                temp.append([data['orderId'],price,amount])
                setattr(self,prefix,temp)
                self._recordOrders(temp,exc)

        elif exc=='huobi':
            MAKE_ORDER = 'POST /api/v1/contract_order'
            orderInfo = orderType.split('-')
            params = {'contract_code':symbol.upper(),'direction':orderInfo[0],'volume':amount,
                      'order_price_type':orderInfo[1],'offset':offset,'lever_rate':leverRate}
            extraKey = ['price','client-order-id']
            extra = [price,clientId]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(MAKE_ORDER,exc='huobiF')
            data = self._httpReq(MAKE_ORDER,url,params=params,exc='huobiF')
            # print(data)
            if 'data' in data:
                temp = getattr(self,prefix)
                temp.append([data['data'],price,amount])
                setattr(self,prefix,temp)
                self._recordOrders(temp,exc)

        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data       


    def makePSOrder(self,contractId,amount,offset='open',leverRate=10,orderType='buy-limit',orderSubType=0,price=None,symbol=None,marginType=1,marginRate=0,clientOrderId=None,exc='wbf'):
        '''same to makeOrder for perpetual swap'''
        if exc=='wbf':
            req = 'POST /api/v1/future/order'
            side,orderType = orderType.split('-')
            side = 1 if side=='buy' else -1
            orderType = 1 if orderType=='limit' else 3
            offset = 1 if offset=='open' else 2
            body = {'side':side,'quantity':str(amount),'orderType':orderType,'positionEffect':offset,
                    'marginType':marginType,'marginRate':str(marginRate),'orderSubType':orderSubType}
            extraKey = ['price','symbol','contractId','clientOrderId']
            extra = [str(price),symbol,contractId,str(clientOrderId)]
            for i,e in enumerate(extra):
                if (e is not None) and (e != 'None'):
                    body[extraKey[i]] = e
            data = self._httpReq(req,body=json.dumps(body,separators=(',',':')),exc=exc)
            return data
        elif exc=='bitmex':
            req = 'POST /api/v1/order'
            side,orderType = orderType.split('-')
            side = 'Buy' if side=='buy' else 'Sell'
            orderType = 'Market' if orderType=='market' else 'Limit'
            body = {'symbol':contractId.upper(),'side':side,'orderQty':amount,'ordType':orderType}
            extraKey = ['price']
            extra =  [str(price)]
            for i,e in enumerate(extra):
                if (e is not None) and (e != 'None'):
                    body[extraKey[i]] = e
            data = self._httpReq(req,body=json.dumps(body),exc=exc)
            return data


    def makePSOrders(self,contractId,amount,price=None,orderTypeList=None,offset='open',leverRate=10,orderType='buy-limit',marginType=1,exc='wbf'):
        '''批量下单'''
        if exc=='wbf':
            req = 'POST /api/v1/future/orders'
            price = [None]*len(amount) if price is None else price
            side,orderType = orderType.split('-')
            offset = 1 if offset=='open' else 2

            if orderTypeList is None:
                side = 1 if side=='buy' else -1
                orderType = 1 if orderType=='limit' else 3
                body = {'orders':[{'side':side,'orderQty':str(amount[i]),'orderType':orderType,'positionEffect':offset,
                                   'marginType':marginType,'orderPrice':str(price[i]),'contractId':contractId} for i in range(len(amount))]}
            else:
                sideList = [1 if 'buy' in i else -1 for i in orderTypeList]
                orderTypeList = [1 if 'limit' in i else 3 for i in orderTypeList]
                body = {'orders':[{'side':sideList[i],'orderQty':str(amount[i]),'orderType':orderTypeList[i],'positionEffect':offset,
                                   'marginType':marginType,'orderPrice':str(price[i]),'contractId':contractId} for i in range(len(amount))]}
            data = self._httpReq(req,body=json.dumps(body,separators=(',',':')),exc=exc)

        elif exc=='bitmex':
            req = 'POST /api/v1/order/bulk'
            price = [None]*len(amount) if price is None else price
            side,orderType = orderType.split('-')
            side = 'Buy' if side=='buy' else 'Sell'
            orderType = 'Market' if orderType=='market' else 'Limit'
            body = {'orders':[{'symbol':contractId.upper(),'side':side,'price':price[i],'orderQty':amount[i],'ordType':orderType} for i in range(len(amount))]}
            data = self._httpReq(req,body=json.dumps(body),exc=exc)
        return data

    def cancelOrder(self,orderId,symbol=None,clientId=False,exc='huobi'):
        '''
        clientId default False
        if True, the orderId is client diy id

        cancel batchOrders if orderId is list type

        binance cancel need symbol
        '''
        if exc=='huobi':
            if isinstance(orderId,list):
                CANCEL_ORDER = 'POST /v1/order/orders/batchcancel'
                params = {'order-ids':orderId} if not clientId else {'client-order-ids':orderId}
            else:
                CANCEL_ORDER = f'POST /v1/order/orders/{orderId}/submitcancel' if not clientId else\
                               'POST /v1/order/orders/submitCancelClientOrder'
                params = {'order-id':str(orderId)} if not clientId else {'client-order-id':str(orderId)}
            
            url = self._getUrl(CANCEL_ORDER,exc=exc)
            data = self._httpReq(CANCEL_ORDER,url,params=params,exc=exc)
            # if 'data' in data
            # return data
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_cancel'
            params = {'order_id':orderId, 'client_order_id':clientId,'symbol':symbol.split('_')[0].upper()}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_cancel'
            params = {'order_id':orderId,'contract_code':self.huobiSwapDic[symbol]}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='binance':
            CANCEL_ORDER = "DELETE /api/v3/order"
            params = {'symbol':symbol.upper(),'orderId':int(orderId)}
            url = self._getUrl(CANCEL_ORDER,params=params,exc=exc)
            data = self._httpReq(CANCEL_ORDER,url,exc=exc)  
        elif exc=='binanceSwap':
            CANCEL_ORDER = "DELETE /fapi/v1/order"
            params = {'symbol':symbol.upper(),'orderId':int(orderId)}
            url = self._getUrl(CANCEL_ORDER,params=params,exc=exc)
            data = self._httpReq(CANCEL_ORDER,url,exc=exc)       
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def cancelAll(self,symbol=None,exc='wbf'):
        if exc=='huobiF':
            req = 'POST /api/v1/contract_cancelall'
            symbol,contract_type = symbol.split('_')
            params = {'symbol':symbol.upper(),'contract_type':contract_type}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc) 

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_cancelall'
            params = {'contract_code':self.huobiSwapDic[symbol]}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc) 

        elif exc=='binance':
            req = 'DELETE /api/v3/openOrders'
            params = {'symbol':symbol.upper()}
            url = self._getUrl(req,params=params,exc=exc)
            # print(url)
            data = self._httpReq(req,url,exc=exc)

        elif exc=='huobi':
            req = 'POST /v1/order/orders/batchCancelOpenOrders'
            accId = self.getAccounts(exc='huobi')[0]['id']
            params = {'account-id':accId,'symbol':symbol}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)     

        else:
            data = self.cancelPSAll(symbol,exc=exc)
        return data

    def cancelFOrder(self,orderId,clientId=False,exc='binance',symbol=None):
        '''cancelOrder for futures'''
        if exc=='binance':
            CANCEL_ORDER = "DELETE /fapi/v1/order"
            params = {'symbol':symbol.upper(),'orderId':int(orderId)}
            url = self._getUrl(CANCEL_ORDER,params=params,exc='binanceSwap')
            data = self._httpReq(CANCEL_ORDER,url,exc='binanceSwap')    
        elif exc=='huobi':
            CANCEL_ORDER = f'POST /api/v1/contract_cancel'
            params = {'order_id':str(orderId),'symbol':symbol.upper()}
            
            url = self._getUrl(CANCEL_ORDER,exc='huobiF')
            data = self._httpReq(CANCEL_ORDER,url,params=params,exc='huobiF')              
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data        


    def cancelPSOrder(self,contractId=None,orderId=None,exc='wbf'):
        '''cancelOrder for perpetual swap'''
        if exc=='wbf':
            req = 'DELETE /api/v1/future/order'
            data = self._httpReq(req,params={'filter':{'contractId':contractId,
                                                       'originalOrderId':str(orderId)}},exc=exc)
        elif exc=='bitmex':
            req = 'DELETE /api/v1/order'
            body = {'orderID':orderId}
            data = self._httpReq(req,body=json.dumps(body),exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def cancelPSOrders(self,contractId,orderIds,clientOrderIds=None,exc='wbf'):
        '''批量撤单'''
        if exc=='wbf':
            req ='DELETE /api/v1/future/orders'
            if clientOrderIds is None:
                lis = [{"contractId":contractId,"originalOrderId":f"{i}"} for i in orderIds]
            else:
                lis = [{"contractId":contractId,"originalOrderId":f"{orderIds[i]}","clientOrderId":f"{clientOrderIds[i]}"} for i in range(len(orderIds))]
            body = {"cancels":lis}
            # print(lis)
            # print(body)
            # data = self._httpReq(req,params={'filter':{'cancels':lis}},exc=exc)
            # print({'filter':{'cancels':lis}})
            # body = {"cancels":[{"contractId":999999,"originalOrderId":"11586153576946031"},{"contractId":999999,"originalOrderId":"11586153576946032"}]}
            data = self._httpReq(req,body=json.dumps(body,separators=(',',':')),exc=exc)
        else:
            data = {'error':'ExchangeError'}
        return data


    def cancelPSAll(self,contractId=None,exc='wbf'):
        '''撤所有未完成订单'''
        if exc=='wbf':
            req = 'DELETE /api/v1/future/order/all'
            data = self._httpReq(req,exc=exc)
            return data
        elif exc=='bitmex':
            req = 'DELETE /api/v1/order/all'
            body = {'symbol':contractId.upper()} 
            data = self._httpReq(req,body=json.dumps(body),exc=exc)
            return data
        elif exc == 'binanceSwap':
            CANCELALL = 'DELETE /fapi/v1/allOpenOrders'
            params = {'symbol': contractId.upper() }
            url = self._getUrl(CANCELALL, params=params, exc=exc)
            data = self._httpReq(CANCELALL, url, exc=exc)
            return data


    def increVol(self,contractId,price,qty,side):
        side = 1 if side=='buy' else -1
        req = 'POST /api/v1/future/rpo'
        body = {'cId':contractId,'mp':str(price),'mq':str(qty),'ts':side}
        # headers = {'Content-Type':'application/json','apiKey':'12345'}
        data = self._httpReq(req,body=json.dumps(body,separators=(',',':')),exc='wbf')
        return data


    # def marketClosePosition(self,contractId,maxQty=100,exc='wbf'):
    #     '''自动撤补 拆单平仓'''
    #     if exc=='wbf':
    #         self.cancelPSAll(exc=exc)
    #         pos = self.getPosition(contractId=contractId,exc=exc)['data']
    #         # print(pos)
    #         if pos==[]:
    #             return {'msg':'success','data':'success'}
    #         else:
    #             qty = int(pos[0]['posiQty'])
            
    #         side = -1 if qty>0 else 1 
    #         qty = abs(qty)
    #         qtyList = [maxQty]*(qty//maxQty)+[qty%maxQty] if qty%maxQty!=0 else [maxQty]*(qty//maxQty)
    #         # print(qtyList)
    #         for i,qty in enumerate(qtyList):
    #             matchQty=0
    #             flag=0
    #             while matchQty<qty:
    #                 if flag>0:
    #                     self.cancelPSOrder(contractId,orderId,exc=exc)
    #                 qty -= matchQty
    #                 depth = self.das.getPSDepth(contractId,exc=exc)
    #                 price = depth['bidPrice'][0] if side==-1 else depth['askPrice'][0] if side==1 else None
    #                 orderType = 'sell-limit' if side==-1 else 'buy-limit' if side==1 else None
    #                 result = self.makePSOrder(contractId,qty,offset='close',orderType=orderType,price=price)
    #                 if result['data'] is None:
    #                     # print(result)
    #                     time.sleep(1)
    #                     continue
    #                 orderId = result['data']
    #                 time.sleep(1)
    #                 matchQty = int(self.queryPSOrder(orderId,exc=exc)['data']['matchQty'])
    #                 flag+=1 
    #         return {'msg':'success','data':'success'}



    def getOpenOrders(self,contractId=None,side=None,exc='huobi'):
        '''查询未成交订单
        side: buy/sell
        '''
        if exc=='huobi':
            # try:
            accId = self.getAccounts(exc='huobi')[0]['id']
            # except:
            #     return {'error': 'initExchange Huobi Firstly'}
            OPEN_ORDERS = 'GET /v1/order/openOrders'
            params = {'account-id':accId,'symbol':contractId}
            if side is not None:
                params['side'] = side
            url = self._getUrl(OPEN_ORDERS,params,exc=exc)
            data = self._httpReq(OPEN_ORDERS,url,params=params,exc=exc)
            # return data
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_openorders'
            params = {'symbol':contractId.split('_')[0].upper()}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_openorders'
            params = {'contract_code':self.huobiSwapDic[contractId]}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)     

        elif exc=='binance':
            OPEN_ORDERS = "GET /api/v3/openOrders"
            params = {'symbol':contractId.upper()}
            url = self._getUrl(OPEN_ORDERS,params=params,exc=exc)
            data = self._httpReq(OPEN_ORDERS,url,exc=exc)  
        # elif exc=='huobiF':
        #     OPEN_ORDERS = 'POST /api/v1/contract_openorders'
        #     params = {'symbol':contractId}
        #     url = self._getUrl(OPEN_ORDERS,exc='huobiF')
        #     data = self._httpReq(OPEN_ORDERS,url,params=params,exc='huobiF')
            # return data
        elif exc=='wbf':
            req = 'GET /api/v1/future/queryActiveOrder'
            # req = 'GET /api/v1/future/queryAOrder'
            data = self._httpReq(req,exc=exc)
            # print(data)
            if data['msg']=='Trade server error':
                return {'data':[]}
            elif data['data']==[]:
                return data
            # for i in data['data']:       # adjust
            #     i['clOrderId'] = i['clientOrderId']
            #     i['orderQty'] = i['quantity']
            #     i['orderPrice'] = i['price']
            if contractId is not None:
                data['data'] = [i for i in data['data'] if i['contractId']==contractId]
            # return data
        elif exc=='bitmex':
            req = 'GET /api/v1/order'
            data = self._httpReq(req,params={'symbol':contractId.upper()},exc=exc)
            # return data
        elif exc == 'binanceSwap':
            OPENORDERS = 'GET /fapi/v1/openOrders'
            params = {'symbol': contractId.upper() }
            url = self._getUrl(OPENORDERS, params=params, exc=exc)
            data = self._httpReq(OPENORDERS, url, exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getFOpenOrders(self,symbol,exc='huobi'):
        '''查询合约未成交订单'''
        if exc=='huobi':
            OPEN_ORDERS = 'POST /api/v1/contract_openorders'
            params = {'symbol':symbol}
            url = self._getUrl(OPEN_ORDERS,exc='huobiF')
            data = self._httpReq(OPEN_ORDERS,url,params=params,exc='huobiF')
            return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getPSOrderList(self,contractId=None,exc='wbf'):
        '''获取当前订单列表'''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryActiveOrder'
            data = self._httpReq(req,exc=exc)
            return data
        elif exc=='bitmex':
            req = 'GET /api/v1/order'
            data = self._httpReq(req,params={'symbol':contractId.upper()},exc=exc)
            return data


    def queryOrder(self,orderId,symbol=None,clientId=False,exc='huobi'):
        '''
        查询订单详情
        clientId default False
        if True, the orderId is client diy id
        '''
        if exc=='huobi':
            QUERY_ORDER = f'GET /v1/order/orders/{orderId}' if not clientId else\
                          'GET /v1/order/orders/getClientOrder'
            params = {'order-id':orderId} if not clientId else {'clientOrderid':orderId}
            url = self._getUrl(QUERY_ORDER,params,exc=exc)
            data = self._httpReq(QUERY_ORDER,url,params=params,exc=exc) 
            # return data
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_order_info'
            params = {'order_id':orderId,'client_order_id':clientId,'symbol':symbol.split('_')[0].upper()}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc) 

        elif exc=='huobiSwap':
            req = 'POST /swap-api/v1/swap_order_info'
            params = {'order_id':orderId,'client_order_id':clientId,'contract_code':self.huobiSwapDic[symbol]}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='binance':
            QUERY_ORDER = "GET /api/v3/order"
            params = {'symbol':symbol.upper(),'orderId':int(orderId)}
            url = self._getUrl(QUERY_ORDER,params=params,exc=exc)
            data = self._httpReq(QUERY_ORDER,url,exc=exc) 
        elif exc == 'binanceSwap':
            QUERY_ORDER = 'GET /fapi/v1/openOrder'
            params = {'symbol': symbol.upper() ,"orderId":orderId}
            url = self._getUrl(QUERY_ORDER, params=params, exc=exc)
            data = self._httpReq(QUERY_ORDER, url, exc=exc)
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data




    def queryFOrder(self,orderId,symbol,exc='huobi'):
        '''查询期货委托'''
        if exc=='huobi':
            QUERY_ORDER = 'POST /api/v1/contract_order_info'
            params = {'symbol':symbol.upper(),'order_Id':orderId}
            if orderId is not None:
                params['order_id'] = orderId
            url = self._getUrl(QUERY_ORDER,exc='huobiF')
            data =self._httpReq(QUERY_ORDER,url,params=params,exc='huobiF')
            return data



    def queryPSOrder(self,orderId,exc='wbf'):
        '''查询合约委托'''
        if exc=='wbf':
            req = 'GET /api/v1/future/order'
            data = self._httpReq(req,params={'filter':{'orderId':str(orderId)}},exc=exc)
                
        return data     


    def getDealDetail(self,orderId,exc='huobi'):
        '''获取某个订单成交明细'''
        if exc=='huobi':
            DEAL_ORDER = f'GET /v1/order/orders/{orderId}/matchresults'
            params = {'order-id':orderId}
            url = self._getUrl(DEAL_ORDER,params,exc=exc)
            data = self._httpReq(DEAL_ORDER,url,params=params,exc=exc)
            # return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getHistoryOrders(self,symbol,status='filled',orderType=None,startDate=None,endDate=None,exc='huobi'):
        '''查询历史委托
            status: submitted已提交/partial-filled部成/partial-canceld部撤/filled已成/canceled已撤    
            orderType: buy-market/sell-market/buy-limit/sell-limit/buy-ioc/sell-ioc/buy-limit-maker/
                       sell-limit-maker/buy-stop-limit/sell-stop-limit 
            startDate: yyyy-mm-dd
            endDate: yyyy-mm-dd  
        '''
        if exc=='huobi':
            HISTORY_ORDERS = 'GET /v1/order/orders'
            params = {'symbol':symbol,'states':status}
            extraKey = ['types','start-date','end-date','states']
            extra = [orderType,startDate,endDate,status]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(HISTORY_ORDERS,params,exc=exc)
            data = self._httpReq(HISTORY_ORDERS,url,params=params,exc=exc)
            # return data
        elif exc=='binance':
            HISTORY_ORDERS = "GET /api/v3/allOrders"
            params = {'symbol':symbol.upper()}
            url = self._getUrl(HISTORY_ORDERS,params=params,exc=exc)
            data = self._httpReq(HISTORY_ORDERS,url,exc=exc) 
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getPSHistoryOrders(self,exc='wbf'):
        '''合约历史委托'''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryHisOrder'
            data = self._httpReq(req,exc=exc)
            return data


    def getDeals(self,symbol,orderType=None,startDate=None,endDate=None,size=500,startId=None,direction=None,exc='huobi'):
        '''查询历史成交
            orderType: buy-market/sell-market/buy-limit/sell-limit/buy-ioc/sell-ioc/buy-limit-maker/
                       sell-limit-maker/buy-stop-limit/sell-stop-limit 
            startDate: yyyy-mm-dd
            endDate: yyyy-mm-dd 
        '''
        if exc=='huobi':
            DEAL_ORDERS = 'GET /v1/order/matchresults'
            params = {'symbol':symbol}
            extraKey = ['types','start-date','end-date','size','from','direct']
            extra = [orderType,startDate,endDate,size,startId,direction]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = e
            url = self._getUrl(DEAL_ORDERS,params,exc=exc)
            data = self._httpReq(DEAL_ORDERS,url,params=params,exc=exc)
            # return data
        elif exc=='huobiF':
            req = 'POST /api/v1/contract_matchresults'
            params = {'symbol':symbol.split('_')[0].upper(),'trade_type':0,'create_date':3}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc == 'huobiSwap':
            req = 'POST /swap-api/v1/swap_matchresults'
            params = {'contract_code':self.huobiSwapDic[symbol],'trade_type':0,'create_date':3}
            url = self._getUrl(req,exc=exc)
            data = self._httpReq(req,url,params=params,exc=exc)

        elif exc=='binance':
            DEAL_ORDERS = "GET /api/v3/myTrades"
            params = {'symbol':symbol.upper()}
            url = self._getUrl(DEAL_ORDERS,params=params,exc=exc)
            data = self._httpReq(DEAL_ORDERS,url,exc=exc) 
        elif exc=='binanceSwap':
            DEAL_ORDERS = 'GET /fapi/v1/userTrades'
            params = {'symbol': symbol.upper()}
            url = self._getUrl(DEAL_ORDERS, params=params, exc=exc)
            data = self._httpReq(DEAL_ORDERS, url, exc=exc)

        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data


    def getFDeals(self,symbol,tradeType=0,backwardDate=1,exc='huobi'):
        '''查询合约历史成交
        tradeType: 0-all,1-openlong,2-openshort,3-closeshort,4-closelong,5-forcecloselong,6-forcecloseshort
        backwardDate maximum is 90
        '''
        if exc=='huobi':
            DEAL_ORDERS = 'POST /api/v1/contract_matchresults'
            params = {'symbol':symbol.upper(),'trade_type':tradeType,'create_date':backwardDate}
            url = self._getUrl(DEAL_ORDERS,exc='huobiF')
            data = self._httpReq(DEAL_ORDERS,url,params=params,exc='huobiF')
            return data
        else:
            data = {'error':'ExchangeError'}
        # print(data)
        return data     


    def getPSDeals(self,contractId=None,pageSize=None,exc='wbf'):
        '''合约成交'''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryHisMatch'
            data = self._httpReq(req,params={'filter':{'contractId':contractId,'pageSize':pageSize}},exc=exc)
            if 'data' in data:
                return data
            else:
                return data


    def getForceQueue(self,exc='wbf'):
        '''强平队列'''
        if exc=='wbf':
            req = 'GET /api/v1/future/queryForceLower'
            data = self._httpReq(req,exc=exc)
            return data 


    def getHisAccount(self,currency='ht',qType='fee-deduction',exc='huobi'):
        '''查询账户流水'''
        if exc=='huobi':
            accId = self.getAccounts(exc=exc)[0]['id']
            req = 'GET /v1/account/history'
            params = {'account-id':str(accId),'transact-types':qType,
                      'size':500,'currency':currency}
            url = self._getUrl(req,params=params,exc=exc)
            data = self._httpReq(req,url,exc=exc)
            return data  



    '''======================================================================='''
    '''============================= Quote ==============================='''
    '''=======================================================================''' 
    # def getPSKline(self,symbol,period,count=1500,start=None,end=None,exc='binance'):
    #     '''restful get swap kline'''
    #     if exc=='binance':
    #         periodDic={'1min':'1m','3min':'3m','5min':'5m',
    #                    '15min':'15m','30min':'30m','1hour':'1h',
    #                    '2hour':'2h','4hour':'4h','6hour':'6h',
    #                    '12hour':'12h','1day':'1d','1week':'1w'}
    #         period = periodDic[period]
    #         req = "GET /fapi/v1/klines"
    #         params = {'symbol':symbol.upper(),'interval':period,'limit':count}
    #         extraKey = ['startTime','endTime']
    #         extra = [start,end]
    #         for i,e in enumerate(extra):
    #             if e is not None:
    #                 params[extraKey[i]] = int(time.mktime(time.strptime(e,'%Y-%m-%d'))*1000)
    #         # print(params)
    #         url = self._getUrl(req,params=params,exc='binanceSwap')
    #         data = self._httpReq(req,url,exc='binanceSwap')
    #         return data
    #     elif exc=='wbf':
    #         req = 'GET /api/v1/futureQuot/queryCandlestick'
    #         periodDic={'1min':'60000','3min':'180000','5min':'300000',
    #                    '15min':'900000','30min':'1800000','1hour':'3600000',
    #                    '2hour':'7200000','4hour':'14400000','6hour':'21600000',
    #                    '12hour':'43200000','1day':'86400000','1week':'604800000'}
    #         period = periodDic[period] if period in periodDic else period
    #         params = {'contractId':symbol,'range':int(period)}
    #         # print(params)
    #         data = self._httpReq(req,params=params,exc=exc)
    #         return data
    def getTick(self,symbol,exc='huobi'):
        if exc == "okex":
            symbol = self.okexSymbolDic[symbol] if symbol in self.okexSymbolDic else symbol
            # req = f"GET /api/swap/v3/instruments/{symbol}/depth"
            req = f"GET /api/swap/v3/instruments/{symbol}/ticker"
            params = {'instrument_id':symbol}
            data = self._httpReq(req,params=params,exc='okexPS')
        if exc == "polo":
            url = "https://poloniex.com/public?command=returnTicker"
            data = []
        if exc == "hitbtc":
            url = "https://api.hitbtc.com/api/2/public/ticker?symbols=EOSUSD"
            data = requests.get(url)
            data = data.json()

        if exc == "mxc":
            url = "https://www.mxcio.co/open/api/v2/market/ticker?api_key=mx0mJzcApU2k5QGurd&symbol=COMP_USDT"
            data = requests.get(url)
            data = data.json()

        if exc == "biki":
            url = "https://openapi.biki.com/open/api/get_ticker?symbol=compusdt"
            data = requests.get(url)
            data = data.json()

        if exc=='huobi':
            url = "https://api.huobi.pro/market/detail/merged?symbol=btcusdt"
            data = requests.get(url)
            data = data.json()

        elif exc=='binance':
            req = "GET /api/v3/trades"
            params = {'symbol':symbol.upper(),'limit':1}
            url = self._getUrl(req,params=params,exc='binance')
            url = url.split('recv')[0][:-1]
            data = self._httpReq(req,url,exc='binance')

        return data


    def getDepth(self,symbol,exc='huobi'):
        '''restful get spot depth'''
        if exc=='huobi':
            req = 'GET /market/depth'
            params = {'symbol':symbol,'type':'percent10'}
            url = self._getUrl(req,params=params,exc='huobi')
            data = self._httpReq(req,url,exc='huobi')['tick']
        elif exc=='binance':
            req = "GET /api/v3/depth"
            params = {'symbol':symbol.upper(),'limit':1000}
            url = self._getUrl(req,params=params,exc='binance')
            url = url.split('recv')[0][:-1]
            data = self._httpReq(req,url,exc='binance')
        elif exc=="binanceSwap":
            req = "GET /fapi/v1/depth"
            params = {'symbol':symbol.upper(),'limit':1000}
            url = self._getUrl(req,params=params,exc=exc)
            # print(url)
            url = url.split('recv')[0][:-1]
            data = self._httpReq(req,url,exc=exc)
        elif exc=='bitmex':
            dic = {'btcusd':'xbtusd'}
            symbol = dic[symbol] if symbol in dic else symbol
            req = "GET /api/v1/orderBook/L2"
            params = {'symbol':symbol.upper(),'depth':1000}
            data= self._httpReq(req,params=params,exc='bitmex')
            # print(data)
            data = {'asks':[[i['price'],i['size']]for i in data if i['side']=='Sell'],'bids':[[i['price'],i['size']]for i in data if i['side']=='Buy']}
        elif exc=='okex':
            symbol = self.okexSymbolDic[symbol] if symbol in self.okexSymbolDic else symbol
            req = f"GET /api/swap/v3/instruments/{symbol}/depth"
            params = {'size':'200'}
            data = self._httpReq(req,params=params,exc='okexPS')
        elif exc=='wbf':
            symbol = self.wbfSymbolDic[symbol] if symbol in self.wbfSymbolDic else symbol
            req = 'GET /api/v1/futureQuot/querySnapshot'
            data = self._httpReq(req,params={'contractId':symbol},exc=exc)
        return data


    def getPSDepth(self,symbol,exc='huobi'):
        '''restful get swap depth'''
        if exc=='huobi':
            symbol = 'BTC-USD' if symbol=='btcusd' else symbol
            req = "GET /swap-ex/market/depth"
            # req = "GET /market/depth"
            # req = "GET /swap-api/v1/swap_contract_info"
            params = {'contract_code':symbol,'type':'step0'}
            url = self._getUrl(req,params=params,exc='huobiF')
            data = self._httpReq(req,url,exc='huobiF')['tick']
        elif exc=='binance':
            req = "GET /fapi/v1/depth"
            params = {'symbol':symbol.upper(),'limit':1000}
            url = self._getUrl(req,params=params,exc='binanceSwap')
            data = self._httpReq(req,url,exc='binanceSwap')
        elif exc=='bitmex':
            req = "GET /api/v1/orderBook/L2"
            params = {'symbol':symbol.upper(),'depth':1000}
            data= self._httpReq(req,params=params,exc='bitmex')
            data = {'asks':[[i['price'],i['size']]for i in data if i['side']=='Sell'],'bids':[[i['price'],i['size']]for i in data if i['side']=='Buy']}
        elif exc=='okex':
            symbol = 'BTC-USDT-SWAP' if symbol=='btcusdt' else symbol
            req = f"GET /api/swap/v3/instruments/{symbol}/depth"
            params = {'size':'200'}
            data = self._httpReq(req,params=params,exc='okexPS')
        elif exc=='wbf':
            req = 'GET /api/v1/futureQuot/querySnapshot'
            data = self._httpReq(req,params={'contractId':symbol},exc=exc)
        return data


    def getPSQuote(self,symbol,exc='wbf'):
        '''restful get swap quote'''
        if exc=='wbf':
            req = 'GET /api/v1/futureQuot/querySnapshot'
            data = self._httpReq(req,params={'contractId':symbol},exc=exc)
            return data['result']


    def getKline(self,symbol,period,count=1500,start=None,end=None,exc='wbf'):
        '''restful get kline'''
        if exc=='binance':
            req = "GET /api/v3/klines"
            params = {'symbol':symbol.upper(),'interval':period,'limit':count}
            extraKey = ['startTime','endTime']
            extra = [start,end]
            for i,e in enumerate(extra):
                if e is not None:
                    params[extraKey[i]] = int(time.mktime(time.strptime(e,'%Y-%m-%d'))*1000)
            url = self._getUrl(req,params=params,exc='binance')
            url = url.split('recv')[0][:-1]
            data = {}
            data['lines'] = self._httpReq(req,url,exc='binance')
            data['header'] = ['startTime','open','high','low','close','volume','endTime','amount','count','activeBuy','activeSell','none']

        elif exc=='wbf':
            req = 'GET /api/v1/futureQuot/queryCandlestick'
            periodDic={'1m':'60000','3m':'180000','5m':'300000',
                       '15m':'900000','30m':'1800000','1h':'3600000',
                       '2h':'7200000','4h':'14400000','6h':'21600000',
                       '12h':'43200000','1d':'86400000','1w':'604800000'}
            period = periodDic[period] if period in periodDic else period
            symbol = self.wbfSymbolDic[symbol] if symbol in self.wbfSymbolDic else symbol 
            params = {'contractId':symbol,'range':int(period)}
            # print(params)
            data = self._httpReq(req,params=params,exc=exc)['data']
            data['header'] = ['time','open','high','low','close','volume']

        elif exc=='huobi':
            req = 'GET /market/history/kline'
            periodDic={'1m':'1min','5m':'5mon','60m':'60min',
                       '15m':'15min','30m':'30min','1h':'60min','4h':'4hour',
                       '1d':'1day','1M':'1mon','1w':'1week','1y':'1year'}
            period = periodDic[period]
            params = {'symbol':symbol,'period':period,'size':count}
            url = self._getUrl(req,params=params,exc='huobi')
            data = self._httpReq(req,url,exc='huobi')

        elif exc=='bitmex':
            req = "GET /api/v1/trade/bucketed"
            params = {'symbol':symbol.upper(),'binSize':period,'count':1000,'reverse':True}
            data= self._httpReq(req,params=params,exc='bitmex')

        elif exc=='okex':
            symbol = self.okexSymbolDic[symbol] if symbol in self.okexSymbolDic else symbol
            req = f"GET /api/swap/v3/instruments/{symbol}/candles"
            period = self.okexKlineDic[period] if period in self.okexKlineDic else period
            params = {'granularity':period}
            data = {}
            data['lines'] = self._httpReq(req,params=params,exc='okexPS')  
            data['header'] = ['time','open','high','low','close','volume','currency_volume']  

        return data  






if __name__ == '__main__':
    config = {'temp':22,
              'wbfPublicKey': '93705949d9fec6340fd71f2d5e879e20',  #near1 btc
              'wbfPrivateKey': '8024e85f3e7ac1cc78d5c9b9cca1e883',
              # 'wbfPublicKey': '85dbcb6392ceba01f9806269f9504e74',  #near1 eth
              # 'wbfPrivateKey': '6d31a2ee5f47fcb9335d3d0cf11aa669',
              # 'wbfPublicKey': '44c2200ffd2e5816c15d716509100fb0',  #near1 eth??
              # 'wbfPrivateKey': '369cfc19fe9b2c11a5fdde741a1d672a',
              # 'wbfPublicKey': '8101d64ee1aae7b8b07bc53857f8ff9b',  #far2 btc
              # 'wbfPrivateKey': 'b156e4b77be0ae858eb9deae1fa421ed',
              # 'wbfPublicKey': 'e451d561c4c0aae9757b79f3a9b4e1c2',  #far1 btc
              # 'wbfPrivateKey': '76bd1b9f85639bdfa88ac098fe8f2fbd',
              # 'wbfPublicKey': '27c4cc61672ef1d5f9e82b0f75ba6e5c',  #far2 eth
              # 'wbfPrivateKey': '255a0929c7cc0c9f57278cf86abe76b1',
              # 'wbfPublicKey': '3d4e5ae8d3275e43417fb9e72ef8937d',  #far1 eth
              # 'wbfPrivateKey': '742c43b2aaa0554a3c9a1b4a3d95709c',
              # 'wbfPublicKey': '44c2200ffd2e5816c15d716509100fb0',  #incre eth
              # 'wbfPrivateKey': '369cfc19fe9b2c11a5fdde741a1d672a',
              # 'wbfPublicKey': '38eb42a6d9f7dcf66526de91c73492e9',  # increvol
              # 'wbfPrivateKey': '39abc6d33eb3c15d751511a44f87e5f9',
              # 'wbfPublicKey': 'd745fd9b7b1d9960109f3f9709ae55e7',  # adl1 btc
              # 'wbfPrivateKey': '9d0654fa1b4e487084dabbd2ead5ed06',
              # 'wbfPublicKey': 'b4092b3d0a5ebdddf274913f43cb49cd',  # adl2 btc
              # 'wbfPrivateKey': '842069610160527d10d87694f8cd04d8',


              # 'huobiPublicKey': 'eef329d5-e7e5c1fa-49670e25-qz5c4v5b6n', #far2 eth
              # 'huobiPrivateKey': 'e328b056-7dfd6b60-15a14403-13348',
              # 'huobiPublicKey': '64e5627b-25523cb8-75b36945-hrf5gdfghe', #far1 btc
              # 'huobiPrivateKey': 'a8a2a5ad-510dd845-e49edac8-4aca1',
              'huobiPublicKey': '215af0f6-8743e9df-3d2xc4v5bu-97413', #combo 
              'huobiPrivateKey': '101c2d94-f16fd115-8d11d13f-96279',
              'huobiFPublicKey': 'a8f1c058-e2d9cafc-4c20f30f-bg5t6ygr6y',
              'huobiFPrivateKey': '28a72da2-55f15b18-0f69d158-638d3',
              'huobiSwapPublicKey': '92dbc79f-gr4edfki8l-c7eb6eed-ae3fa',
              'huobiSwapPrivateKey': '791c082c-4ad5603d-e0a38969-35260',
              # 'huobiPublicKey': '1qdmpe4rty-f8576631-d958564b-e4f51', #far1 btc
              # 'huobiPrivateKey': '1f0d5275-2e33783b-98e581ca-473ce',
              'binanceSwapPublicKey':'jMuAxrXnZq2NDQofpF8dRLIN53ZA5VR5fW3j5gYg7GUYJYzN71vgt9Nfoic3oId4',
              'binanceSwapPrivateKey':'frKpUaAISmf6mIBlZR3BTI5FkaKSsmZzAvx0n0FCHkEb05dL2LsOJgdctAB29fvL',
              'binancePublicKey': 'ONqN1tjQnl59tAnRnq39i1WeFOWMqww7vQEkgvogd3KJCd1odSp77EQ3z9ApetLM',
              'binancePrivateKey': 'RTgyyhxl4KW6DSzVS86cE7YkPOI1EO8A44Gk1sW1C6wGtxtskxS6Mo667OyXGfZO',
              # 'bitmexPublicKey':'R8nh8RWoo_U8xrxj6ikveJlP',
              # 'bitmexPrivateKey':'AhIkqWh7kMfhgv3TPZ0vrkVY7u4AAq3T1DZ8taNJk13U41N1',
              # 'okexPublicKey':'4f5ae0a0-d184-40c7-a24d-a3f8fg85679f9d',
              # 'okexPrivateKey':'C7A2807080D952EFDB11973F2D298CB6',
              # 'okexPassphrase':'323040',
              'strategyName':'testing',
              'strategyId':'9'}

    task = SDK(config)
    # print(task.getPosition(100000,exc='wbf'))
    # print(task.makeOrder('atomusdt',10,price=3,orderType='buy-limit',exc='binance'))
    print(task.cancelAll('btcusdt',exc='huobi'))
    # print(task.getOpenOrders('atomusdt',exc='binance'))
    # print(task.getDeals('compusdt',exc='binanceSwap'))
    # data = task.getKline('btcusdt','1m',exc='okex')
    # data = task.getKline('xbtusdt','1m',exc='bitmex')
    # data = task.getKline('btcusdt','1m',exc='huobi')
    # data = task.getKline('btcusdt','1m',exc='binance')
    # data = task.getKline('btcusdt','1m',exc='wbf')
    # data = task.getHisAccount(qType='trade',exc='huobi')
    # data = task.getAccounts(exc='binanceSwap')
    # data = task.getPSDeals(exc='wbf')['data']
    # print(len(data['data']))
    # for i in data:
        # print(i)
    # print(task.getDeals('btcusdt',exc='binanceSwap'))
    # print(task.getDeals('btc',0.1,price=100,orderType='buy-limit'))
    # data = task.cancelOrder(12131313,'btcusd',exc='huobiSwap')
    # data = task.getKline(100001,period='5m',count=int(24*60),exc='wbf')
    # print(data['lines'])
    # data = task.getKline('btcusdt','1m',count=1440,exc='huobi')
    # print(data,len(data))
    # data = task.getKline(100000,'1m',exc='wbf')
    # print(len(data['lines']))
    # print([i for i in data if i[0]==1597921200000])
    # print(time.time())
    # data = task.makeOrder('btc_cq',1,price=1000,orderType='buy-limit',leverRate=20,exc='huobiF')
    # data = task.getPSDeals(exc='wbf')
    # data = task.cancelOrder('735610197560745984',symbol='btc_cq',exc='huobiF')
    # data = task.cancelAll('btc_cq',exc='huobiF')
    # print(data)
    # data = task.queryOrder('735618743597694977',symbol='btc_cq',exc='huobiF')
    # data = task.getOpenOrders('btc_cq',exc='huobiF')
    # data = task.getPSDeals(100000,exc='wbf')
    # print(task.cancelOrder(748932801880956928,symbol='btcusd',exc='huobiSwap'))
    # print(task.getBalance('btcusd',exc='huobiSwap'))
    # print(task.cancelOrder(748938818224128000,'btcusd',exc='huobiSwap'))
    # print(task.makeOrder('btcusd',1,price=99999,orderType='sell-limit',exc='huobiSwap'))
    # print(task.getOpenOrders('btcusd',exc='huobiSwap'))
    # data = task.getOpenOrders('btcusdt',exc='huobi')
    # print(data)
    # print([i for i in data['list'] if i['balance']!='0'])
    # t1=time.time()
    # data = task.getOpenOrders(100001,exc='wbf')
    # print(time.time()-t1)
    # contractId,amount,price=None,orderTypeList=None,subOrderTypeList=None
    # data = task.makePSOrders(999999,[1,2,3],[5,6,7],orderType='buy-limit',subOrderTypeList=[1,1,1])
    # data = task.getBalance('compusdt',exc='binance')
    # data = task.makeOrder('compusdt',0,'sell-limit',price=170.5,exc='binance')
    # data = task.getKline('bnbusdt','1m',exc='binance')
    # data = task.getKline('htusdt','1m',exc='huobi')
    # periodDic={'1m':'1min','5m':'5mon','60m':'60min',
               # '15m':'15min','30m':'30min','1h':'60min','4h':'4hour',
               # '1d':'1day','1M':'1mon','1w':'1week','1y':'1year'}

    #binanceSwap Example
    # print(task.getAccounts(exc='huobi'))
    # print(task.getDeals('mkrusdt',exc='binanceSwap'))
    # print(task.getDepth('btcusdt',exc='binanceSwap'))
    # print(task.makeOrder('btcusdt',1,orderType='buy-limit',price=0.01,exc='binanceSwap'))
    # print(task.getOpenOrders('btcusdt',exc='binanceSwap'))
    # print(task.queryOrder(5627007027,'btcusdt',exc='binanceSwap'))
    # print(task.cancelOrder(5627007027,'btcusdt',exc='binanceSwap'))
    # print(task.cancelPSAll('btcusdt',exc='binanceSwap'))
    # print(data)

    #######################################################################
    # data = task.makePSOrder(999999,100,offset='open',orderType='sell-market')
    # data = task.makePSOrder(100000,358,offset='open',orderType='sell-limit',price=9525.5,clientOrderId=f'close{time.time()}')
    # data = task.makeOrder('btcusdt',1.079,'sell-limit',price=9550.,exc='huobi')
    # data = task.makePSOrder(100001,100,offset='open',orderType='buy-limit',price=235.15,clientOrderId=f'close{time.time()}')
    # data = task.makeOrder('htusdt',10,'sell-limit',price=100.,exc='huobi')
    # print(data)
    # print(task.cancelOrder(56485921958513,'htusdt',exc='huobi'))
    #######################################################################
