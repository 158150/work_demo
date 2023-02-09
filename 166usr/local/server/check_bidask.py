import sys
sys.path.append('/usr/local/server')
import time
import requests
import schedule
import Toolbox as tb

# from cointrSpot import DataWss as cointr_datawss
# from coinTRUsdtSwap import DataWss as cointr_swap_datawss
from wbfAPI.exchange.binanceSpot import DataWss as binance_spot_datawss
from wbfAPI.exchange.binanceUsdtSwap import DataWss as binance_swap_datawss
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

cointr_spot_data = {}
cointr_swap_data = {}
cs_spot_data = {}
cs_swap_data = {}
binance_spot_data = {}
binance_swap_data = {}

notice_tr_spot = {}
notice_tr_swap = {}
notice_cs_spot = {}
notice_cs_swap = {}

instruments = {"TR_Spot":{},"TR_Swap":{},"CS_Spot":{},"CS_Swap":{}}
instruments['CS_Spot'] = {'btc/usdt': '2', 'eth/usdt': '2', 'trx/usdt': '6', 'uni/usdt': '4', 'doge/usdt': '6', '1inch/usdt': '6',
     'lrc/usdt': '4', 'grt/usdt': '4', 'mana/usdt': '4', 'rsr/usdt': '6', 'matic/usdt': '5', 'alice/usdt': '4',
     'chz/usdt': '5', 'sand/usdt': '5', 'shib/usdt': '8', 'cake/usdt': '3', 'bat/usdt': '4', 'ape/usdt': '4',
     'crv/usdt': '3', 'town/usdt': '5', 'mtrm/usdt': '5', 'usdc/usdt': '4', 'bico/usdt': '4', 'akita/usdt': '9','sushi/usdt':'4'}
instruments['CS_Swap'] = {'btc/usdt': 1, 'eth/usdt': 2, 'dot/usdt': 3, 'link/usdt': 3, 'doge/usdt': 6, 'xrp/usdt': 4,
      'ada/usdt': 5, 'ltc/usdt': 2, 'etc/usdt': 2, 'fil/usdt': 2, 'axs/usdt': 2, 'eos/usdt': 3, 'matic/usdt': 4,
      'uni/usdt': 3, 'trx/usdt': 5, 'dydx/usdt': 3, 'bch/usdt': 0.05, 'sol/usdt': 0.05, 'atom/usdt': 3, 'celo/usdt': 3,
      'avax/usdt': 2, 'ftm/usdt': 4, 'theta/usdt': 3, 'bnb/usdt': 0.05, 'ksm/usdt': 0.05, 'celr/usdt': 5, 'hbar/usdt': 5,
      'sand/usdt': 4, 'bico/usdt': 3, 'people/usdt': 4, 'raca/usdt': 6, 'icp/usdt': 0.05}

