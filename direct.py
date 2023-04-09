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
from pydebugger.debug import debug

print("PID:", os.getpid())

class Direct(object):    

    CONFIGNAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cust_direct.ini')
    CONFIG = configset(CONFIGNAME)
    CURRENT_HEIGHT = 0
    TERM_SIZE = shutil.get_terminal_size()
    
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
        data = json.loads(body)
        if shutil.get_terminal_size().lines < self.CURRENT_HEIGHT:
            if sys.platform == 'win32':
                os.system('cls')
            else:
                os.system('clear')
            self.TERM_SIZE = shutil.get_terminal_size()
            self.CURRENT_HEIGHT = 0
        else:
            self.CURRENT_HEIGHT += 1
        print(
            make_colors(str(self.CURRENT_HEIGHT).zfill(2), 'lw', 'bl') + " " + \
            make_colors(datetime.strftime(datetime.fromisoformat(data.get('timestamp')), '%Y/%m/%d %H:%M:%S:%f'), 'lc') + " [" + \
            make_colors(*self.set_color(data.get('severity'))) + "] " + \
            make_colors(data.get('facility'), 'lm') + " " + \
            make_colors(data.get('ip'), 'ly') + " " + \
            make_colors(data.get('hostname'), 'lg') + " " + \
            make_colors(data.get('appname'), 'b', 'y') + " " + \
            make_colors(data.get('message'), 'lc')
        )
        ch.basic_ack(delivery_tag = met.delivery_tag)
    
    @classmethod
    def connection(self, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13', queue = ''):
        #establish connection to RabbitMQ
        #credentials = pika.PlainCredentials('root', 'Xxxnuxer')
        # parameters = pika.ConnectionParameters(host='192.168.0.9', port = 5672, credentials=credentials)
        #parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
        parameters = pika.URLParameters('amqp://{}:{}@{}:{}/%2F'.format(username, password, hostname, port))
        
        conn = pika.BlockingConnection(parameters)
        channel = conn.channel()
        
        #create a queue to send messages
        #channel.queue_declare(queue='syslog', durable=True)
        channel.exchange_declare(exchange = exchange_name, exchange_type='direct', durable=True, auto_delete=False)
        
        result = channel.queue_declare(queue=queue, exclusive=False, durable = True)
        queue_name = result.method.queue
        #channel.queue_bind(exchange = exchange_name, queue = queue_name)
        channel.queue_bind(exchange = exchange_name, queue = queue)
        return channel, queue_name, conn
    
    @classmethod
    def main(self, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13', queue = ''): 
        channel, queue_name,conn = self.connection(exchange_name, hostname, port, username, password, queue)
        channel.basic_consume(queue = queue_name, on_message_callback = self.call_back, consumer_tag='all', auto_ack = False)
        #channel.basic_recover(requeue = True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("exit ...")
        
        conn.close()
        
    @classmethod
    def pub(self, message, exchange_name, hostname = '192.168.0.9', port = 5672, username = 'root', password = 'Xxxnuxer13', queue = ''): 
        channel, _,conn = self.connection(exchange_name, hostname, port, username, password, queue)
        channel.basic_publish(exchange_name, '', message)
        conn.close
    
    @classmethod
    def usage(self):
        parser = argparse.ArgumentParser('direct')
        parser.add_argument('EXCHANGE')
        parser.add_argument('-H', '--host', help = 'Rabbitmmq Server Host/IP', default = '192.168.0.9')
        parser.add_argument('-P', '--port', help = 'Rabbitmmq Server Port, default: 5672', type = int, default = 5672)
        parser.add_argument('-u', '--username', help = 'Rabbitmq admin/user name', default = 'root')
        parser.add_argument('-p', '--password', help = 'Rabbitmq password admin/user', default = 'Xxxnuxer13')
        parser.add_argument('-q', '--queue', help = 'Rabbitmq Queue name, default: "logs"', default = 'logs')
        
        cons = parser.add_subparsers()
        
        parser_cons = cons.add_parser('push')
        parser_cons.add_argument('-m', '--message', help = 'send message')
        
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            print(f'Terminal height: {self.TERM_SIZE.lines}, Terminal width: {self.TERM_SIZE.columns}')
            args = parser.parse_args()
            if hasattr(args, 'message'):
                self.pub(args.message, args.EXCHANGE, args.host, args.port, args.username, args.password, args.queue)
            else:
                self.main(args.EXCHANGE, args.host, args.port, args.username, args.password, args.queue)
            
if __name__ == '__main__':
    Direct.usage()