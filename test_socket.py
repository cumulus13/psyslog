import socket
import socketserver
from datetime import datetime
from pydebugger.debug import debug
import os
import signal
import traceback
from make_colors import make_colors

import importlib
from pathlib import Path

import psyslog
p = psyslog.Psyslog()
CONFIG = p.CONFIG

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

HANDLER = ['rabbitmq']
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 515

class ThreadingUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

class UDPHandler(socketserver.BaseRequestHandler):
    has_sent = False
    def sendto(self, data, server_address, socket): 
        yield socket.sendto(data.encode('utf-8'), server_address)
        
    def sendto_rabbitmq(self, data, raw=False, verbose=False):
        debug("run handler rabbitmq [client]")
        exchange_name = 'psyslog'
        debug(exchange_name=exchange_name, debug=verbose)
        exchange_type = 'fanout'
        debug(exchange_type=exchange_type, debug=verbose)
        queue = 'q_psyslog'
        debug(queue=queue, debug=verbose)
        durable = True
        debug(durable=durable, debug=verbose)
        auto_delete = False
        debug(auto_delete=auto_delete, debug=verbose)
        routing_key = 'syslog.all'
        debug(routing_key=routing_key, debug=verbose)
        delivery_mode = False
        debug(delivery_mode=delivery_mode, debug=verbose)
        vhost = 'psyslog'
        debug(vhost=vhost, debug=verbose)
        exclusive = False
        debug(exclusive=exclusive, debug=verbose)
        auto_ack = False
        debug(auto_ack=auto_ack, debug=verbose)
        hostname = '192.168.100.2'
        debug(hostname=hostname, debug=verbose)
        port = 5672
        debug(port=port, debug=verbose)
        username = 'root'
        debug(username=username, debug=verbose)
        password = 'root'
        debug(password=password, debug=verbose)
        verbose = verbose

        RabbitMQHandler.send(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue, auto_ack, routing_key, vhost, raw, None, CONFIG, verbose=False)

        if raw:
            exchange_name = f"{exchange_name}_raw"
            RabbitMQHandler.send(data.encode('utf-8') if not isinstance(data, bytes) else data, exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue, auto_ack, routing_key, vhost, raw, None, CONFIG, verbose=False)

    def handle(self):
        debug("run handle ...")
        data = self.request[0].strip()
        debug(data=data, debug=1)
        server_address = (SERVER_HOST, SERVER_PORT)
        for hand in HANDLER:
            debug(hand=hand)
            if hand in ['rabbit', 'rabbitmq']:
                debug("handler is RABBITMQ ...")
                self.sendto_rabbitmq(data)
            elif hand == 'socket' or hand == '':
                debug("handler is SOCKET ...")
                for _ in self.sendto(data, server_address, socket):
                    pass

def main():
    print(f"Syslog Client Bind: {make_colors('127.0.0.1', 'b', 'y')}:{make_colors(str(515), 'b', 'lc')} [{make_colors(str(os.getpid()), 'lw', 'm')}]")
    try:
        server = ThreadingUDPServer(('127.0.0.1', 515), UDPHandler)
        debug(server=server)
        server.serve_forever()
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGTERM)
    except:
        print(traceback.format_exc())
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == '__main__':
    main()
