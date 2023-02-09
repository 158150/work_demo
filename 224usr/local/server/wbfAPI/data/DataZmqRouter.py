#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import threading
import time
import traceback
import zmq

sys.path.append('/usr/local/server')
from wbfAPI.config._pushServerNew import pushServerDict


class Router(object):

    def __init__(self, port=None):

        if not port:
            self.run_all()
        else:
            self.run_one(port)

    def run_all(self):
        for port, config in pushServerDict.items():
            server_ports = config['server']
            t = threading.Thread(target=self.start, args=(port, server_ports))
            t.start()

    def run_one(self, port):
        config = pushServerDict[port]
        server_ports = config['server']
        t = threading.Thread(target=self.start, args=(port, server_ports))
        t.start()

    def start(self, client_port, server_ports):
        context = zmq.Context()
        f_socket = context.socket(zmq.ROUTER)
        b_socket = context.socket(zmq.DEALER)

        connect = False

        while not connect:
            try:
                # 绑定客户端
                f_socket.bind(f"tcp://*:{client_port}")
                # 绑定服务端
                [b_socket.bind(f"tcp://*:{i}") for i in server_ports]
                connect = True
            except:
                print(traceback.format_exc())
                time.sleep(1)
                continue

        poller = zmq.Poller()
        poller.register(f_socket, zmq.POLLIN)
        poller.register(b_socket, zmq.POLLIN)

        print(f'===== server({"|".join(server_ports)})-client({client_port}) zmq 路由分发,负载均衡准备完毕 =====')

        while 1:
            socks = dict(poller.poll())

            # 处理客户端请求, 转发至服务端
            if socks.get(f_socket) == zmq.POLLIN:
                msg = f_socket.recv_multipart()
                # print('client', msg)
                b_socket.send_multipart(msg)

            # 处理服务端相应, 转发至客户端
            if socks.get(b_socket) == zmq.POLLIN:
                msg = b_socket.recv_multipart()
                # print('server', msg)
                f_socket.send_multipart(msg)


if __name__ == '__main__':
    Router()
