#!/usr/bin/env python3

import pika
import sys
from datetime import datetime
from make_colors import make_colors
from datetime import datetime
import os
from configset import configset
import json
import argparse
import shutil
import re
from pydebugger.debug import debug

print("PID:", os.getpid())

class Fanout(object):

    CONFIGNAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cust_fanout.ini')
    CONFIG = configset(CONFIGNAME)
    CURRENT_HEIGHT = 0
    TERM_SIZE = shutil.get_terminal_size()
    AUTO_CLEAR = False

    @classmethod
    def set_color(self, level):
        if 'emerg' in 'emerge' in str(level).lower():
            return "EMERGE", self.CONFIG.get_config('LEVEL_EMERGENCY', 'fore', value='white'), self.CONFIG.get_config('LEVEL_EMERGENCY', 'back', value='magenta')
        elif 'aler' in str(level).lower():
            return "ALERT", self.CONFIG.get_config('LEVEL_ALERT', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ALERT', 'back', value='blue')
        elif 'crit' in str(level).lower():
            return "CRITI", self.CONFIG.get_config('LEVEL_CRITICAL', 'fore', value='black'), self.CONFIG.get_config('LEVEL_CRITICAL', 'back', value='green')
        elif 'err' in str(level).lower():
            return "ERROR", self.CONFIG.get_config('LEVEL_ERROR', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ERROR', 'back', value='red')
        elif 'warn' in str(level).lower():
            return "WARNI", self.CONFIG.get_config('LEVEL_WARNING', 'fore', value='black'), self.CONFIG.get_config('LEVEL_WARNING', 'back', value='yellow')
        elif 'not' in str(level).lower():
            return "NOTIC", self.CONFIG.get_config('LEVEL_NOTICE', 'fore', value='black'), self.CONFIG.get_config('LEVEL_NOTICE', 'back', value='cyan')
        elif 'inf' in str(level).lower():
            return "INFO",  self.CONFIG.get_config('LEVEL_INFO', 'fore', value='green'), self.CONFIG.get_config('LEVEL_INFO', 'back', value='black')
        elif 'deb' in str(level).lower():
            return "DEBUG", self.CONFIG.get_config('LEVEL_DEBUG', 'fore', value='yellow'), self.CONFIG.get_config('LEVEL_DEBUG', 'back', value='black')
        else:
            return "UNKNOWN", self.CONFIG.get_config('LEVEL_UNKNOWN', 'fore', value='red'), self.CONFIG.get_config('LEVEL_UNKNOWN', 'back', value='white')


    @classmethod
    def call_back(self, ch, met, prop, body):
        #print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
        debug(body = body, debug = 1)
        data = ''
        try:
            data = json.loads(body)
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
            #print(
                #make_colors(str(self.CURRENT_HEIGHT).zfill(2), 'lw', 'bl') + " " + \
                #make_colors(datetime.strftime(datetime.fromtimestamp(data.get('created')), '%Y/%m/%d %H:%M:%S:%f'), 'lc') + " [" + \
                #make_colors(*self.set_color(data.get('levelname'))) + "][" + \
                #make_colors(str(data.get('levelno')), 'lw', 'bl') + "] " + \
                #make_colors(data.get('env'), 'lm') + " " + \
                #make_colors(data.get('source'), 'ly') + " " + \
                #make_colors(data.get('host'), 'lg') + " " + \
                #make_colors(data.get('name'), 'b', 'y') + " " + \
                #make_colors(data.get('message'), 'lc')
            #)
        except:
            try:
                data = body.decode('utf-8')
                data = re.sub("\r\n\r\n", "", data)
                data = re.sub("\r\n|\n", " - ", data)
                print(data)
            except:
                try:
                    data = re.sub("\r\n|\n", " - ", body)
                    print(data)
                except:
                    data = 'DATA ERROR'
                    print(make_colors(data, 'lw', 'r'))
        ch.basic_ack(delivery_tag = met.delivery_tag)

    @classmethod
    def connection(self, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13'):
        #establish connection to RabbitMQ
        #credentials = pika.PlainCredentials('root', 'Xxxnuxer')
        # parameters = pika.ConnectionParameters(host='192.168.0.9', port = 5672, credentials=credentials)
        #parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
        parameters = pika.URLParameters('amqp://{}:{}@{}:{}/%2F'.format(username, password, hostname, port))

        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()

        #create a queue to send messages
        #channel.queue_declare(queue='syslog', durable=True)
        channel.exchange_declare(exchange = exchange_name, exchange_type='fanout', durable=True, auto_delete=False)

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange = exchange_name, queue = queue_name)
        return channel, queue_name, conn

    @classmethod
    def main(self, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13'):
        channel, queue_name,conn = self.connection(exchange_name, hostname, port, username, password)
        channel.basic_consume(queue = queue_name, on_message_callback = self.call_back, consumer_tag='all', auto_ack = False)
        #channel.basic_recover(requeue = True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("exit ...")

        conn.close()

    @classmethod
    def pub(self, message, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13'):
        channel, _,conn = self.connection(exchange_name, hostname, port, username, password)
        channel.basic_publish(exchange_name, '', message)
        conn.close

    @classmethod
    def usage(self):
        parser = argparse.ArgumentParser('fanout')
        parser.add_argument('EXCHANGE', default = 'django')
        parser.add_argument('-H', '--host', help = 'Rabbitmmq Server Host/IP', default = '192.168.0.9')
        parser.add_argument('-P', '--port', help = 'Rabbitmmq Server Port, default: 5672', type = int, default = 5672)
        parser.add_argument('-u', '--username', help = 'Rabbitmq admin/user name', default = 'root')
        parser.add_argument('-p', '--password', help = 'Rabbitmq password admin/user', default = 'Xxxnuxer13')
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
                self.main(args.EXCHANGE, args.host, args.port, args.username, args.password)

if __name__ == '__main__':
    Fanout.usage()