tr_category ={"TR_Spot":{
                '1main': ['btcusdt', 'ethusdt', 'usdttry', 'btctry', 'shibtry', 'ethtry'],
                '2popular': ['xrpusdt', 'etcusdt', 'solusdt', 'adausdt', 'shibusdt', 'chzusdt', 'maticusdt', 'avaxusdt',
                              'dogeusdt', 'atomusdt', 'nearusdt', 'avaxtry', 'chztry', 'apetry', 'spelltry', 'soltry'],
                '3innovative': ['aaveusdt', 'ankrusdt', 'axsusdt', 'crvusdt', 'dotusdt', 'enjusdt', 'eosusdt', 'filusdt',
                                 'ftmusdt', 'gmtusdt', 'grtusdt', 'lrcusdt', 'ltcusdt', 'manausdt', 'sandusdt', 'spellusdt',
                                 'uniusdt', 'adatry', 'dottry', 'enjtry', 'eostry', 'ftmtry', 'galatry', 'gmttry', 'linktry',
                                 'manatry', 'sandtry', 'xrptry', 'xtztry', 'ziltry', 'ankrtry', 'grttry', 'axstry', 'api3try',
                                 'onetry', 'storjtry', 'tlmtry', 'dartry', 'arpatry', 'beltry', 'jasmytry', 'slptry',
                                 'santostry', 'galtry', 'etctry', 'neartry', 'enstry', 'filtry', 'atomtry', 'dogetry', 'lrctry',
                                 'trxtry', 'matictry', 'trxusdt', 'apeusdt', 'galausdt', 'snxusdt', 'linkusdt', 'ensusdt',
                                 'bchusdt', 'galusdt', 'flowusdt', 'balusdt', 'trbusdt', 'darusdt', 'santosusdt', 'arpausdt',
                                 'belusdt', 'jasmyusdt', 'slpusdt']
                        },
             "TR_Swap":{
                '1main': ['btcusdt', 'ethusdt'],
                '2popular': ['etcusdt', 'solusdt', 'adausdt', 'eosusdt', 'maticusdt', 'chzusdt', 'xrpusdt', 'avaxusdt','1000shibusdt'],
                '3innovative': ['aaveusdt', 'apeusdt', 'atomusdt', 'bchusdt', 'crvusdt', 'ensusdt', 'galausdt', 'galusdt',
                                 'gmtusdt', 'linkusdt', 'manausdt', 'nearusdt', 'sandusdt', 'trbusdt', 'ftmusdt', 'snxusdt',
                                 'lrcusdt', 'filusdt', 'dogeusdt', 'dotusdt', 'axsusdt', 'ltcusdt', 'balusdt', 'flowusdt',
                                 'ankrusdt', 'uniusdt', 'grtusdt', 'spellusdt', 'enjusdt']
             }
             }

log1 = tb.Log('check_pankou.log')

def callPhone(info):
    url = (f'http://api.aiops.com/alert/api/event?app=6af5e4bdac8045a89a35ecf77138cbe9&'
           f'eventType=trigger&priority=1&eventId={str(int(time.time()))}&alarmContent={info}')
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


def update_instrment_tr():

    data = requests.get("https://api.cointr.com/v1/spot/public/instruments").json()['data']
    data2 = requests.get("https://api.cointr.com/v1/futures/public/instruments").json()['data']

    for i in data:
        if i['instId'].lower() not in instruments["TR_Spot"].keys():
            instruments["TR_Spot"][i['instId'].lower()] = i['pxPrecision']
        else:
            instruments["TR_Spot"][i['instId'].lower()] = i['pxPrecision']
    for i in data2:
        if i['instId'].lower() not in instruments['TR_Swap'].keys():
            instruments['TR_Swap'][i['instId'].lower()] = i['pxPrecision']
        else:
            instruments['TR_Swap'][i['instId'].lower()] = i['pxPrecision']

def rspFunc_cointrSpot(_s, content):
    try:
        if content and len(content) != 1:
            _t = content[0]
            _bid = content[1][0][0]
            _ask = content[2][0][0]

            cointr_spot_data[_s][0] = _t
            cointr_spot_data[_s][1] = _bid
            cointr_spot_data[_s][2] = _ask

        if content and len(content) == 1:
            _p = content[0][1]

            cointr_spot_data[_s][3] = _p
    except Exception as e:
        print(e)
        print("TR_Spot:",_s,content)

def rspFunc_cointrSwap(_s, content):
    try:
        if len(content) != 1:
            _t = content[0]
            _bid = content[1][0][0]
            _ask = content[2][0][0]

            cointr_swap_data[_s][0] = _t
            cointr_swap_data[_s][1] = _bid
            cointr_swap_data[_s][2] = _ask

        if len(content) == 1:
            _p = content[0][1]

            cointr_swap_data[_s][3] = _p
    except Exception as e:
        print(e)
        print("TR_Swap:",_s,content)

