import pandas as pd
import Toolbox as tb
import numpy as np
import os
import requests
import json
import psutil
import time
import platform
# print(get_depthlist())

def mkdir(path):
    # 引入模块

    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    if(platform.system()=='Windows'):
        path = path.rstrip("\\")
        print('Windows系统')
    elif(platform.system()=='Linux'):
        path = path.rstrip("/")
        print('Linux系统')
    else:
        print('其他系统','请检查配置')
        raise '主动抛出的异常'

    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)

        Log(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        Log(path + ' 目录已存在')
        return False

def Log(*args):
    print(args)

def init_csv(mypath):

    # path = path.strip()
    # 去除尾部 \ 符号
    if(platform.system()=='Windows'):
        mypath = mypath + "\\"
        print('Windows系统')
    elif(platform.system()=='Linux'):
        mypath = mypath + "/"
        print('Linux系统')
    else:
        print('其他系统','请检查配置')
        raise '主动抛出的异常'
    mkpath = mypath

    try:  # 初始化orderList
        filename = mkpath + 'zhengOrderList' + '.csv'
        print(filename)
        if os.path.exists(filename):
            try:
                filename = open(filename, encoding='UTF-8')
                zhengOrderList = pd.read_csv(filename, sep=',', header=0, index_col=0)
                Log('已成交正向单数', zhengOrderList.iloc[:, 0].size)
            except Exception as e:
                filename = mkpath + 'zhengOrderList' + "_copy" + '.csv'
                filename = open(filename, encoding='UTF-8')
                zhengOrderList = pd.read_csv(filename, sep=',', header=0, index_col=0)
                Log('已成交正向单数', zhengOrderList.iloc[:, 0].size)
        else:
            zhengOrderList = pd.DataFrame(
                columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "time_wbf",
                         "time_binance", "precent_profit", "fee_wbf", "fee_binance"])
            zhengOrderList.to_csv(filename, sep=',', header=True, index=True)  # index=False,
            Log('第一次运行机器人，没有本地保存的订单信息')
    except Exception as e:
        print("error")
        filename = mkpath + 'zhengOrderList' + '.csv'
        print(filename)
        zhengOrderList = pd.DataFrame(
            columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "time_wbf",
                     "time_binance", "precent_profit", "fee_wbf", "fee_binance"])
        zhengOrderList.to_csv(filename, sep=',', header=True, index=True)  # index=False,
        Log('第一次运行机器人，没有本地保存的订单信息')


    if 1:  # 对挂单处理
        filename = mkpath + 'zhengPendingList' + '.csv'
        if os.path.exists(filename):
            try:
                filename = open(filename, encoding='UTF-8')
                zhengPendingList = pd.read_csv(filename, sep=',', header=0, index_col=0)
                Log('导入挂单数', zhengPendingList.iloc[:, 0].size)
            except Exception as e:
                filename = mkpath + 'zhengPendingList' + "_copy" + '.csv'
                filename = open(filename, encoding='UTF-8')
                zhengPendingList = pd.read_csv(filename, sep=',', header=0, index_col=0)
                Log('导入挂单数', zhengPendingList.iloc[:, 0].size)
        else:
            zhengPendingList = pd.DataFrame(
                columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "qty_binance",
                         "match_price_binance", "match_qty_binance", "time_wbf", "time_binance", "precent_profit",
                         "match_type","fee"])  # 挂单列表
            # {"time": time.time(), 'id_wbf': match['orderId'], "id_binance": 0, "price_wbf": match['matchPrice'],"price_binance": 0, "qty_wbf": match['matchQty'], "match_qty_binance": 0, "time_wbf": match['matchTime'],
            #  "time_binance": 0, "precent_profit": 0}
            zhengPendingList.to_csv(filename, sep=',', header=True, index=True)  # index=False,
            Log('没有本地保存的挂单信息')


    try:  # 对挂单处理
        # self.wbf_wss_execId_list.append([match['matchTime'],match['execId']])
        filename = mkpath + 'wbf_wss_execId_list' + '.csv'
        if os.path.exists(filename):
            filename = open(filename, encoding='UTF-8')
            wbf_wss_execId_list = pd.read_csv(filename, sep=',', header=0, index_col=0)
            Log('历史wss订单', wbf_wss_execId_list.iloc[:, 0].size)
        else:
            wbf_wss_execId_list = pd.DataFrame(
                columns=['matchTime', 'execId'])  # 挂单列表
            wbf_wss_execId_list.to_csv(filename, sep=',', header=True, index=True)  # index=False,
            Log('没有本地保存的历史wss订单信息')
    except Exception as e:
        print("error")
        filename = mkpath + 'wbf_wss_execId_list' + '.csv'
        wbf_wss_execId_list = pd.DataFrame(
            columns=['matchTime', 'execId'])  # 挂单列表
        wbf_wss_execId_list.to_csv(filename, sep=',', header=True, index=True)  # index=False,
        Log('没有本地保存的历史wss订单信息')


    try:  # 对挂单处理
        filename = mkpath + 'min_zhengPendingList' + '.csv'
        if os.path.exists(filename):
            filename = open(filename, encoding='UTF-8')
            min_zhengPendingList = pd.read_csv(filename, sep=',', header=0, index_col=0)
            Log('导入min挂单数', min_zhengPendingList.iloc[:, 0].size)
        else:
            min_zhengPendingList = pd.DataFrame(
                columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "qty_binance",
                         "match_price_binance", "match_qty_binance", "time_wbf", "time_binance", "precent_profit",
                         "match_type","fee"])  # 挂单列表
            min_zhengPendingList.to_csv(filename, sep=',', header=True, index=True)  # index=False,
            Log('没有本地保存的min挂单信息')
    except Exception as e:
        print("error")
        filename = mkpath + 'min_zhengPendingList' + '.csv'
        min_zhengPendingList = pd.DataFrame(
            columns=["time", 'id_wbf', "id_binance", "price_wbf", "price_binance", "qty_wbf", "qty_binance",
                     "match_price_binance", "match_qty_binance", "time_wbf", "time_binance", "precent_profit",
                     "match_type", "fee"])  # 挂单列表
        min_zhengPendingList.to_csv(filename, sep=',', header=True, index=True)  # index=False,
        Log('没有本地保存的min挂单信息')

    return zhengOrderList,zhengPendingList,wbf_wss_execId_list,min_zhengPendingList

