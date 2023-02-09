import sys
sys.path.append('../..')
from wbfAPI.base import _zmq as zmq
import time


class SDK():

    def __init__(self, port=1234):
        self.zmq = zmq.ZMQ('REQ', port)

    def getTick(self, **kwargs):
        return self.zmq.request(['getTick', kwargs])

    def getDepth(self, **kwargs):
        """symbol , exc , type
        
        Args:
            *args: Description
        
        Returns:
            TYPE: Description
        """
        return self.zmq.request(['getDepth', kwargs])

    def getIncreDepth(self, **kwargs):
        return self.zmq.request(['getIncreDepth', kwargs])

    def getKline(self, **kwargs):
        return self.zmq.request(['getKline', kwargs])

    def getClearPrice(self, **kwargs):
        return self.zmq.request(['getClearPrice', kwargs])

    def getFundingRate(self, **kwargs):
        return self.zmq.request(['getFundingRate', kwargs])

    def getbidAsk(self, **kwargs):
        return self.zmq.request(['getbidAsk', kwargs])


if __name__ == '__main__':
    port = 9100000
    task = SDK(port)
    exc = 'huobiSpot'
    
    # print(task.getClearPrice('btc/usdt', 'wbfUsdtSwap'))
    excList = ['wbfUsdtSwap', 'huobiSpot', 'binanceSpot', 'okexSpot', 'poloSpot']
    while 1:
        try:
            for exc in excList:
                print(exc)
                t = time.time()
                data = task.getTick('btc/usdt', exc)
                print((time.time()-t)*1000)
                print(type(data))

                t = time.time()
                data = task.getDepth('btc/usdt', exc)
                print((time.time()-t)*1000)
                print(type(data))

                t = time.time()
                data = task.getIncreDepth('btc/usdt', exc)
                print((time.time()-t)*1000)
                print(type(data))

                t = time.time()
                data = task.getClearPrice('btc/usdt', exc)
                print((time.time()-t)*1000)
                print(data)

                t = time.time()
                data = task.getFundingRate('btc/usdt', exc)
                print((time.time()-t)*1000)
                print(data)
        except:
            pass

        time.sleep(1)

