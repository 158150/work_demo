import numpy as np
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
import logging.handlers
import traceback
import inspect
import redis
from collections import deque
import smtplib
import threading
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


def warning(content, contractSymbol='btc/usdt', method='normal'):
    '''dingtask alert

    Args:
        content (str): alert content
        contractSymbol (str, optional): contract involved
    '''
    # return
    # self._log('_warning',content,'')
    if method=='normal':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=0da22b17f12ad45450bec43750913f179b215666e0ca4739de1fdc18dca966f0'
        content = f"==={timestamp()} 策略报警 {contractSymbol}===\n{content}\n"
    elif method=='transfer':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=afa238a5ed5f9a2d19b16a8c1e26159b38011837e646d6e4447b9ceb8c86e048'
        content = f"==={timestamp()} 转账 {contractSymbol}===\n{content}\n"
    elif method=='mistake':
        #url = 'https://oapi.dingtalk.com/robot/send?access_token=8e4665536d69d10e9b37bf40a6d3c942cc33345470bce4bf59adb4a23311f9d4'
        url = 'https://oapi.dingtalk.com/robot/send?access_token=0a69d59ef440fd21aa5e0a447cea591931a9927ae19a69f8abfb55789abf6cb8'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='gamble':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=e22759d0b1fca12729f38fa4e06f8e825e072921b45f5b53ed312f9b4e7d79b5'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='adl':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=8e393755a70186b9771337754bf428f78c79efa96f758604f3d199b65f5955da'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='fakeIncreVol':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=bc34ae6cc2702df56bbaec25503cf17d012ad46805fddf20f8d5faa8d6fa456e'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='hedge':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=cf7771db6144140c0edad9d3d46aecf1d2ab799b96e2725c6bfbb560bb10e64a'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n" 
    elif method=='etp':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=77bbba5c090f8be0804a280f5302f3a3dcbf12ec4402ed47be6f29d68c956e4f'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='margin':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=f90a0367816bf1c088c093e2c10ae8d24cb38f2751a20cc4db36fd44fdee5974'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='stop':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=81b4276642842a6eea4fcb11e881a9ef12fa787d8085ba8f15ef3da7463c2c71'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='basis':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=a3050105da2f19314947c5bcbd2fd7f4f87d6070d46e415ed65f9927125abe52'
        content = f"==={timestamp()} 基差 {contractSymbol}===\n{content}\n"
    elif method == 'arbitrage':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=189ec03ba8a2c581628835c9d82339b9edba1f9417c6aa25ec8976b1bb747513'
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
        

    headers = {"Content-Type": "application/json ;charset=utf-8 "}
    print(content)
    msg = {'msgtype': 'text',
           'text': {'content': content}}
    requests.post(url, headers=headers, data=json.dumps(msg))

def callPhone(strategy, symbol, content):
    url = f"http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&\
            eventType=trigger&alarmName={strategy}{content}&eventId=21946515-9eb2-4078-813f-a8420baf0dab-7&\
            alarmContent={strategy}{content}&entityName={symbol}交易对&entityId=123456&priority=1"
    info = requests.post(url=url)
    print(f"拨电话{info.text}")

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
    content = f"==={timestamp()}  资金报警binanceSwap {contractSymbol}===\n{content}\n"
    print(content)
    msg = {'msgtype': 'text',
            'text': {'content': content}}
    requests.post(url, headers=headers, data=json.dumps(msg))

def warningCall(mobiles=['15210166821','18981142505']):
    # mobiles = ['18981142505','15210166821','15832260052','13811286063']
    # mobiles = ['15210166821','18981142505']
    # mobiles = ['18981142505','15210166821']
    host = 'http://yuyintz.market.alicloudapi.com'
    path = '/ts/voiceNotifySms'
    # appcode = '6d47356ceff2477f95f30cefa6572b50'
    appcode = '10a0b810017c4cd798dfc2500231772b'
    for m in mobiles:
        params = {'mobile': m, 'tpl_id': 'TP18040813'}
        querys = urllib.parse.urlencode(params)
        # print(querys)
        url = f'{host}{path}?{querys}'
        headers = {'Authorization': f'APPCODE {appcode}'}
        try:
            res = requests.post(url, headers=headers)
            print(res)
        except:
            print('电话报警失败')


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
    return np.round(np.round(number, length),length)

