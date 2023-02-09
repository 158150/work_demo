import os
import pandas as pd
from operator import itemgetter
import data_process

symbolList = []

def run(symbol, zhengOrderList):
    if zhengOrderList.shape[0] == 0:
        print(f"{symbol}交易对没有成交")
        return
    if symbol != 'shibusdt':
        zhengOrderList.loc[zhengOrderList['qty_wbf']<0, 'profit'] = zhengOrderList['price_wbf']-zhengOrderList['price_binance']
        zhengOrderList.loc[zhengOrderList['qty_wbf']>0, 'profit'] = zhengOrderList['price_binance']-zhengOrderList['price_wbf']
    else:
        zhengOrderList.loc[zhengOrderList['qty_wbf']<0, 'profit'] = zhengOrderList['price_wbf']-zhengOrderList['price_binance']/1000
        zhengOrderList.loc[zhengOrderList['qty_wbf']>0, 'profit'] = zhengOrderList['price_binance']-zhengOrderList['price_wbf']/1000
    profit = zhengOrderList.loc[zhengOrderList['profit']>0]
    loss = zhengOrderList.loc[zhengOrderList['profit']<0]
    allprofit = round(profit['profit'].sum(axis=0),4)
    allloss = round(loss['profit'].sum(axis=0), 4)
    symbolList.append([symbol, zhengOrderList.shape[0], profit.shape[0], f"{round(profit.shape[0]/zhengOrderList.shape[0]*100,2)}%", 
                        loss.shape[0], f"{round(loss.shape[0]/zhengOrderList.shape[0]*100,2)}%", allprofit, allloss, allprofit+allloss])

def data_process_init(path):
    zhengOrderList, zhengPendingList, wbf_wss_execId_list, min_zhengPendingList = data_process.init_csv(path)
    return zhengOrderList


def main():
    allcsv = os.popen('find /usr/local/strategy -name zhengOrderList.csv')
    for line in allcsv.readlines():
        path = line.split('/zhengOrderList.csv')[0]
        symbol = line.split('strategy/')[1].split('-')[0]
        zhengOrderList = data_process_init(path)
        run(symbol, zhengOrderList)
    sortList = sorted(symbolList, key=itemgetter(-1), reverse=True)
    # for i in range(len(sortList)):
    #     print(f"{sortList[i][0]} 总成交:{sortList[i][1]}笔, 盈利:{sortList[i][2]}笔,占{sortList[i][3]}%, "
    #           f"亏损:{sortList[i][4]}笔,占{sortList[i][5]}%,总盈利:{sortList[i][6]}，总亏损:{sortList[i][7]},净盈亏{sortList[i][8]}")
    
    data = pd.DataFrame(sortList)
    data.columns = ['交易对','总成交','盈利笔数','盈利占比','亏损笔数','亏损占比','总盈利','总亏损','净盈亏']
    print(data)
    


if __name__ == "__main__":
    main()




