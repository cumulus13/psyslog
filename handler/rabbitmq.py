from __future__ import absolute_import, unicode_literals
import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback

try:
    from . psyslog import console
except:
    from psyslog import console
from configset import configset
from pathlib import Path
from rich.text import Text

CONFIGNAME = str(Path(__file__).parent.parent / 'psyslog.ini')
CONFIG = configset(CONFIGNAME)

import json
import pika
import tenacity
from tenacity import retry, stop_after_delay, wait_fixed
import os
from amqp import Connection, Message
import socket
import re
from pydebugger.debug import debug
from kombu import Connection, Exchange, Queue
import logging

def send_log_to_rabbitmq(log_message):
    debug(log_message = log_message)
    try:
        exchange = Exchange(
            CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog', type=CONFIG.get_config('rabbitmq', 'exchange_type') or 'fanout', durable=CONFIG.get_config('rabbitmq', 'durable') or True)
        queue = Queue(name='', exchange=exchange, routing_key=CONFIG.get_config('rabbitmq', 'routing_key') or '', durable=CONFIG.get_config('rabbitmq', 'durable') or True)
        username = CONFIG.get_config('rabbitmq', 'username') or 'guest'
        password = CONFIG.get_config('rabbitmq', 'password') or 'guest'
        host = CONFIG.get_config('rabbitmq', 'host') or '127.0.0.1'
        port = int(CONFIG.get_config('rabbitmq', 'port') or 5672)
        
        with Connection(f'amqp://{username}:{password}@{host}:{port}//') as conn:
            with conn.Producer(serializer='json') as producer:
                producer.publish(
                    log_message,
                    exchange=exchange,
                    routing_key='',
                    delivery_mode=2,
                    mandatory=True,
                    priority=0,
                    expiration=None,
                    headers=None,
                    retry=True,
                    declare=[queue],
                )
    except:
        CTraceback(*sys.exc_info())

class RabbitMQHandler:
    def __init__(self, exchange_name='syslog', exchange_type='fanout', durable=True, username='guest', password='guest', host=None, port=None):
        self.exchange_name = CONFIG.get_config('rabbitmq', 'exchange_name') or exchange_name
        self.exchange_type = CONFIG.get_config('rabbitmq', 'exchange_type') or exchange_type
        self.durable = CONFIG.get_config('rabbitmq', 'durable') or durable
        self.username = CONFIG.get_config('rabbitmq', 'username') or username or 'guest'
        self.password = CONFIG.get_config('rabbitmq', 'password') or password or 'guest'
        self.host = CONFIG.get_config('rabbitmq', 'host') or host or '127.0.0.1'
        self.port = CONFIG.get_config('rabbitmq', 'port') or port or 5672
        self.connection = None
        self.channel = None
        self.connect()

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def connect(self):
        debug(self_username = self.username)
        debug(self_password = self.password)
        debug(self_host = self.host)
        debug(self_port = self.port)

        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
        debug(parameters = parameters)
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            durable=self.durable,
        )

    def send(self, body):
        self.connect()
        self.channel.basic_publish(exchange=self.exchange_name, routing_key=CONFIG.get_config('rabbitmq', 'routing_key'), body=body.encode('utf-8'))

    def close(self):
        try:
            self.connection.close()
        except:
            pass

class RabbitMQHandler2():
    def __init__(self, host = '127.0.0.1', port = 5672, username = 'guest', password = 'guest', exchange = 'syslog', routing_key = '', max_retries=3, durable = True, exchange_type = 'fanout', delivery_mode = 2):
        self.host = CONFIG.get_config('rabbitmq', 'host') or host
        self.port = int(CONFIG.get_config('rabbitmq', 'port') or port or 5672)
        self.username = CONFIG.get_config('rabbitmq', 'username') or username
        self.password = CONFIG.get_config('rabbitmq', 'password') or password
        self.exchange = CONFIG.get_config('rabbitmq', 'exchange_name') or exchange
        self.exchange_type = CONFIG.get_config('rabbitmq', 'exchange_type') or exchange_type or 'fanout'
        self.routing_key = CONFIG.get_config('rabbitmq', 'routing_key') or routing_key
        self.max_retries = CONFIG.get_config('rabbitmq', 'max_tries') or max_retries
        self.connection = None
        self.channel = None
        self.durable = CONFIG.get_config('rabbitmq', 'durable') or durable
        self.delivery_mode = CONFIG.get_config('rabbitmq', 'delivery_mode') or delivery_mode

    def connect(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(self.host, self.port, '/', credentials, heartbeat=0)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, durable=self.durable, exchange_type=self.exchange_type)

    def close(self):
        if self.connection: self.connection.close()

    def send(self, record):
        try:
            self.retry_send(record)
        except Exception as e:
            print(f'Error while sending log to RabbitMQ: {e}')

    @retry(stop=stop_after_delay(60), wait=wait_fixed(10))
    def retry_send(self, logentry):
        if not self.connection or self.connection.is_closed:
            self.connect()
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=logentry,
            properties=pika.BasicProperties(delivery_mode=self.delivery_mode)
        )

class RabbitMQHandler3():

    def send(self, message):
        # send_log_to_rabbitmq.delay({'message': message})
        send_log_to_rabbitmq({'message': message})

class AMQPHandlerConfigError(Exception):
    pass

class AMQPHandler():
    def __init__(self, connection_url = None, exchange_name = None, exchange_type = None, username = None, password = None, durable = None):
        self.connection_url = connection_url or CONFIG.get_config('rabbitmq', 'url')
        if self.connection_url:
            self.exchange_name = exchange_name or CONFIG.get_config('rabbitmq', 'exchange_name')
            self.connection = Connection(connection_url, userid=username or CONFIG.get_config('rabbitmq', 'username'), password=password or CONFIG.get_config('rabbitmq', 'password'))
            self.channel = self.connection.channel()
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