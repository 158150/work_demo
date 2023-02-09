import sys
import traceback

sys.path.append('/usr/local/server')
import time
import requests
import schedule
import Toolbox as tb

#from wbfAPI.exchange.cointrSpot import AccountRest as trspot_accountrest
#from wbfAPI.exchange.coinTRUsdtSwap import AccountRest as trswap_accountrest

from wbfAPI.exchange.coinStoreSpot import DataWss as cs_spot_datawss
from wbfAPI.exchange.coinStoreUsdtSwap import DataWss as cs_swap_datawss


coins_tr_spot = ['xtztry', 'ziltry', 'ankrtry', 'grttry', 'axstry',
                 'api3try', 'onetry', 'storjtry', 'tlmtry', 'dartry',
                 'arpatry', 'beltry', 'jasmytry', 'slptry', 'santostry',
                 'dottry', 'galtry', 'etctry', 'neartry', 'enstry',
                 'adatry', 'filtry', 'atomtry', 'dogetry', 'xrptry',
                 'enjtry', 'gmttry', 'lrctry', 'linktry', 'spelltry',
                 'trxtry', 'manatry', 'matictry', 'eostry', 'sandtry',
                 'avaxtry', 'ftmtry', 'shibtry', 'apetry', 'galatry',
                 'chztry', 'soltry', 'usdttry', 'btctry', 'ethtry',
                 'btcusdt', 'ethusdt', 'trxusdt', 'apeusdt', 'galausdt',
                 'chzusdt', 'manausdt', 'solusdt', 'maticusdt', 'ftmusdt',
                 'sandusdt', 'aaveusdt', 'snxusdt', 'gmtusdt', 'lrcusdt',
                 'linkusdt', 'avaxusdt', 'adausdt', 'filusdt', 'atomusdt',
                 'dogeusdt', 'etcusdt', 'xrpusdt', 'dotusdt', 'nearusdt',
                 'ensusdt', 'eosusdt', 'ankrusdt', 'crvusdt', 'uniusdt',
                 'axsusdt', 'ltcusdt', 'grtusdt', 'bchusdt', 'galusdt',
                 'enjusdt','spellusdt','shibusdt','flowusdt','balusdt',
                 'trbusdt','darusdt', 'santosusdt', 'arpausdt','belusdt',
                 'jasmyusdt', 'slpusdt'
                 ]

coins_tr_swap = ['btcusdt', 'ethusdt', 'apeusdt', 'chzusdt', 'galausdt',
                 'manausdt', '1000shibusdt', 'solusdt', 'maticusdt', 'ftmusdt',
                 'sandusdt', 'aaveusdt', 'snxusdt', 'gmtusdt', 'lrcusdt',
                 'linkusdt', 'avaxusdt', 'adausdt', 'filusdt', 'atomusdt',
                 'dogeusdt', 'etcusdt', 'xrpusdt', 'dotusdt', 'nearusdt',
                 'ensusdt', 'eosusdt', 'axsusdt', 'crvusdt', 'ltcusdt',
                 'bchusdt', 'galusdt', 'trbusdt', 'balusdt', 'flowusdt',
                 'ankrusdt', 'uniusdt', 'grtusdt', 'spellusdt', 'enjusdt'
                 ]

coins_cs_spot = ['btcusdt', 'ethusdt', 'trxusdt', 'uniusdt', 'sushiusdt',
                 'dogeusdt', '1inchusdt', 'lrcusdt', 'grtusdt', 'manausdt',
                 'rsrusdt', 'maticusdt',   'aliceusdt',
                 'chzusdt', 'sandusdt', 'shibusdt',
                 'cakeusdt', 'batusdt', 'apeusdt', 'crvusdt',# binanceawap
                 # 'townusdt', 'mtrmusdt', 'uppusdt'
                 # 'usdcusdt', 'bicousdt', # huobi
                 # 'dogekingusdt', 'briseusdt'  #mxc
                 # 'akitausdt',  # okx
                 ]

