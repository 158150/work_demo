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
from email.mime.image import MIMEImage
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


def warning(content, contractSymbol='', method='normal'):
    '''dingtask alert

    Args:
        content (str): alert content
        contractSymbol (str, optional): contract involved
    '''
    # return
    # self._log('_warning',content,'')
    larkDic = {
        'arbitrage02': 'https://open.larksuite.com/open-apis/bot/v2/hook/730d6fba-a03a-4742-975f-7edbfc74a606',
        'arbitrage03': 'https://open.larksuite.com/open-apis/bot/v2/hook/58b639d2-80d5-457e-b346-bcb1cd6c890c',
        'arbitrage06': 'https://open.larksuite.com/open-apis/bot/v2/hook/75f12be9-980e-4f5e-891d-7e9f812d4a56',
        'arbitrage07': 'https://open.larksuite.com/open-apis/bot/v2/hook/3e26a3db-1c65-4e59-a9cb-38a67f7f2ef5',
        'mlTaker08': 'https://open.larksuite.com/open-apis/bot/v2/hook/266a5bfb-38b5-4d6c-9bab-a7dfd3ed28b8',
        'mlTaker07': 'https://open.larksuite.com/open-apis/bot/v2/hook/e489fb18-9f5c-4a5d-9347-d84d6fe4f2dc',
        'dualExchange': 'https://open.larksuite.com/open-apis/bot/v2/hook/b6499515-2c29-4b85-81c2-89b599f0d9dc',
    }
    if method in larkDic:
        url = larkDic.get(method)
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
        headers = {"Content-Type": "application/json ;charset=utf-8 "}
        msg = {"msg_type": "text",
               "content": {"text": content}
            }    # 飞书
        try:
            requests.post(url, headers=headers, data=json.dumps(msg))
        except:
            print(f'飞书报错 {traceback.format_exc()}')
        return



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
        # url = 'https://oapi.dingtalk.com/robot/send?access_token=49e5307691a4979c4ed0edb91e394f828167d07019512216d0c6db0b556e01d0'
        url = 'https://oapi.dingtalk.com/robot/send?access_token=8bda6375209d29ef9dc704fe75990743a007670dd23bd9107f8c12a83854c8c6'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='adl':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=8e393755a70186b9771337754bf428f78c79efa96f758604f3d199b65f5955da'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='fakeIncreVol':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=bc34ae6cc2702df56bbaec25503cf17d012ad46805fddf20f8d5faa8d6fa456e'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='hedge':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=42ebddc7eb940cd8e3644328d7559919c83e1911683ebe7bc6fee6fe7b0e2285'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n" 
    elif method=='etp':
        url ='https://oapi.dingtalk.com/robot/send?access_token=e62c3cee667ec88a56d79374d26903a089438c306a9bef7140eeeda7c7fa7662'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='margin':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=a41bfb800bddc11dfb84d4777903fdf222601a4362e8f73c87c1ea8e562daac6'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='stop':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=81b4276642842a6eea4fcb11e881a9ef12fa787d8085ba8f15ef3da7463c2c71'
        content = f"==={timestamp()} 策略报错 {contractSymbol}===\n{content}\n"
    elif method=='basis':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=a3050105da2f19314947c5bcbd2fd7f4f87d6070d46e415ed65f9927125abe52'
        content = f"==={timestamp()} 基差 {contractSymbol}===\n{content}\n"
    elif method == 'arbitrage':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=cc99df4c1db61ff85f920c75484158ec22822a6eca2c822346f778cd49cf733e'
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
    elif method == 'hare':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=1f0be82e1a7454557fb9bf993f7453591b5d40b4076209a026cbac5560232231'
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
    elif method == 'option':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=8f77fb08f9a64441be1c3ee523e98140c1b564a57818684a00f26043d59299de'
        content = f"==={timestamp()} 期权报警 {contractSymbol}===\n{content}\n"
    elif method == 'deribit':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=dea095af534e14bdb5ee2297138ff98818ab311e9bc8aa586fb7f29318558776'
        content = f"==={timestamp()} deribit {contractSymbol}===\n{content}\n"
    elif method == 'my':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=b9854dee6cb1e7b1e2d448f38b67843a1658b472c54ec93c9146b7d957126822'
        content = f"==={timestamp()} 我的策略报警 {contractSymbol}===\n{content}\n"
    elif method == 'coinStoreUsdtSwap':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=bfda41fe95e6bb2278d07f91b19c334b55e0516ff8a835a0bb8c5cb248090239'
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
    elif method == 'dataBase':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=ee42f7d471daf27873cbc16b4517478dfe8ecc665ee5f320c62d85d92955770c'
        content = f"==={timestamp()} 提示 ===\n{content}\n"
    elif method == 'arbitrage02':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=e8f3ec0a0767ad088ff548ceb866c3119805238e89baa9fccf8a88c2490ee343'
        content = f"==={timestamp()} 提示 ===\n{content}\n"
    elif method == 'arbitrage06':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=4460ff09dc23bf01b39d3d5d418fd8a6f0d9c789eb449f3a5019e5b166a8b062'
        content = f"==={timestamp()} 提示 ===\n{content}\n"
    elif method == 'makerMonitor':
        url = 'https://oapi.dingtalk.com/robot/send?access_token=05b241ebc17c0a12820ee228c47c92cfd88b3c204083ebae30e6ceed722cbbac'
        content = f"==={timestamp()} 提示 {contractSymbol}===\n{content}\n"
    headers = {"Content-Type": "application/json ;charset=utf-8 "}
    print(content)
    msg = {'msgtype': 'text',
           'text': {'content': content}}
    try:
        requests.post(url, headers=headers, data=json.dumps(msg))
    except:
        print(f'钉钉报错 {traceback.format_exc()}')

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

