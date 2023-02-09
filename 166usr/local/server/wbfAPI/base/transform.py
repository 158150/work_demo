import time


def assignment(ori, target):
    """Summary

    Args:
        ori (dict): Original Data
        target (dict): Description
    """
    if isinstance(target, dict):
        ori.update(target)
    elif isinstance(target, list):
        # target = [{}] if target == [] else target  # 异常处理
        data = [ori]*len(target)
        ori = []
        for i, dic in enumerate(target):
            data[i].update(dic)
            ori.append(data[i].copy())
    return ori


def normalizeTick(**kwargs):
    """[[时间戳(exc), 价格, 数量, 方向(1, -1)]]

    Args:
        **kwargs: Description

    Returns:
        TYPE: Description
    """
    data = {
        'status': 'success',
        'data': [[None, None, None, None]],
        'extra': None,
    }
    return assignment(data, kwargs)


def normalizeDepth(**kwargs):
    """[时间戳(exc), [[买价，买量]], [[卖价，卖量]], 时间戳(sys)]

    Args:
        **kwargs: Description

    Returns:
        TYPE: Description
    """
    data = {
        'status': 'success',
        'data': [None, [[None, None]], [[None, None]], None],
        'extra': None,
    }
    return assignment(data, kwargs)


def normalizeKline(**kwargs):
    """[[时间戳，开，高，低，收，量，额]]

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': [[None, None, None, None, None, None, None]],
        'extra': None,
    }
    return assignment(data, kwargs)


def normalizeClearPrice(**kwargs):
    """[时间戳(exc)，指数价格，标记价格，时间戳(sys)]

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': [None, None, None, None],
        'extra': None
    }
    return assignment(data, kwargs)


def normalizeFundingRate(**kwargs):
    """[时间戳(exc)，资金费率，预测资金费率，时间戳(sys)]

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': [None, None, None, None],
        'extra': None
    }
    return assignment(data, kwargs)


def normalizeAccount(**kwargs):
    """[]

    Args:
        **kwargs: Description
    """
    pass


def normalizeBalance(**kwargs):
    """

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeBalance([]),
        'extra': None
    }
    kwargs['data'] = _normalizeBalance(kwargs.get('data', []))
    return assignment(data, kwargs)


def _normalizeBalance(dataList):
    """[{symbol, balance（totalBalance）, available, frozen, initMargin}]

    Args:
        **kwargs: Description
    """
    data = {
        'symbol': None,
        'balance': None,
        'available': None,
        'frozen': None,
        'initMargin': None,
    }
    return assignment(data, dataList)


def normalizePosition(**kwargs):
    """Summary

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizePosition([]),
        'extra': None
    }
    kwargs['data'] = _normalizePosition(kwargs.get('data', []))
    return assignment(data, kwargs)


def _normalizePosition(dataList):
    """[{symbol, pos, posSide, openPrice, holdPrice, liquidationPrice, 
        unrealProfitLoss, closeProfitLoss, openAmt, lever}]

    Args:
        **kwargs: Description
    """
    data = {
        'symbol': None,
        'pos': None,
        'posSide': None,
        'openPrice': None,
        'openAmt': None,
        'holdPrice': None,
        'liquidationPrice': None,
        'unrealProfitLoss': None,
        'closeProfitLoss': None,
        'lever': None,
    }
    return assignment(data, dataList)


def normalizeMakeOrder(**kwargs):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeMakeOrder({}),
        'extra': None,
    }
    kwargs['data'] = _normalizeMakeOrder(kwargs.get('data', {}))
    return assignment(data, kwargs)


def _normalizeMakeOrder(dic):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        dataList (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'orderId': None,
        'code': -1,
        'info': None,
    }
    return assignment(data, dic)


def normalizeMakeOrders(**kwargs):
    """Summary

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeMakeOrders([]),
        'extra': None,
    }
    kwargs['data'] = _normalizeMakeOrders(kwargs.get('data', []))
    return assignment(data, kwargs)


def _normalizeMakeOrders(dataList):
    """[{下单时间戳（13位）, orderid, code, 备注}]

    Args:
        dataList (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'orderId': None,
        'code': -1,
        'info': None,
    }
    return assignment(data, dataList)


def normalizeCancelOrder(**kwargs):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeCancelOrder({}),
        'extra': None,
    }
    kwargs['data'] = _normalizeCancelOrder(kwargs.get('data', {}))
    return assignment(data, kwargs)


def _normalizeCancelOrder(dic):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        dic (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'orderId': None,
        'code': -1,
        'info': None,
    }
    return assignment(data, dic)


def normalizeCancelOrders(**kwargs):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeCancelOrder([]),
        'extra': None,
    }
    kwargs['data'] = _normalizeCancelOrder(kwargs.get('data', {}))
    return assignment(data, kwargs)


def _normalizeCancelOrders(dataList):
    """{下单时间戳（13位）, orderid, code, 备注}

    Args:
        dataList (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'orderId': None,
        'code': -1,
        'info': None,
    }
    return assignment(data, dataList)