coins_cs_swap = ['btcusdt', 'ethusdt', 'dotusdt', 'linkusdt', 'dogeusdt',
                 'xrpusdt', 'icpusdt', 'adausdt', 'ltcusdt', 'etcusdt',
                 'filusdt', 'axsusdt', 'eosusdt', 'maticusdt', 'uniusdt',
                 'trxusdt', 'dydxusdt', 'bchusdt', 'solusdt',
                 'atomusdt', 'celousdt', 'avaxusdt', 'ftmusdt', 'thetausdt',
                 'bnbusdt', 'ksmusdt', 'celrusdt', 'hbarusdt', 'sandusdt',
                 'bicousdt','peopleusdt',
                 # 'racausdt', # okx
                 ]

coins_trspot_depth = {'btcusdt': ['0.0002', '0.0008', '0.001', '0.0025', '0.004', '0.0055', '0.01', '0.02'],
                     'ethusdt': ['0.0002', '0.0008', '0.001', '0.0025', '0.004', '0.0055', '0.01', '0.02'],
                     'xrpusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'etcusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'solusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'adausdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'shibusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'chzusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'maticusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'avaxusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'dogeusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'atomusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'nearusdt': ['0.001', '0.0015', '0.002', '0.004', '0.007', '0.011', '0.02', ''],
                     'aaveusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'ankrusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'axsusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'crvusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'dotusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'enjusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'eosusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'filusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'ftmusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'gmtusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'grtusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'lrcusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'ltcusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'manausdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'sandusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'spellusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'uniusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'usdttry': ['0.0005', '0.0015', '0.002', '0.0035', '0.007', '0.015', '0.02', ''],
                     'btctry': ['0.0005', '0.0015', '0.002', '0.0035', '0.007', '0.015', '0.02', ''],
                     'shibtry': ['0.0005', '0.0015', '0.002', '0.0035', '0.007', '0.015', '0.02', ''],
                     'ethtry': ['0.0005', '0.0015', '0.002', '0.0035', '0.007', '0.015', '0.02', ''],
                     'avaxtry': ['0.001', '0.0015', '0.002', '0.005', '0.01', '0.015', '0.02', ''],
                     'chztry': ['0.001', '0.0015', '0.002', '0.005', '0.01', '0.015', '0.02', ''],
                     'apetry': ['0.001', '0.0015', '0.002', '0.005', '0.01', '0.015', '0.02', ''],
                     'spelltry': ['0.001', '0.0015', '0.002', '0.005', '0.01', '0.015', '0.02', ''],
                     'soltry': ['0.001', '0.0015', '0.002', '0.005', '0.01', '0.015', '0.02', ''],
                     'adatry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'dottry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'enjtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'eostry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'ftmtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'galatry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'gmttry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'linktry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'manatry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'sandtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'xrptry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'xtztry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'ziltry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'ankrtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'grttry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'axstry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'api3try': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'onetry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'storjtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'tlmtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'dartry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'arpatry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'beltry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'jasmytry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'slptry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'santostry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'galtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'etctry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'neartry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'enstry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'filtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'atomtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'dogetry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'lrctry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'trxtry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'matictry': ['0.001', '0.0025', '0.004', '0.01', '0.02', '0.028', '0.035', ''],
                     'trxusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'apeusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'galausdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'snxusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'linkusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'ensusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'bchusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'galusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'flowusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'balusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'trbusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'darusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'santosusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'arpausdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'belusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'jasmyusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', ''],
                     'slpusdt': ['0.001', '0.002', '0.003', '0.006', '0.012', '0.02', '0.03', '']
                      }

