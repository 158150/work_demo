import time
import Toolbox
import threading
import os
import pandas as pd
import data_process
import signal
import traceback
import numpy as np
import random
import requests
from concurrent.futures import ThreadPoolExecutor  # 线程池
import sys
import threadpool

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.append("/usr/local/server")
from wbfAPI import exchange
from wbfAPI.data import DataClient as dc

pd.options.display.max_columns = None  # 显示全部列
pd.options.display.max_rows = None  # 显示全部行
pd.set_option('display.width', 180)  # 输出宽度
pd.set_option('display.unicode.ambiguous_as_wide', True)  # 对齐
pd.set_option('display.unicode.east_asian_width', True)
################################################### 打印日志
log = Toolbox.Log("./log_print.log")
def localprint(*args):
    p = ""
    for i in args:
        p = p + str(i) + ", "
    log.write(p)

# 保证程序重启保证储存基本对冲信息，减少人工操作
# 申请两把锁
mutex = threading.Lock()
mutex_open_binance = threading.Lock()

executor = ThreadPoolExecutor(max_workers=5)  # 建立线程池，最大线程数为5
wss_executor = ThreadPoolExecutor(max_workers=3)  # 建立线程池，最大线程数为5

# os.environ['http_proxy'] = 'http://127.0.0.1:1080'
# os.environ['https_proxy'] = 'https://127.0.0.1:1080'

data_process.mkdir("./log")


