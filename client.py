#!/usr/bin/python
#Author: cumulus13
#Email: cumulus13@gmail.com
#Syslog Client (Receive & Processing & Forward to Server) Receive then forward to Server

from __future__ import print_function
import socketserver
from make_colors import make_colors
import traceback
import socket
import sys
import re
import signal
import os
import time
from pydebugger.debug import debug
import psyslog

PID = os.getpid()
HOST = ''
PORT = ''

p = psyslog.Psyslog()
SERVER_HOST = p.HOST or '127.0.0.1'
SERVER_PORT = p.PORT or 1514
if SERVER_PORT: SERVER_PORT = int(SERVER_PORT)
if SERVER_HOST == '0.0.0.0': SERVER_HOST = '127.0.0.1'

CLIENT_HOST = p.read_config('CLIENT', 'host', value='0.0.0.0') or '0.0.0.0'
CLIENT_PORT = p.read_config('CLIENT', 'port', value= '516') or 516
LINE_NUMBER = 1
PID = os.getpid()
FOREGROUND = False

class Server(socketserver.UDPServer):
    allow_reuse_address = True

class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    SOCKET = None
    
    def generator(self, data, server_address, socket):
        debug(data=data)
        debug(server_address=server_address)
        yield socket.sendto(data.encode('utf-8'), server_address)

    def handle(self):
        global CLIENT_HOST
        global CLIENT_PORT
        global SERVER_HOST
        global SERVER_PORT
        global LINE_NUMBER
        global FOREGROUND
        debug(self_request = self.request)
        data = self.request[0].strip()
        debug(data = data)
        socket = self.request[1]
        self.SOCKET = socket
        
        # print "{} wrote:".format(self.client_address[0])
        # print data
        debug(self_client_address = self.client_address)
        debug(data = data)
        data, LINE_NUMBER = p.handle(data, self.client_address)
        
        #server_address = (SERVER_HOST, SERVER_PORT)
        if isinstance(SERVER_HOST, list) and isinstance(SERVER_PORT, list):
            for s in SERVER_HOST:
                for po in SERVER_PORT:
                    server_address = (s, po)
                    debug(server_address = server_address)
                    self.server_address = server_address
                    
                    #socket.sendto(data, server_address)
                    data_client_ip = re.findall(r'Original Address=(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', data.decode('utf-8'))
                    debug(data_client_ip=data_client_ip)
                    if data_client_ip:
                        data = re.sub(r'Original Address=\d{0,3}\.\d{0,3}\.\d{0,0}\.\d{0,3}\.\d{0,3}', f'Original Address={self.client_address[0]}', data.decode('utf-8'))
                        debug(data=data)
                    else:
                        data = f"Original Address={self.client_address[0]}" + data.decode('utf-8')
                    for i in self.generator(data, server_address, socket):
                        pass
        elif not isinstance(SERVER_HOST, list) and isinstance(SERVER_PORT, list):
            for po in SERVER_PORT:
                server_address = (SERVER_HOST, po)
                debug(server_address = server_address)
                self.server_address = server_address
                
                #socket.sendto(data, server_address)
                data_client_ip = re.findall(r'Original Address=(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', data.decode() if hasattr(data, 'decode') else data)
                debug(data_client_ip=data_client_ip)
                if data_client_ip:
                    data = re.sub(r'Original Address=\d{0,3}\.\d{0,3}\.\d{0,0}\.\d{0,3}\.\d{0,3}', f'Original Address={self.client_address[0]}', data.decode('utf-8'))
                    debug(data=data)
                else:
                    data = f"Original Address={self.client_address[0]}" + data.decode() if hasattr(data, 'decode') else data
                for i in self.generator(data, server_address, socket):
                    pass
        else:
            if not isinstance(SERVER_HOST, list): SERVER_HOST = [SERVER_HOST]
            if not isinstance(SERVER_PORT, list): SERVER_PORT = [SERVER_PORT]
            if len(SERVER_PORT) < len(SERVER_HOST):
                SERVER_PORT.append(SERVER_PORT[0])
            for i in SERVER_HOST:
                server_address = (i, SERVER_PORT[SERVER_HOST.index(i)])
                data, LINE_NUMBER = p.handle(data, self.client_address)
                for _ in self.generator(data, server_address, socket):
                    pass
        LINE_NUMBER += 1
        if FOREGROUND:
            print(f"{LINE_NUMBER}@{data}")

udphandle = MyUDPHandler

def check_open_port(port):
    debug(port = port)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('0.0.0.0', int(port)))
        sock.settimeout(0)
        # print "SOCK OPEN"
        return True
    except:
        print(traceback.format_exc())
        return False

def main(rebind=False, host = None, port = None, server_port = None, this_udphandle = None):
    global CLIENT_HOST
    global CLIENT_PORT
    global SERVER_PORT
    if server_port: SERVER_PORT = server_port
    global PID
    if not host: host = CLIENT_HOST
    if not port: port = int(CLIENT_PORT)
    if rebind:
        print(f"Syslog Client ({make_colors('Re', 'lw', 'r')}) Bind: {make_colors(host, 'lw', 'm')}:{make_colors(str(port), 'lw', 'bl')} [{make_colors(str(PID), 'b', 'y')}]")
    else:
        print(f"Syslog Client Bind: {make_colors(host, 'b', 'y')}:{make_colors(str(port), 'b', 'lc')} [{make_colors(str(PID), 'lw', 'm')}]")
    
    udphandle = this_udphandle or udphandle
    try:
        #server = SocketServer.UDPServer((host, port), udphandle)
        server = Server((host, port), udphandle)
        server.serve_forever()
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGTERM)
    except:
        print(traceback.format_exc())
        os.kill(os.getpid(), signal.SIGTERM)

def monitor(host=None, port=None, server_port=None, foreground=False, udphandle=None):
    udphandle = udphandle or MyUDPHandler
    host = host or '0.0.0.0'
    port = port or 514
    server_port = server_port or 1514
    debug(host = host)
    debug(port = port)
    debug(server_port = server_port)
    debug(foreground = foreground)
    global FOREGROUND
    FOREGROUND = foreground
    is_rebind = False
    port = int(port)
    while 1:
        try:
            if check_open_port(port):
                try:
                    main(is_rebind, host, port, server_port, udphandle)
                except:
                    print(traceback.format_exc())
                    #is_rebind = True
                    #port = int(port) + 1
                    pass
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
    # server = SocketServer.UDPServer((CLIENT_HOST, CLIENT_PORT), MyUDPHandler)
    # server.serve_forever()
    # check_open_port(sys.argv[1])

#if __name__ == '__main__':
    #client()
