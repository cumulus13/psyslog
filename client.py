from __future__ import print_function
import SocketServer
from make_colors import make_colors
import traceback
import socket
import sys
import os
import time
PID = os.getpid()
from pydebugger.debug import debug
HOST = ''
PORT = ''

import psyslog
p = psyslog.Psyslog()
debug(dir_p = dir(p))

SERVER_HOST = p.HOST or '127.0.0.1'
SERVER_PORT = p.PORT or 1514
if SERVER_PORT: SERVER_PORT = int(SERVER_PORT)
if SERVER_HOST == '0.0.0.0': SERVER_HOST = '127.0.0.1'

CLIENT_HOST = ''
CLIENT_PORT = ''
CLIENT_HOST = p.read_config('CLIENT', 'host', value='0.0.0.0') or '0.0.0.0'
CLIENT_PORT = p.read_config('CLIENT', 'port', value= '516') or 516
LINE_NUMBER = 1
PID = os.getpid()
FOREGROUND = False

class MyUDPHandler(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    def generator(self, data, server_address, socket):
        yield socket.sendto(data, server_address)

    def handle(self):
        global CLIENT_HOSTHOST
        global CLIENT_HOSTPORT
        global LINE_NUMBER
        global FOREGROUND
        data = self.request[0].strip()
        debug(data = data)
        socket = self.request[1]
        # print "{} wrote:".format(self.client_address[0])
        # print data
        server_address = (SERVER_HOST, SERVER_PORT)
        debug(self_client_address = self.client_address)
        debug(data = data)
        data, LINE_NUMBER = p.handle(data, self.client_address)
        #socket.sendto(data, server_address)
        for i in self.generator(data, server_address, socket):
            pass
        LINE_NUMBER += 1
        if FOREGROUND: print (str(LINE_NUMBER) + "@" + data.unicode('utf-8'))

def check_open_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('0.0.0.0', int(port)))
        sock.settimeout(0)
        # print "SOCK OPEN"
        return True
    except:
        return False
        # print "SOCK CLOSED"

def main(rebind=False, host = None, port = None, server_port = None):
    global CLIENT_HOST
    global CLIENT_PORT
    global SERVER_PORT
    if server_port:
        SERVER_PORT = server_port
    global PID
    if not host:
        host = CLIENT_HOST
    if not port:
        port = int(CLIENT_PORT)
    if rebind:
        print ("Syslog Client (%s) Bind: %s:%s [%s]" %(make_colors('Re', 'white', 'lightred'), make_colors(host, 'green'), make_colors(str(port), 'cyan'), PID))
    else:
        print ("Syslog Client Bind: %s:%s [%s]" %(make_colors(host, 'green'), make_colors(str(port), 'cyan'), PID))

    server = SocketServer.UDPServer((host, port), MyUDPHandler)
    server.serve_forever()

def monitor(host = '0.0.0.0', port=516, server_port = 1514, foreground = False):
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
                    main(is_rebind, host, port, server_port)
                except:
                    traceback.format_exc()
                    is_rebind = True
                    port = int(port) + 1
                    pass
            else:
                is_rebind = True
                time.sleep(1)
        except:
            is_rebind = True
            error = traceback.format_exc()
            print ("ERROR:", error)
            pass
                
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