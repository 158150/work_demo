from wbfAPI.data import DataPushServer as dps
from wbfAPI.config import _indexPrice
from wbfAPI.base import transform as tf
import numpy as np
import time
import os


class SDK(dps.SDK):

    def getClearPrice(self, **kwargs):
        symbol = kwargs.get('symbol')
        exc = kwargs.get('exc')
        timestamp = int(time.time()*1000)
        if 'wbf' not in exc:
            data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_clearPrice")[-1]
            return tf.normalizeClearPrice(data=data)
        else:
            excList, weightList, bias = _indexPrice.indexPriceConfig[symbol]
            indx = np.full(len(excList), np.nan)
            for i, exchange in enumerate(excList):
                try:
                    indx[i] = getattr(getattr(self, f"{exchange}_{symbol}_wss"), f'_wssData_{symbol}_tick')[-1][-1][1]
                except:
                    pass
            condition = abs(indx/np.nanmedian(indx)-1) < bias
            avl = np.nansum(condition)
            if avl >= 3:
                indx[~condition] = np.nan
                weightArr = np.array(weightList)
                weightArr[~condition] = np.nan
                weightArr = weightArr / np.nansum(weightArr)
                data = [timestamp, np.nansum(indx*weightArr), np.nan, timestamp]
            else:
                data = getattr(getattr(self, f"{exc}_{symbol}_wss"), f"_wssData_{symbol}_clearPrice")[-1]
                weightArr = np.zeros(len(indx))
            extra = {'compo': indx, 'weight': weightArr, 'compoName': excList}
            return tf.normalizeClearPrice(data=data, extra=extra)


port = os.path.basename(__file__).split('.')[0].split('DataPushServer')[-1]
task = SDK(port=port)