coins_trswap_depth = {'btcusdt': ['0.0002', '0.0004', '0.0006', '0.001', '0.002', '0.004', '0.008', '0.015', '0.02', '0.025'],
                     'ethusdt': ['0.0002', '0.0004', '0.0006', '0.001', '0.002', '0.004', '0.008', '0.015', '0.02', '0.025'],
                     'etcusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'solusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'adausdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'eosusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'maticusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'chzusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'xrpusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'avaxusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     '1000shibusdt': ['0.0005', '0.001', '0.0012', '0.002', '0.004', '0.008', '0.016', '0.025', '0.035', '0.045'],
                     'aaveusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'apeusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'atomusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'bchusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'crvusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'ensusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'galausdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'galusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'gmtusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'linkusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'manausdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'nearusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'sandusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'trbusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'ftmusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'snxusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'lrcusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'filusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'dogeusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'dotusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'axsusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'ltcusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'balusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'flowusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'ankrusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'uniusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'grtusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'spellusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05'],
                     'enjusdt': ['0.001', '0.0015', '0.002', '0.003', '0.006', '0.01', '0.02', '0.03', '0.04', '0.05']}

cointr_spot_data = {}
cointr_swap_data = {}
cs_spot_data = {}
cs_swap_data = {}

notice_tr_spot = {}
notice_tr_swap = {}
notice_cs_spot = {}
notice_cs_swap = {}

log1 = tb.Log('check_depth.log')

def callPhone(info):
    url = (f'http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&'
           f'eventType=trigger&priority=2&eventId={str(int(time.time()))}&alarmContent={info}')
    info = requests.post(url=url)
    print(f"拨电话:{info.text}")

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_CONFIG = [
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
]


def sendmail(_title, _text):
    for config in EMAIL_CONFIG:
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
            print('sendemail successful!', smtp_server, sender_mail)
            break
        except Exception as e:
            print('sendemail failed:', e)


def rspFunc_csSpot(content):
    try:
        if content['T'] == 'depth' and 'data' not in content.keys():
            _s = content['symbol'].lower()[:-4] + "/" + 'usdt'
            bid = content['b']
            ask = content['a']

            """
            cs_spot_data > {
                'btc/usdt': [
                    # bid
                    [  # Bids to be updated
                        [
                            "0.0024",  # Price level to be updated
                            "10"  # Quantity
                        ]
                    ],
            
                    # ask
                    [  # Asks to be updated
                        [
                            "0.0026",  # Price level to be updated
                            "100"  # Quantity
                        ]
                    ]
                ]
            }
            """
            cs_spot_data[_s] = [bid,ask]
    except Exception as e:
        print(e)
        print("CS_Spot:",content)


def rspFunc_csSwap(_s, content):
    try:
        if 'future_snapshot_depth' in content:
            bid = content[1]['bids']
            ask = content[1]['asks']

            cs_swap_data[_s] = [bid,ask]
    except Exception as e:
        print(e)
        print("CS_Swap:",_s, content)

def run_start():
    for _c in coins_tr_spot:
        if _c not in cointr_spot_data.keys():
            cointr_spot_data[_c] = []

        if _c not in notice_tr_spot.keys():
            notice_tr_spot[_c] = [0,0,0]

    for _c in coins_tr_swap:
        if _c not in cointr_swap_data.keys():
            cointr_swap_data[_c] = []

        if _c not in notice_tr_swap.keys():
            notice_tr_swap[_c] = [0,0,0]

    run_tr()

def run_tr():
    try:
        task_spot = trspot_accountrest('990ef7b0efa40ed74d9c624031e29a0c', '167d55f5ab13610f5c267d61b2acc334')
        task_swap = trswap_accountrest('990ef7b0efa40ed74d9c624031e29a0c', '167d55f5ab13610f5c267d61b2acc334', '')
        for _c in coins_tr_spot:
            data = task_spot.getDepth(_c, 100)
            bid = data['data'][1]
            ask = data['data'][2]

            cointr_spot_data[_c] = [bid,ask]
            time.sleep(0.2)
        for _c in coins_tr_swap:
            data = task_swap.getDepth(_c, 100)
            bid = data['data'][1]
            ask = data['data'][2]

            cointr_swap_data[_c] = [bid,ask]
            time.sleep(0.2)
    except Exception as e:
        traceback.format_exc()
        print(e)