# def warningCall(mobiles=['15210166821','18981142505']):
#     # mobiles = ['18981142505','15210166821','15832260052','13811286063']
#     # mobiles = ['15210166821','18981142505']
#     # mobiles = ['18981142505','15210166821']
#     host = 'http://yuyintz.market.alicloudapi.com'
#     path = '/ts/voiceNotifySms'
#     # appcode = '6d47356ceff2477f95f30cefa6572b50'
#     appcode = '10a0b810017c4cd798dfc2500231772b'
#     for m in mobiles:
#         params = {'mobile': m, 'tpl_id': 'TP18040813'}
#         querys = urllib.parse.urlencode(params)
#         # print(querys)
#         url = f'{host}{path}?{querys}'
#         headers = {'Authorization': f'APPCODE {appcode}'}
#         try:
#             res = requests.post(url, headers=headers)
#             print(res)
#         except:
#             print('电话报警失败')

def warningCall(content, number):
    keys = {
        '18981142505': '56578358-a58e-4952-96c4-5176945e7dcc',
        '18810925011': '453c978b-db1e-4c2c-9f94-c04bcc0fd46e',
        '15210166821': '9a0032f1-4b02-4b03-8137-6b9e5c31e70a',

    }
    key = keys.get(str(number), keys['15210166821'])
    if key == '9a0032f1-4b02-4b03-8137-6b9e5c31e70a':
        url = (f'http://api.aiops.com/alert/api/event?app=9a0032f1-4b02-4b03-8137-6b9e5c31e70a&'
               f'eventType=trigger&priority=2&eventId={str(int(time.time()))}&alarmContent={str(content)}异常')
        res = requests.post(url=url)
    else:
        res = requests.post(url=f"http://api.aiops.com/alert/api/event?app={key}&eventType=trigger&alarmName="+str(content)+"异常&eventId="
                      +str(int(time.time()))+"&alarmContent=停机")
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
    return np.round(np.round(number, length),length)


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