def rspFunc_csSpot(content):
    try:
        if content['T'] == 'trade' and 'data' not in content.keys():
            _s = content['symbol'].lower()[:-4] + "/" + 'usdt'
            _t = content['ts']
            _p = content['price']

            cs_spot_data[_s][0] = _t
            cs_spot_data[_s][3] = float(_p)

        if content['T'] == 'depth' and 'data' not in content.keys():
            _s = content['symbol'].lower()[:-4] + "/" + 'usdt'
            _bid = content['b'][0][0]
            _ask = content['a'][0][0]

            cs_spot_data[_s][1] = float(_bid)
            cs_spot_data[_s][2] = float(_ask)
    except Exception as e:
        print(e)
        print("CS_Spot:",content)


def rspFunc_csSwap(_s, content):
    try:
        if 'future_tick' in content:
            data = content[1]['trades']
            _t = int(data[0] / 1000)
            _p = data[1]

            cs_swap_data[_s][0] = _t
            cs_swap_data[_s][3] = _p

        if 'future_snapshot_depth' in content:
            _bid = float(content[1]['bids'][0][0])
            _ask = float(content[1]['asks'][0][0])

            cs_swap_data[_s][1] = _bid
            cs_swap_data[_s][2] = _ask
    except Exception as e:
        print(e)
        print("CS_Swap 深度数据null:",_s, content)


def rspFunc_binanceSpot(content):
    try:
        for data in content:
            _s = data['s'].lower()
            if _s in binance_spot_data.keys():
                _e = data['E']
                _l = data['L']
                _p = data['c']
                _bid = float(data['b'])
                _ask = float(data['a'])
                if not binance_spot_data[_s]:
                    binance_spot_data[_s] = [_e, _p, _l, 0, _bid, _ask]
                if binance_spot_data[_s][2] != _l:
                    binance_spot_data[_s] = [_e, _p, _l, 1, _bid, _ask]
    except Exception as e:
        print(e)
        print("bin_Spot",content, e)

def rspFunc_binanceSpot2(content):
    try:
        for data in content:
            _s = data['s'].lower()[:-4] + "/" + 'usdt'
            if _s in binance_spot_data.keys():
                _e = data['E']
                _l = data['L']
                _p = data['c']
                _bid = float(data['b'])
                _ask = float(data['a'])
                if not binance_spot_data[_s]:
                    binance_spot_data[_s] = [_e, _p, _l, 0, _bid, _ask]
                if binance_spot_data[_s][2] != _l:
                    binance_spot_data[_s] = [_e, _p, _l, 1, _bid, _ask]
    except Exception as e:
        print(e)
        print("bin_Spot", content, e)

def rspFunc_binanceSwap(content):
    try:
        if not isinstance(content,list):
            if 'e' in content.keys():
                _s = content['s'].lower()
                _bid = float(content['b'])
                _ask = float(content['a'])

                binance_swap_data[_s][4] = _bid
                binance_swap_data[_s][5] = _ask
        else:
            for data in content:
                _s = data['s'].lower()
                if _s in binance_swap_data.keys():
                    _e = data['E']
                    _l = data['L']
                    _p = data['c']

                    if not binance_swap_data[_s]:
                        binance_swap_data[_s][3] = 0
                    if binance_swap_data[_s][2] != _l:
                        binance_swap_data[_s][3] = 1

                    binance_swap_data[_s][0] = _e
                    binance_swap_data[_s][1] = _p
                    binance_swap_data[_s][2] = _l

    except Exception as e:
        print("bin_Swap",content, e)