def adjustPrecision(number, unit, direction):
    """精度调整

    Args:
        number (float): targeted number
        unit (float): minimum unit of targeted number
        direction (str): round direction (up/down/random)

    Returns:
        float: rounded number
    """        
    sign = np.sign(number)
    number = abs(number)
    length = len(str(unit).split('.')[1]) if '.' in str(unit) else int(str(unit)[-2:])
    # print(length)
    direction = random.random.choice([0, 1]) if direction == 'random' else \
            1 if direction == 'up' else \
            0
    a = number*10**length
    b = unit*10**length
    intPart = a//b
    # print(intPart)
    number = intPart*unit + direction*unit
    number = round(number, length)
    number = round(number, length)
    return sign * number 


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


def sendMail(subject,receivers,content,sender='499425216@qq.com',pwd='fswuzgijfocibiah',SMTP='smtp.qq.com',fromHeader='Rexxar',toHeader='群发',style='text'):
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
        style (str): text, html
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    message = MIMEMultipart()
    message['From'] = Header(fromHeader,'utf-8')
    message['To'] = Header(toHeader,'utf-8')
    message['Subject'] = Header(subject)

    if style == 'text':
        message.attach(MIMEText(f'=={timestamp}==\n\n{content}','plain','utf-8'))
    elif style == 'html':
        message.attach(MIMEText(content, _subtype='html', _charset='utf-8'))


    try:
        smtp = smtplib.SMTP_SSL(SMTP,465)
        smtp.login(sender,pwd)
        smtp.sendmail(sender, receivers, message.as_string())
        smtp.quit()
        print('邮件发送成功！')
    except:
        print('邮件发送失败！!!')
        print(traceback.format_exc())


def saveStrategyRunTime(logname, strategy1, strategy2, timestamp=None, path='/usr/local/server/timelog'):
    '''
        将每个策略循环时产生的时间戳保存为日志
    '''
    timestamp = time.time() if timestamp is None else timestamp
    with open(os.path.join(path,logname), 'w') as file:
        file.write(strategy1+','+strategy2+','+str(timestamp))

class Redis():

    """Redis
    
    Attributes:
        client (TYPE): redis client
    """
    
    # def __init__(self,host='10.254.2.249',port=6379):10.0.2.79
    def __init__(self,host='127.0.0.1',port=6379):
        pool = redis.ConnectionPool(host=host,port=port,decode_responses=True)
        self.client = redis.Redis(connection_pool=pool)

    def set(self,key,content):
        self.client.set(key,str(content))

    def get(self,key):
        try:
            # print(self.client.get(key))
            data = eval(self.client.get(key))
        except:
            # print(traceback.format_exc())
            data = []
        return data

    def lrange(self,key,start=0,end=-1):
        return self.client.lrange(key,start,end)

    def query(self):
        return self.client.keys()

    def delete(self,key):
        self.client.delete(key)

    def lpush(self,key,*args,length=0):
        self.client.lpush(key,*args)
        if length != 0:
            self.client.ltrim(key,0,length-1)

