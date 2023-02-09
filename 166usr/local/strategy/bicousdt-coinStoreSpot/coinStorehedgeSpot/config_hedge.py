config = {'wbfPublicKey': '100716',
          'wbfPrivateKey': '00715e04-f19a-4255-85a4-31c3b25d5e70',
          'binanceSwapPublicKey': '3b899831-5170-44d8-a41d-01eaa086009a',
          'binanceSwapPrivateKey': 'B7CC0BAB1AF4267779C0345AA36DBBB0//qvk2zrg7y!nx7F3b',
}

hedge_exchange = "binanceUsdtSwap"
accountlever = 3            # 账户杠杆倍数  0 为不使用杠杆（现货）
market_make_sleeptime = 3   # 做市模块最大睡眠时间
chack_index_time = 3        # 检查价格异常时间
order_timeout = 3           # 追单时间
timeout_close_timeout = 3   # 追单函数延时

initbalance = 200           # 剩余低于2000usdt 需要报警
every_qty_precent = 20      # 每次下单占总balance 比例
profit_percent = 0.1        # 预期盈利百分比
slip_percent = 0.05         # 追单滑点百分比
max_percent = 0.05          # 最大偏移百分比           #套利成本
qty_precent = 10            # 镜像仓位最大百分比       #外盘深度占比
num_maker = 20              # 最大摆盘档位       

ask_percent = 0             # 手动偏离
bid_percent = 0             # 手动偏离
taker_ask_percent = 0.2     # taker 偏离
taker_bid_percent = 0.2     # taker 偏离

wbf_contractId = 700009
binance_symbol = "bico/usdt"
wbf_qty_unit = 0.0001       # 内盘数量最小单位
wbf_qty_digital = 4         # 数量最小单位位数
fee_qty_digital = round(wbf_qty_digital + 4)
binance_qty_unit = 1        # 外盘数量最小单位
binance_qty_digital = 0     # 数量最小单位位数

wbf_price_unit = 0.0001      # 价格最小单位
binance_price_unit = 0.0001  # 价格最小单位

init_usdt = 10000            # 内盘usdt金额
init_coin = 5350             # 内盘币数量
init_usdt_binance = 3100     # 外盘usdt金额
init_coin_binance = 852.389  # 外盘币数量

check_wss_wbf_sleeptime = 1

# 在策略内部提出来的参数，有需要修改的在这里设置，否则不用设置
# contract_base = 9000000    # DataPushServer的编号
# base_exchange = 'coinStore'    # 内盘交易所
# hedge_exchange = 'binanceSpot'    # 对冲交易所
# expost_amt = 5000       # 暴露金额
# timeout_percent = 0.05      # 下单延时高，扩大摆盘的比例
# risk_percent = 5            # 触发风控时，扩大摆盘的比例
# warn_balance = 1/5          # 保证金不足初始百分比触发报警
# coins_amt = 20              # 内盘币的金额少于20usdt报警
# reduceTag = False           # 是否将盘口缩到最小