# https://oapi.dingtalk.com/robot/send?access_token=ff9007a930eee45c6280202cdba347ba4c39be32c5e9038fb4e4833a6f4a6b60
def warning_ram_1(content, contractSymbol='btc/usdt'):
    '''dingtask alert

    Args:
        content (str): alert content
        contractSymbol (str, optional): contract involved
    '''
    # return
    # self._log('_warning',content,'')

    # pass
    url = 'https://oapi.dingtalk.com/robot/send?access_token=6770cb9970fece7fdc8327f75194d8b357cf2dff0fb249b3e1bfe169c8e2c68c'
    headers = {"Content-Type": "application/json ;charset=utf-8 "}
    content = f"==={tb.timestamp()}  资金报警binanceSwap {contractSymbol}===\n{content}\n"
    print(content)
    msg = {'msgtype': 'text',
            'text': {'content': content}}
    requests.post(url, headers=headers, data=json.dumps(msg))

def warning_ram(symbol):
    pid = os.getpid()
    p = psutil.Process(pid)
    info = p.memory_full_info()
    info = int(info.rss/1024/1024)
    if info > 10:
        print(info)
        warning_ram_1("内存占用: "+str(info)+" M",symbol)
    return info




def percentage_pq(myDepth,percentlist):  #获取价量百分比
    global price
    buy_price = 0
    guadanshu = 0
    pankouDepth_min_bids = len(myDepth[1])
    pankouDepth_min_asks = len(myDepth[2])

    now_price = (myDepth[1][0][0] + myDepth[2][0][0])/2
    price = now_price
    pankoucha = (myDepth[2][0][0]/myDepth[1][0][0]-1)*100

    #print(myDepth[2][0][0],myDepth[1][0][0])
    bid_guadanshu_list = []
    ask_guadanshu_list = []
    for mypercent in percentlist:           # 获取盘口
        bid_guadanshu = 0
        for dangwei in range(0, pankouDepth_min_bids):  # 5 len(current_depth.Bids)
            bid_guadanshu = bid_guadanshu + myDepth[1][dangwei][1]
            if myDepth[1][dangwei][0] <= now_price*(1-mypercent/100):          #and dangwei==pankouDepth-1
                bid_guadanshu_list.append(bid_guadanshu)
                break
            if dangwei == pankouDepth_min_bids-1:
                bid_guadanshu_list.append(bid_guadanshu)


    for mypercent in percentlist:           # 获取盘口
        ask_guadanshu = 0
        for dangwei in range(0, pankouDepth_min_asks):  # 5 len(current_depth.Bids)
            ask_guadanshu = ask_guadanshu + myDepth[2][dangwei][1]
            if myDepth[2][dangwei][0] >= now_price*(1+mypercent/100):          #and dangwei==pankouDepth-1
                ask_guadanshu_list.append(ask_guadanshu)
                break
            if dangwei == pankouDepth_min_asks-1:
                ask_guadanshu_list.append(ask_guadanshu)
    new = []
    for i in range(len(bid_guadanshu_list)):
        new.append(bid_guadanshu_list[i]+ask_guadanshu_list[i])

    return [myDepth[0],new,pankoucha,myDepth[3]]


