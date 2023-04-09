import pika
import sys
from datetime import datetime
from make_colors import make_colors
from datetime import datetime
import os
from configset import configset
import json

print("PID:", os.getpid())

CONFIGNAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cust_fanout.ini')
CONFIG = configset(CONFIGNAME)

def set_color(level):
    if 'emerg' in 'emerge' in str(level):
        return "EMERGE", CONFIG.get_config('LEVEL_EMERGENCY', 'fore', value='white'), CONFIG.get_config('LEVEL_EMERGENCY', 'back', value='magenta')
    elif 'aler' in str(level):
        return "ALERT", CONFIG.get_config('LEVEL_ALERT', 'fore', value='white'), CONFIG.get_config('LEVEL_ALERT', 'back', value='blue')
    elif 'crit' in str(level):
        return "CRITI", CONFIG.get_config('LEVEL_CRITICAL', 'fore', value='black'), CONFIG.get_config('LEVEL_CRITICAL', 'back', value='green')
    elif 'err' in str(level):
        return "ERROR", CONFIG.get_config('LEVEL_ERROR', 'fore', value='white'), CONFIG.get_config('LEVEL_ERROR', 'back', value='red')
    elif 'warn' in str(level):
        return "WARNI", CONFIG.get_config('LEVEL_WARNING', 'fore', value='black'), CONFIG.get_config('LEVEL_WARNING', 'back', value='yellow')
    elif 'not' in str(level):
        return "NOTIC", CONFIG.get_config('LEVEL_NOTICE', 'fore', value='white'), CONFIG.get_config('LEVEL_NOTICE', 'back', value='cyan')
    elif 'inf' in str(level):
        return "INFO",  CONFIG.get_config('LEVEL_INFO', 'fore', value='green'), CONFIG.get_config('LEVEL_INFO', 'back', value='black')
    elif 'deb' in str(level):
        return "DEBUG", CONFIG.get_config('LEVEL_DEBUG', 'fore', value='yellow'), CONFIG.get_config('LEVEL_DEBUG', 'back', value='black')
    else:
        return "UNKNOWN", CONFIG.get_config('LEVEL_UNKNOWN', 'fore', value='red'), CONFIG.get_config('LEVEL_UNKNOWN', 'back', value='white')


def call_back(ch, met, prop, body):
    #print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
    data = json.loads(body)
    print(
        make_colors(datetime.strftime(datetime.fromisoformat(data.get('timestamp')), '%Y/%m/%d %H:%M:%S:%f'), 'lc') + " [" + \
        make_colors(*set_color(data.get('severity'))) + "] " + \
        make_colors(data.get('facility'), 'lm') + " " + \
        make_colors(data.get('ip'), 'ly') + " " + \
        make_colors(data.get('hostname'), 'lg') + " " + \
        make_colors(data.get('appname'), 'b', 'y') + " " + \
        make_colors(data.get('message'), 'lc')
    )
    ch.basic_ack(delivery_tag = met.delivery_tag)

#establish connection to RabbitMQ
credentials = pika.PlainCredentials('root', 'Xxxnuxer')
# parameters = pika.ConnectionParameters(host='192.168.0.9', port = 5672, credentials=credentials)
parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

#create a queue to send messages
#channel.queue_declare(queue='syslog', durable=True)
channel.exchange_declare(exchange = 'syslog', exchange_type='fanout', durable=True, auto_delete=False)

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange = 'syslog', queue = queue_name)

channel.basic_consume(queue = queue_name, on_message_callback = call_back, consumer_tag='all', auto_ack = False)
#channel.basic_recover(requeue = True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("exit ...")


connection.close()

