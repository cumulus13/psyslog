from __future__ import absolute_import, unicode_literals
import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback

from rich.console import Console
from rich.theme import Theme

severity_theme1 = Theme({
    "emergency": "#FFFFFF on #ff00ff",
    "emerg": "#FFFFFF on #ff00ff",
    "alert": "white on #005500",
    "ale": "white on #005500",
    "aler": "white on #005500",
    'critical': "white on #0000FF",
    'criti': "white on #0000FF",
    'crit': "white on #0000FF",
    "error": "white on red",
    "err": "white on red",
    "warning": "black on #FFFF00",
    "warni": "black on #FFFF00",
    "warn": "black on #FFFF00",
    'notice': "black on #55FFFF",
    'notic': "black on #55FFFF",
    'noti': "black on #55FFFF",
    "info": "bold #AAFF00",
    "debug": "black on #FFAA00",
    "deb": "black on #FFAA00",
    "unknown": "white on #FF00FF"
})

console = Console(theme=severity_theme1)

from configset import configset
from pathlib import Path
from rich.text import Text

CONFIGNAME = str(Path(__file__).parent.parent / 'psyslog.ini')
CONFIG = configset(CONFIGNAME)

import json
import pika
import tenacity
from tenacity import wait_exponential, stop_after_attempt #, retry, stop_after_delay, wait_fixed
import os
from amqp import Connection, Message
import socket
import re
from pydebugger.debug import debug
# from kombu import Connection, Exchange, Queue
import logging

# def send_log_to_rabbitmq(log_message):
#     debug(log_message = log_message)
#     try:
#         exchange = Exchange(
#             CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog', type=CONFIG.get_config('rabbitmq', 'exchange_type') or 'fanout', durable=CONFIG.get_config('rabbitmq', 'durable') or True)
#         queue = Queue(name='', exchange=exchange, routing_key=CONFIG.get_config('rabbitmq', 'routing_key') or '', durable=CONFIG.get_config('rabbitmq', 'durable') or True)
#         username = CONFIG.get_config('rabbitmq', 'username') or 'guest'
#         password = CONFIG.get_config('rabbitmq', 'password') or 'guest'
#         host = CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
#         port = int(CONFIG.get_config('rabbitmq', 'port') or 5672)
        
#         with Connection(f'amqp://{username}:{password}@{host}:{port}//') as conn:
#             with conn.Producer(serializer='json') as producer:
#                 producer.publish(
#                     log_message,
#                     exchange=exchange,
#                     routing_key='',
#                     delivery_mode=2,
#                     mandatory=True,
#                     priority=0,
#                     expiration=None,
#                     headers=None,
#                     retry=True,
#                     declare=[queue],
#                 )
#     except:
#         CTraceback(*sys.exc_info())