class Log():

    def __init__(self, fileName=None,sizeMB=200, backupNum=3):
        """initial logging (critical level)
        
        Args:
            fileName (str, optional): fileName
            sizeMB (int, optional): how many MB
            backupNum (int, optional): how many backup files        
        """
        self.logger = logging.getLogger(fileName)
        filename = sys.argv[0].split('\\')[-1].replace('py', 'log') if fileName is None else fileName
        self.filename = filename
        formatter = logging.Formatter('%(message)s')
        handler = logging.handlers.RotatingFileHandler(filename=filename,
                                                       maxBytes=1024*1024*sizeMB,
                                                       backupCount=backupNum,
                                                       encoding='utf-8',
                                                       delay=False)
        handler.setFormatter(formatter)
        handler.setLevel(logging.CRITICAL)
        self.logger.addHandler(handler)
        # logging.basicConfig(level=logging.CRITICAL,
        #                     format='%(message)s',
        #                     filename=f'./{filename}',
        #                     filemode='a')
        self.write('================启动Log================', '')

    def write(self, content='', funcName=None):
        '''recording

        Args:
            funcName (None, optional): in which function when recording
            content (str, optional): content 
        '''
        funcName = inspect.stack()[1][3] if funcName is None else funcName
        content = f"== {timestamp(strFormat='%Y-%m-%d %H:%M:%S')} {funcName}== | {content}"
        print(f'{self.filename}: {content}')
        self.logger.critical(content)
        # logging.critical(content)