def run_tr():
    for _c in coins_tr_spot:
        if _c not in binance_spot_data.keys():
            binance_spot_data[_c] = []

        if _c not in cointr_spot_data.keys():
            cointr_spot_data[_c] = [0,0,0,0]

        if _c not in notice_tr_spot.keys():
            notice_tr_spot[_c] = [0,0,0]

        time.sleep(0.3)
        cointr_datawss(symbol=_c, rspFunc=rspFunc_cointrSpot, acctId='2199023255565')

    for _c in coins_tr_swap:
        if _c not in binance_swap_data.keys():
            binance_swap_data[_c] = [0,0,0,0,0,0]

        if _c not in cointr_swap_data.keys():
            cointr_swap_data[_c] = [0,0,0,0]

        if _c not in notice_tr_swap.keys():
            notice_tr_swap[_c] = [0,0,0]

        time.sleep(0.3)
        cointr_swap_datawss(symbol=_c, rspFunc=rspFunc_cointrSwap)
        binance_swap_datawss(_c, topics=['bidAsk'], rspFunc=rspFunc_binanceSwap)

    binance_spot_datawss('', topics='ticks', rspFunc=rspFunc_binanceSpot)
    binance_swap_datawss('', topics=['tickers'], rspFunc=rspFunc_binanceSwap)

    update_instrment_tr()

def run_cs():
    for _c in coins_cs_spot:
        _c = _c[:-4] + "/" + 'usdt'
        if _c not in binance_spot_data.keys():
            binance_spot_data[_c] = []

        if _c not in cs_spot_data.keys():
            cs_spot_data[_c] = [0,0,0,0]

        if _c not in notice_cs_spot.keys():
            notice_cs_spot[_c] = [0,0,0]

        time.sleep(0.3)
        cs_spot_datawss(symbol=_c, rspFunc=rspFunc_csSpot)

    for _c in coins_cs_swap:
        _c = _c[:-4] + "/" + 'usdt'
        if _c not in binance_spot_data.keys():
            binance_spot_data[_c] = []

        if _c not in cs_swap_data.keys():
            cs_swap_data[_c] = [0,0,0,0]

        if _c not in notice_cs_swap.keys():
            notice_cs_swap[_c] = [0,0,0]

        time.sleep(0.3)
        cs_swap_datawss(symbol=_c, rspFunc=rspFunc_csSwap)

    binance_spot_datawss('', rspFunc=rspFunc_binanceSpot2,topics=['ticks'])