def str_to_num(depth):          # 转化为数字
    my_depth = []
    for i in depth:
        i[0],i[1] = float(i[0]),float(i[1])
        my_depth.append([i[0],i[1]])
    return my_depth

def data_a(data,exc):
    new = [exc]
    try:
        new.append(str_to_num(data["b"]))
    except:
        new.append(str_to_num(data["bids"]))
    try:
        new.append(str_to_num(data["a"]))
    except:
        new.append(str_to_num(data["asks"]))
    new.append(exc)
    return new




def binance_list(data,minUnit,percent,qty_unit):   #

    spot_bid_price = np.array(data[1])[:, 0].astype('float').tolist()
    spot_bid_vol = np.array(data[1])[:, 1].astype('float').tolist()

    spot_ask_price = np.array(data[2])[:, 0].astype('float').tolist()
    spot_ask_vol = np.array(data[2])[:, 1].astype('float').tolist()
    temp_bid_list = []
    temp_ask_list = []
    for i in spot_bid_price:  # 买盘价格精度向下取整
        temp_bid_list.append(tb.round(i, minUnit, 'down'))
    spot_bid_price = temp_bid_list
    for i in spot_ask_price:  # 卖盘价格精度向上取整
        temp_ask_list.append(tb.round(i, minUnit, 'up'))
    spot_ask_price = temp_ask_list
    df = pd.DataFrame({'price': spot_bid_price, 'vol': spot_bid_vol})  # list转dataframe
    spot_bid_price = df['price'].drop_duplicates().values.tolist()  # 价格去重
    # print(spot_bid_price[0:10])
    spot_bid_vol = df.groupby('price')['vol'].sum().tolist()[::-1]  # 挂单量按价格分组后聚合
    # print(spot_bid_vol[0:10])
    spot_bid_vol = list(map(lambda x: int(x*percent/100/qty_unit),spot_bid_vol)) # 标准化处理
    # print(spot_bid_vol[0:10])
    df = pd.DataFrame({'price': spot_ask_price, 'vol': spot_ask_vol})
    # print(df)
    spot_ask_price = df['price'].drop_duplicates().values.tolist()
    # print(spot_ask_price)
    spot_ask_vol = df.groupby('price')['vol'].sum().tolist()
    # print(spot_ask_vol)
    spot_ask_vol = list(map(lambda x: int(x * percent / 100 / qty_unit), spot_ask_vol))  # 标准化处理
    return spot_bid_price,spot_bid_vol,spot_ask_price,spot_ask_vol