def normalizeCancelAll(**kwargs):
    """Summary

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeCancelAll({}),
        'extra': None,
    }
    kwargs['data'] = _normalizeCancelAll(kwargs.get('data', {}))
    return assignment(data, kwargs)


def _normalizeCancelAll(dic):
    """{ts, code, info}

    Args:
        dic (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'code': -1,
        'info': None,
    }
    return assignment(data, dic)


def normalizeQueryOrder(**kwargs):
    """Summary

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeQueryOrder({}),
        'extra': None,
    }
    kwargs['data'] = _normalizeQueryOrder(kwargs.get('data', {}))
    return assignment(data, kwargs)


def _normalizeQueryOrder(dic):
    """{'symbol':None, 'orderId':None, 'clientOrderId':None, 'ts':None, 'price':None, \
               'vol':None, 'side':None, 'offset':None, 'type':None, 'amt':None, 'matchVol':None, \
               'matchAmt':None, 'fee':None, 'feeAseet':None, 'status':None, 'source':None, \
               'machTs':None, 'cancelTs':None}

    Args:
        dic (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'symbol': None,
        'orderId': None,
        'clientOrderId': None,
        'price': None,
        'matchPrice': None,
        'vol': None,
        'matchVol': None,
        'amt': None,
        'matchAmt': None,
        'side': None,
        'offset': None,
        'type': None,
        'postOnly': None,
        'fee': None,
        'feeAsset': None,
        'status': None,
        'matchTs': None,
        'cancelTs': None,
        'source': None,
        'info': None,
    }
    return assignment(data, dic)


def normalizeOpenOrders(**kwargs):
    """Summary

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeOpenOrders([]),
        'extra': None,
    }
    kwargs['data'] = _normalizeOpenOrders(kwargs.get('data', []))
    return assignment(data, kwargs)


def _normalizeOpenOrders(dataList):
    """{'symbol':None, 'orderId':None, 'clientOrderId':None, 'ts':None, 'openPrice':None, \
               'vol':None, 'side':None, 'offset':None, 'type':None, 'amt':None, 'matchVol':None, \
               'matchAmt':None, 'fee':None, 'feeAseet':None, 'status':None, 'source':None}

    Args:
        dataList (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'symbol': None,
        'orderId': None,
        'clientOrderId': None,
        'price': None,
        'vol': None,
        'matchVol': None,
        'amt': None,
        'matchAmt': None,
        'side': None,
        'offset': None,
        'type': None,
        'postOnly': None,
        'fee': None,
        'feeAsset': None,
        'status': None,
        'source': None,
    }
    return assignment(data, dataList)


def normalizeDeals(**kwargs):
    """

    Args:
        **kwargs: Description
    """
    data = {
        'status': 'success',
        'data': _normalizeDeals([]),
        'extra': None,
    }
    kwargs['data'] = _normalizeDeals(kwargs.get('data', []))
    return assignment(data, kwargs)


def _normalizeDeals(dataList):
    """{'symbol':None, 'myUserId':None, 'oppUserId':None, 'myOrderId':None, 'oppOrderId':None, \
               'clientOrderId':None, 'tradeId':None, 'ts':None, 'price':None, 'vol':None, 'amt':None, \
               'side':None, 'offset':None, 'type':None, 'role':None, 'fee':None, 'feeAseet':None, \
               'source':None}

    Args:
        dataList (TYPE): Description
    """
    data = {
        'ts': int(time.time()*1000),
        'symbol': None,
        'myUserId': None,
        'oppUserId': None,
        'myOrderId': None,
        'oppOrderId': None,
        'clientOrderId': None,
        'tradeId': None,
        'side': None,
        'type': None,
        'offset': None,
        'price': None,
        'vol': None,
        'amt': None,
        'fee': None,
        'feeAsset': None,
        'role': None,
        'source': None,
    }
    return assignment(data, dataList)


if __name__ == '__main__':
    # t = time.time()
    # lis = [{'symbol': 'abc', 'balance': 1, 'frozen': 2}]*300
    # data = normalizeTick()
    # data = normalizeDepth()
    # data = normalizeKline()
    # data = normalizeClearPrice()
    # data = normalizeFundingRate()
    # data = normalizeBalance(data=lis)
    # data = normalizePosition()
    # data = normalizeMakeOrder()
    # data = normalizeMakeOrders()
    # data = normalizeCancelOrder()
    # data = normalizeCancelAll()
    # data = normalizeQueryOrder()
    # data = normalizeOpenOrders(data=[])
    # data = normalizeDeals()
    # print(time.time()-t)
    # print(data)
    data = []
    a = [{d[0]:1} for d in data]
    print(a)
    pass