class strategy():
    def __init__(self, config_hedge, is_stop=False):

        self.pool = threadpool.ThreadPool(5)    # 创建线程池

        [setattr(self, k, v) for k, v in vars(config_hedge).items()]        # 批量生成所有参数
        config = config_hedge.config

        self.hedge_exchange = getattr(self, 'hedge_exchange', "binanceUsdtSwap")    # 对冲交易所
        self.contract_base = getattr(self, 'contract_base', 9000000)                # DataPushServer编号
        # self.profit_percent_close = getattr(self, 'profit_percent_close', 0.07)
        self.base_exchange = getattr(self, 'base_exchange', "coinStoreSpot")        # 内盘交易所
        self.warn_balance = getattr(self, 'warn_balance', 0.2)                      # 保证金不足初始百分比触发报警
        self.open_postonly = getattr(self, 'open_postonly', True)
        self.close_postonly = getattr(self, 'close_postonly', True)
        self.risk_percent = getattr(self, 'risk_percent', 0.5)                      # 触发风控时，扩大摆盘的比例
        self.min_amt = getattr(self, 'min_amt', 1)                                  # 最小下单金额
        self.minHedgeAmt = getattr(self, 'minHedgeAmt', 11)                         # 外盘最小下单金额
        # self.coins_amt = getattr(self, 'coins_amt', 1000)                         # 内盘币的金额少于20usdt报警
        self.timeout_percent = getattr(self, 'timeout_percent', 0.05)               # 下单延时偏离
        self.offset = getattr(self, 'offset', 7)                                    # 补足订单时，间隔几个最小单位的价格
        self.ratio1 = getattr(self, 'ratio1', 0.005)                                # 远端买一价格是近端最远价格后面千5
        self.ratio2 = getattr(self, 'ratio2', 0.03)                                 # 远端最远摆到近端最远价格后面百三
        self.sellRatio = getattr(self, 'sellRatio', 0.15)                           # 卖盘每次下单的比例
        self.nearRatio = getattr(self, 'nearRatio', 0.002)                          # 近端第二档的摆盘起点
        if self.binance_symbol.split("/")[1] == 'usdt':
            self.riskAmt = getattr(self, 'riskAmt', 100)                            # 近端第二档的摆盘起点
            self.depth_timeout = getattr(self, 'depth_timeout', 1000)               # 数据过期时间

        self.init_bid_percent = self.bid_percent
        self.init_ask_percent = self.ask_percent
        self.timeout_order = False
        self.balance = 0                    # 内盘usdt余额
        self.position_qty = 0
        self.binance_balance = 0            # 外盘usdt金额
        self.binance_balance_raw = 0
        self.binance_position_qty = 0       # 外盘持仓
        self.coins = 0                      # 内盘币的余额
        self.market_make_flag = True
        self.risk = False
        self.risk_num = 0                   # 累计报警次数
        self.diff_qty_list = []             # 保存内外盘持仓和
        self.call_tag = False               # 是否打过电话
        self.send_tag = False               # 是否发送信息
        self.buyNearOrders = []             # 保存近端orderId
        self.sellNearOrders = []
        self.lastNearBuyOrders = []
        self.lastNearSellOrders = []
        self.farOrders = []                 # 保存远端orderId
        self.lastfarOrders = []             # 保存上一次摆盘orderId
        self.wbf_history_execId_list = []   # 历史成交tradeId的列表
        self.now_index_price = 0            # 指数价格，是外盘现货或合约的盘口中间价
        self.send_err_time = 0              # 记录上次报错的时间戳
        self.accountlever = 2               # 外盘放2倍杠杆
        self.except_num = 0
        weight = np.array([i**(-i/self.num_maker) for i in range(1, int(self.num_maker+1))])
        self.weight = weight[::-1]/np.nansum(weight)  # 摆盘量权重
        self.binance_symbol2 = self.binance_symbol if getattr(self, 'binance_symbol2', 0) == 0 else self.binance_symbol2    # 为了兼容外盘与内盘同一标的
        self.unitNum = len(np.format_float_positional(self.wbf_price_unit).split('.')[1])           # 获取内盘小数点后的位数
        self.unitTag = np.format_float_positional(self.wbf_price_unit).split('.')[1].endswith('1')  # 判断价格精度的尾数是否是1
        self.lastFarBidPrice = 0    # 远端买一价格
        self.lastFarAskPrice = 0    # 远端卖一价格
        self.messNum = 0
        self.lastRiskTime = 0       # 上次暴露打电话的时间
        self.lastRiskTime2 = 0      # 上次连续亏损打电话的时间

        self.allNums = {'111':0, '222':0, '333':0, '444':0, '555':0, '666':0, '777':0, '888':0}

        self.init_time = time.time()
        if is_stop == False:
            self.account_wss_wbf = getattr(exchange,self.base_exchange).AccountWss(config['wbfPublicKey'], config['wbfPrivateKey'],
                                                                  self.wbf_accout)
            self.account_wss_binance = getattr(exchange,self.hedge_exchange).AccountWss(config['binanceSwapPublicKey'],
                                                                           config['binanceSwapPrivateKey'], self.binance_account)
        self.wbf_rest = getattr(exchange,self.base_exchange).AccountRest(config['wbfPublicKey'],config['wbfPrivateKey'])  # , proxy=True
        self.binance_rest = getattr(exchange,self.hedge_exchange).AccountRest(config['binanceSwapPublicKey'],config['binanceSwapPrivateKey'])  # , proxy=True
        
        # self.wsstask_timeout_close = dc.SDK(round(self.contract_base + self.wbf_contractId))
        self.wsstask_market_maker = dc.SDK(round(self.contract_base + self.wbf_contractId))     # 不同线程不能共享zmq
        self.wsstask_market_maker_far = dc.SDK(round(self.contract_base + self.wbf_contractId))
        self.wsstask_open_binance = dc.SDK(round(self.contract_base + self.wbf_contractId))
        self.lasttime, self.last_price_ask, self.last_price_bid, self.last_indexprice = 0, [0], [0], 0

        self.log_order = Toolbox.Log("./log/log_order")         # 记录成交订单
        self.log = Toolbox.Log("./log/log")                     # 记录所有
        self.log_warning = Toolbox.Log("./log/log_warning")     # 记录报错
        self.log_ansys = Toolbox.Log("./log/log_ansys")         # 记录订单
        self.checkRest = Toolbox.Log("./log/log_restNum")       # 记录rest请求次数
        self.detailLog = Toolbox.Log("./log/hedgeDetail.log")   # 记录所有详细信息
        self.cookLog =  Toolbox.Log("./log/hedgeCook.log")      # 只记录最重要信息

        self.binance_cancelall()
        self.wbf_cancelall(111)

        self.EMAIL_CONFIG = [
            dict(
                smtp_server='smtp.mxhichina.com',
                sender_mail='shiyang@longvega.onaliyun.com',
                sender_pass='Lsy@01247712521',
            ),
            dict(
                smtp_server='smtp.qq.com',
                sender_mail='lishiyang1205@foxmail.com',
                sender_pass='hyreebyupyqmbeja'
            ),
            dict(
                smtp_server='smtp.163.com',
                sender_mail='lishiyang1205@163.com',
                sender_pass='QDTUKHJZBJBQJGCW'
            ),
            dict(
                smtp_server='smtp.126.com',
                sender_mail='linjie0113@126.com',
                sender_pass='ERRAMJAPVBBHXJCM'
            ),
            dict(
                smtp_server='smtp.163.com',
                sender_mail='kawujielu1@163.com',
                sender_pass='CJCRJMZMWZSLDWCE'
            ),
            dict(
                smtp_server='smtp.126.com',
                sender_mail='kawujielu1@126.com',
                sender_pass='ACNYIMNCNYKTIJOV'
            ),
            dict(
                smtp_server='smtp.qq.com',
                sender_mail='kawujielu@foxmail.com',
                sender_pass='fbplezyoillubfdf'
            )
        ]
    
    def sendmail(self, _title, _text):
        t1 = time.time()
        for config in self.EMAIL_CONFIG:
            try:
                smtp_server = config.get('smtp_server')
                sender_mail = config.get('sender_mail')
                sender_pass = config.get('sender_pass')

                to = ['linjie0113@126.com', 'hilda_001@163.com', ]

                msg_root = MIMEMultipart('mixed')

                msg_root['From'] = sender_mail
                msg_root['To'] = ','.join(to)

                msg_root['subject'] = Header(_title, 'utf-8')

                text_sub = MIMEText(_text, 'html', 'utf-8')
                msg_root.attach(text_sub)
                
                sftp_obj = smtplib.SMTP_SSL(smtp_server)
                sftp_obj.login(sender_mail, sender_pass)
                sftp_obj.sendmail(sender_mail, to, msg_root.as_string())
                sftp_obj.quit()
                localprint('sendemail successful!', smtp_server, sender_mail)
                localprint(f"发送邮件耗时:{time.time()*1000-t1*1000}ms")
                break
            except Exception as e:
                localprint('sendemail failed:', e)

    def adjustPrecision(self, number, unit, direction):
        """精度调整

        Args:
            number (float): targeted number
            unit (float): minimum unit of targeted number
            direction (str): round direction (up/down/random)

        Returns:
            float: rounded number
        """        
        sign = np.sign(number)
        number = abs(number)
        length = len(str(unit).split('.')[1]) if '.' in str(unit) else int(str(unit)[-2:])
        direction = random.random.choice([0, 1]) if direction == 'random' else \
                1 if direction == 'up' else \
                0
        a = number*10**length
        b = unit*10**length
        intPart = a//b
        number = intPart*unit + direction*unit
        number = round(number, length)
        return sign * number

    def wss_init(self):
        self.wbf_wss_execId_list = wbf_wss_execId_list

    # 拆分成20次的批量下单
    def _cancelOrders(self, orders):
        if len(orders) == 0:
            return
        while len(orders)>0:
            try:
                if len(orders) == 1:
                    res = self.wbf_rest.cancelOrder(self.binance_symbol, orders[0])['data']
                    if res['code'] != 0:
                        break
                else:
                    res = self.wbf_rest.cancelOrders(self.binance_symbol, orders[:20])['data']
                    failed = [i for i in res if i['code'] != 0]
                    self.detailLog.write(f"撤单回报:{failed}")
                    if len([r for r in res if (r['code'] != 0 )]) > 0:
                        break
            except:
                self.wbf_cancelall(444)
                self.errHandle(f"{self.base_exchange}撤单错误:{traceback.format_exc()}")
            orders = orders[20:]

    def wbf_cancelall(self, tag='???'):
        localprint(f'内盘全撤:{tag}')
        while True:
            try:
                mass = self.wbf_rest.cancelAll(self.binance_symbol)
                if mass["status"] == 'success':
                    return
                else:
                    data = self.wbf_rest.getOpenOrders(self.binance_symbol)
                    if data['data'] == []:
                        return
            except Exception as e:
                self.errHandle(f"{self.base_exchange}撤单错误:{traceback.format_exc()}")
            time.sleep(0.1)

    def binance_cancelall(self):
        while True:
            try:
                mass = self.binance_rest.cancelAll(self.binance_symbol2)
                self.allNums['222'] = self.allNums['222']+1
                if mass["status"] == 'success':
                    return
                else:
                    data = self.binance_rest.getOpenOrders(self.binance_symbol2)
                    self.allNums['333'] = self.allNums['333']+1
                    if data['data'] == []:
                        return
            except Exception as e:
                self.errHandle(f"{self.hedge_exchange}撤单错误:{traceback.format_exc()}")
            time.sleep(0.3)
    
    def errHandle(self, content):
        self.bid_percent = self.risk_percent
        self.ask_percent = self.risk_percent
        self.log_warning.write(f"记录报错内容:{self.binance_symbol}\n{content}")
        if time.time()-self.send_err_time > 60:
            # self.sendMessage(f"{self.binance_symbol}\n{content}")
            self.send_err_time = time.time()
    
    def sendMessage(self, info):
        url = (f'http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&'
               f'eventType=trigger&priority=1&eventId={str(int(time.time()))}&alarmContent={info}')
        info = requests.post(url=url)
        localprint(f"发消息:{info.text}")
    
    def callPhone(self, info):
        url = (f'http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&'
               f'eventType=trigger&priority=2&eventId={str(int(time.time()))}&alarmContent={info}')
        info = requests.post(url=url)
        localprint(f"拨电话:{info.text}")
    
    def callPhone2(self, info):
        url = (f'http://api.aiops.com/alert/api/event?app=9f18109a9db54227bcd8ae5eca99b0e5&'
               f'eventType=trigger&priority=2&eventId={str(int(time.time()))}&alarmContent={info}')
        info = requests.post(url=url)
        localprint(f"拨电话:{info.text}")

    def restart_wss_binance(self):
        try:
            self.account_wss_binance.restart()
        except Exception as e:
            self.errHandle(Toolbox.timestamp(), "binancerestart", traceback.format_exc())

    def restart_wss_wbf(self):
        try:
            self.account_wss_wbf.restart()
        except Exception as e:
            self.errHandle(Toolbox.timestamp(), "wbfrestart", traceback.format_exc())
    
    # 外盘对冲
    def open_binance(self):  # 与用合约对冲的区别有2点，1是价格，2是开平仓判断
        global zhengPendingList
        with mutex_open_binance:
            for index, row in zhengPendingList.iterrows():  # 下对冲单
                if row["qty_binance"] == 0:
                    if self.binance_symbol == self.binance_symbol2:
                        qty = round(abs(row["qty_wbf"]) * self.wbf_qty_unit, self.binance_qty_digital)
                    else:
                        qty = round(abs(row["qty_wbf"]) * self.wbf_qty_unit / self.qty_lever, self.binance_qty_digital)
                    Dict = 0
                    if row["qty_wbf"] > 0:
                        price = Toolbox.round(row["price_wbf"] / (
                                1 - (self.profit_percent - self.slip_percent) / 100) - self.wbf_price_unit,
                                                self.binance_price_unit, 'down')
                        try:
                            depth_binance_swap = self.wsstask_open_binance.getDepth(symbol=self.binance_symbol2, exc=self.hedge_exchange)
                            spot_bid_price = np.array(depth_binance_swap["data"][1])[:, 0].astype('float').tolist()
                        except Exception as e:
                            self.errHandle(f"open_binance没有获取到币安数据1:{traceback.format_exc()}")
                            self.wsstask_open_binance = dc.SDK(round(self.contract_base + self.wbf_contractId))
                            time.sleep(0.5)
                        
                        if row["match_type"] == "risk_close" or time.time() > float(row["time_wbf"]) / 1000 + 20:  # 实现时间风控
                            while True:
                                try:
                                    try:
                                        depth_binance_swap = self.wsstask_open_binance.getIncreDepth(
                                            symbol=self.binance_symbol2, exc=self.hedge_exchange)
                                        spot_bid_price = np.array(depth_binance_swap["data"][1])[:, 0].astype(
                                            'float').tolist()
                                    except Exception as e:
                                        depth_binance_swap = self.wsstask_open_binance.getDepth(
                                            symbol=self.binance_symbol2, exc=self.hedge_exchange)
                                        spot_bid_price = np.array(depth_binance_swap["data"][1])[:, 0].astype(
                                            'float').tolist()
                                    price = spot_bid_price[1] * (1 - self.slip_percent/100)
                                    break
                                except Exception as e:
                                    self.errHandle(f"open_binance没有获取到币安数据2:{traceback.format_exc()}")
                                    self.wsstask_open_binance = dc.SDK(round(self.contract_base + self.wbf_contractId))
                                    time.sleep(0.5)
                        try:
                            price = Toolbox.round(price, self.binance_price_unit, "down")
                            price = np.format_float_positional(price, trim='-')
                            qty = np.format_float_positional(qty, trim='-')
                            localprint(f"{self.binance_symbol2} 对冲价格:{price} 数量:{qty} 方向:sell")
                            Dict = self.binance_rest.makeOrder(symbol=self.binance_symbol2, price=price, vol=qty,
                                                               orderType='sell-limit')
                            localprint(f"对冲下单1:{Dict}")
                            if Dict['status'] == 'failed':
                                self.messNum += 1
                                if self.messNum > 100:
                                    mess = f"{self.base_exchange} {self.binance_symbol}对冲失败:{Dict}"
                                    self.sendMessage(mess)
                                    send = threadpool.WorkRequest(self.sendmail, args=('cs交易失败', mess,))
                                    self.pool.putRequest(send)
                                    self.messNum = 0
                                time.sleep(1)
                            else:
                                self.messNum = 0
                            self.allNums['444'] = self.allNums['444']+1
                        except Exception as e:
                            self.errHandle(f"外盘sell对冲下单错误:{traceback.format_exc()}")
                            return
                    elif row["qty_wbf"] < 0:
                        price = Toolbox.round(row["price_wbf"] / (
                                    1 + (self.profit_percent - self.slip_percent) / 100) + self.wbf_price_unit,
                                                self.binance_price_unit, 'up')
                        try:
                            depth_binance_swap = self.wsstask_open_binance.getDepth(symbol=self.binance_symbol2,
                                                                                    exc=self.hedge_exchange)
                            spot_ask_price = np.array(depth_binance_swap["data"][2])[:, 0].astype('float').tolist()
                        except Exception as e:
                            self.errHandle(f"open_binance没有获取到币安数据3:{traceback.format_exc()}")
                            self.wsstask_open_binance = dc.SDK(round(self.contract_base + self.wbf_contractId))
                            time.sleep(0.5)

                        if row["match_type"] == "risk_close" or time.time() > float(row["time_wbf"]) / 1000 + 20:  # 实现时间风控
                            while True:
                                try:
                                    try:
                                        depth_binance_swap = self.wsstask_open_binance.getIncreDepth(
                                            symbol=self.binance_symbol2, exc=self.hedge_exchange)
                                        spot_ask_price = np.array(depth_binance_swap["data"][2])[:, 0].astype(
                                            'float').tolist()
                                    except Exception as e:
                                        depth_binance_swap = self.wsstask_open_binance.getDepth(
                                            symbol=self.binance_symbol2, exc=self.hedge_exchange)
                                        spot_ask_price = np.array(depth_binance_swap["data"][2])[:, 0].astype(
                                            'float').tolist()
                                    price = spot_ask_price[1] * (1 + self.slip_percent/100)
                                    break
                                except Exception as e:
                                    self.errHandle(f"open_binance没有获取到币安数据4:{traceback.format_exc()}")
                                    self.wsstask_open_binance = dc.SDK(round(self.contract_base + self.wbf_contractId))
                                    time.sleep(0.5)
                        try:
                            price = Toolbox.round(price, self.binance_price_unit, "up")
                            price = np.format_float_positional(price, trim='-')
                            qty = np.format_float_positional(qty, trim='-')
                            localprint(f"{self.binance_symbol2} 对冲价格:{price} 数量:{qty} 方向:buy")
                            Dict = self.binance_rest.makeOrder(symbol=self.binance_symbol2, price=price, vol=qty,
                                                                orderType='buy-limit')
                            localprint(f"对冲下单2:{Dict}")
                            if Dict['status'] == 'failed':
                                self.messNum += 1
                                if self.messNum > 100:
                                    mess = f"{self.base_exchange} {self.binance_symbol}对冲失败:{Dict}"
                                    self.sendMessage(mess)
                                    send = threadpool.WorkRequest(self.sendmail, args=('cs交易失败', mess,))
                                    self.pool.putRequest(send)
                                    self.messNum = 0
                                time.sleep(1)
                            else:
                                self.messNum = 0
                                self.allNums['555'] = self.allNums['555']+1
                        except Exception as e:
                            self.errHandle(f"外盘buy对冲下单错误:{traceback.format_exc()}")
                            return

                    if Dict:
                        try:
                            if Dict["data"]['orderId']:
                                with mutex:  # 上锁:
                                    zhengPendingList.loc[index, "id_binance"] = Dict["data"]['orderId']
                                    zhengPendingList.loc[index, "price_binance"] = price
                                    zhengPendingList.loc[index, "qty_binance"] = float(qty)
                                    zhengPendingList.loc[index, "time_binance"] = time.time() * 1000
                        except Exception as e:
                            self.errHandle(f"dict error:{traceback.format_exc()}")
                            return
                        self.log.write(str("open_binance___") + str(Toolbox.timestamp()) + str(Dict))
                time.sleep(0.1)

    def wbf_accout(self, content):
        global zhengOrderList, zhengPendingList, wbf_wss_execId_list, min_zhengPendingList
        if content['status'] == 'balance':
            for bal in content["data"]:
                if bal["symbol"] == self.binance_symbol.split("/")[1]:
                    if bal['available']:
                        self.balance = bal['balance']
                if bal["symbol"] == self.binance_symbol.split("/")[0]:
                    self.coins = bal['balance']
        # elif content['status'] == 'deals':
        elif 0:
            for match in content["data"]:
                with mutex:
                    localprint("正常订单wbf——wss",match)
                    if match['selfDealingQty'] != 0:
                        localprint(f"自成交:{match}")
                        continue
                    if match["tradeId"] in self.wbf_wss_execId_list["execId"].tolist():
                        localprint(Toolbox.timestamp(), "wbf—wss rest已经处理过了")
                        continue
                    if match["symbol"] == self.binance_symbol:
                        content = {'time': match['ts'], 'id': match['tradeId'], "orderid": match['myOrderId'],
                                   'price': match['price'],
                                   'qty': match['vol'], 'side': match['side'], 'fee': match['fee'],
                                   'opp': match['oppUserId'], 'myid': match['myOrderId'],
                                   'pos': self.position_qty,
                                   'balance': self.balance}
                        self.log_order.write(content)   # 内盘成交记录
                        # 订单记录
                        wss_content = {'matchTime': match['ts'], 'execId': match['tradeId']}
                        self.wbf_wss_execId_list = self.wbf_wss_execId_list.append(wss_content, ignore_index=True)
                        if self.wbf_wss_execId_list.shape[0] > 1000:
                            for index, row in self.wbf_wss_execId_list.iterrows():
                                self.wbf_wss_execId_list.drop(index, inplace=True)
                                break
                        match["vol"] = round(match["vol"] / self.wbf_qty_unit)
                        price_wbf = float(match['price'])
                        qty_wbf = round(int(match['vol']) * 1) if match['side'] == "buy" else round(
                            int(match['vol']) * -1)
                        # 手续费监控
                        if match["fee"] > 0 and match['role'] == 'maker':
                            info = f"{self.base_exchange}-{self.binance_symbol}交易对手续费不为0,立即检查！"
                            localprint(info)
                        if abs(match["fee"]) >0 and match["feeAsset"] == self.binance_symbol.split("/")[0]:
                            fee = round(match["fee"] / self.wbf_qty_unit,round(self.fee_qty_digital-self.wbf_qty_digital))
                            qty_wbf = round(qty_wbf + fee,round(self.fee_qty_digital-self.wbf_qty_digital))
                        if match['role'] == "taker":
                            localprint("norm wbf—wss平仓", price_wbf, qty_wbf)
                            match_type = "close"
                        else:
                            localprint("norm wbf—wss开仓", price_wbf, qty_wbf)
                            match_type = "open"

                        new = pd.Series(
                            {"time": time.time(), 'id_wbf': match['tradeId'], "id_binance": 0, "price_wbf": price_wbf,
                             "price_binance": 0, "qty_wbf": qty_wbf, "qty_binance": 0, "match_price_binance": 0,
                             "match_qty_binance": 0, "time_wbf": match['ts'],
                             "time_binance": 0, "precent_profit": 0, "match_type": match_type, "fee": match['fee']},
                            name=match['tradeId'])
                        min_zhengPendingList = min_zhengPendingList.append(new)
                        for index, row in min_zhengPendingList.iterrows():
                            mydict = row.to_dict()
                            side = 1 if min_zhengPendingList["qty_wbf"].sum() >= 0 else -1
                            # 确定余数
                            qtyUnit = round(self.binance_qty_unit/self.wbf_qty_unit) if round(self.binance_qty_unit/self.wbf_qty_unit) != 0 else 1
                            mydict["qty_wbf"] = round(side * (abs(min_zhengPendingList["qty_wbf"].sum())
                                                                % qtyUnit),round(self.fee_qty_digital-self.wbf_qty_digital))
                            new_df = pd.DataFrame([mydict], index=[index])
                            diff_qty = round(float(min_zhengPendingList["qty_wbf"].sum() - mydict["qty_wbf"]),round(self.binance_qty_unit/self.wbf_qty_unit))  # 确定对冲量
                            qty = round(diff_qty * self.wbf_qty_unit,self.binance_qty_digital) # self.binance_qty_digital
                            amount = abs(qty * float(price_wbf))
                            if amount < self.minHedgeAmt:
                                mydict["qty_wbf"] = round(mydict["qty_wbf"]+diff_qty)
                                new_df = pd.DataFrame([mydict], index=[index])
                                diff_qty = 0
                            if abs(diff_qty) > 0:
                                mydict["qty_wbf"] = diff_qty
                                new.qty_wbf = diff_qty
                                zhengPendingList = zhengPendingList.append(new)
                            break
                        min_zhengPendingList = new_df
                        # return zhengPendingList,min_zhengPendingList
                    self.log.write(str("wbfaccout___") + str(content))
            task = executor.submit(self.open_binance)

    def check_wss_wbf_loop(self):
        while True:
            try:
                self.check_wss_wbf()
            except Exception as e:
                self.errHandle(f"检查漏单模块报错:{traceback.format_exc()}")
            time.sleep(self.check_wss_wbf_sleeptime)
    
    # 复用函数
    def check_wss_gongxiang(self, new, price_wbf):
        pass
    
    # 复用函数
    def resetzpl(self, zhengPendingList, index):
        pass
    
    # 复用函数
    def deleteOrder(self, qty_min, row, index, a):
        pass

    def check_wss_wbf(self):
        global zhengOrderList, zhengPendingList, wbf_wss_execId_list, min_zhengPendingList
        try:
            history = self.wbf_rest.getDeals(self.binance_symbol, 100)
            history = pd.DataFrame(history['data'])
        except Exception as e:
            self.errHandle(f"check_wss_wbf,获取历史订单错误:{traceback.format_exc()}")
            return
        if history.shape[0] == 0:
            return

        # self.init_time = 1616069466000/1000
        history = history[(history.ts > self.init_time*1000) & (history.symbol == self.binance_symbol)] # self.init_time * 1000
        history["tradeId"] = history["tradeId"].astype("int64")

        self.wbf_history_execId_list = [int(i) for i in history["tradeId"].tolist()]
        execId_list = self.wbf_wss_execId_list["execId"].tolist()
        mix_list = list(set(self.wbf_history_execId_list) & set(execId_list))
        diff_list = list(set(self.wbf_history_execId_list) - set(mix_list))
        flag_restart = 0
        if diff_list:
            for index, match in history.iterrows():
                if int(match["tradeId"]) in diff_list:  # wss 漏推
                    flag_restart = 1
                    with mutex:
                        localprint(Toolbox.timestamp(), "wbf—wss漏推", diff_list)
                        if match["tradeId"] in self.wbf_wss_execId_list["execId"].tolist():  # 已经处理就跳过
                            localprint("已处理")
                            continue
                        wss_content = {'matchTime': match['ts'], 'execId': match['tradeId']}
                        self.wbf_wss_execId_list = self.wbf_wss_execId_list.append(wss_content,ignore_index=True)
                        localprint(Toolbox.timestamp(),"已执行",int(match["tradeId"]))

                        if match["selfDealingQty"] != 0:
                            localprint("自成交", match, match["tradeId"])
                            # self.sendMessage(f"cs现货-合约策略{match['symbol']}交易对自成交{match['selfDealingQty']}张合约")
                            continue
                        self.log_order.write(match.to_dict())
                        price_wbf = float(match['price'])
                        match["vol"] = round(match["vol"] / self.wbf_qty_unit)
                        qty_wbf = round((match['vol']) * 1) if match['side'] == "buy" else round((match['vol']) * -1)
                        if abs(match["fee"]) >0 and match["feeAsset"] == self.binance_symbol.split("/")[0]:
                            fee = round(match["fee"] / self.wbf_qty_unit,round(self.fee_qty_digital-self.wbf_qty_digital))
                            qty_wbf = round(qty_wbf + fee,round(self.fee_qty_digital-self.wbf_qty_digital))
                        if match['role'] == "taker":
                            localprint("漏推wbf—wss平仓", price_wbf, qty_wbf)
                            match_type = "close"
                        else:
                            localprint("漏推wbf—wss开仓", price_wbf, qty_wbf)
                            match_type = "open"  # open risk_close
                        new = pd.Series({"time": time.time(), 'id_wbf': match['tradeId'], "id_binance": 0, "price_wbf": price_wbf,
                             "price_binance": 0, "qty_wbf": qty_wbf, "qty_binance": 0, "match_price_binance": 0,
                             "match_qty_binance": 0, "time_wbf": match['ts'],
                             "time_binance": 0, "precent_profit": 0, "match_type": match_type,"fee":match['fee']},name= match['tradeId'])
                        
                        min_zhengPendingList = min_zhengPendingList.append(new)
                        for index, row in min_zhengPendingList.iterrows():
                            mydict = row.to_dict()
                            side = 1 if min_zhengPendingList["qty_wbf"].sum() >= 0 else -1
                            # 确定余数
                            qtyUnit = round(self.binance_qty_unit/self.wbf_qty_unit) if round(self.binance_qty_unit/self.wbf_qty_unit) != 0 else 1
                            mydict["qty_wbf"] = round(side * (abs(min_zhengPendingList["qty_wbf"].sum())
                                                                % qtyUnit),round(self.fee_qty_digital-self.wbf_qty_digital))
                            new_df = pd.DataFrame([mydict], index=[index])
                            diff_qty = round(float(min_zhengPendingList["qty_wbf"].sum() - mydict["qty_wbf"]),round(self.binance_qty_unit/self.wbf_qty_unit))  # 确定对冲量
                            qty = round(diff_qty * self.wbf_qty_unit,self.binance_qty_digital) # , self.binance_qty_digital
                            amount = abs(qty * float(price_wbf))
                            if amount < self.minHedgeAmt:
                                mydict["qty_wbf"] = round(mydict["qty_wbf"]+diff_qty, self.wbf_qty_digital)
                                new_df = pd.DataFrame([mydict], index=[index])
                                diff_qty = 0
                            if abs(diff_qty) > 0:
                                mydict["qty_wbf"] = diff_qty
                                new.qty_wbf = diff_qty
                                zhengPendingList = zhengPendingList.append(new)
                            break
                        min_zhengPendingList = new_df

        if flag_restart:
            self.restart_wss_wbf()
            localprint(f"内盘wss重连")
            # try:
            #     data_wbf = self.wbf_rest.getBalance()
            #     self.balance = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[1]]
            #     self.balance = self.balance[0]['balance']
            #     data_wbf['data'] = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[0]]
            #     if data_wbf['data']:
            #         self.position_qty = round(data_wbf['data'][0]['balance'] - self.init_coin, self.wbf_qty_digital)    # 内盘持仓
            #         self.coins = data_wbf['data'][0]['balance']
            # except Exception as e:
            #     self.errHandle(f"check_wss_wbf,get balance错误:{traceback.format_exc()}")
        Toolbox._GCSV(mkpath, "zhengOrderList", zhengOrderList)
        Toolbox._GCSV(mkpath, "zhengPendingList", zhengPendingList)
        Toolbox._GCSV(mkpath, "wbf_wss_execId_list", self.wbf_wss_execId_list)
        Toolbox._GCSV(mkpath, "min_zhengPendingList", min_zhengPendingList)
        task = executor.submit(self.open_binance)

    # 外盘推送
    def binance_wss_order(self, content):
        localprint("币安开始处理订单")
        global zhengOrderList, zhengPendingList, wbf_wss_execId_list
        with mutex_open_binance:
            with mutex:
                if float(content['matchVol']) and not (content['status'] == 'cancel'):  # 累计成交数量 > 0
                    localprint("正常订单bianance——wss", content['price'], content['matchPrice'], content['matchVol'])
                    for index, row in zhengPendingList.iterrows():
                        if content['orderId'] == row["id_binance"]:  # 订单 id
                            zhengPendingList.loc[index, "match_qty_binance"] = float(content['matchVol'])
                            zhengPendingList.loc[index, "match_price_binance"] = float(
                                content["matchPrice"])  # 订单平均成交价格
                            self.log.write(str("binance_accout___") + str(content))
                elif content['status'] == 'cancel':
                    localprint("取消订单bianance——wss")
                    executedQty = float(content['matchVol'])  # 累计成交量
                    executedPrice = float(content['matchPrice'])
                    side = "SELL" if content['side'] == "sell" else "BUY"
                    for index, row in zhengPendingList.iterrows():
                        if content['orderId'] == row["id_binance"]:  # 订单 id
                            if executedQty == 0:
                                zhengPendingList.loc[index, "id_binance"] = 0
                                zhengPendingList.loc[index, "price_binance"] = 0
                                zhengPendingList.loc[index, "qty_binance"] = 0
                                zhengPendingList.loc[index, "match_price_binance"] = 0
                                zhengPendingList.loc[index, "match_qty_binance"] = 0
                                zhengPendingList.loc[index, "time_binance"] = 0
                                zhengPendingList.loc[index, "match_type"] = "risk_close"
                                self.log.write("binance_accout___" + str(row) + str(content))
                            
                            elif executedQty > 0 and executedQty < abs(row["qty_binance"]):  # 未成交完全
                                new = {"time": time.time(), 'id_wbf': int(row['id_wbf']),
                                       "id_binance": row["id_binance"],
                                       "price_wbf": row["price_wbf"], "price_binance": executedPrice,
                                       "qty_wbf": round(executedQty / self.wbf_qty_unit) if side == "SELL" else round(
                                           -executedQty / self.wbf_qty_unit),
                                       "time_wbf": row["time_wbf"], "time_binance": row["time_binance"],
                                       "precent_profit": 0, "fee_wbf": 0, "fee_binance": 0}
                                zhengOrderList = zhengOrderList.append(new, ignore_index=True)  # 转移开仓订单
                                
                                zhengPendingList.loc[index, "qty_wbf"] = round(int(zhengPendingList.loc[
                                                                                       index, "qty_wbf"]) - executedQty / self.wbf_qty_unit) if side == "SELL" else \
                                                    round(int(zhengPendingList.loc[index, "qty_wbf"]) + executedQty / self.wbf_qty_unit)
                                
                                zhengPendingList.loc[index, "id_binance"] = 0
                                zhengPendingList.loc[index, "price_binance"] = 0
                                zhengPendingList.loc[index, "qty_binance"] = 0
                                zhengPendingList.loc[index, "match_price_binance"] = 0
                                zhengPendingList.loc[index, "match_qty_binance"] = 0
                                zhengPendingList.loc[index, "time_binance"] = 0
                                zhengPendingList.loc[index, "match_type"] = "risk_close"
                                self.log.write("binance_accout___" + str(row) + str(content))
                            elif executedQty == abs(row["qty_binance"]):  # 成交完全
                                new = {"time": time.time(), 'id_wbf': int(row['id_wbf']),
                                       "id_binance": row["id_binance"],
                                       "price_wbf": row["price_wbf"], "price_binance": executedPrice,
                                       "qty_wbf": row["qty_wbf"],
                                       "time_wbf": row["time_wbf"], "time_binance": row["time_binance"],
                                       "precent_profit": 0, "fee_wbf": 0, "fee_binance": 0}
                                zhengOrderList = zhengOrderList.append(new, ignore_index=True)  # 转移开仓订单
                                zhengPendingList.drop(index=index, inplace=True)  # 删除完全对冲订单
                                self.log_ansys.write(str(row.to_dict()))
                                self.log.write("binance_accout___" + str(row) + str(content))
                elif float(content['matchVol']) == 0:
                    pass
                else:
                    self.errHandle("binance异常情况", content)
        task = executor.submit(self.open_binance)

    def binance_account(self, content):
        global zhengOrderList, zhengPendingList
        if content['status'] == 'position':
            for pos in content['data']:
                if pos['symbol'] == self.binance_symbol2:
                    self.binance_position_qty = pos['pos']   # pos自带方向
                    self.binance_balance = self.binance_balance_raw + pos["unrealProfitLoss"]
        elif content['status'] == 'balance':
            for bal in content["data"]:
                if bal["symbol"] == self.binance_symbol2.split("/")[1]:
                    self.binance_balance_raw = bal['balance']
                    self.binance_balance = self.binance_balance_raw
        
        elif content['status'] == 'orders':  #
            task = wss_executor.submit(self.binance_wss_order, (content['data']))

    def merge_zhengOrderList(self):
        """
        # 对冲仓位订单
        :return:
        """

        global zhengOrderList, zhengPendingList
        # mutex.acquire()  # 上锁
        # mutex.release()  # 解锁
        rows = zhengOrderList.shape[0]
        if rows == 0:
            return
        while True:
            order_list = zhengOrderList["qty_wbf"].tolist()
            order_list_new = [1 if i > 0 else -1 for i in order_list]
            b = len(set(order_list_new))
            if b == 1 or b == 0:
                break

            with mutex:
                if zhengOrderList["qty_wbf"].sum() >= 0:
                    for index, row in zhengOrderList.iterrows():
                        if row["qty_wbf"] == 0:
                            zhengOrderList.drop(index=index, inplace=True)  # 删除完全收敛单订单
                        if row["qty_wbf"] < 0:  # 收敛单已经成交
                            diff = (zhengOrderList["price_binance"] - zhengOrderList["price_wbf"]) / zhengOrderList["price_wbf"]
                            index_max = diff[diff == diff.max()].index.tolist()[0]
                            time_min = zhengOrderList[zhengOrderList.index == index_max].time.tolist()[0]
                            qty_min = zhengOrderList.loc[zhengOrderList["time"] == time_min]["qty_wbf"].tolist()[0]
                            a = zhengOrderList.loc[zhengOrderList["time"] == time_min].index.tolist()[0]
                            if abs(qty_min) < abs(row["qty_wbf"]):
                                qty_wbf = round(row["qty_wbf"] + qty_min)
                                zhengOrderList.loc[index, "qty_wbf"] = qty_wbf
                                zhengOrderList.drop(index=a, inplace=True)      # 删除完全收敛单订单
                                return True
                            elif abs(qty_min) > abs(row["qty_wbf"]):
                                qty_wbf = round(qty_min + row["qty_wbf"])
                                zhengOrderList.loc[a, "qty_wbf"] = qty_wbf
                                zhengOrderList.drop(index=index, inplace=True)  # 删除完全收敛单订单
                                return True
                            elif abs(qty_min) == abs(row["qty_wbf"]):
                                zhengOrderList.drop(index=a, inplace=True)      # 删除完全收敛单订单
                                return True
                elif zhengOrderList["qty_wbf"].sum() < 0:
                    for index, row in zhengOrderList.iterrows():
                        if row["qty_wbf"] == 0:
                            zhengOrderList.drop(index=index, inplace=True)      # 删除完全收敛单订单
                        if row["qty_wbf"] > 0:  # 收敛单已经成交
                            diff = (zhengOrderList["price_wbf"] - zhengOrderList["price_binance"]) / zhengOrderList[
                                "price_wbf"]
                            index_max = diff[diff == diff.max()].index.tolist()[0]
                            time_min = zhengOrderList[zhengOrderList.index == index_max].time.tolist()[0]
                            qty_min = zhengOrderList.loc[zhengOrderList["time"] == time_min]["qty_wbf"].tolist()[0]
                            a = zhengOrderList.loc[zhengOrderList["time"] == time_min].index.tolist()[0]
                            if abs(qty_min) < abs(row["qty_wbf"]):
                                qty_wbf = round(row["qty_wbf"] + qty_min)
                                zhengOrderList.loc[index, "qty_wbf"] = qty_wbf
                                zhengOrderList.drop(index=a, inplace=True)      # 删除完全收敛单订单
                                return True
                            elif abs(qty_min) > abs(row["qty_wbf"]):
                                qty_wbf = round(qty_min + row["qty_wbf"])
                                zhengOrderList.loc[a, "qty_wbf"] = qty_wbf
                                zhengOrderList.drop(index=index, inplace=True)  # 删除完全收敛单订单
                                return True
                            elif abs(qty_min) == abs(row["qty_wbf"]):
                                zhengOrderList.drop(index=a, inplace=True)  # 删除完全收敛单订单
                                return True

    def timeout_close(self):
        while True:
            try:
                self.timeout_close_attch()
            except:
                self.errHandle(f"timeout_close,追单模块报错:{traceback.format_exc()}")
                # self.wsstask_timeout_close = dc.SDK(round(self.contract_base + self.wbf_contractId))
            time.sleep(3)

    # 拆除定时炸弹 追单 （3秒）
    def timeout_close_attch(self):
        global zhengPendingList, zhengOrderList
        flag_restart = 0
        for index, row in zhengPendingList.iterrows():
            if row["qty_binance"] == row["match_qty_binance"] and not (row["qty_binance"] == 0):  # 处理已经对冲完成订单
                new = {"time": time.time(), 'id_wbf': int(row['id_wbf']), "id_binance": row["id_binance"],
                       "price_wbf": row["price_wbf"],
                       "price_binance": row["match_price_binance"], "qty_wbf": row["qty_wbf"],
                       "time_wbf": row["time_wbf"], "time_binance": row["time_binance"],
                       "precent_profit": 0, "fee_wbf": 0, "fee_binance": 0}
                with mutex:
                    zhengOrderList = zhengOrderList.append(new, ignore_index=True)  # 转移开仓订单
                    zhengPendingList.drop(index=index, inplace=True)  # 删除完全对冲订单
                    self.log_ansys.write(str(row.to_dict()))
                self.log.write("timeout_close___" + str(row) + str("row[qty_binance] == row[match_qty_binance]"))
            elif abs(row["qty_binance"]) > abs(row["match_qty_binance"]) and (
                    time.time() - row["time_binance"] / 1000) > self.order_timeout:  # 追单
                #  撤销订单
                orderId_binance = row["id_binance"]
                try:
                    Dict = self.binance_rest.cancelOrder(symbol=self.binance_symbol2, orderId=orderId_binance)
                    self.allNums['666'] = self.allNums['666']+1
                except Exception as e:
                    self.errHandle(f"timeout_close 撤单错误:{traceback.format_exc()}")
                    return
                if Dict:  # 对binance _wss 修正处理
                    try:
                        Dict = self.binance_rest.queryOrder(symbol=self.binance_symbol2, orderId=orderId_binance)
                        self.allNums['777'] = self.allNums['777']+1
                        if Dict['status'] == 'success':
                            localprint("超过3秒，撤单", "延时", time.time() - Dict["data"]["ts"] / 1000, "s")
                        else:
                            return
                    except Exception as e:
                        self.errHandle(f"查询订单错误:{traceback.format_exc()}")
                        return
                    if (time.time() - Dict["data"]["ts"]/1000)>20:     # 订单在撤销20s 没有回报处理 # Dict['status'] == 'CANCELED' and
                        executedQty = float(Dict["data"]['matchVol'])
                        executedPrice = float(Dict["data"]['matchPrice'])
                        side = "SELL" if Dict["data"]['side'] == "sell" else "BUY"
                        localprint("订单超过20秒未处理","executedQty", executedQty)
                        if executedQty == 0:
                            with mutex:
                                zhengPendingList.loc[index, "id_binance"] = 0
                                zhengPendingList.loc[index, "price_binance"] = 0
                                zhengPendingList.loc[index, "qty_binance"] = 0
                                zhengPendingList.loc[index, "match_price_binance"] = 0
                                zhengPendingList.loc[index, "match_qty_binance"] = 0
                                zhengPendingList.loc[index, "time_binance"] = 0
                                zhengPendingList.loc[index, "match_type"] = "risk_close"
                            self.log.write("timeout_close___" + str(row) + str(Dict))
                        elif executedQty > 0 and executedQty < abs(row["qty_binance"]):  # 未成交完全
                            new = {"time": time.time(), 'id_wbf': int(row['id_wbf']), "id_binance": row["id_binance"],
                                 "price_wbf": row["price_wbf"], "price_binance": executedPrice,
                                 "qty_wbf": round(executedQty / self.wbf_qty_unit) if side == "SELL" else round(-executedQty / self.wbf_qty_unit),
                                 "time_wbf": row["time_wbf"], "time_binance": row["time_binance"],
                                 "precent_profit": 0, "fee_wbf": 0, "fee_binance": 0}
                            with mutex:
                                zhengOrderList = zhengOrderList.append(new,ignore_index=True)  # 转移开仓订单
                                zhengPendingList.loc[index, "qty_wbf"] = round(int(zhengPendingList.loc[index, "qty_wbf"]) - executedQty / self.wbf_qty_unit) if side == "SELL" else \
                                                                          round(int(zhengPendingList.loc[index, "qty_wbf"]) + executedQty / self.wbf_qty_unit)
                                zhengPendingList.loc[index, "price_binance"] = 0
                                zhengPendingList.loc[index, "qty_binance"] = 0
                                zhengPendingList.loc[index, "match_price_binance"] = 0
                                zhengPendingList.loc[index, "match_qty_binance"] = 0
                                zhengPendingList.loc[index, "time_binance"] = 0
                                zhengPendingList.loc[index, "match_type"] = "risk_close"
                            self.log.write("timeout_close___" + str(row) + str(Dict))
                        elif executedQty == abs(row["qty_binance"]):  # 成交完全
                            new = {"time": time.time(), 'id_wbf': int(row['id_wbf']), "id_binance": row["id_binance"],
                                 "price_wbf": row["price_wbf"],
                                 "price_binance": executedPrice, "qty_wbf": row["qty_wbf"],
                                 "time_wbf": row["time_wbf"], "time_binance": row["time_binance"],
                                 "precent_profit": 0 ,"fee_wbf": 0, "fee_binance": 0}
                            with mutex:
                                zhengOrderList = zhengOrderList.append(new,ignore_index=True)  # 转移开仓订单
                                zhengPendingList.drop(index=index, inplace=True)  # 删除完全对冲订单
                                self.log_ansys.write(str(row.to_dict()))
                            self.log.write("timeout_close___" + str(row) + str(Dict))
                        flag_restart = 1
                        task = executor.submit(self.open_binance)

        if flag_restart:
            self.restart_wss_binance()

        if zhengOrderList.shape[0]>0:
            sum_qty = round(zhengOrderList["qty_wbf"].sum()*self.wbf_qty_unit, self.wbf_qty_digital)
            diff_qty = round(zhengOrderList["qty_wbf"].sum()*self.wbf_qty_unit-self.position_qty, self.wbf_qty_digital)
            localprint(Toolbox.timestamp(),"zhengOrderList",zhengOrderList.shape[0],"总计",sum_qty,diff_qty,
             "预期盈利",(zhengOrderList["qty_wbf"] * self.wbf_qty_unit * (zhengOrderList["price_binance"] - zhengOrderList["price_wbf"])).sum())

    def strategy_init(self):
        self.wss_init()
        # 获取内盘当前持仓
        while True:
            try:
                data_wbf = self.wbf_rest.getBalance()
                self.balance = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[1]]
                self.balance = self.balance[0]['balance']
                data_wbf['data'] = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[0]]
                if data_wbf['data'] :
                    self.position_qty = round(data_wbf['data'][0]['balance'] - self.init_coin, self.wbf_qty_digital)
                    self.coins = data_wbf['data'][0]['balance']
                else:
                    self.position_qty = 0
                break
            except:
                self.errHandle(f"内盘init获取到{self.base_exchange}仓位错误:{traceback.format_exc()}")
            time.sleep(1)
        localprint(f"init获取到{self.base_exchange}仓位",self.position_qty)

        # 获取外盘当前持仓
        while True:
            try:
                data_binance = self.binance_rest.getPosition(symbol=self.binance_symbol2)
                if data_binance["data"]:
                    data = [i for i in data_binance["data"] if i['symbol'] == self.binance_symbol2]
                    if data:
                        self.binance_position_qty = float(data[0]['pos'])
                    else:
                        self.binance_position_qty = 0
                    break
            except:
                localprint(f"init获取到{getattr(self, 'base_exchange', 'binanceUsdtSwap')}仓位错误:{traceback.format_exc()}")
            time.sleep(2)
        localprint("init获取到{getattr(self, 'base_exchange', 'binanceUsdtSwap')}仓位",self.binance_position_qty)

        # 获取外盘usdt资金
        while True:
            try:
                data = self.binance_rest.getBalance()
            except Exception as e:
                self.errHandle(f"外盘查询getBalance错误:{traceback.format_exc()}")
                time.sleep(0.5)
                continue
            try:
                data = [i for i in data["data"] if i['symbol'] == self.binance_symbol2.split("/")[1]]   # 获取usdt余额
                self.binance_balance_raw = float(data[0]['balance'])
            except Exception as e:
                self.binance_balance_raw = 0

            data_binance = self.binance_rest.getPosition(symbol=self.binance_symbol2)
            self.binance_balance = self.binance_balance_raw
            # 内外盘usdt金额都要大于0
            if self.balance > 0 and self.binance_balance > 0:  # 全部触发 # and self.accountwbf_flag == True and self.accountbianance_flag == True
                break
            
            localprint("保证金小于零,不执行策略")
            if not self.send_tag:
                self.callPhone(f"{self.binance_symbol}现货交易对资金或币不足")
                self.send_tag = True
            time.sleep(2)

    # 风控模块
    def risk_mange(self):
        global t_list, zhengOrderList
        while True:
            try:
                localprint("风控模块正常运行")
                for k,v in self.allNums.items():
                    if v > 100 and k != '888':
                        if self.xianpinerr < 1:
                            mess = f"{self.base_exchange}  {self.binance_symbol}交易对 有限频风险，立即查看"
                            self.sendMessage(mess)
                            send = threadpool.WorkRequest(self.sendmail, args=('cs限频风险', mess,))
                            self.pool.putRequest(send)
                            self.xianpinerr += 1
                self.checkRest.write(f"{self.allNums}\n")

                # 连续亏损报警
                zhengOrderList.loc[zhengOrderList['qty_wbf']<0, 'profit'] = zhengOrderList['price_wbf']-zhengOrderList['price_binance']
                zhengOrderList.loc[zhengOrderList['qty_wbf']>0, 'profit'] = zhengOrderList['price_binance']-zhengOrderList['price_wbf']
                profit = zhengOrderList.tail(6).loc[zhengOrderList['profit']>0]
                lxrisk = False
                if zhengOrderList.shape[0] >= 6 and profit.empty:
                    if time.time() - self.lastRiskTime2 >= 600:
                        lxrisk = True
                        self.wbf_cancelall()
                        self.binance_cancelall()
                        localprint(f"连续亏损{zhengOrderList.tail(6).loc[zhengOrderList['profit']<0]}")
                        mess = f"{self.base_exchange}  {self.binance_symbol}交易对 出现连续亏损"
                        self.callPhone(mess)
                        send = threadpool.WorkRequest(self.sendmail, args=(f'cs {self.binance_symbol}连续亏损', mess,))
                        self.pool.putRequest(send)
                        self.lastRiskTime2 = time.time()
                
                data_wbf = self.wbf_rest.getBalance()
                self.balance = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[1]]
                self.balance = self.balance[0]['balance']
                data_wbf['data'] = [i for i in data_wbf['data'] if i['symbol'] == self.binance_symbol.split("/")[0]]
                if data_wbf['data']:
                    pos_wbf = round(data_wbf['data'][0]['balance'] - self.init_coin, self.wbf_qty_digital)
                    self.position_qty = pos_wbf
                    self.coins = data_wbf['data'][0]['balance']
                else:
                    pos_wbf = 0
                
                data_binance = self.binance_rest.getPosition(symbol=self.binance_symbol2)
                self.allNums['888'] = self.allNums['888']+1
                if data_binance["data"]:
                    data = [i for i in data_binance["data"] if i['symbol'] == self.binance_symbol2]
                    if data:
                        pos_binance = 0
                        for data_pos in data:
                            pos_binance += float(data_pos['pos'])
                    else:
                        pos_binance = 0
                self.binance_position_qty = pos_binance
                self.posAmt = abs(self.binance_position_qty) * self.now_index_price
                
                self.cookLog.write(f"内盘usdt:{self.balance:0.2f} 币:{self.coins} 持仓:{pos_wbf} 名义资产:{abs(pos_wbf)*self.now_index_price:0.2f}usdt")
                self.cookLog.write(f"外盘usdt:{self.binance_balance:0.2f} 持仓:{pos_binance} 名义资产:{abs(pos_binance)*self.now_index_price:0.2f}usdt\n")

                # 计算暴露
                self.diff_qty_list.append(pos_wbf + pos_binance)
                if len(self.diff_qty_list) >= 6:
                    del self.diff_qty_list[0]  # 删除第一个数
                risk = False
                self.market_make_flag = True
                if len(self.diff_qty_list) >= 5:
                    self.diff_qty_list = [i if (abs(i) > 2*self.binance_qty_unit and abs(i)*self.now_index_price > self.riskAmt)*self.binance_qty_unit else 0 for i in self.diff_qty_list]
                    b = len(set(self.diff_qty_list))
                    # 统计连续2次暴露间的差
                    new_diff_qty_list = [
                        self.diff_qty_list[i] - self.diff_qty_list[i - 1] if i > 0 else self.diff_qty_list[i] for i in
                        range(len(self.diff_qty_list))]
                    zheng_list = [1 for i in new_diff_qty_list if i > 0]
                    fan_list = [-1 for i in new_diff_qty_list if i < 0]
                    # 若flag_zengjia为True，表示暴露连续扩大
                    flag_zengjia = (len(zheng_list) == len(new_diff_qty_list)) or \
                                   (len(fan_list) == len(new_diff_qty_list))
                    if (b >= 1 and not (self.diff_qty_list[0] == 0)) or flag_zengjia:  # 持续有暴露 或者 有持续增加趋势
                        risk = True  # 触发风控
                        localprint(time.strftime('%Y-%m-%d %H:%M:%S'), "rest触发风控")
                
                if (risk == True):  # 同时触发风控 # or risk_timeout == True # and wss_risk == True
                    if time.time() - self.lastRiskTime >= 600:
                        localprint(f"{time.strftime('%Y-%m-%d %H:%M:%S')}打电话,暴露:{self.diff_qty_list}")
                        self.diff_qty_list = [abs(i) for i in self.diff_qty_list]
                        mess = f"{self.base_exchange}  {self.binance_symbol}交易对 出现{int(max(self.diff_qty_list)*self.now_index_price)}usdt暴露"
                        self.callPhone(mess)
                        send = threadpool.WorkRequest(self.sendmail, args=('bit暴露', mess,))
                        self.pool.putRequest(send)
                        self.risk_num += 1
                        if self.risk_num >=3 or abs(max(self.diff_qty_list))*self.now_index_price > self.riskAmt*10:
                            self.callPhone2(f"{self.base_exchange}  {self.binance_symbol}交易对 出现{int(max(self.diff_qty_list)*self.now_index_price)}usdt暴露")
                            pass
                        # self.wbf_cancelall()
                        self.binance_cancelall()
                        self.risk = True
                        self.lastRiskTime = time.time()
                    localprint(time.strftime('%Y-%m-%d %H:%M:%S'), f"{self.base_exchange}  {self.binance_symbol}交易对 出现{int(max(self.diff_qty_list)*self.now_index_price)}usdt暴露")
                    time.sleep(3)
                    continue
                else:
                    self.risk_num = 0
                    self.risk = lxrisk if lxrisk else False
            except Exception as e:
                self.errHandle(f"风控异常:{traceback.format_exc()}")
                self.market_make_flag = False
            time.sleep(60)
    
    def get_list_orders(self):
        data_orders = self.wbf_rest.getOpenOrders(self.binance_symbol)
        list_orders_taker_buy = []
        list_orders_taker_sell = []
        for data_order in data_orders["data"]:
            if data_order["side"] == "buy":
                list_orders_taker_buy.append([data_order["price"], data_order["orderId"],data_order["vol"]])
            elif data_order["side"] == "sell":
                list_orders_taker_sell.append([data_order["price"], data_order["orderId"],data_order["vol"]])
        try:
            buyAmt = np.array(list_orders_taker_buy)[:, 2].astype('float')*float(list_orders_taker_buy[1][0])
            sellAmt = np.array(list_orders_taker_sell)[:, 2].astype('float')*float(list_orders_taker_sell[1][0])
            localprint(f"当前挂单总笔数{len(data_orders['data'])},buy {len(list_orders_taker_buy)}  sell {len(list_orders_taker_sell)} "
                  f"金额buy {buyAmt.astype(float).sum()} sell{sellAmt.astype(float).sum()}")
        except:
            self.errHandle(f"查openOrders报错:{traceback.format_exc()}")
        return list_orders_taker_buy ,list_orders_taker_sell

    def market_make_attch(self):  # 挂撤单，做市
        # 计算摆盘用资金
        binance_balance = self.binance_balance * (1 + self.accountlever)      # 外盘实际可用usdt金额
        wbf_balance = self.balance                                            # 内盘usdt余额
        
        # 保证金不足报警,内盘或外盘usdt不足初始的20%
        if binance_balance < self.warn_balance * self.outinit_usdt or wbf_balance < self.warn_balance * self.init_usdt:
            localprint(f"外盘权益:{binance_balance}不足初始保证金{self.outinit_usdt}的{self.warn_balance*100}%\n"
                  f"内盘权益:{wbf_balance}不足初始保证金{self.init_usdt}的{self.warn_balance*100}%")
            try:
                # 电话强报警,盘口摆宽
                self.bid_percent = self.risk_percent
                self.ask_percent = self.risk_percent
                if not self.call_tag:
                    mess = f'cs现货{self.binance_symbol}交易对现货保证金{binance_balance}usdt不足初始的{self.warn_balance}'
                    self.callPhone(mess)
                    send = threadpool.WorkRequest(self.sendmail, args=('cs保证金不足', mess,))
                    self.pool.putRequest(send)
                    self.call_tag = True
            except Exception as e:
                self.errHandle(f"保证金报警错误:{traceback.format_exc()}")
            if binance_balance == 0:    # 资金为0不摆近端
                localprint(f"近端摆盘进程正常:资金是0")
                return
        else:
            self.call_tag = False
            self.bid_percent = self.init_bid_percent
            self.ask_percent = self.init_ask_percent
        
        list_orders_taker_buy, list_orders_taker_sell = self.get_list_orders()   # 获取当前getOpenOrders所有挂单

        t1 = time.time()
        try:
            # 从币安合约拿深度
            tt1 = time.time()
            depth_binance = self.wsstask_market_maker.getDepth(symbol=self.binance_symbol2, exc=self.hedge_exchange)
            spot_depth_binance = self.wsstask_market_maker.getDepth(symbol=self.binance_symbol2, exc='binanceSpot')
            tt2 = time.time()-tt1

            depth_binance = depth_binance["data"]
            self.now_index_price = (depth_binance[1][0][0] + depth_binance[2][0][0]) / 2
            spotBid = spot_depth_binance["data"][1][0][0]   # 现货买一
            spotAsk = spot_depth_binance["data"][2][0][0]   # 现货卖一
            spot_index = (spotBid+spotAsk)/2

            # 过滤深度数据
            diff = time.time()*1000 - float(depth_binance[0])
            if diff > getattr(self, 'depth_timeout', 1000):
                self.errHandle(f"深度数据延时达到{diff}ms,过滤本次深度")
                return
            
            # 数据标准化
            spot_bid_price = np.array(depth_binance[1])[:self.num_maker, 0].tolist()
            spot_ask_price = np.array(depth_binance[2])[:self.num_maker, 0].tolist()
            spot_bid_vol = np.array(depth_binance[1])[:self.num_maker, 1]*self.qty_precent/100
            spot_ask_vol = np.array(depth_binance[2])[:self.num_maker, 1]*self.qty_precent/100
        except Exception as e:
            self.errHandle(f"wss没有获取到数据:{traceback.format_exc()}")
            self.wsstask_market_maker = dc.SDK(round(self.contract_base + self.wbf_contractId))
            return
        
        # 当内盘价格精度大于外盘价格精度时,精度不同,聚合价格
        if self.wbf_price_unit > self.binance_price_unit:
            spot_bid_price =  [j - n*self.wbf_price_unit for n,j in enumerate(spot_bid_price)]
            spot_ask_price =  [j + n*self.wbf_price_unit for n,j in enumerate(spot_ask_price)]
        
        # 补齐档位
        for i,price_list in enumerate([spot_bid_price,spot_ask_price]):
            diffnum = round(self.num_maker-len(price_list))
            if diffnum > 0:
                if i == 0:
                    if self.nearRatio == 0:
                        spot_bid_price.extend([spot_bid_price[-1] - offset*num_diff for num_diff in range(diffnum)])
                    else:
                        spot_bid_price.extend([spot_bid_price[0] - self.nearRatio*spot_bid_price[0] - offset*num_diff for num_diff in range(diffnum)])
                if i == 1:
                    if self.nearRatio == 0:
                        spot_ask_price.extend([spot_ask_price[-1] + offset*num_diff for num_diff in range(diffnum)])
                    else:
                        spot_ask_price.extend([spot_ask_price[0] + self.nearRatio*spot_ask_price[0] + offset*num_diff for num_diff in range(diffnum)])

        # 根据现货价差调整,max_percent表示最大偏离现货价格的比例,若升贴水超过千2，摆盘价差会扩大，为了防止套利发生，这段代码很有必要
        bidslip = 1-self.profit_percent/100
        askslip = 1+self.profit_percent/100
        # 若合约买盘大于现货卖一价格超过手续费+预期收益(有套利空间),则调整买盘价格,只升水手续费率
        if spot_bid_price[0] > spotAsk*(1+self.max_percent/100+self.profit_percent/100):
            spot_bid_price = [(i-(spot_bid_price[0]-spotAsk))*(1+self.max_percent/100) for i in spot_bid_price]
        else:
            spot_bid_price = [i*bidslip for i in spot_bid_price]
        # 若合约卖盘小于现货买一价格超过手续费+预期收益(有套利空间)，则调整卖盘价格，只贴水手续费率
        if spot_ask_price[0] < spotBid*(1-self.max_percent/100-self.profit_percent/100):
            spot_ask_price = [(i+(spotBid-spot_ask_price[0]))*(1-self.max_percent/100) for i in spot_ask_price]
        else:
            spot_ask_price = [i*askslip for i in spot_ask_price]

        # 根据杠杆率调整摆盘
        self.lever = abs(self.binance_position_qty)*self.now_index_price/self.binance_balance               # 外盘实际杠杆倍数
        self.offsetPoint = np.nanmin([(getattr(self, 'lever', 0)/getattr(self, 'leverLimit', 3))**0.5, 1])  # 偏移参数
        self.offsetPoint = np.nanmax([self.offsetPoint, -1])
        bidPriceOffset = -getattr(self, 'maxPriceOffset', 0.001) * self.offsetPoint \
                if self.binance_position_qty > 0 else \
                    getattr(self, 'maxPriceOffset', 0.001) * self.offsetPoint
        askPriceOffset = getattr(self, 'maxPriceOffset', 0.001) * self.offsetPoint \
                if self.binance_position_qty < 0 else \
                    -getattr(self, 'maxPriceOffset', 0.001) * self.offsetPoint
        
        # 偏移聚合
        bid_move = self.bid_percent+bidPriceOffset                                    # 预期收益率
        bid_move = bid_move+self.timeout_percent if self.timeout_order else bid_move  # 下单延时偏移
        bid_move = bid_move+self.risk_percent if self.risk else bid_move              # 触发风控偏移
        ask_move = self.ask_percent+askPriceOffset
        ask_move = ask_move+self.timeout_percent if self.timeout_order else ask_move
        ask_move = ask_move+self.risk_percent if self.risk else ask_move
        localprint(f"偏移量:{bid_move} 延时:{self.timeout_order}{self.timeout_percent} 暴露:{self.risk}{self.risk_percent}")
        spot_bid_price = np.array(spot_bid_price)*(1 - bid_move / 100)
        spot_ask_price = np.array(spot_ask_price)*(1 + ask_move / 100)
        if (spot_ask_price[0]-spot_bid_price[0])/spot_bid_price[0] > 0.01:
            localprint(f"摆盘价差异常扩大:buy{spot_bid_price} sell{spot_ask_price}")
        
        # 根据主动taker的价格调整后面的摆盘价格
        buy_price_list = [spot_bid_price[i] * (1 - self.taker_bid_percent / 100) if i >= 5 else spot_bid_price[i]
                          for i in range(len(spot_bid_price))]
        sell_price_list = [spot_ask_price[i] * (1 + self.taker_ask_percent / 100) if i >= 5 else spot_ask_price[i]
                          for i in range(len(spot_ask_price))]
        
        # 内盘币不足报警
        if self.coins < self.warn_balance*self.init_coin:
            if not self.send_tag:
                mess = f'cs现货{self.binance_symbol}交易对币数量{self.coins}个,不足初始{self.init_coin}的{self.warn_balance},尽快入金!'
                send = threadpool.WorkRequest(self.sendmail, args=('cs现货币不足', mess,))
                self.pool.putRequest(send)
                self.callPhone(mess)
                self.send_tag = True
        
        # 计算下单量,根据持仓修改
        ratio = self.every_qty_precent/100
        amount_buy = round(wbf_balance*ratio/self.now_index_price, self.wbf_qty_digital)      # 买盘总下单量, 内盘usdt余额*百分比/价格,只跟内盘u相关，不管外盘币数量
        amount_buynear = round(min(wbf_balance*ratio/self.now_index_price, np.nansum(spot_bid_vol)), self.wbf_qty_digital)      # 只跟内盘u和外盘真实深度相关
        amount_sell = round(self.coins*self.sellRatio, self.wbf_qty_digital)
        amount_sellnear = round(min(self.coins*self.sellRatio, np.nansum(spot_ask_vol)), self.wbf_qty_digital)

        # self.lever = self.binance_position_qty*self.now_index_price/self.binance_balance     # 外盘实际杠杆倍数
        # adjBuyAmt = 1              # 挂单量根据实际杠杆调整的参数
        # adjSellAmt = 1
        # if self.lever > 1:
        #     adjBuyAmt = 1/self.lever
        # elif self.lever < -1:
        #     adjSellAmt = 1/abs(self.lever)
        # balance = min(binance_balance, wbf_balance)*self.every_qty_precent/100    # 每次下单金额占总账户的比例
        # amount_buy = round(balance/self.now_index_price*adjSellAmt, self.wbf_qty_digital)     # 买盘总下单量
        # amount_sell = round(min(self.coins*self.every_qty_precent/100*adjBuyAmt, binance_balance/self.now_index_price*adjBuyAmt), self.wbf_qty_digital)    # 卖盘总下单量，内盘币和外盘可用u的较小值
        # if self.position_qty < 0:   # 持有空单
        #     balance = min(self.balance, self.binance_balance*(1 + self.accountlever)) # 可以多算金额，买盘多摆没问题
        #     balance = balance*self.every_qty_precent/100
        #     amount_buy = round(balance/self.now_index_price*adjSellAmt, self.wbf_qty_digital)
        # elif self.position_qty > 0: # 持有多单
        #     balance = self.binance_balance*(1 + self.accountlever)
        #     balance = balance*self.every_qty_precent/100
        #     amount_sell = round(min(self.coins*self.every_qty_precent/100*adjBuyAmt, balance/self.now_index_price*adjBuyAmt),self.wbf_qty_digital)
        # self.far_buy_amt = amount_buy*self.now_index_price      # 远端摆盘金额参考近端
        # self.far_sell_amt = amount_sell*self.now_index_price    # 远端摆盘金额参考近端

        # 根据外盘深度和可用资金调整摆盘数量
        for i in range(len(spot_bid_vol)):
            if spot_bid_vol[i] > amount_buynear/len(spot_bid_vol):
                spot_bid_vol[i] = amount_buynear/len(spot_bid_vol)*(random.uniform(0.9,1.1))
        volRatio = spot_bid_vol/spot_bid_vol.sum()    # 计算每档占比
        num_maker = self.num_maker-len(spot_bid_vol) if self.num_maker-len(spot_bid_vol)>1 else self.num_maker
        weight = np.array([i**(-i/num_maker) for i in range(1, int(num_maker+1))])
        random.shuffle(weight)             # list随机打乱
        weight = weight/np.nansum(weight)  # 摆盘量权重
        buy_amount_list1 = volRatio*amount_buynear
        buy_amount_list2 = amount_buy*weight
        buy_amount_list = np.hstack((buy_amount_list1, buy_amount_list2))

        for i in range(len(spot_ask_vol)):
            if spot_ask_vol[i] > amount_sellnear/len(spot_ask_vol):
                spot_ask_vol[i] = amount_sellnear/len(spot_ask_vol)*(random.uniform(0.9,1.1))
        volRatio = spot_ask_vol/spot_ask_vol.sum()    # 计算每档占比
        num_maker = self.num_maker-len(spot_ask_vol) if self.num_maker-len(spot_ask_vol)>1 else self.num_maker
        weight = np.array([i**(-i/num_maker) for i in range(1, int(num_maker+1))])
        random.shuffle(weight)             # list随机打乱
        weight = weight/np.nansum(weight)  # 摆盘量权重
        sell_amount_list1 = volRatio*amount_sellnear
        sell_amount_list2 = amount_sell*weight
        sell_amount_list = np.hstack((sell_amount_list1, sell_amount_list2))
        self.far_buy_amt = amount_buy*self.now_index_price*1.5         # 远端摆盘金额是近端的1.5倍
        # self.far_sell_amt = (self.coins-sell_amount_list.sum()*2)*self.now_index_price    # 动态调整远端摆盘量
        self.far_sell_amt = amount_sell*self.now_index_price*1.5    # 固定远端摆拍量

        # 最小和最大挂单量优化
        min_vol = self.min_amt/self.now_index_price+self.wbf_qty_unit
        buy_amount_list = np.array(buy_amount_list)
        buy_amount_list[buy_amount_list<min_vol] = min_vol
        sell_amount_list = np.array(sell_amount_list)
        sell_amount_list[sell_amount_list<min_vol] = min_vol
        
        # 数量精度优化
        buy_amount_list = [f"%.{self.wbf_qty_digital}f" % i for i in buy_amount_list]       # 延时0.02ms
        sell_amount_list = [f"%.{self.wbf_qty_digital}f" % i for i in sell_amount_list]

        # 价格精度优化
        if self.unitTag:
            buy_price_list = [float(f"%.{self.unitNum}f" % i) for i in buy_price_list]        # 延时0.05ms
            sell_price_list = [float(f"%.{self.unitNum}f" % i) for i in sell_price_list]
        else:
            buy_price_list = [Toolbox.round(i, self.wbf_price_unit, 'down') for i in buy_price_list]
            sell_price_list = [Toolbox.round(i, self.wbf_price_unit, 'up') for i in sell_price_list]

        # cress挂单撤销
        cancal_list = []
        cancal_list.extend([i[1] for i in list_orders_taker_buy if i[0] > buy_price_list[0]])
        cancal_list.extend([i[1] for i in list_orders_taker_sell if i[0] < sell_price_list[0]])

        # 撤销重复挂单+大额挂单
        def get_cancal_order(list_orders):
            list_price = []
            list_orders_cancal = []
            for i in list_orders:
                if i[0] in list_price:  # or i[2]*i[0] > 30000:
                    list_orders_cancal.append(i[1])
                list_price.append(i[0])
            return list_orders_cancal

        cancal_list.extend(get_cancal_order(list_orders_taker_buy))
        cancal_list.extend(get_cancal_order(list_orders_taker_sell))

        cancal_list = list(filter(lambda x: x!=None, cancal_list))
        t2 = time.time()-t1
        self._cancelOrders(cancal_list)
        localprint(f"摆盘耗时:{round(t2*1000, 2)}ms  其中zmq耗时:{round(tt2*1000, 2)}ms 计算耗时:{round((t2-tt2)*1000, 2)}ms")

        ########################  下单  ########################
        task_list = []
        if len(sell_price_list) > 0:
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(sell_price_list[:5], sell_amount_list[:5], 'sell-limit',True)))
        if len(buy_price_list) > 0:
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(buy_price_list[:5], buy_amount_list[:5], 'buy-limit',True)))
        if len(sell_amount_list) > 5:
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(sell_price_list[5:20], sell_amount_list[5:20], 'sell-limit', False)))
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(sell_price_list[20:], sell_amount_list[20:], 'sell-limit', False)))
        if len(buy_amount_list) > 5:
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(buy_price_list[5:20], buy_amount_list[5:20], 'buy-limit', False)))
            task_list.append(threading.Thread(target=self.parallelOrder,
                                                args=(buy_price_list[20:], buy_amount_list[20:], 'buy-limit', False)))

        for p in task_list:
            p.start()
        for p in task_list:
            p.join()
        
        # 撤上次的挂单
        canTh = threading.Thread(target=self._cancelOrders, args=(self.lastNearBuyOrders, ))
        canTh.start()
        self._cancelOrders(self.lastNearSellOrders)
        canTh.join()

        self.lastNearBuyOrders = list(filter(lambda x: x!=None, self.buyNearOrders))
        self.lastNearSellOrders = list(filter(lambda x: x!=None, self.sellNearOrders))
        self.buyNearOrders = []
        self.sellNearOrders = []
        
        # self.farBidOne = buy_price_list[0]     # 近端最远价格是远端摆盘价格的起点
        # self.farAskOne = sell_price_list[0]    # 近端最远价格是远端摆盘价格的起点

    def parallelOrder(self, sell_price_list, sell_amount_list, mytype, postonly=True, ty='near'):
        try:
            time_init = time.time()
            if len(sell_price_list) == 0:
                return
            localprint(f"{ty}下单信息:{mytype} 价{sell_price_list} 量{sell_amount_list} 金额:{np.nansum(np.array(sell_amount_list).astype('float'))} "
                  f"{round(np.nansum(np.array(sell_amount_list).astype('float'))*self.now_index_price,2)}  价{len(sell_price_list)} 量{len(sell_amount_list)}")
            res = self.wbf_rest.makeOrders(symbol=self.binance_symbol, vol=sell_amount_list, price=sell_price_list,
                                             offset='open', orderType=mytype,
                                             postOnly=postonly)
            failed = [i for i in res['data'] if i['code'] != 0]
            self.detailLog.write(f"{ty} {mytype} 单笔下单耗时:{round((time.time()-time_init)*1000, 2)}ms {failed}")
            try:
                if round((time.time()-time_init)*1000, 2)>1000:
                    # self.sendMessage(f"土耳其现货{self.binance_symbol}交易对,下单耗时:{round((time.time()-time_init)*1000, 2)}ms")
                    localprint(f"土耳其现货{self.binance_symbol}交易对,下单耗时:{round((time.time()-time_init)*1000, 2)}ms")
            except:
                pass
            if ty == 'far':
                if mytype == 'buy-limit':
                    self.buyfarOrders = [i['orderId'] for i in res['data']]
                else:
                    self.sellfarOrders = [i['orderId'] for i in res['data']]
            else:
                if mytype == 'buy-limit':
                    self.buyNearOrders += [i['orderId'] for i in res['data']]
                else:
                    self.sellNearOrders += [i['orderId'] for i in res['data']]
            difftime = time.time() - time_init
            self.timeout_order = True if (difftime) > 0.5 else False
        except Exception as e:
            self.errHandle(f"{mytype}下单错误{traceback.format_exc()}")
            return

    def market_make(self):
        while True:
            try:
                self.market_make_attch()
            except:
                self.errHandle(f"做市摆盘报错:{traceback.format_exc()}")
                self.wsstask_market_maker = dc.SDK(round(self.contract_base + self.wbf_contractId))
            time.sleep(self.chack_index_time)
    
    def far_market_make(self):
        time.sleep(2)
        while True:
            try:
                self.far_market_make_attch()
            except:
                self.errHandle(f"远端做市摆盘报错:{traceback.format_exc()}")
                self.wsstask_market_maker_far = dc.SDK(round(self.contract_base + self.wbf_contractId))
            time.sleep(self.chack_index_time*2)

    # 远端摆盘
    def far_market_make_attch(self):
        # 在近端失效的情况下，远端可以随价格波动
        depth_binance = self.wsstask_market_maker_far.getDepth(symbol=self.binance_symbol2, exc=self.hedge_exchange)['data']
        farBidOne = depth_binance[1][0][0]
        farAskOne = depth_binance[2][0][0]
        self.now_index_price = (farBidOne + farAskOne) / 2
        ratio = self.every_qty_precent/100*1.5
        amount_buy = round(self.balance*ratio/self.now_index_price, self.wbf_qty_digital)
        amount_sell = round(self.coins*self.sellRatio*1.5, self.wbf_qty_digital)

        buyamt1 = getattr(self, 'farBuyAmt1', amount_buy)       # 远端使用资金量，是余额的1/2
        sellamt1 = getattr(self, 'farSellAmt1', amount_sell/2)
        buyprice1 = round(farBidOne*(1-self.ratio1), self.unitNum)
        buyprice2 = round(farBidOne*(1-self.ratio2), self.unitNum)
        sellprice1 = round(farAskOne*(1+self.ratio1), self.unitNum)
        sellprice2 = round(farAskOne*(1+self.ratio2), self.unitNum)
        # 传参价格必须前高后低
        bp1, bv1 = self.countPV(buyprice1, buyprice2, buyamt1, 'buy')
        sp1, sv1 = self.countPV(sellprice2, sellprice1, sellamt1, 'sell')
        buyTh = threading.Thread(target=self.parallelOrder, args=(bp1, bv1, 'buy-limit', True, 'far'))
        buyTh.start()
        self.parallelOrder(sp1, sv1, 'sell-limit', True, 'far')
        buyTh.join()
        # self.detailLog.write(f"撤单orderID {self.lastfarOrders}")
        self._cancelOrders(self.lastfarOrders)
        self.lastfarOrders = []
        self.lastfarOrders += self.buyfarOrders
        self.lastfarOrders += self.sellfarOrders
        self.lastfarOrders = list(filter(lambda x: x!=None, self.lastfarOrders))
        self.buyfarOrders = []
        self.sellfarOrders = []
        self.lastFarBidPrice = bp1[0]
        self.lastFarAskPrice = sp1[0]
    
    # 根据外盘实际深度计算摆盘量,由于rest接口1000档都不足以获取深度信息，且没有聚合挡位，故暂时不计算
    # def countVol(self, amt1, amt2, price1, price2, price3, outDepth, side):
    #     p1Vol = 0
    #     p2Vol = 0
    #     if side == 'buy':
    #         for p in outDepth[1]:
    #             if p[0] < price1 and p[0] >= price2:
    #                 p1Vol += p[1]
    #             elif p[0] < price2 and p[0] >= price3:
    #                 p2Vol += p[1]
    #     else:
    #         for p in outDepth[2]:
    #             if p[0] > price1 and p[0] <= price2:
    #                 p1Vol += p[1]
    #             elif p[0] > price2 and p[0] <= price3:
    #                 p2Vol += p[1]
    #     localprint(p1Vol, p2Vol)
    #     return max(amt1, p1Vol), max(amt2, p2Vol)
    
    # 生成远端买盘价量
    def countPV(self, price1, price2, amt, side, step=20):
        priceList = list(set(list(np.round_(np.linspace(price1, price2, step), decimals=self.unitNum))))   # 按照价格区间生成指定数量、指定精度的均匀列表，并排序
        if side == 'buy':
            priceList.sort(reverse=True)
        else:
            priceList.sort()
        weight = np.array([i**(-i/len(priceList)) for i in range(1, int(len(priceList)+1))])
        weight = weight[::-1]/np.nansum(weight)  # 摆盘量权重
        amts = amt*weight
        amts = [self.adjustPrecision(v, self.wbf_qty_unit, 'down') for v in amts]
        amts = np.array(amts)
        amts[amts<self.wbf_qty_unit] = self.wbf_qty_unit
        return list(priceList), list(amts)
    
    # 盈利平仓
    def profit_close(self, binance_depth, wbf_bid_price, wbf_ask_price):
        global zhengPendingList, zhengOrderList
        try:
            binance_depth[1][0][0]
        except Exception as e:
            self.errHandle(f"profit_close未获取到数据:{traceback.format_exc()}")
            return
        
        if zhengPendingList.shape[0] == 0:
            # 处理正向收敛
            self.merge_zhengOrderList()  # 压缩对冲订单
            min_profit = max(self.profit_percent_close,0.5*self.profit_percent)
            if (zhengOrderList["qty_wbf"].sum() > 0 and self.position_qty < 0) or (zhengOrderList["qty_wbf"].sum() < 0 and self.position_qty > 0):
                self.except_num += 1
                localprint("except_num", self.except_num)
            if self.except_num >=5:
                zhengOrderList = pd.DataFrame(columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "time_wbf","time_binance", "precent_profit", "fee_wbf", "fee_binance"])
                self.except_num = 0
            if zhengOrderList["qty_wbf"].sum() > 0 and self.position_qty > 0 and wbf_bid_price > 0:
                price_binance, qty_binance = float(binance_depth[2][1][0]), float(binance_depth[2][0][1]) + float(
                    binance_depth[2][1][1])
                price_binance = Toolbox.round(price_binance, self.wbf_price_unit, "up")
                qty_max = round(qty_binance / self.wbf_qty_unit * self.qty_precent / 100)
                diff = (zhengOrderList["price_binance"] - zhengOrderList["price_wbf"]) / zhengOrderList["price_wbf"]
                index_max = diff[diff == diff.max()].index.tolist()[0]
                time_min = zhengOrderList[zhengOrderList.index == index_max].time.tolist()[0]
                qty_min = zhengOrderList.loc[zhengOrderList["time"] == time_min]["qty_wbf"].tolist()[0]
                qty = min(abs(qty_max), abs(qty_min))
                qty = round(qty * self.wbf_qty_unit, self.binance_qty_digital)
                order_price_wbf = zhengOrderList.loc[zhengOrderList["time"] == time_min]["price_wbf"].tolist()[0]
                order_price_binance = \
                zhengOrderList.loc[zhengOrderList["time"] == time_min]["price_binance"].tolist()[0]
                if not ((order_price_binance - order_price_wbf) / order_price_wbf > (0.4 * min_profit / 100)):
                    localprint(round((order_price_binance - order_price_wbf) / order_price_wbf, 5),
                            f"zheng not enough {min_profit}")
                    return
                # 抢一档
                min_profit = min_profit + 0.01
                precent_profit = min((order_price_binance - order_price_wbf) / order_price_wbf , self.profit_percent_close/100)- min_profit / 100
                price_binance = price_binance * (1 - precent_profit)
                price_binance = wbf_bid_price + self.wbf_price_unit if (wbf_bid_price + self.wbf_price_unit) > price_binance else price_binance
                price_binance = Toolbox.round(price_binance, self.wbf_price_unit, 'up')
                try:
                    qty = max(round(20/self.now_index_price, self.binance_qty_digital),qty)
                    self.parallelOrder([price_binance], [qty], "sell-limit", postonly=self.close_postonly)
                    localprint("下收敛单", "sell-limit", price_binance, qty, price_binance - wbf_bid_price,(order_price_binance - order_price_wbf) / order_price_wbf)
                except Exception as e:
                    self.errHandle(f"profit_close下单错误:{traceback.format_exc()}")
                    return 1
            # 处理反向收敛
            elif zhengOrderList["qty_wbf"].sum() < 0 and self.position_qty < 0 and wbf_ask_price > 0:
                price_binance, qty_binance = float(binance_depth[1][1][0]), float(binance_depth[1][0][1]) + float(
                    binance_depth[1][1][1])
                price_binance = Toolbox.round(price_binance, self.wbf_price_unit, "down")
                qty_max = round(qty_binance / self.wbf_qty_unit * self.qty_precent / 100)
                diff = (zhengOrderList["price_wbf"] - zhengOrderList["price_binance"]) / zhengOrderList["price_wbf"]
                index_max = diff[diff == diff.max()].index.tolist()[0]
                time_min = zhengOrderList[zhengOrderList.index == index_max].time.tolist()[0]
                qty_min = zhengOrderList.loc[zhengOrderList["time"] == time_min]["qty_wbf"].tolist()[0]
                qty = min(abs(qty_max), abs(qty_min))
                qty = round(qty * self.wbf_qty_unit, self.binance_qty_digital)
                order_price_wbf = zhengOrderList.loc[zhengOrderList["time"] == time_min]["price_wbf"].tolist()[0]
                order_price_binance = \
                zhengOrderList.loc[zhengOrderList["time"] == time_min]["price_binance"].tolist()[0]
                if not ((order_price_wbf - order_price_binance) / order_price_wbf > 0.4 * min_profit / 100) and not (
                        order_price_binance == 0):
                    localprint(round((order_price_wbf - order_price_binance) / order_price_wbf, 5),
                            f"fan not enough {min_profit}")
                    return
                # 抢一档
                min_profit = min_profit + 0.01
                precent_profit = min((order_price_wbf - order_price_binance) / order_price_wbf ,self.profit_percent/100 + 0.0002)- min_profit / 100
                price_binance = price_binance * (1 + precent_profit)
                price_binance = wbf_ask_price - self.wbf_price_unit if (wbf_ask_price - self.wbf_price_unit) < price_binance else price_binance
                price_binance = Toolbox.round(price_binance, self.wbf_price_unit, 'down')
                try:
                    qty = max(round(20 / self.now_index_price, self.binance_qty_digital), qty)
                    self.parallelOrder([price_binance], [qty], "buy-limit", postonly=self.close_postonly)
                    localprint("下收敛单", "buy-limit", price_binance, qty, wbf_ask_price - price_binance,min((order_price_wbf - order_price_binance) / order_price_wbf ,self.profit_percent/100 + 0.0002))
                except Exception as e:
                    self.errHandle(f"profit_close下单错误:{traceback.format_exc()}")
                    return 1