class RabbitMQHandler:
    
    @classmethod
    def set(self, exchange_name = None, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, verbose = False):
        username = username or CONFIG.get_config('rabbitmq', 'username') or CONFIG.get_config('rabbitmq', 'username') or 'guest'
        
        password = password or CONFIG.get_config('rabbitmq', 'password') or CONFIG.get_config('rabbitmq', 'password') or 'guest'
        
        hostname = hostname or CONFIG.get_config('rabbitmq', 'host') or CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
        
        port = int(port or CONFIG.get_config('rabbitmq', 'port') or CONFIG.get_config('rabbitmq', 'port') or 5672)
        
        exchange_name = exchange_name or CONFIG.get_config('rabbitmq', 'exchange_name') or CONFIG.get_config('rabbitmq', 'exchange_name') or 'fanout'
        
        exchange_type = exchange_type or CONFIG.get_config('rabbitmq', 'exchange_type') or CONFIG.get_config('rabbitmq', 'exchange_type') or 'fanout'
        
        durable = durable or CONFIG.get_config('rabbitmq', 'durable') or CONFIG.get_config('rabbitmq', 'durable') or False
        
        auto_delete = auto_delete or CONFIG.get_config('rabbitmq', 'auto_delete') or CONFIG.get_config('rabbitmq', 'auto_delete') or False
        
        exclusive = exclusive or CONFIG.get_config('rabbitmq', 'exclusive') or CONFIG.get_config('rabbitmq', 'exclusive') or False
        
        queue_name = queue_name or CONFIG.get_config('rabbitmq', 'queue') or CONFIG.get_config('rabbitmq', 'queue') or 'psyslog_queue'
        
        auto_ack = auto_ack or CONFIG.get_config('rabbitmq', 'auto_ack') or CONFIG.get_config('rabbitmq', 'auto_ack') or False
        
        routing_key = routing_key or CONFIG.get_config('rabbitmq', 'routing_key') or CONFIG.get_config('rabbitmq', 'routing_key') or ''
        
        vhost = vhost or CONFIG.get_config('rabbitmq', 'vhost') or CONFIG.get_config('rabbitmq', 'vhost') or '/'
        
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
            debug(configfile = CONFIG.configname, debug = 1)
        
        return exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost

    @classmethod
    @tenacity.retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
    def connect(self, exchange_name = None, hostname = '127.0.0.1', port = 5672, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, configfile = None, config = None, verbose = False):
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
            CONFIG = config
            
        elif (configfile and not config) or config and not isinstance(config, configset):
            CONFIG = configset(configfile)
            
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
                    
        # parameters = pika.URLParameters('amqp://{}:{}@{}:{}/{}'.format(username, password, hostname, port, vhost or '%2F'))
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host = hostname, port = port, credentials = credentials, virtual_host = vhost)
        
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
            debug(vhost = vhost, debug = 1)
            debug(parameters = parameters, debug = 1)

        while 1:
            try:
                conn = pika.BlockingConnection(parameters)
                channel = conn.channel()

                channel.exchange_declare(
                    exchange = exchange_name, 
                    exchange_type = exchange_type, 
                    durable = durable, 
                    auto_delete = auto_delete
                )

                result = channel.queue_declare(
                    queue=queue_name, 
                    exclusive=exclusive, 
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
    @tenacity.retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
    def send(self, message, exchange_name = None, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, raw = False, configfile = None, config = None, verbose = False):
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if config and isinstance(config, configset):
            CONFIG = config
        elif (configfile and not config) or config and not isinstance(config, configset):
            CONFIG = configset(configfile)
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if raw: exchange_name = f"{exchange_name}_raw" if raw and not exchange_name[-3:] == 'raw' else exchange_name
            
        if verbose:
            debug(config = config, debug = 1)
            debug(configfile = configfile, debug = 1)
            debug(configfile_CONFIG = CONFIG.filename(), debug = 1)
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
        
        conn = None
        
        try:
            while 1:
                try:
                    channel, queue_name, conn = self.connect(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost, verbose=verbose)
            
                    channel.basic_publish(exchange_name, routing_key = routing_key, body=message, properties=pika.BasicProperties(delivery_mode=2) if durable else None)
                except Exception:
                    CTraceback(*sys.exc_info(), print_it = verbose or False)
                    if conn: conn.close
        except KeyboardInterrupt:
            print("exit ...")
            if conn: conn.close()
        except:
            CTraceback(*sys.exc_info())        
            if conn: conn.close()
            
        if conn: conn.close()
    
    @classmethod
    def pub(self, *args, **kwargs):
        return self.send(*args, **kwargs)

    @classmethod
    @tenacity.retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
    def consume(self, call_back = None, exchange_name = None, hostname = None, port = None, username = None, password = None, exchange_type = None, durable = False, auto_delete = False, exclusive=False, queue_name = None, auto_ack = False, routing_key = None, vhost = None, raw = False, configfile = None, config = None, verbose = False):
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if config and isinstance(config, configset):
            CONFIG = config
        elif (configfile and not config) or config and not isinstance(config, configset):
            CONFIG = configset(configfile)
        
        exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost = self.set(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost)
        
        if raw: exchange_name = f"{exchange_name}_raw" if raw and not exchange_name[-3:] == 'raw' else exchange_name
            
        if verbose:
            debug(config = config, debug = 1)
            debug(configfile = configfile, debug = 1)
            debug(configfile_CONFIG = CONFIG.filename(), debug = 1)
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
        
        conn = None
        
        try:
            while 1:
                try:
                    channel, queue_name, conn = self.connect(exchange_name, hostname, port, username, password, exchange_type, durable, auto_delete, exclusive, queue_name, auto_ack, routing_key, vhost, verbose=verbose)
                    
                    channel.basic_consume(queue = queue_name, on_message_callback = call_back, consumer_tag=CONFIG.get_config('rabbitmq', 'consumer_tag') or 'all', auto_ack = auto_ack)
                    #channel.basic_recover(requeue = True)
                    channel.start_consuming()
                    break
                except KeyboardInterrupt:
                    print("exit ...")
                    break
                except:
                    CTraceback(*sys.exc_info())
                    if conn: conn.close()
        except KeyboardInterrupt:
            print("exit ...")
            if conn: conn.close()
        except:
            CTraceback(*sys.exc_info())        
            if conn: conn.close()
            
        if conn: conn.close()

    
    @classmethod
    def con(self, *args, **kwargs):
        return self.send(*args, **kwargs)

    def close(self):
        try:
            self.connect.close()
        except:
            pass

class AMQPHandlerConfigError(Exception):
    pass

class AMQPHandler():
    def __init__(self, connection_url = None, exchange_name = None, exchange_type = None, username = None, password = None, durable = None):
        self.connect_url = connection_url or CONFIG.get_config('rabbitmq', 'url')
        if self.connect_url:
            self.exchange_name = exchange_name or CONFIG.get_config('rabbitmq', 'exchange_name')
            self.connect = Connection(connection_url, userid=username or CONFIG.get_config('rabbitmq', 'username'), password=password or CONFIG.get_config('rabbitmq', 'password'))
            self.channel = self.connect.channel()
            self.channel.exchange_declare(exchange_name, exchange_type, durable=durable or CONFIG.get_config('rabbitmq', 'durable') or True)
        else:
            self.channel = None

    def send(self, message):
        if self.channel:
            self.channel.basic_publish(message, exchange=self.exchange_name)
        else:
            raise AMQPHandlerConfigError(Text(f"Please check configuration !", style = "white on red blink"))

class SysLogJSONHandler(logging.handlers.SysLogHandler):
    def __init__(self, *args, **kwargs):
        self.env = kwargs.get('env')
        #self.server_host = kwargs.get('server_host')
        kwargs.pop('env', None)
        #kwargs.pop('server_host', None)
        super().__init__(*args, **kwargs)
        self.sock = None

    def send(self, message):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps(message)
        if isinstance(message, str):
            message = message.encode('utf-8')
        self.sock.sendto(message, self.address)

    def emit(self, record):
        pattern = r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}"
        timestamp = re.findall(pattern, self.format(record))
        if timestamp:
            timestamp = timestamp[0]
        else:
            timestamp = self.format(record)
        try:
            log_entry = {
                'timestamp': timestamp,
                'levelname': record.levelname,
                'pid': record.process,
                'tid': record.thread,
                'filename': record.filename,
                'lineno': record.lineno,
                'message': record.getMessage(),
                'logmessage': self.format(record),
                'env': self.env,
                #'client_ip': self.get_client_ip(),
                #'server_ip': self.get_server_ip(),
            }
            self.send_json(log_entry)
        except Exception:
            self.handleError(record)

    def send_json(self, log_entry):
        message = json.dumps(log_entry)
        self.send(message)

    def get_client_ip(self):
        try:
            return socket.gethostbyaddr(self.address[0])[0]
        except Exception:
            return None

    def get_server_ip(self):
        try:
            return socket.gethostbyname(self.server_host)
        except Exception:
            return None

if __name__ == '__main__':
    pass