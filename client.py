#!/usr/bin/python
#Author: cumulus13
#Email: cumulus13@gmail.com
#Syslog Client (Receive & Processing & Forward to Server) Receive then forward to Server

from __future__ import print_function
import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback
import socketserver
from make_colors import make_colors
from rich.text import Text
from ctraceback.custom_traceback import console
import traceback
import socket
import re
import signal
import os
import time
from pydebugger.debug import debug
from datetime import datetime
import psyslog
import importlib
try:
    from .handler.RABBITMQ import RabbitMQHandler
except Exception:
    try:
        from handler.RABBITMQ import RabbitMQHandler
    except Exception:
        spec_handler_rabbitmq = importlib.util.spec_from_file_location("RABBITMQ", str(Path(__file__).parent / 'handler' / 'RABBITMQ.py'))
        RABBITMQ = importlib.util.module_from_spec(spec_handler_rabbitmq)
        spec_handler_rabbitmq.loader.exec_module(RABBITMQ)
        RabbitMQHandler = RABBITMQ.RabbitMQHandler

PID = os.getpid()
HOST = ''
PORT = ''

p = psyslog.Psyslog()
CONFIG = p.CONFIG
SERVER_HOST = p.HOST or '127.0.0.1'
SERVER_PORT = p.PORT or 1514
if SERVER_PORT: SERVER_PORT = int(SERVER_PORT)
if SERVER_HOST == '0.0.0.0': SERVER_HOST = '127.0.0.1'

CLIENT_HOST = CONFIG.get_config('CLIENT', 'host', value='0.0.0.0') or '0.0.0.0'
CLIENT_PORT = CONFIG.get_config('CLIENT', 'port', value= '516') or 516
LINE_NUMBER = 1
PID = os.getpid()
FOREGROUND = False
HANDLER = CONFIG.get_config('SERVER', 'handle') or 'socket'
NC = 0

RABBITMQ_TAG = 'all'
RABBITMQ_HOST = '192.168.100.2'
RABBITMQ_PORT = 5672
RABBITMQ_USERNAME = 'root'
RABBITMQ_PASSWORD = 'root'
RABBITMQ_VHOST = '/'
RABBITMQ_EXCHANGE = 'syslog'
RABBITMQ_EXCHANGE_TYPE = 'fanout'
RABBITMQ_ROUTING_KEY = 'syslog.all'
RABBITMQ_DURABLE = True
RABBITMQ_DELIVERY_MODE = 2 
RABBITMQ_AUTO_DELETE = False
RABBITMQ_RAW = 0

class Server(socketserver.UDPServer):
    debug("run Server ...")
    allow_reuse_address = True

class UDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    SOCKET = None
    NCOLOR = {
        0: "white on #AA00FF",
        1: "white on #FF00FF",
        2: "black on #FF5500",
        3: "black on #FFFF00",
        4: "black on #00FFFF",
        5: "white on #0000FF",
        6: "black on #AAFF00",
        7: "white on #005500",
        8: "black on #FFAAFF",
        9: "white on #5500FF"
    }
    
    def sendto(self, data, server_address, socket): 
        yield socket.sendto(data.encode('utf-8'), server_address)
        
    def sendto_rabbitmq(self, data, raw = False):
        
        global RABBITMQ_TAG
        global RABBITMQ_HOST
        global RABBITMQ_PORT
        global RABBITMQ_USERNAME
        global RABBITMQ_PASSWORD
        global RABBITMQ_VHOST
        global RABBITMQ_EXCHANGE
        global RABBITMQ_EXCHANGE_TYPE
        global RABBITMQ_ROUTING_KEY
        global RABBITMQ_DURABLE
        global RABBITMQ_DELIVERY_MODE
        global RABBITMQ_AUTO_DELETE
        global RABBITMQ_RAW
        
        debug("run handler rabbitmq [client]")
        exchange_name = RABBITMQ_EXCHANGE or CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog'
        debug(exchange_name = exchange_name)
        exchange_type = RABBITMQ_EXCHANGE_TYPE or CONFIG.get_config('rabbitmq', 'exchange_type') or 'syslog'
        debug(exchange_type = exchange_type)
        hostname = RABBITMQ_HOST or CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
        debug(hostname = hostname)
        port = RABBITMQ_PORT or CONFIG.get_config('rabbitmq', 'port') or 5672
        debug(port = port)
        username = RABBITMQ_USERNAME or CONFIG.get_config('rabbitmq', 'username') or 'guest'
        debug(username = username)
        password = RABBITMQ_PASSWORD or CONFIG.get_config('rabbitmq', 'password') or 'guest'
        debug(password = password)
        #yield fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password)
        if os.getenv('VERBOSE') == '1':
            debug(raw = raw, debug = 1)
            debug(RABBITMQ_RAW = RABBITMQ_RAW, debug = 1)
        
        if raw or RABBITMQ_RAW:
            exchange_name = f"{exchange_name}_raw"
            if os.getenv('VERBOSE') == '1': debug(exchange_name = exchange_name, debug = 1)
            # fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password, verbose= os.getenv('VERBOSE'), config = CONFIG)        
            RabbitMQHandler.send(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname, port, username, password, exchange_type)
        else:
            fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password, verbose=os.getenv('VERBOSE'), config = CONFIG)        
        
    #NOT USED
    def generator(self, data, server_address, socket, handler = None):
        debug(data=data)
        debug(server_address=server_address)
        debug(handler = handler)
        if handler:
            if handler in ['rabbit', 'rabbitmq'] or CONFIG.get_config('SERVER', 'handle') in ['rabbit', 'rabbitmq']:
                debug("run handler rabbitmq [client]")
                exchange_name = CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog'
                debug(exchange_name = exchange_name)
                hostname = CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
                debug(hostname = hostname)
                port = CONFIG.get_config('rabbitmq', 'port') or 5672
                debug(port = port)
                username = CONFIG.get_config('rabbitmq', 'username') or 'guest'
                debug(username = username)
                password = CONFIG.get_config('rabbitmq', 'password') or 'guest'
                debug(password = password)
                #yield fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password)
                fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password)
            elif handler == 'socket' or handler == '':
                yield socket.sendto(data.encode('utf-8'), server_address)                          
        else:
            yield socket.sendto(data.encode('utf-8'), server_address)
    
    #NOT USED
    def generator1(self, data, server_address, socket, handler = None):
        debug(data=data)
        debug(server_address=server_address)
        debug(handler = handler)
        if handler:
            if not isinstance(handler, list or tuple):
                handler = [handler]
            else:
                handler = list(set(handler))
            
            for hand in handler:
                if hand in ['rabbit', 'rabbitmq'] or CONFIG.get_config('SERVER', 'handle') in ['rabbit', 'rabbitmq']:
                    debug("run handler rabbitmq [client]")
                    exchange_name = CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog'
                    debug(exchange_name = exchange_name)
                    hostname = CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
                    debug(hostname = hostname)
                    port = CONFIG.get_config('rabbitmq', 'port') or 5672
                    debug(port = port)
                    username = CONFIG.get_config('rabbitmq', 'username') or 'guest'
                    debug(username = username)
                    password = CONFIG.get_config('rabbitmq', 'password') or 'guest'
                    debug(password = password)
                    #yield fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password)
                    fanout.Fanout.pub(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname = hostname, port = port, username = username, password = password)
                elif hand == 'socket' or hand == '':
                    #yield socket.sendto(data.encode('utf-8'), server_address)
                    for _ in self.sendto(data, server_address, socket):
                        pass                                        
        else:
            yield socket.sendto(data.encode('utf-8'), server_address)

    def handle(self):
        debug("run handle ...")
        #os.environ.update({'DEBUG': '1',})
        global CLIENT_HOST
        global CLIENT_PORT
        global SERVER_HOST
        global SERVER_PORT
        global LINE_NUMBER
        global FOREGROUND
        global HANDLER
        global NC
        
        console.print(f"[bold #00FFFF]{datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f')}[/]", Text("get message from:", style = self.NCOLOR.get(NC)), f"[bold #FFFF00]{self.client_address[0]}[/]:[bold #00FFFF]{self.client_address[1]}[/]")
        
        if NC >= 9:
            NC = 0
        else:
            NC += 1    
            
        debug(HANDLER = HANDLER)
        debug(self_request = self.request)
        data = self.request[0].strip()
        debug(data = data)
        socket = self.request[1]
        self.SOCKET = socket
        
        # print "{} wrote:".format(self.client_address[0])
        # print data
        debug(self_client_address = self.client_address)
        debug(data = data)
        #data, LINE_NUMBER = p.handle(data, self.client_address)
        #debug(data = data)
        debug(LINE_NUMBER = LINE_NUMBER)
        debug(SERVER_HOST = SERVER_HOST)
        debug(SERVER_PORT = SERVER_PORT)
        #server_address = (SERVER_HOST, SERVER_PORT)
        if isinstance(SERVER_HOST, list) and isinstance(SERVER_PORT, list):
            debug("RUN PROCESS 1")
            for s in list(set(SERVER_HOST)):
                for po in list(set(SERVER_PORT)):
                    server_address = (s, po)
                    debug(server_address = server_address)
                    self.server_address = server_address
                    
                    debug(self_client_address = self.client_address)
                    data, LINE_NUMBER = p.handle(data, self.client_address)
                    debug(HANDLER = HANDLER)
                    
                    if not isinstance(HANDLER, list or tuple):
                        HANDLER = [HANDLER]
                    else:
                        HANDLER = list(set(HANDLER))
                    debug(HANDLER = HANDLER)
                    for hand in HANDLER:
                        debug(hand = hand)
                        if hand in ['rabbit', 'rabbitmq']:
                            debug("handler is RABBITMQ ...")
                            self.sendto_rabbitmq(data)
                            if CONFIG.get_config('rabbitmq', 'raw') in ["1", 1, 'True', 'true', True]:
                                self.sendto_rabbitmq(data_raw, True)
                        elif hand == 'socket' or hand == '':
                            debug("handler is SOCKET ...")
                            #for _ in self.generator(data, server_address, socket, hand):
                            for _ in self.sendto(data, server_address, socket):
                                pass                                        
                    
                    #self.generator(data, server_address, socket, HANDLER)
                    #for _ in self.generator(data, server_address, socket, HANDLER):
                        #pass                    
                    #data_client_ip = re.findall(r'Original Address=(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', data.decode('utf-8'))
                    #debug(data_client_ip=data_client_ip)
                    #if data_client_ip:
                        #data = re.sub(r'Original Address=\d{0,3}\.\d{0,3}\.\d{0,0}\.\d{0,3}\.\d{0,3}', f'Original Address={self.client_address[0]}', data.decode('utf-8'))
                        #debug(data=data)
                    #else:
                        #data = f"Original Address={self.client_address[0]}" + data.decode('utf-8')
                    #debug(HANDLER = HANDLER)
                    #for i in self.generator(data, server_address, socket, HANDLER):
                        #pass
        elif not isinstance(SERVER_HOST, list) and isinstance(SERVER_PORT, list):
            debug("RUN PROCESS 2")
            for po in list(set(SERVER_PORT)):
                server_address = (SERVER_HOST, po)
                debug(server_address = server_address)
                self.server_address = server_address
                
                debug(self_client_address = self.client_address)
                data, LINE_NUMBER = p.handle(data, self.client_address)
                debug(HANDLER = HANDLER)
                
                if not isinstance(HANDLER, list or tuple):
                    HANDLER = [HANDLER]
                    debug(HANDLER = HANDLER)
                else:
                    HANDLER = list(set(HANDLER))
                    debug(HANDLER = HANDLER)
                debug(HANDLER = HANDLER)
                for hand in HANDLER:
                    debug(hand = hand)
                    if hand in ['rabbit', 'rabbitmq']:
                        debug("handler is RABBITMQ ...")
                        self.sendto_rabbitmq(data)
                        if CONFIG.get_config('rabbitmq', 'raw') in ["1", 1, 'True', 'true', True]:
                            self.sendto_rabbitmq(data_raw, True)
                    elif hand == 'socket' or hand == '':
                        debug("handler is SOCKET ...")
                        #for _ in self.generator(data, server_address, socket, hand):
                        for _ in self.sendto(data, server_address, socket):
                            pass                                    
                
                #self.generator(data, server_address, socket, HANDLER)
                #for _ in self.generator(data, server_address, socket, HANDLER):
                    #pass                
                
                #data_client_ip = re.findall(r'Original Address=(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', data.decode() if hasattr(data, 'decode') else data)
                #debug(data_client_ip=data_client_ip)
                #if data_client_ip:
                    #data = re.sub(r'Original Address=\d{0,3}\.\d{0,3}\.\d{0,0}\.\d{0,3}\.\d{0,3}', f'Original Address={self.client_address[0]}', data.decode('utf-8'))
                    #debug(data=data)
                #else:
                    #data = f"Original Address={self.client_address[0]}" + data.decode() if hasattr(data, 'decode') else data
                    #debug(HANDLER = HANDLER)
                #for i in self.generator(data, server_address, socket, HANDLER):
                    #pass
        else:
            debug("RUN PROCESS 3")
            #if not isinstance(SERVER_HOST, list): SERVER_HOST = [SERVER_HOST]
            #if not isinstance(SERVER_PORT, list): SERVER_PORT = [SERVER_PORT]
            #if len(SERVER_PORT) < len(SERVER_HOST): SERVER_PORT.append(SERVER_PORT[0])
            debug(SERVER_HOST = SERVER_HOST)
            debug(SERVER_PORT = SERVER_PORT)
            #for i in SERVER_HOST:
            server_address = (SERVER_HOST, SERVER_PORT)
            debug(server_address = server_address)
            debug(self_client_address = self.client_address)
            data_raw = data
            data, LINE_NUMBER = p.handle(data, self.client_address)
            debug(HANDLER = HANDLER)
            #for _ in self.generator(data, server_address, socket, HANDLER):
                #pass
            if not isinstance(HANDLER, list or tuple):
                HANDLER = [HANDLER]
            else:
                HANDLER = list(set(HANDLER))
            debug(HANDLER = HANDLER)
            for hand in HANDLER:
                debug(hand = hand)
                if hand in ['rabbit', 'rabbitmq']:
                    debug("handler is RABBITMQ ...")
                    self.sendto_rabbitmq(data)
                    if CONFIG.get_config('rabbitmq', 'raw') in ["1", 1, 'True', 'true', True]:
                        self.sendto_rabbitmq(data_raw, True)
                elif hand == 'socket' or hand == '':
                    debug("handler is SOCKET ...")
                    #for _ in self.generator(data, server_address, socket, hand):
                    for _ in self.sendto(data, server_address, socket):
                        pass                    
        LINE_NUMBER += 1
        if FOREGROUND:
            print(f"{LINE_NUMBER}@{data}")