import platform
def data_process_init(path):
    global zhengOrderList, zhengPendingList, wbf_wss_execId_list, min_zhengPendingList
    zhengOrderList, zhengPendingList, wbf_wss_execId_list, min_zhengPendingList = data_process.init_csv(path)
    global mkpath
    mypath = path
    if (platform.system() == 'Windows'):
        mypath = mypath + "\\"
        localprint('Windows系统')
    elif (platform.system() == 'Linux'):
        mypath = mypath + "/"
        localprint('Linux系统')
    else:
        localprint('其他系统', '请检查配置')
        raise '主动抛出的异常'
    mkpath = mypath


def _stop(path='config_hedge.py'):
    drv, left = os.path.split(path)
    if drv:
        sys.path.append(drv)
    config = left
    config_hedge = __import__(config.split(".py")[0])
    my_str = strategy(config_hedge, is_stop=True)
    my_str.binance_cancelall()
    my_str.wbf_cancelall()


def main(path='config_hedge.py'):
    global t_list
    config = path
    config_hedge = __import__(config.split(".py")[0])
    data_process_init(sys.path[0])
    t_list = []
    my_str = strategy(config_hedge)
    my_str.strategy_init()

    # 设置初始时间
    my_str.init_time = time.time()

    t_risk = threading.Thread(target=my_str.risk_mange)  # 风控控制  触发风控时  杀死 追单，做市
    t_risk.start()

    t2 = threading.Thread(target=my_str.timeout_close)   # 追单 + 收敛处理
    t2.start()
    
    t4 = threading.Thread(target=my_str.check_wss_wbf_loop)  # 预防漏单
    t4.start()

    t3 = threading.Thread(target=my_str.market_make)  # 做市 + 收敛
    t3.start()
    t_list.append(t3)

    t5 = threading.Thread(target=my_str.far_market_make)        # 远端摆盘
    t5.start()


if __name__ == "__main__":
    main()