def getHead():
    head = \
            """
            <head>
                <meta charset="utf-8">
                <STYLE TYPE="text/css" MEDIA=screen>

                    table.dataframe {
                        border-collapse: collapse;
                        border: 2px solid #a19da2;
                        /*居中显示整个表格*/
                        margin: auto;
                    }

                    table.dataframe thead {
                        border: 2px solid #91c6e1;
                        background: #f1f1f1;
                        padding: 10px 10px 10px 10px;
                        color: #333333;
                    }

                    table.dataframe tbody {
                        border: 2px solid #91c6e1;
                        padding: 10px 10px 10px 10px;
                    }

                    table.dataframe tr {

                    }

                    table.dataframe th {
                        vertical-align: top;
                        font-size: 14px;
                        padding: 10px 10px 10px 10px;
                        color: #105de3;
                        font-family: arial;
                        text-align: center;
                    }

                    table.dataframe td {
                        text-align: center;
                        padding: 10px 10px 10px 10px;
                    }

                    body {
                        font-family: 宋体;
                    }

                    h1 {
                        color: #5db446
                    }

                    div.header h2 {
                        color: #0002e3;
                        font-family: 黑体;
                    }

                    div.content h2 {
                        text-align: center;
                        font-size: 28px;
                        text-shadow: 2px 2px 1px #de4040;
                        color: #fff;
                        font-weight: bold;
                        background-color: #008eb7;
                        line-height: 1.5;
                        margin: 20px 0;
                        box-shadow: 10px 10px 5px #888888;
                        border-radius: 5px;
                    }

                    h3 {
                        font-size: 22px;
                        background-color: rgba(0, 2, 227, 0.71);
                        text-shadow: 2px 2px 1px #de4040;
                        color: rgba(239, 241, 234, 0.99);
                        line-height: 1.5;
                    }

                    h4 {
                        color: #e10092;
                        font-family: 楷体;
                        font-size: 20px;
                        text-align: center;
                    }

                    td img {
                        /*width: 60px;*/
                        max-width: 300px;
                        max-height: 300px;
                    }

                </STYLE>
            </head>
            """
    return head


def getBody(df):
    df_html = df.to_html(escape=False)
    body = \
            """
            <body>
            <hr>

            <div class="content">
                <!--正文内容-->
                <h2> </h2>

                <div>
                    <h4></h4>
                    {df_html}

                </div>
                <hr>

                <p style="text-align: center">

                </p>
            </div>
            </body>
            """.format(df_html=df_html)
    return body
    
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
    elif style == 'img':
        if isinstance(content, list):
            for i in content:
                img = MIMEImage(i)
                img.add_header('Content-ID', 'imageid')
                message.attach(img)
        else:
            img = MIMEImage(content)
            img.add_header('Content-ID', 'imageid')
            message.attach(img)


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
    # def __init__(self,host='10.223.0.169',port=6379):
    def __init__(self,host='10.57.7.241',port=6379):
        pool = redis.ConnectionPool(host=host,port=port,decode_responses=True)
        self.client = redis.Redis(connection_pool=pool)
        print(pool)
        print(self.client)

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

    def __init__(self, fileName=None, sizeMB=50, backupNum=3):
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
        content = f"== {timestamp(strFormat='%Y-%m-%d %H:%M:%S.%f')} {funcName}== | {content}"
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

class KafkaNew():
    topicDict = {
        # 'usdtSwap': 'wbf_match_position',
        # 'coins': 'full_match_position',
        # 'coinSwap': 'coin_match_position',
        'coinTRUsdtSwap': {
            'topic': 'prd.market-swap.clearing-result',
            'config': dict(
                auto_offset_reset='earliest',
                sasl_mechanism="SCRAM-SHA-256",
                security_protocol='SASL_PLAINTEXT',
                sasl_plain_username="trading-user",
                sasl_plain_password="RPKCWZgyseTvfw==",
                bootstrap_servers="trading-kafka-01:19092,trading-kafka-02:19093,trading-kafka-03:19094",
                enable_auto_commit='False'
            )
        },
        'cointrSpot': {
            'topic': 'prd.market-spot.clearing-result',
            'config': dict(
                auto_offset_reset='earliest',
                sasl_mechanism="SCRAM-SHA-256",
                security_protocol='SASL_PLAINTEXT',
                sasl_plain_username="trading-user",
                sasl_plain_password="RPKCWZgyseTvfw==",
                bootstrap_servers="trading-kafka-01:19092,trading-kafka-02:19093,trading-kafka-03:19094",
                enable_auto_commit='False'
            )
        }
    }

    def __init__(self, topic, **kwargs):
        from kafka3 import KafkaConsumer, TopicPartition
        topic = self.topicDict[topic]
        config = topic['config']
        config.update(kwargs)
        self.consumer = KafkaConsumer(
            **config
        )

        self.tp = TopicPartition(topic['topic'], 0)
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
            message = [message.offset, eval(str(message.value, encoding='utf-8'))]
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
    # process.start(
    # warning('test', method='dualExchange')
    # print(warningCall('测试', 15210166821))
    # 15210166821
    re = Redis()
    re.set('text',1)