#udphandle = MyUDPUDPHandler

def check_open_port(port):
    debug(port = port)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        debug(f"Try bind 0.0.0.0:{port}")
        sock.bind(('0.0.0.0', int(port)))
        sock.settimeout(0)
        # print "SOCK OPEN"
        debug(f"End Try bind 0.0.0.0:{port}")
        return True
    except:
        print(traceback.format_exc())
        return False

def main(rebind=False, host = None, port = None, server_port = None, handle = None):
    global CLIENT_HOST
    global CLIENT_PORT
    global SERVER_PORT
    global HANDLER
    
    debug(handle = handle)
    if handle: HANDLER = handle
    debug(HANDLER = HANDLER)
    
    debug(server_port = server_port)
    if server_port: SERVER_PORT = server_port
    debug(SERVER_PORT = SERVER_PORT)
    global PID
    if not host: host = CLIENT_HOST
    debug(host = host)
    if not port: port = int(CLIENT_PORT)
    debug(port = port)
    debug(rebind = rebind)
    if rebind:
        print(f"Syslog Client ({make_colors('Re', 'lw', 'r')}) Bind: {make_colors(host, 'lw', 'm')}:{make_colors(str(port), 'lw', 'bl')} [{make_colors(str(PID), 'b', 'y')}]")
    else:
        print(f"Syslog Client Bind: {make_colors(host, 'b', 'y')}:{make_colors(str(port), 'b', 'lc')} [{make_colors(str(PID), 'lw', 'm')}]")
    
    #udphandle = this_udphandle or udphandle
    try:
        #server = SocketServer.UDPServer((host, port), udphandle)
        server = Server((host, port), UDPHandler)
        debug(server = server)
        server.serve_forever()
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGTERM)
    except:
        CTraceback(*sys.exc_info())
        #print(traceback.format_exc())
        os.kill(os.getpid(), signal.SIGTERM)