def run_cs():
    for _c in coins_cs_spot:
        _c = _c[:-4] + "/" + 'usdt'
        if _c not in cs_spot_data.keys():
            cs_spot_data[_c] = []

        if _c not in notice_cs_spot.keys():
            notice_cs_spot[_c] = [0,0,0]

        time.sleep(0.3)
        cs_spot_datawss(symbol=_c, rspFunc=rspFunc_csSpot)

    for _c in coins_cs_swap:
        _c = _c[:-4] + "/" + 'usdt'
        if _c not in cs_swap_data.keys():
            cs_swap_data[_c] = []

        if _c not in notice_cs_swap.keys():
            notice_cs_swap[_c] = [0,0,0]

        time.sleep(0.3)
        cs_swap_datawss(symbol=_c, rspFunc=rspFunc_csSwap)

def deal_cal_bids(num,_c,depth_data,e):

    total_num = 0
    _d1 = float(depth_data[0][0])
    for  data in depth_data:
        if float(data[0]) >= _d1 * (1-e):
            total_num += float(data[0]) * float(data[1])
        else:
            break
    if total_num >= num:
        return True,0
    else:
        return False,round(num - total_num,2)

def deal_cal_asks(num,_c,depth_data,e):

    total_num = 0
    _d1 = float(depth_data[0][0])
    for data in depth_data:
        if float(data[0]) <= _d1 * (1+e):
            total_num += float(data[0]) * float(data[1])
        else:
            break
    if total_num >= num:
        return True, 0
    else:
        return False,round(num - total_num,2)

def run_cal(ex,_c,bids,asks):
    trspot_anum = [100, 500, 1000, 2000, 5000, 10000, 20000, 40000]
    trswap_anum = [100, 500, 1000, 2000, 5000, 10000, 20000, 30000, 40000, 50000]

    if ex == 'TR_Spot':
        depth_aim = coins_trspot_depth
        depth_anum = trspot_anum
    if ex == 'TR_Swap':
        depth_aim = coins_trswap_depth
        depth_anum = trswap_anum

    for k,num in enumerate(depth_anum):
        if _c in depth_aim.keys():
            e = depth_aim[_c][k]
            if e:
                is_full_b,_nb = deal_cal_bids(num, _c, bids, float(e))
                is_full_a,_na = deal_cal_asks(num, _c, asks, float(e))
                if not is_full_b:
                    log1.write(f'{ex} {_c} 买盘{num}档深度不足,差{_nb}U')
                if not is_full_a:
                    log1.write(f'{ex} {_c} 卖盘{num}档深度不足,差{_na}U')
        # else:
        #     print(ex,_c,'深度数据null')

def run_check(ex,coin_data,notice_data):

    try:
        """
        cs_spot_data > {
            'btc/usdt': [
                # bid
                [  # Bids to be updated
                    [
                        "0.0024",  # Price level to be updated
                        "10"  # Quantity
                    ]
                ],

                # ask
                [  # Asks to be updated
                    [
                        "0.0026",  # Price level to be updated
                        "100"  # Quantity
                    ]
                ]
            ]
        }
        """
        """
        coin_info > (btc/usdt,[[[0.0024,10],[0.0024,10]],[[[0.0026,10],[0.0026,10]]]])
        """
        for coin_info in coin_data.items():
            _c = coin_info[0] # symbol
            if coin_info[1][0] and coin_info[1][1]:
                notice_data[_c][0] = 0
                # 前两档价差不能超过万五
                b1 = abs(float(coin_info[1][0][0][0]) / float(coin_info[1][0][1][0]) - 1)
                a1 = abs(float(coin_info[1][1][1][0]) / float(coin_info[1][1][0][0]) - 1)
                if b1 > 0.0005 or a1 > 0.0005:
                    notice_data[_c][1] += 1
                if b1 <= 0.0005 and a1 <= 0.0005:
                    notice_data[_c][1] = 0
                # TR单边连续5次不能少于40档,CS 20
                l1 = len(coin_info[1][0])
                l2 = len(coin_info[1][1])
                if ex == 'CS_Spot':
                    if l1 < 20 or l2 < 20:
                        notice_data[_c][2] += 1
                    if l1 >= 20 and l2 >= 20:
                        notice_data[_c][2] = 0
                if ex == 'CS_Swap':
                    if l1 < 5 or l2 < 5:
                        notice_data[_c][2] += 1
                    if l1 >= 5 and l2 >= 5:
                        notice_data[_c][2] = 0
                if ex == 'TR_Spot':
                    if l1 < 20 or l2 < 20:
                        notice_data[_c][2] += 1
                    if l1 >= 20 and l2 >= 20:
                        notice_data[_c][2] = 0
                if ex == 'TR_Swap':
                    if l1 < 20 or l2 < 20:
                        notice_data[_c][2] += 1
                    if l1 >= 20 and l2 >= 20:
                        notice_data[_c][2] = 0
                # 价格范围内深度要求,
                    run_cal(ex,_c,coin_info[1][0],coin_info[1][1])
            else:
                notice_data[_c][0] += 1
                log1.write(f'{ex},{_c}深度数据null,{coin_info[1]}')


            # TODO 土耳其现货单边委托金额不少于2Wusdt，合约单边委托金额不少于5Wusdt，邮件报警
    except Exception as e:
        print(e,ex,_c,coin_info)