def run_check(ex,coin_data,binance_data,notice_data):

    for coin_info in coin_data.items():
        _c = coin_info[0]
        if coin_info[1][0] and coin_info[1][-1] and binance_data[_c] and binance_data[_c][3]:
            # 判断是否盘口贴近
            _price_w = int(instruments[ex][_c])
            if '.' in str(_price_w):
                minpx = _price_w
                a = round(int(coin_info[1][2]*100) - int(coin_info[1][1]*100)/100,2)
            else:
                minpx = round(1 * 10 ** -float(_price_w), _price_w)
                a = round(coin_info[1][2] - coin_info[1][1],_price_w)

            if a == minpx:
                notice_data[_c][0] += 1
                log1.write(f'{ex},{_c}价差相差一个tick,{coin_info[1]}')
            else:
                notice_data[_c][0] = 0
            # 内盘价差和外盘价差的比较
            _p = coin_info[1][2] / coin_info[1][1]
            if 'CS' in ex:
                _p2 = binance_data[_c][5] / binance_data[_c][4] + 0.0006 + 0.05  # 外盘盘口价差+万六+百五
            if 'TR' in ex:
                _p2 = (binance_data[_c][5] / binance_data[_c][4] + 0.0006) * 1.2 #(外盘盘口价差+万六)*20%
            if _p > _p2*5:
                notice_data[_c][1] += 1
                log1.write(f'{ex},{_c}价差大于外盘价差,{coin_info[1]}{binance_data[_c][-2:]},内盘当前价差{_p},外盘当前价差{_p2*5}')
            else:
                notice_data[_c][1] = 0

            # s使用两个价格的最大精度来统一价格精度,比较内盘价格和外盘价格的差距，0.0042,0.0039.0.00189,0.0016,0.00196,
            n_price = float(coin_info[1][3])
            w_price = float(binance_data[_c][1])
            # if '.' not in str(n_price):
            #     _price_w1 = 0
            # else:
            #     _price_w1 = len(str(n_price)) - 1 - str(n_price).index('.')
            # if '.' not in str(w_price):
            #     _price_w2 = 0
            # else:
            #     _price_w2 = len(str(w_price)) - 1 - str(w_price).index('.')
            # _price_w = min(_price_w1,_price_w2)
            # n_price = round(n_price,_price_w)
            # w_price = round(w_price,_price_w)
            px = max(w_price / n_price, n_price / w_price)
            if 'CS' in ex:
                if px > 1.002:
                    notice_data[_c][2] = 1
                    log1.write(
                        f'{ex},{_c}内外盘价差大于千二,内盘价格：{coin_info[1][3]} 币安价格：{binance_data[_c][1]} 价差{px}')
            if 'TR' in ex:
                if _c in  tr_category[ex]['1main']:
                    if px > 1.002:
                        notice_data[_c][2] = 1
                        log1.write(f'{ex},{_c}内外盘价差大于千二,内盘价格：{coin_info[1][3]} 币安价格：{binance_data[_c][1]} 价差{px}')
                if _c in  tr_category[ex]['2popular']:
                    if px > 1.002:
                        notice_data[_c][2] = 1
                        log1.write(f'{ex},{_c}内外盘价差大于千二,内盘价格：{coin_info[1][3]} 币安价格：{binance_data[_c][1]} 价差{px}')
                if _c in  tr_category[ex]['3innovative']:
                    if px > 1.0035:
                        notice_data[_c][2] = 1
                        log1.write(f'{ex},{_c}内外盘价差大于千四,内盘价格：{coin_info[1][3]} 币安价格：{binance_data[_c][1]} 价差{px}')

        else:
            print(f'{ex},{_c} data not update,{coin_info[1]},{binance_data[_c]}')

def check_notice(ex,notice_data):
    # 每分钟检测一次，5次检测结果一致的话，判断电话报警；若一致则继续等待。

    for i in notice_data.keys():
        a = notice_data[i][0]
        b = notice_data[i][1]
        c = notice_data[i][2]

        if a >= 5:
            sendmail(ex + '连续5次盘口贴上', i)
            log1.write(f'已发邮件{ex} {i} 连续5次盘口贴上')
            notice_data[i][0] = 0
        if b >= 5:
            sendmail(ex + '连续5次盘口过大', i)
            log1.write(f'已发邮件{ex} {i} 连续5次盘口大于外盘盘口')
            notice_data[i][1] = 0
        if c >= 5:
            # sendmail(ex + '内外盘价差大于千二', i)
            log1.write(f'已打电话{ex} {i} 内外盘价差大于千二')
            notice_data[i][2] = 0


def check():

    # check_notice('TR_Spot', notice_tr_spot)
    # check_notice('TR_Swap', notice_tr_swap)
    check_notice('CS_Spot', notice_cs_spot)
    check_notice('CS_Swap', notice_cs_swap)

if __name__ == '__main__':
    # run_tr()
    #
    # schedule.every(1).minutes.do(run_check,'TR_Spot',cointr_spot_data,binance_spot_data,notice_tr_spot)
    # schedule.every(1).minutes.do(run_check,'TR_Swap',cointr_swap_data,binance_swap_data,notice_tr_swap)
    # schedule.every(1).minutes.do(check)
    # schedule.every(1).hour.do(update_instrment_tr)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

    run_cs()

    schedule.every(1).minutes.do(run_check, 'CS_Spot', cs_spot_data, binance_spot_data, notice_cs_spot)
    schedule.every(1).minutes.do(run_check, 'CS_Swap', cs_swap_data, binance_spot_data, notice_cs_swap)
    schedule.every(1).minutes.do(check)
    while True:
        schedule.run_pending()
        time.sleep(1)