def monitor(host=None, port=None, server_port=None, foreground=False, handler=None):
    print(f"RAW CONFIG: {CONFIG.get_config('rabbitmq', 'raw')}")    
    print(f"RAW CONFIG is valid ? : {CONFIG.get_config('rabbitmq', 'raw') in ['1', 1, 'True', 'true', True]}")    
    host = host or '0.0.0.0'
    port = port or 514
    server_port = server_port or 1514
    debug(host = host)
    debug(port = port)
    debug(server_port = server_port)
    debug(foreground = foreground)
    global FOREGROUND
    FOREGROUND = foreground
    global HANDLER
    debug(handler = handler)
    handler = handler or CONFIG.get_config('SERVER', 'handle')
    debug(handler = handler)
    HANDLER = handler
    debug(HANDLER = HANDLER)
    is_rebind = False
    port = int(port)
    while 1:
        try:
            if check_open_port(port):
                try:
                    main(is_rebind, host, port, server_port, handler)
                except:
                    CTraceback(*sys.exc_info())
                    #print(traceback.format_exc())
                    #is_rebind = True
                    #port = int(port) + 1
                    #pass
            else:
                #is_rebind = True
                time.sleep(1)
        except:
            #is_rebind = True
            error = traceback.format_exc()
            print ("ERROR:", error)
            os.kill(os.getpid(), signal.SIGTERM)
                
if __name__ == "__main__":
    print ("PID:", PID)
    monitor()
    #HOST, PORT = "localhost", 9999
    
    # print "Syslog Client Bind: %s:%s [%s]" %(make_colors(CLIENT_HOST, 'green'), make_colors(str(CLIENT_PORT), 'cyan'), PID)
    # server = SocketServer.UDPServer((CLIENT_HOST, CLIENT_PORT), MyUDPUDPHandler)
    # server.serve_forever()
    # check_open_port(sys.argv[1])

#if __name__ == '__main__':
    #client()
