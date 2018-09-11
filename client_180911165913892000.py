import socket
from make_colors import make_colors
import traceback
import sys
import os
PID = os.getpid()
from debug import debug
import psyslog

def client(host='0.0.0.0', port=514, server_port=1514):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    p = psyslog.Psyslog()
    try:
        sock.bind((host, port))
        print "Syslog Client Bind: %s:%s [%s]" %(make_colors(host, 'green'), make_colors(str(port), 'cyan'), PID)
        while 1:
            data, client_address = sock.recvfrom(65565)
            if data:
                if data == 'EXIT':
                    sys.exit('server shutdown ....')
                data = p.handle(data, client_address)
                sock.sendto(data, ('127.0.0.1', server_port))
    except:
        ERROR = traceback.format_exc()
        debug(ERROR)
        #print "Closing .. by system"
        #print make_colors('SYSTEM EXIT !', 'white', 'lightred', attrs= ['blink'])
        #sock.close()
        #sys.exit('SYSTEM EXIT !')
        
if __name__ == '__main__':
    client()