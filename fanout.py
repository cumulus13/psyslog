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
    def connection(self, exchange_name, hostname = '127.0.0.1', port = 5672, username = 'guest', password = 'guest', exchange_type = 'fanout', durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, verbose = False, configfile = None, config = None):
        """
        The function establishes a connection to a RabbitMQ server with specified parameters and returns
        the channel, queue name, and connection object.
        
        :param exchange_name: The `exchange_name` parameter in the `connection` method refers to the exchange name of rabbitmq specify
        :param hostname: The `hostname` parameter in the `connection` method refers to the host address
        of the RabbitMQ server to which you want to establish a connection. By default, it is set to
        '127.0.0.1', which is the loopback address for the local machine. If you want, defaults to
        127.0.0.1 (optional)
        :param port: The `port` parameter in the `connection` method is used to specify the port number
        for the RabbitMQ server connection. By default, the port is set to `5672` if no value is
        provided when calling the method, defaults to 5672 (optional)
        :param username: The `username` parameter in the `connection` method is used to specify the
        username for connecting to the RabbitMQ server. It is typically used along with the `password`
        parameter to authenticate the user. The default value for `username` is set to 'guest', but you
        can provide a different, defaults to guest (optional)
        :param password: The `password` parameter in the `connection` method is used to specify the
        password for connecting to the RabbitMQ server. It is a string parameter that defaults to
        'guest' if not provided. This password is typically used along with the `username` parameter to
        authenticate and establish a connection to the, defaults to guest (optional)
        :param exchange_type: The `exchange_type` parameter in the `connection` method specifies the
        type of exchange to be declared in RabbitMQ. It determines how messages are routed to queues.
        The possible values for `exchange_type` include 'fanout', 'direct', 'topic', and 'headers',
        defaults to fanout (optional)
        :param durable: The `durable` parameter in the `connection` method is used to specify whether
        the exchange or queue should survive a broker restart. If `durable` is set to `True`, the
        exchange or queue will be re-declared upon broker restart, ensuring that the messages are not
        lost. If, defaults to False (optional)
        :param auto_delete: The `auto_delete` parameter in the `connection` method is used to specify
        whether the exchange should be automatically deleted when no more queues are bound to it. If
        `auto_delete` is set to `True`, the exchange will be automatically deleted when there are no
        more queues bound to it. If, defaults to False (optional)
        :param exclusive: The `exclusive` parameter in the `connection` method is used to specify
        whether the queue should be exclusive or not. An exclusive queue can only be used by the
        connection that created it, and it will be deleted when that connection closes. If `exclusive`
        is set to `True`, the queue, defaults to False (optional)
        :param queue_name: The `queue_name` parameter in the `connection` method is used to specify the
        name of the queue that will be declared and bound to the exchange. If a specific `queue_name` is
        provided, it will be used for the queue declaration. If not provided, the method will attempt to
        retrieve
        :param auto_ack: Auto_ack is a parameter in the connection method that is used to specify
        whether the messages delivered to the consumer should be acknowledged automatically. If auto_ack
        is set to True, the messages will be acknowledged automatically once they are delivered to the
        consumer. If set to False, the consumer will need to manually acknowledge, defaults to False
        (optional)
        :param routing_key: The `routing_key` parameter in the `connection` method is used to specify
        the routing key for binding a queue to an exchange in RabbitMQ. When a message is published to
        an exchange with a specific routing key, the message will be routed to the queue(s) that are
        bound to that exchange
        :param verbose: The `verbose` parameter in the `connection` method is a boolean flag that
        controls whether debug information should be printed during the execution of the method. If
        `verbose` is set to `True`, debug information such as connection details, exchange settings,
        queue settings, and parameters will be printed to aid, defaults to False (optional)
        :param configfile: alternative config file *.ini path
        :param config: `configset` object if configfile not provided
        :param vhost: rabbitmq Virtual host name, default is '/'
        :return: The `connection` method returns a tuple containing three elements: `channel`,
        `queue_name`, and `conn`.
        """
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if config and isinstance(config, configset):
            self.CONFIG = config
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        elif (configfile and not config) or config and not isinstance(config, configset):
            self.CONFIG = configset(configfile)
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
                    
        parameters = pika.URLParameters('amqp://{}:{}@{}:{}/{}'.format(username, password, hostname, port, vhost or '%2F'))
        conn = None
                
        if verbose:
            debug(username = username, debug = 1)
            debug(password = password, debug = 1)
            debug(hostname = hostname, debug = 1)
            debug(port = port, debug = 1)
            debug(exchange_name = exchange_name, debug = 1)
            debug(exchange_type = exchange_type, debug = 1)
            debug(durable = durable, debug = 1)
            debug(auto_delete = auto_delete, debug = 1)
            debug(exclusive = exclusive, debug = 1)
            debug(queue_name = queue_name, debug = 1)
            debug(auto_ack = auto_ack, debug = 1)
            debug(routing_key = routing_key, debug = 1)
            debug(parameters = parameters, debug = 1)

        while 1:
            try:
                conn = pika.BlockingConnection(parameters)
                channel = conn.channel()

                #create a queue to send messages
                #channel.queue_declare(queue='syslog', durable=True)
                channel.exchange_declare(
                    exchange = exchange_name, 
                    exchange_type = exchange_type or self.CONFIG.get_config('GENERAL', 'exchange_type') or 'fanout', 
                    durable = durable or self.CONFIG.get_config('GENERAL', 'durable') or True, 
                    auto_delete = auto_delete or self.CONFIG.get_config('GENERAL', 'auto_delete') or False
                )

                result = channel.queue_declare(
                    queue=queue_name or self.CONFIG.get_config('GENERAL', 'queue') or '', 
                    exclusive=exclusive or self.CONFIG.get_config('GENERAL', 'exclusive') or True, 
                    durable=durable
                )
                
                queue_name = result.method.queue
                channel.queue_bind(
                    exchange = exchange_name, 
                    queue = queue_name, 
                    routing_key=routing_key
                )
                break
            except Exception:
                CTraceback(*sys.exc_info(), print_it = verbose or False)
                if conn: conn.close()
        
        return channel, queue_name, conn

    @classmethod
    # exchange_name, hostname = '127.0.0.1', port = 5672, username = 'guest', password = 'guest', exchange_type = 'fanout', durable = False, auto_delete = False, exclusive=False, queue_name = None, verbose = False
    def main(self, exchange_name, call_back, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, raw = False, vhost = None, verbose = False, configfile = None, config = None):
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if config and isinstance(config, configset):
            self.CONFIG = config
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        elif (configfile and not config) or config and not isinstance(config, configset):
            self.CONFIG = configset(configfile)
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
            
        if verbose:
            debug(config = config, debug = 1)
            debug(configfile = configfile, debug = 1)
            debug(username = username, debug = 1)
            debug(password = password, debug = 1)
            debug(hostname = hostname, debug = 1)
            debug(port = port, debug = 1)
            debug(exchange_name = exchange_name, debug = 1)
            debug(exchange_type = exchange_type, debug = 1)
            debug(durable = durable, debug = 1)
            debug(auto_delete = auto_delete, debug = 1)
            debug(exclusive = exclusive, debug = 1)
            debug(queue_name = queue_name, debug = 1)
            debug(auto_ack = auto_ack, debug = 1)
            debug(routing_key = routing_key, debug = 1)
            debug(vhost = vhost, debug = 1)

        if raw: exchange_name = f"{exchange_name}_raw" if raw and not exchange_name[-3:] == 'raw' else exchange_name
        
        try:
            while 1:
                try:
                    channel, queue_name, conn = self.connection(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost, verbose)
                    channel.basic_consume(queue = queue_name, on_message_callback = call_back, consumer_tag=self.CONFIG.get_config('GENERAL', 'consumer_tag') or 'all', auto_ack = auto_ack or self.CONFIG.get_config('GENERAL', 'auto_ack') or False)
                    #channel.basic_recover(requeue = True)
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
    def set(self, exchange_name, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, verbose = False):
        username = username or self.CONFIG.get_config('AUTH', 'username') or self.CONFIG.get_config('rabbitmq', 'username') if not self.CONFIG.configname == 'cust_fanout.ini' else 'guest'
        password = password or self.CONFIG.get_config('AUTH', 'password') or self.CONFIG.get_config('rabbitmq', 'password') if not self.CONFIG.configname == 'cust_fanout.ini' else 'guest'
        hostname = hostname or self.CONFIG.get_config('AUTH', 'host') or self.CONFIG.get_config('rabbitmq', 'host') if not self.CONFIG.configname == 'cust_fanout.ini' else '127.0.0.1'
        port = int(port or self.CONFIG.get_config('AUTH', 'port') or self.CONFIG.get_config('rabbitmq', 'port') if not self.CONFIG.configname == 'cust_fanout.ini' else 5672)
        exchange_type = exchange_type or self.CONFIG.get_config('EXCHANGE', 'type') or self.CONFIG.get_config('rabbitmq', 'exchange_name') if not self.CONFIG.configname == 'cust_fanout.ini' else 'fanout'
        durable = durable or self.CONFIG.get_config('GENERAL', 'durable') or self.CONFIG.get_config('rabbitmq', 'durable') if not self.CONFIG.configname == 'cust_fanout.ini' else False
        auto_delete = auto_delete or self.CONFIG.get_config('GENERAL', 'auto_delete') or self.CONFIG.get_config('rabbitmq', 'auto_delete') if not self.CONFIG.configname == 'cust_fanout.ini' else False
        exclusive = exclusive or self.CONFIG.get_config('GENERAL', 'exclusive') or self.CONFIG.get_config('rabbitmq', 'exclusive') if not self.CONFIG.configname == 'cust_fanout.ini' else False
        queue_name = queue_name or self.CONFIG.get_config('GENERAL', 'queue') or self.CONFIG.get_config('rabbitmq', 'queue') if not self.CONFIG.configname == 'cust_fanout.ini' else 'psyslog'
        auto_ack = auto_ack or self.CONFIG.get_config('GENERAL', 'auto_ack') or self.CONFIG.get_config('rabbitmq', 'auto_ack') if not self.CONFIG.configname == 'cust_fanout.ini' else False
        routing_key = routing_key or self.CONFIG.get_config('AUTH', 'routing_key') or self.CONFIG.get_config('rabbitmq', 'routing_key') if not self.CONFIG.configname == 'cust_fanout.ini' else ''
        vhost = vhost or self.CONFIG.get_config('GENERAL', 'vhost') or self.CONFIG.get_config('rabbitmq', 'vhost') if not self.CONFIG.configname == 'cust_fanout.ini' else '/'
        
        if verbose or os.getenv('VERBOSE') == '1':
            debug(username = username, debug = 1)
            debug(password = password, debug = 1)
            debug(hostname = hostname, debug = 1)
            debug(port = port, debug = 1)
            debug(port = port, debug = 1)
            debug(exchange_name = exchange_name, debug = 1)
            debug(exchange_type = exchange_type, debug = 1)
            debug(durable = durable, debug = 1)
            debug(auto_delete = auto_delete, debug = 1)
            debug(exclusive = exclusive, debug = 1)
            debug(queue_name = queue_name, debug = 1)
            debug(auto_ack = auto_ack, debug = 1)
            debug(routing_key = routing_key, debug = 1)
            debug(vhost = vhost, debug = 1)
            debug(configfile = self.CONFIG.configname, debug = 1)
        
        return exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost
    
    
    @classmethod
    def pub(self, message, exchange_name, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, verbose = False, configfile = None, config = None):
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if config and isinstance(config, configset):
            self.CONFIG = config
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        elif (configfile and not config) or config and not isinstance(config, configset):
            self.CONFIG = configset(configfile)
            exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
            
        if verbose:
            debug(config = config, debug = 1)
            debug(configfile = configfile, debug = 1)
            debug(configfile_CONFIG = self.CONFIG.filename(), debug = 1)
            debug(username = username, debug = 1)
            debug(password = password, debug = 1)
            debug(hostname = hostname, debug = 1)
            debug(port = port, debug = 1)
            debug(exchange_name = exchange_name, debug = 1)
            debug(exchange_type = exchange_type, debug = 1)
            debug(durable = durable, debug = 1)
            debug(auto_delete = auto_delete, debug = 1)
            debug(exclusive = exclusive, debug = 1)
            debug(queue_name = queue_name, debug = 1)
            debug(auto_ack = auto_ack, debug = 1)
            debug(routing_key = routing_key, debug = 1)
            debug(vhost = vhost, debug = 1)
        
        # channel, _,conn = self.connection(exchange_name, hostname, port, username, password)
        channel, queue_name, conn = self.connection(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost, verbose)
        # channel.basic_consume(queue = queue_name, on_message_callback = call_back, consumer_tag=self.CONFIG.get_config('GENERAL', 'consumer_tag') or 'all', auto_ack = auto_ack or False)
        channel.basic_publish(exchange_name, routing_key = routing_key or '', body=message, properties=pika.BasicProperties(delivery_mode=2) if durable else None)
        conn.close

    @classmethod
    def usage(self):
        parser = argparse.ArgumentParser('fanout')
        parser.add_argument('EXCHANGE', nargs='?')
        parser.add_argument('-H', '--host', help = 'Rabbitmmq Server Host/IP', default = '127.0.0.1')
        parser.add_argument('-P', '--port', help = 'Rabbitmmq Server Port, default: 5672', type = int, default = 5672)
        parser.add_argument('-u', '--username', help = 'Rabbitmq admin/user name', default = 'guest')
        parser.add_argument('-p', '--password', help = 'Rabbitmq password admin/user', default = 'guest')
        parser.add_argument('-e', '--exchange-name', help = 'Rabbitmq Exchange Name')
        parser.add_argument('-t', '--exchange-type', help = 'Rabbitmq Exchange Type')
        parser.add_argument('-q', '--queue', help = 'Rabbitmq Exchange Queue')
        parser.add_argument('-r', '--routing-key', help = 'Rabbitmq Routing Key')
        parser.add_argument('-d', '--durable', help = 'Rabbitmq Durable', action = 'store_true')
        parser.add_argument('-dv', '--delivery-mode', help = 'Rabbitmq Delivery Mode', type = int, default = 2)
        parser.add_argument('-ad', '--auto-delete', help = 'Rabbitmq Auto Delete', action = 'store_true')
        parser.add_argument('-a', '--auto-clear', help = 'Auto clear display if full', action = 'store_true')
        parser.add_argument('-x', '--exclusive', help = 'Exclusive', action = 'store_true')
        parser.add_argument('-A', '--ack', help = 'Auto Ack', action = 'store_true')
        parser.add_argument('-v', '--verbose', help = 'verbose', action = 'store_true')
        

        cons = parser.add_subparsers()

        parser_cons = cons.add_parser('pub', help="Publish / Send Message")
        parser_cons.add_argument('message', help = 'send message')

        if len(sys.argv) == 1:
            parser.print_help()
        else:
            print(f'Terminal height: {self.TERM_SIZE.lines}, Terminal width: {self.TERM_SIZE.columns}')
            args = parser.parse_args()
            if args.auto_clear: self.AUTO_CLEAR = True
            # if hasattr(args, 'message'):
            if args.message:
                self.pub(
                    args.message, 
                    args.EXCHANGE or args.exchange_name, 
                    args.host, 
                    args.port, 
                    args.username, 
                    args.password, 
                    args.exchange_type, 
                    args.durable, 
                    args.auto_delete, 
                    args.exclusive, 
                    args.queue, 
                    args.ack, 
                    args.routing_key, 
                    args.verbose
                )
            else:
                self.main(
                    args.EXCHANGE or args.exchange_name, 
                    self.call_back, 
                    args.host, 
                    args.port, 
                    args.username, 
                    args.password, 
                    args.exchange_type, 
                    args.durable, 
                    args.auto_delete,
                    args.exclusive, 
                    args.queue,
                    args.ack,
                    args.routing_key,
                    args.verbose
                )

if __name__ == '__main__':
    Fanout.usage()