def check_notice(ex,notice_data):
    for i in notice_data.keys():
        try:
            a = notice_data[i][0]
            b = notice_data[i][1]
            c = notice_data[i][2]

            if a >= 2:
                callPhone(f'{ex} {i} 连续2次深度数据为空')
                log1.write(f'已发邮件{ex} {i} 连续5次深度数据为空')
                notice_data[i][0] = 0
            if b >= 5:
                # sendmail()
                log1.write(f'已发邮件{ex} {i} 连续5次前两档价位超过万五')
                notice_data[i][1] = 0
            if c >=5 :
                if ex == 'CS_Spot':
                    sendmail(f'{ex} {i} 连续5次单边少于20档',f'{ex} {i} 连续5次单边少于20档')
                    log1.write(f'已打电话{ex} {i} 连续5次单边少于20档')
                if ex == 'CS_Swap':
                    sendmail(f'{ex} {i} 连续5次单边少于5档',f'{ex} {i} 连续5次单边少于5档')
                    log1.write(f'已打电话{ex} {i} 连续5次单边少于5档')
                if ex == 'TR_Spot':
                    sendmail(f'{ex} {i} 连续5次单边少于40档',f'{ex} {i} 连续5次单边少于40档')
                    log1.write(f'已打电话{ex} {i} 连续5次单边少于40档')
                if ex == 'TR_Swap':
                    sendmail(f'{ex} {i} 连续5次单边少于36档',f'{ex} {i} 连续5次单边少于36档')
                    log1.write(f'已打电话{ex} {i} 连续5次单边少于36档')
                notice_data[i][2] = 0
        except Exception as e:
            print(e)
            continue


def check():

    # check_notice('TR_Spot', notice_tr_spot)
    # check_notice('TR_Swap', notice_tr_swap)
    check_notice('CS_Spot', notice_cs_spot)
    check_notice('CS_Swap', notice_cs_swap)

if __name__ == '__main__':
    # run_start()
    # schedule.every(1).minutes.do(run_check,'TR_Spot',cointr_spot_data,notice_tr_spot)
    # schedule.every(1).minutes.do(run_check,'TR_Swap',cointr_swap_data,notice_tr_swap)
    # schedule.every(1).minutes.do(check)
    # schedule.every(1).minutes.do(run_tr)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

    run_cs()
    schedule.every(1).minutes.do(run_check, 'CS_Spot', cs_spot_data, notice_cs_spot)
    schedule.every(1).minutes.do(run_check, 'CS_Swap', cs_swap_data, notice_cs_swap)
    schedule.every(1).minutes.do(check)
    while True:
        schedule.run_pending()
        time.sleep(1)
