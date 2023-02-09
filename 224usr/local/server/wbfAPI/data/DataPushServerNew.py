import sys

sys.path.append('/usr/local/server')

from wbfAPI import exchange
from wbfAPI.base import transform as tf
from wbfAPI.base import _zmq_new as zmq
from wbfAPI.config import _pushServerNew as _pushServer
from wbfAPI.config import _indexPrice

import threading
import time
import traceback
import numpy as np


# import os
# os.environ['http_proxy'] = 'http://127.0.0.1:1080'
# os.environ['https_proxy'] = 'https://127.0.0.1:1080'


class SDK():

    def __init__(self, port):
        config = _pushServer.pushServerDict[port]
        self.pushServerList = []

        process = threading.Thread(target=self._dataDrop)
        process.start()  # 开启数据丢弃及延迟重连功能
        self.init_ws(config['target'])
        self.start(config['server'])

    def init_ws(self, targetList: dict):
        print('websocket实例', targetList)
        for symbol, exc_list in targetList.items():  # 创建ws实例
            for exc in exc_list:
                setattr(self, f"{exc}_{symbol}_wss", getattr(getattr(exchange, exc), 'DataWss')(symbol))
                self.pushServerList.append(getattr(self, f"{exc}_{symbol}_wss"))

    def start(self, server_ports: list):
        for port in server_ports:
            thread = threading.Thread(target=self.server, args=(port,))
            thread.start()

    def server(self, port):
        connect = False
        while not connect:
            try:
                self.zmq = zmq.ZMQ('REP', port)
                connect = True
            except:
                print(traceback.format_exc())
                time.sleep(1)
                continue
        self.zmq.listen(self._listen)  # 监听

    # def restart(self):
    #     for exc in self.pushServerList:
    #         getattr(exc, 'stop')()
    #     self.start()

    def _listen(self, message):
        data = getattr(self, message[0])(**message[-1])
        return data

    def _dataDrop(self, timeout1=5000, timeout2=8000):

        """数据丢弃和重连websocket (通过深度判断)

        Args:
            timeout1 (int, optional): 重连websocket延迟
            timeout2 (int, optional): 删除数据延迟

        """
        while 1:
            time.sleep(int(timeout1 / 1000) - 1)
            try:
                for exc in self.pushServerList:
                    current = int(time.time() * 1000)
                    dataList = [
                        [getattr(exc, i)[0], i]
                        for i in dir(exc) if '_wssData_' in i and 'epth' in i
                    ]
                    exc.restart()
                    # 重连
                    if np.array([(current - i[0]) >= timeout1 for i in dataList]).any():
                        exc.restart()  # 重连
                        print(f"{exc} {dataList} {current} 延迟 {timeout1}ms 触发重连")
                    # 删除latency数据
                    if np.array([(current - i[0]) >= timeout2 for i in dataList]).any():
                        [delattr(exc, i) for i in dir(exc) if '_wssData_' in i]
                        print(f"{exc} 延迟 {timeout2}ms 触发数据删除")
            except:
                print('_dataDrop Function Error!', traceback.format_exc())

    def getTick(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_tick")[-1]
        return tf.normalizeTick(data=data)

    def getDepth(self, **kwargs):  # 火币需要整合颗粒度
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        tp = kwargs.get('type', 'step0')
        if 'huobi' in exc:
            data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_depth_{tp}")[-1]
        else:
            data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_depth")[-1]
        return tf.normalizeDepth(data=data)

    def getIncreDepth(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_increDepth")[-1]
        return tf.normalizeDepth(data=data)

    def getKline(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        period = kwargs.get('period', '1m')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_kline_{period}")[-1]
        return tf.normalizeKline(data=data)

    def getClearPrice(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_clearPrice")[-1]
        return tf.normalizeClearPrice(data=data)

    def getFundingRate(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_fundingRate")[-1]
        return tf.normalizeFundingRate(data=data)

    def getbidAsk(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_bidAsk")[-1]
        return tf.normalizeBidAsk(data=data)


if __name__ == '__main__':
    task = SDK('9800001')