class LocalDB():

    """Summary

    Attributes:
        copyFile (TYPE): back-up file of dataBase
        file (TYPE): dataBase
        maxlen (TYPE): max length of saved data
    """

    def __init__(self, file, maxlen=3000, ds='list'):
        """Summary

        Args:
            file (file): {fileName}.log
            maxlen (int, optional): max length of saved data
        """
        self.file = file
        self._file = file.split('.')
        self.copyFile = f"{self._file[0]}_Copy.{self._file[1]}"
        self.maxlen = maxlen
        self.ds = ds
        


    def load(self):
        """load file data

        Returns:
            list/dictionary: existed data
        """
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                content = eval(f.read())
            if content == '':  # if the file is empty(interrupted during writing)
                with open(self.copyFile, 'r') as f:  # load the back-up file
                    content = eval(f.read())
            # content = eval(content)
            if self.ds=='list':
                content = deque(content, maxlen=self.maxlen)
                setattr(self, f"{self._file[0]}Data", content)
                return list(content)
            elif self.ds=='dict':
                setattr(self, f"{self._file[0]}Data", content)
                return content
            elif self.ds=='array':
                content = np.array(content)
                setattr(self, f"{self._file[0]}Data", content)
                return content
            # if isinstance(content[0], dict):
            #     return {k: v for i in content for k, v in i.items()}
            # else:
            #     return list(content)

        else:  # create the new file
            if self.ds=='list':
                setattr(self, f"{self._file[0]}Data", deque(maxlen=self.maxlen))
                return []
            elif self.ds=='dict':
                setattr(self, f"{self._file[0]}Data", {})
                return {}
            elif self.ds=='array':
                setattr(self, f"{self._file[0]}Data", [])
                return []


    def save(self, data):
        """save data to file

        Args:
            data (number/str/list/dict): data

        Returns:
            list/dict: updated data
        """
        if self.ds=='array':
            if os.path.exists(self.file):  # back up
                shutil.copyfile(self.file, self.copyFile)
            with open(self.file, 'w') as f:  # writing
                f.write(f'{data.tolist()}') 
            return data


        content = getattr(self, f"{self._file[0]}Data")
        if self.ds=='list':
            content.append(data)
        elif self.ds=='dict':
            for k,v in data.items():
                content[k] = v
        setattr(self, f"{self._file[0]}Data", content)

        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')

        if self.ds=='list':
            return list(content)
        elif self.ds=='dict':
            return content

    def refresh(self,data):
        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{data}')
        setattr(self, f"{self._file[0]}Data", data)


    def incre(self, data):
        """字典添加
        
        Args:
            data (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        content = getattr(self, f"{self._file[0]}Data")
        for k,v in data.items():
            if k not in content:
                content[k] = v
            else:
                content[k] += v
        setattr(self, f"{self._file[0]}Data", content)
        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')
        return content

    def decre(self, data):
        """删减字典
        
        Args:
            data (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        content = getattr(self, f"{self._file[0]}Data")
        for k,v in data.items():
            if k not in content:
                pass
            else:
                content[k] -= v
                if content[k]<=0:
                    del content[k]
        setattr(self, f"{self._file[0]}Data", content)
        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')
        return content


    def delete(self, key):
        """删除key 字典格式
        
        Args:
            key (TYPE): Description
        """
        content = getattr(self, f"{self._file[0]}Data")
        del content[key]
        setattr(self, f"{self._file[0]}Data", content)
        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')
        return content


    def clear(self):
        """reset localDB
        """
        try:
            os.remove(self.file)
        except:
            pass
        try:
            os.remove(self.copyFile)
        except:
            pass
        if self.ds=='list':
            setattr(self, f"{self._file[0]}Data", deque(maxlen=self.maxlen))
            return []
        elif self.ds=='dict':
            setattr(self, f"{self._file[0]}Data", {})
            return {}

class LocalDict():

    """本地字典
    """

    def __init__(self, file):
        """Summary

        Args:
            file (file): {fileName}.log
            maxlen (int, optional): max length of saved data
        """
        self.file = file
        self.copyFile = f"{file.split('.')[0]}_Copy.{file.split('.')[1]}"
        # self.lock = False
        self.lock = threading.Lock()


    def _write(self, content, lock=True):
        """写入
        
        Args:
            data (TYPE): Description
        """
        if lock:
        #     while self.lock:
        #         time.sleep(0.005)
        #         print('log locking')
        #         continue
        #     self.lock = True
            self.lock.acquire()
        if os.path.exists(self.file):  # back up
            shutil.copyfile(self.file, self.copyFile)
        with open(self.file, 'w') as f:  # writing
            f.write(f'{content}')
        if lock:
            self.lock.release()
        #     self.lock = False
        return content


    def load(self, lock=True):
        """load file data

        Returns:
            list/dictionary: existed data
        """
        if lock:
        #     while self.lock:
        #         time.sleep(0.005)
        #         print('log locking')
        #         continue
        #     self.lock = True
            self.lock.acquire()
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                content = eval(f.read())
            if content == '':  # if the file is empty(interrupted during writing)
                with open(self.copyFile, 'r') as f:  # load the back-up file
                    content = eval(f.read())
        else:  # create the new file
            content = {}
        if lock:
        #     self.lock = False
            self.lock.release()
        return content


    def save(self,data):
        """新建
        
        Args:
            data (TYPE): Description
        """
        # while self.lock:
        #     time.sleep(0.005)
        #     print('log locking')
        #     continue
        # self.lock = True
        self.lock.acquire()
        content = self.load(lock=False)
        for k,v in data.items():
            content[k] = v
        data = self._write(content, lock=False)
        # self.lock = False
        self.lock.release()
        return data


    def incre(self,data):
        """新建或增加
        
        Args:
            data (TYPE): Description
        """
        # while self.lock:
        #     time.sleep(0.005)
        #     print('log locking')
        #     continue
        # self.lock = True
        self.lock.acquire()
        content = self.load(lock=False)
        for k,v in data.items():
            if k not in content:
                content[k] = v
            else:
                content[k] += v 
        data = self._write(content, lock=False)  
        # self.lock = False
        self.lock.release()   
        return data

    def append(self, data):
        """list增加
        
        Args:
            data (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        # while self.lock:
        #     time.sleep(0.005)
        #     print('log locking')
        #     continue
        # self.lock = True
        self.lock.acquire()
        content = self.load(lock=False)
        for k, v in data.items():
            if k not in content:
                content[k] = v
            else:
                content[k] = content[k] + v
        data = self._write(content, lock=False)
        # self.lock = False
        self.lock.release()
        return data

    def delete(self, key):
        # while self.lock:
        #     time.sleep(0.005)
        #     print('log locking')
        #     continue
        # self.lock = True
        self.lock.acquire()
        content = self.load(lock=False)
        if key in content:
            del content[key]
        data = self._write(content, lock=False)
        # self.lock = False
        self.lock.release()
        return data

    def refresh(self,data):
        """重置
        
        Args:
            data (TYPE): Description
        """
        # while self.lock:
        #     time.sleep(0.005)
        #     print('log locking')
        #     continue
        # self.lock = True
        self.lock.acquire()
        data = self._write(data, lock=False)
        # self.lock = False
        self.lock.release()
        return data


class RedisDict():

    """redis字典
    """

    def __init__(self,host='10.0.2.79'):
        """Summary

        Args:
            file (file): {fileName}.log
            maxlen (int, optional): max length of saved data
        """
        self.redis = Redis(host=host)
        # self.key = key
        # self.file = file
        # self.copyFile = f"{file.split('.')[0]}_Copy.{file.split('.')[1]}"


    def _write(self,key,content):
        """写入
        
        Args:
            data (TYPE): Description
        """
        self.redis.set(key,content)
        return content


    def load(self,key):
        """load file data

        Returns:
            list/dictionary: existed data
        """
        data = self.redis.get(key)
        if len(data)==0:
            data = {}
        return data


    def save(self,key,data):
        """新建
        
        Args:
            data (TYPE): Description
        """
        content = self.load(key)
        for k,v in data.items():
            content[k] = v
        return self._write(key,content)


    def incre(self,key,data):
        """新建或增加
        
        Args:
            data (TYPE): Description
        """
        content = self.load(key)
        for k,v in data.items():
            if k not in content:
                content[k] = v
            else:
                content[k] += v      
        return self._write(key,content)

    def refresh(self,key,data):
        """重置
        
        Args:
            data (TYPE): Description
        """
        return self._write(key,data)


class Kafka():

    def __init__(self, topic, group, **kwargs):
        from kafka import KafkaConsumer, TopicPartition
        self.topicDict = {
            'usdtSwap': 'wbf_match_position',
            'coins': 'full_match_position',
            'coinSwap': 'coin_match_position',
        }
        self.consumer = KafkaConsumer(
            # topic,
            group_id=group,
            bootstrap_servers=[
                '10.224.1.153:9092',
                '10.224.1.27:9092',
                '10.224.1.161:9092',    
                ],
            api_version=(0, 9),
            **kwargs,
        )
        self.tp = TopicPartition(self.topicDict[topic], 0)
        self.consumer.assign([self.tp])

    def getOffset(self):
        return self.consumer.position(self.tp)

    def reset(self, offset=None):
        if offset is None:
            self.consumer.seek_to_beginning(self.tp)
        else:
            self.consumer.seek(self.tp, offset)

    def close(self):
        self.consumer.close()

    def _run(self, rsp):
        for message in self.consumer:
            # print(message)
            message = [message.offset, eval(str(message.value, encoding='utf-8').replace('null', '123'))]
            rsp(message)
        # while 1:
        #     message = self.consumer.poll()
        #     rsp(message)
        #     time.sleep(0.01)

    def run(self, rsp):
        process = threading.Thread(target=self._run, args=(rsp,))
        process.start()



if __name__ == '__main__':
    # task = LocalDict('test.log')
    # def _th():
    #     task.save({'abcd': 2})
    # task.save({'abc': 11})
    # time.sleep(2)
    # process = threading.Thread(target=_th)
    # process.start()
    # data = 3.9
    # unit = 1
    # direction = 'up'
    # print(_round(data, unit, direction))
    # print(adjustPrecision(data, unit, direction))
    # print(round(0.000013245643423, 0.00000001, 'up'))
    test = LocalDict('test.log')
    # test.save({'abc':{'a': 1, 'b': 2}})
    # t = test.save({'abc': {'a': 4, 'c': 2}})
    t = test.load()
    # t = test.load()
    t['abc']['c'] += 2
    t = test.save(t)
    a = {'abc':{}}
    a['abc']['cost'] = a.get('abc', {}).get('cost', 0) + 5
    print(a)
    # print(t['abc']['a'])
    print(t)
