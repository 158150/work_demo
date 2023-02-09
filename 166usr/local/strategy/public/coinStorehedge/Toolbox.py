import numpy as np
np.set_printoptions(suppress=True)
import random
import time
import pytz
import os
import sys
import shutil
import yaml
import requests
import urllib
import json
import datetime
import logging
import traceback
import inspect
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders


def timestamp(tz='Asia/Singapore', strFormat='%Y-%m-%d %H:%M:%S'):
    """generate timestamp in particular timezone

    Args:
        tz (str, optional): timezone in pytz.common_timezones
        strFormat (str, optional): string format

    Returns:
        now (String): timestamp
    """
    tz = pytz.timezone(tz)
    now = datetime.datetime.now(tz).strftime(strFormat)
    return now


def warning(content, contractSymbol='btc/usdt'):
    '''dingtask alert

    Args:
        content (str): alert content
        contractSymbol (str, optional): contract involved
    '''
    # return
    # self._log('_warning',content,'')

    pass
    # url = 'https://oapi.dingtalk.com/robot/send?access_token=0da22b17f12ad45450bec43750913f179b215666e0ca4739de1fdc18dca966f0'
    # headers = {"Content-Type": "application/json ;charset=utf-8 "}
    # content = f"==={timestamp()} 策略报警 {contractSymbol}===\n{content}\n"
    # print(content)
    # msg = {'msgtype': 'text',
    #        'text': {'content': content}}
    # requests.post(url, headers=headers, data=json.dumps(msg))


def warningCall(content):
    url = (f'http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&'
           f'eventType=trigger&priority=2&eventId={str(int(time.time()))}&alarmContent={str(content)}异常')
    res = requests.post(url=url)
    return res.text


def loadYaml(fileName=None):
    '''load yaml config

    Args:
        fileName (None, optional): yaml file name, default is same name yaml file

    Returns:
        dict: config
    '''
    fileName = sys.argv[0].replace('py', 'yaml') if fileName is None else fileName
    dic = {}
    with open(fileName, 'r', encoding='utf-8') as f:
        content = yaml.load_all(f.read(), Loader=yaml.FullLoader)
    for i, part in enumerate(content):
        dic[i] = part
    dic = {k: v for d in dic.values() for k, v in d.items()}
    return dic


def round(number, minUnit, direction):
    ''' get number by minUnit
    Args:
        number: float
        direction: 'up' or 'down' or 'random' 向上取整或向下取整或随机
        minUnit (TYPE): Description

    Returns:
        number: float end with 0.5 or 0.
    '''
    strNum = str(minUnit)
    length = len(strNum.split('.')[1]) if '.' in strNum else int(strNum.split('e-')[-1])
    intPart = number//minUnit
    number = intPart*minUnit
    if direction == 'down':
        pass
    elif direction == 'up':
        number += minUnit
    elif direction == 'random':
        i = random.choice([0, 1])
        number = number+i*minUnit
    return np.round(number, length)


def splitList(lis, num):
    '''
    拆分列表

    Args:
        lis: list
        num: max length of divided list
    Returns:
        divided list
    '''
    if len(lis) <= num:
        return [lis]
    newLis = []
    for i in range(int(np.ceil(len(lis)/num))):
        newLis.append(lis[i*num:(i+1)*num])
    return newLis