def percentage_pq(myDepth,percentlist):  # 获取价量百分比

    pankouDepth_min_bids = len(myDepth["bids"])
    pankouDepth_min_asks = len(myDepth["asks"])
    pankouDepth_min_bids = 20
    pankouDepth_min_asks = 20

    now_price = (myDepth["bids"][0][0] + myDepth["asks"][0][0])/2
    pankoucha = (myDepth["asks"][0][0]/myDepth["bids"][0][0]-1)*100

    # print(myDepth[2][0][0],myDepth[1][0][0])
    bid_guadanshu_list = []
    ask_guadanshu_list = []
    for mypercent in percentlist:           #获取盘口
        bid_guadanshu = 0
        bid_price = 0
        for dangwei in range(0, pankouDepth_min_bids):  # 5 len(current_depth.Bids)
            bid_guadanshu = bid_guadanshu + myDepth["bids"][dangwei][1]
            bid_price = myDepth["bids"][dangwei][0]
            if bid_price < now_price*(1-mypercent/100):          #and dangwei==pankouDepth-1
                break


        bid_guadanshu_list.append(bid_price)
        bid_guadanshu_list.append(bid_guadanshu)


    for mypercent in percentlist:            #获取盘口
        ask_guadanshu = 0
        ask_price = 0
        for dangwei in range(0, pankouDepth_min_asks):  # 5 len(current_depth.Bids)
            ask_guadanshu = ask_guadanshu + myDepth["asks"][dangwei][1]
            ask_price = myDepth["asks"][dangwei][0]
            if ask_price > now_price*(1+mypercent/100):       #and dangwei==pankouDepth-1
                break

        ask_guadanshu_list.append(ask_price)
        ask_guadanshu_list.append(ask_guadanshu)

    return  [pankoucha,bid_guadanshu_list ,ask_guadanshu_list]

def percentage_pq_66(myDepth,percentlist):  # 获取价量百分比

    pankouDepth_min_bids = len(myDepth[0])
    pankouDepth_min_asks = len(myDepth[2])

    now_price = (myDepth[0][0] + myDepth[2][0])/2
    print(myDepth[0][0] , myDepth[2][0])
    print(now_price)
    pankoucha = (myDepth[2][0]/myDepth[0][0]-1)*100
    print(len(myDepth[0]))

    bid_guadanshu_list = []
    ask_guadanshu_list = []
    for mypercent in percentlist:           #获取盘口
        bid_guadanshu = 0
        bid_price = 0
        for dangwei in range(0, pankouDepth_min_bids):  # 5 len(current_depth.Bids)
            print(now_price, myDepth[0][dangwei], now_price * (1 - mypercent / 100))
            if myDepth[0][dangwei] < now_price*(1-mypercent/100):          #and dangwei==pankouDepth-1
                break
            print(now_price,myDepth[0][dangwei],now_price*(1-mypercent/100))
            bid_guadanshu = bid_guadanshu + myDepth[1][dangwei]
            bid_price = myDepth[0][dangwei]
        bid_guadanshu_list.append(bid_price)
        bid_guadanshu_list.append(bid_guadanshu)


    for mypercent in percentlist:            #获取盘口
        ask_guadanshu = 0
        ask_price = 0
        for dangwei in range(0, pankouDepth_min_asks):  # 5 len(current_depth.Bids)
            if myDepth[2][dangwei] > now_price*(1+mypercent/100):       #and dangwei==pankouDepth-1
                break
            ask_guadanshu = ask_guadanshu + myDepth[3][dangwei]
            ask_price = myDepth[2][dangwei]
        ask_guadanshu_list.append(ask_price)
        ask_guadanshu_list.append(ask_guadanshu)

    return  [pankoucha,bid_guadanshu_list ,ask_guadanshu_list]