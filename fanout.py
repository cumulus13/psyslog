#!/usr/bin/env python3

import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback
import pika
from datetime import datetime
from make_colors import make_colors
from datetime import datetime
import os
from configset import configset
import json
import argparse
import shutil
from pydebugger.debug import debug
import tenacity

print("PID:", os.getpid())

class Fanout(object):

    CONFIGNAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cust_fanout.ini')
    CONFIG = configset(CONFIGNAME)
    CURRENT_HEIGHT = 0
    TERM_SIZE = shutil.get_terminal_size()
    AUTO_CLEAR = False

    @classmethod
    def set_color(self, level):
        if 'emerg' in 'emerge' in str(level):
            return "EMERGE", self.CONFIG.get_config('LEVEL_EMERGENCY', 'fore', value='white'), self.CONFIG.get_config('LEVEL_EMERGENCY', 'back', value='magenta')
        elif 'aler' in str(level):
            return "ALERT", self.CONFIG.get_config('LEVEL_ALERT', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ALERT', 'back', value='blue')
        elif 'crit' in str(level):
            return "CRITI", self.CONFIG.get_config('LEVEL_CRITICAL', 'fore', value='black'), self.CONFIG.get_config('LEVEL_CRITICAL', 'back', value='green')
        elif 'err' in str(level):
            return "ERROR", self.CONFIG.get_config('LEVEL_ERROR', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ERROR', 'back', value='red')
        elif 'warn' in str(level):
            return "WARNI", self.CONFIG.get_config('LEVEL_WARNING', 'fore', value='black'), self.CONFIG.get_config('LEVEL_WARNING', 'back', value='yellow')
        elif 'not' in str(level):
            return "NOTIC", self.CONFIG.get_config('LEVEL_NOTICE', 'fore', value='black'), self.CONFIG.get_config('LEVEL_NOTICE', 'back', value='cyan')
        elif 'inf' in str(level):
            return "INFO",  self.CONFIG.get_config('LEVEL_INFO', 'fore', value='green'), self.CONFIG.get_config('LEVEL_INFO', 'back', value='black')
        elif 'deb' in str(level):
            return "DEBUG", self.CONFIG.get_config('LEVEL_DEBUG', 'fore', value='yellow'), self.CONFIG.get_config('LEVEL_DEBUG', 'back', value='black')
        else:
            return "UNKNOWN", self.CONFIG.get_config('LEVEL_UNKNOWN', 'fore', value='red'), self.CONFIG.get_config('LEVEL_UNKNOWN', 'back', value='white')

    @classmethod
    def call_back(self, ch, met, prop, body):
        #print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
        debug(body = body)
        try:
            data = json.loads(body)
        except:
            data = body.decode() if hasattr(body, 'decode') else body
        debug(body = body)
        debug(data = data)
        if self.AUTO_CLEAR:
            if shutil.get_terminal_size().lines < self.CURRENT_HEIGHT:
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                self.TERM_SIZE = shutil.get_terminal_size()
                self.CURRENT_HEIGHT = 0
        else:
            self.CURRENT_HEIGHT += 1

        def get_date():
            try:
                data1 = make_colors(datetime.strftime(datetime.fromisoformat(data.get('timestamp')), '%Y/%m/%d %H:%M:%S:%f'), 'lc') if isinstance(data, dict) else make_colors(datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), 'lc')
            except:
                data1 = make_colors(datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), 'lc')
            return data1
        
        debug(data = data)
        # debug(data_get_message = data.get('message'))
        if isinstance(data, dict) and data.get('appname'):
            print(
                make_colors(str(self.CURRENT_HEIGHT).zfill(2), 'lw', 'bl') + " " + \
                get_date() + \
                (" [" + make_colors(*self.set_color(data.get('severity'))) + "] ") if isinstance(data, dict) else ''  + \
                (make_colors(data.get('facility'), 'lm') + " ") if isinstance(data, dict) else '' + \
                (make_colors(data.get('ip'), 'ly') + " ") if isinstance(data, dict) else '' + \
                (make_colors(data.get('hostname'), 'lg') + " ") if isinstance(data, dict) else '' + \
                (make_colors(data.get('appname'), 'b', 'y') + " ") if isinstance(data, dict) else '' + \
                make_colors(data.get('message'), 'lc') if isinstance(data, dict) else data.decode() if hasattr(data, 'decode') else data
            )
        else:
            print(
                make_colors(str(self.CURRENT_HEIGHT).zfill(2), 'lw', 'bl') + " " + \
                get_date() + " " + make_colors(data.get('message'), 'lc') if isinstance(data, dict) else data.decode() if hasattr(data, 'decode') else data
            )
        ch.basic_ack(delivery_tag = met.delivery_tag)

    @classmethod
    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def connection(self, exchange_name, hostname = '127.0.0.1', port = 5672, username = 'guest', password = 'guest'):
        #establish connection to RabbitMQ
        #credentials = pika.PlainCredentials('root', 'Xxxnuxer')
        # parameters = pika.ConnectionParameters(host='192.168.0.9', port = 5672, credentials=credentials)
        #parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
        username = self.CONFIG.get_config('AUTH', 'username') or username
        password = self.CONFIG.get_config('AUTH', 'password') or password
        host = self.CONFIG.get_config('AUTH', 'host') or hostname
        password = self.CONFIG.get_config('AUTH', 'password') or password
        port = int(self.CONFIG.get_config('AUTH', 'port') or port or 5672)
        parameters = pika.URLParameters('amqp://{}:{}@{}:{}/%2F'.format(username, password, hostname, port))

        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        #create a queue to send messages
        #channel.queue_declare(queue='syslog', durable=True)
        channel.exchange_declare(exchange = exchange_name, exchange_type=self.CONFIG.get_config('GENERAL', 'exchange_type') or 'fanout', durable=self.CONFIG.get_config('GENERAL', 'durable') or True, auto_delete=self.CONFIG.get_config('GENERAL', 'auto_delete') or False)

        result = channel.queue_declare(queue='', exclusive=self.CONFIG.get_config('GENERAL', 'exclusive') or True)
        queue_name = result.method.queue
        channel.queue_bind(exchange = exchange_name, queue = queue_name)
        return channel, queue_name, conn

    @classmethod
    def main(self, exchange_name, call_back, hostname = '127.0.0.1', port = 5672, username = 'guest', password = 'guest'):
        username = self.CONFIG.get_config('AUTH', 'username') or username
        password = self.CONFIG.get_config('AUTH', 'password') or password
        host = self.CONFIG.get_config('AUTH', 'host') or hostname
        port = int(self.CONFIG.get_config('AUTH', 'port') or port or 5672)

        debug(username = username)
        debug(password = password)
        debug(host = host)
        debug(port = port)

        channel, queue_name,conn = self.connection(exchange_name, host, port, username, password)
        channel.basic_consume(queue = queue_name, on_message_callback = call_back, consumer_tag=self.CONFIG.get_config('GENERAL', 'consumer_tag') or 'all', auto_ack = self.CONFIG.get_config('GENERAL', 'auto_ack') or False)
        #channel.basic_recover(requeue = True)
        try:
            while 1:
                try:
                    channel.start_consuming()
                    break
                except KeyboardInterrupt:
                    print("exit ...")
                    break
                except:
                    CTraceback(*sys.exc_info())
        except KeyboardInterrupt:
            print("exit ...")
        except:
            CTraceback(*sys.exc_info())        

        conn.close()

    @classmethod
    def pub(self, message, exchange_name, hostname = '127.0.0.1', port = 5672, username = 'guest', password = 'guest'):
        username = self.CONFIG.get_config('AUTH', 'username') or username
        password = self.CONFIG.get_config('AUTH', 'password') or password
        host = self.CONFIG.get_config('AUTH', 'host') or hostname
        port = int(self.CONFIG.get_config('AUTH', 'port') or port or 5672)

        debug(username = username)
        debug(password = password)
        debug(host = host)
        debug(port = port)
        
        self.CONFIG.get_config('GENERAL', 'exchange_name')

        channel, _,conn = self.connection(exchange_name, hostname, port, username, password)
        channel.basic_publish(exchange_name, '', message)
        conn.close

    @classmethod
    def usage(self):
        parser = argparse.ArgumentParser('fanout')
        parser.add_argument('EXCHANGE')
        parser.add_argument('-H', '--host', help = 'Rabbitmmq Server Host/IP', default = '127.0.0.1')
        parser.add_argument('-P', '--port', help = 'Rabbitmmq Server Port, default: 5672', type = int, default = 5672)
        parser.add_argument('-u', '--username', help = 'Rabbitmq admin/user name', default = 'guest')
        parser.add_argument('-p', '--password', help = 'Rabbitmq password admin/user', default = 'guest')
        parser.add_argument('-a', '--auto-clear', help = 'Auto clear display if full', action = 'store_true')

        cons = parser.add_subparsers()

        parser_cons = cons.add_parser('push')
        parser_cons.add_argument('-m', '--message', help = 'send message')

        if len(sys.argv) == 1:
            parser.print_help()
        else:
            print(f'Terminal height: {self.TERM_SIZE.lines}, Terminal width: {self.TERM_SIZE.columns}')
            args = parser.parse_args()
            if args.auto_clear:
                self.AUTO_CLEAR = True
            if hasattr(args, 'message'):
                self.pub(args.message, args.EXCHANGE, args.host, args.port, args.username, args.password)
            else:
                self.main(args.EXCHANGE, self.call_back, args.host, args.port, args.username, args.password)

if __name__ == '__main__':
    Fanout.usage()
