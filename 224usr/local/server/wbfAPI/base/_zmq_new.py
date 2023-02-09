import zmq
import sys
import pickle
import traceback
import time


class ZMQ():

    def __init__(self, method, port=1234):
        getattr(self, method)(port)

    def REP(self, port=1234):
        socket = zmq.Context().socket(zmq.REP)
        socket.connect(f'tcp://localhost:{port}')
        socket.setsockopt(zmq.SNDTIMEO, 3000)
        socket.setsockopt(zmq.LINGER, 0)  # 关闭后所有未发送消息丢弃
        print('==== Build ZMQ Response Server Successfully ====')
        self.socket = socket

    def REQ(self, port):
        socket = zmq.Context().socket(zmq.REQ)
        socket.connect(f'tcp://localhost:{port}')
        socket.setsockopt(zmq.RCVTIMEO, 3000)
        socket.setsockopt(zmq.LINGER, 0)  # 关闭后所有未发送消息丢弃
        print('==== Connect ZMQ Request Server Successfully ====')
        self.socket = socket

    def PUB(self, port=1234):
        socket = zmq.Context().socket(zmq.PUB)
        socket.bind(f'tcp://*:{port}')
        socket.setsockopt(zmq.LINGER, 0)  # 关闭后所有未发送消息丢弃
        socket.setsockopt(zmq.SNDHWM, 100000*60*31*5)  # 对向外发送的消息设置高水位
        socket.setsockopt(zmq.SNDBUF, 100000*60*31*5)  # 对向外发送的消息设置高水位
        print('==== Build ZMQ Publish Server Successfully ====')
        self.socket = socket

    def SUB(self, port=1234):
        socket = zmq.Context().socket(zmq.SUB)
        socket.connect(f'tcp://localhost:{port}')
        socket.setsockopt(zmq.LINGER, 0)  # 关闭后所有未发送消息丢弃
        socket.setsockopt(zmq.RCVHWM, 100000*60*31*5)  # 对进入socket的消息设置高水位
        socket.setsockopt(zmq.RCVBUF, 100000*60*31*5)  # 对进入socket的消息设置高水位
        print('==== Build ZMQ Subscribe Server Successfully ====')
        self.socket = socket

    def request(self, content):
        """request REQ

        Args:
            content (TYPE): 请求字段

        Returns:
            TYPE: 回报内容
        """
        self.socket.send(pickle.dumps(content))
        return pickle.loads(self.socket.recv())

    def listen(self, rsp):
        """REP监听模式
        """
        socket = self.socket
        while 1:
            try:
                info = pickle.loads(socket.recv())
                data = rsp(info)
                socket.send(pickle.dumps(data))
            except:
                socket.send(pickle.dumps(traceback.format_exc()))
                continue
    
    def publish(self, content, topic=''):
        """[发布]

        Args:
            # topic ([str]): [内容头]
            content ([type]): [发送内容]
        """
        # print(pickle.dumps(content))
        # print('123'.encode('utf-8'))
        # print(f"{topic}|{content}")
        # while 1:
            # content = [time.time()*1000]*200
        self.socket.send_string(f"{topic}|{pickle.dumps(content)}")
            # time.sleep(1)
        # self.socket.send(content.encode('utf-8'))
    
    def subscribe(self, topic='', on_msg=None, on_err=None):
        """[接收]

        Args:
            rsp ([type]): [rsp function]
        """        
        socket = self.socket
        socket.setsockopt(zmq.SUBSCRIBE, topic.encode('utf-8'))
        while 1:
            # content = socket.recv_string()
            content = pickle.loads(eval(socket.recv_string().split(f'{topic}|')[-1]))
            try:
                if on_msg:
                    on_msg(content)
                else:
                    print(content)
            except:
                if on_err:
                    on_err(content)
                else:
                    print(traceback.format_exc())

             
if __name__ == '__main__':
    # task = ZMQ('PUB')
    # task.publish('123', topic='test')
    task = ZMQ('PUB', port=1234)
    task.socket.close()
    task = ZMQ('PUB', port=1234)
    # task.subscribe(topic='test')
    