def sendMail(subject,receivers,content,sender='499425216@qq.com',pwd='spbrsdxitwktbjce',SMTP='smtp.qq.com',fromHeader='Rexxar',toHeader='群发'):
    """send email
    
    Args:
        subject (str): title
        receivers (list): list of receivers
        content (str): content
        sender (str, optional): sender
        pwd (str, optional): password
        SMTP (str, optional): SMTP
        fromHeader (str, optional): Description
        toHeader (str, optional): Description
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    message = MIMEMultipart()
    message['From'] = Header(fromHeader,'utf-8')
    message['To'] = Header(toHeader,'utf-8')
    message['Subject'] = Header(subject)

    message.attach(MIMEText(f'=={timestamp}==\n\n{content}','plain','utf-8'))

    try:
        smtp = smtplib.SMTP_SSL(SMTP,465)
        smtp.login(sender,pwd)
        smtp.sendmail(sender, receivers, message.as_string())
        smtp.quit()
        print('邮件发送成功！')
    except:
        print('邮件发送失败！!!')
        print(traceback.format_exc())


def saveStrategyRunTime(logname, strategy, timestamp=None, path='/usr/local/server/timelog'):
    '''
        将每个策略循环时产生的时间戳保存为日志
    '''
    timestamp = time.time() if timestamp is None else timestamp
    with open(os.path.join(path,logname), 'w') as file:
        file.write(strategy+','+str(timestamp))

import logging.handlers
class Log():

    def __init__(self, fileName=None):
        """initial logging (critical level)

        Args:
            filename (TYPE): log file name
        """
        # 先声明一个 Logger 对象
        self.logger = logging.getLogger(fileName)
        filename = sys.argv[0].split('\\')[-1].replace('py', 'log') if fileName is None else fileName
        formatter = logging.Formatter('%(asctime)s --- %(message)s') # %(asctime)s - %(levelname)s -
        handler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=1024 * 20 * 1024, backupCount=10,
                                                       encoding="utf-8", delay=False)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        # self.write('================启动Log================', '')

    def write(self, content='', funcName=None):
        '''recording

        Args:
            funcName (None, optional): in which function when recording
            content (str, optional): content 
        '''
        #funcName = inspect.stack()[1][3] if funcName is None else funcName
        #content = f"== {timestamp(strFormat='%Y-%m-%d %H:%M:%S')} {funcName}== | {content}"
        self.logger.critical(content)



class LocalDB():

    """Summary

    Attributes:
        copyFile (TYPE): back-up file of dataBase
        file (TYPE): dataBase
        maxlen (TYPE): max length of saved data
    """

    def __init__(self, file, maxlen=3000):
        """Summary

        Args:
            file (file): {fileName}.log
            maxlen (int, optional): max length of saved data
        """
        self.file = file
        self._file = file.split('.')
        self.copyFile = f"{self._file[0]}_Copy.{self._file[1]}"
        self.maxlen = maxlen

    def load(self):
        """load file data

        Returns:
            list/dictionary: existed data
        """
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                content = f.read()
            if content == '':  # if the file is empty(interrupted during writing)
                with open(self.copyFile, 'r') as f:  # load the back-up file
                    content = f.read()
            content = eval(content)
            content = deque(content, maxlen=self.maxlen)
            setattr(self, f"{self._file[0]}Deque", content)
            if isinstance(content[0], dict):
                return {k: v for i in content for k, v in i.items()}
            else:
                return list(content)

        else:  # create the new file
            setattr(self, f"{self._file[0]}Deque", deque(maxlen=self.maxlen))
            return []

    def save(self, data):
        """save data to file

        Args:
            data (number/str/list/dict): data

        Returns:
            list/dict: updated data
        """
        content = getattr(self, f"{self._file[0]}Deque")
        content.append(data)  # update data

        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')

        if isinstance(content[0], dict):  # dict data
            return {k: v for i in content for k, v in i.items()}

        else:  # not dict data
            return list(content)


def _C(function, *args):
    res = 0
    while not(res):
        try:
            res = function(*args)
        except Exception:
            print(traceback.format_exc())
            time.sleep(1)
    return res

import requests
import ctypes


def _async_raise(tid, exctype):
    """Raises an exception in the threads with id tid"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

import threading
# 多线程如何返回值
class MyThread(threading.Thread):

    def __init__(self,func,args=()):
        super(MyThread,self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None

def _TO(timeout,fun,*args):
    c = MyThread(fun,args)
    c.start()
    c.join(timeout)
    if c.isAlive():
        stop_thread(c)
        a = Log("log_timeout.log")
        print("timeout")
        a.write("timeout")
    else:
        return c.result



def mkdir(path):
    # 引入模块

    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("/")

    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)

        print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path + ' 目录已存在')
        return False

import shutil
def _GCSV(path,csv_name,csv_list):
    filename = path + csv_name + '.csv'
    filename_copy = path + csv_name + '_copy.csv'
    shutil.copyfile(filename,filename_copy)
    csv_list.to_csv(filename, sep=',', header=True, index=True)  # index=False,


if __name__ == '__main__':
    url = "https://api.wbfutures.pro/api/v1/futureQuot/queryMarketStat?currencyId=8"

    # init_time = time.time()
    # print(_TO(1000, test))
    # time1 = time.time()
    # print(time1-init_time)
    #
    # init_time = time.time()
    # print(test())
    # time1 = time.time()
    # print(time1 - init_time)





    
    # fileName = 'clOrders.log'
    # clOrderBase = localDB(fileName)
    # clOrders = clOrderBase.load()
    # print(clOrders)
    # clOrders = clOrderBase.save({'1231243533': 'close84848291'})
    # print(clOrders)
    # clOrders = clOrderBase.save({'325252352': 'close00003434343'})
    # print(clOrders)
    warningCall("eeee")
    # fileName = 'execIds.log'
    # execIdBase = localDB(fileName)
    # execIds = execIdBase.load()
    # print(execIds)
    # execIds = execIdBase.save(1290931111)
    # print(execIds)
    # execIds = execIdBase.save(12313131313122)
    # print(execIds)

    # warning(content='测试')
    # warning(content='测试',contractSymbol='eth/usdt')
    # sendMail('test',['499425216@qq.com'],'test')
    pass
