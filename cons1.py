import pika
from datetime import datetime
import os

print("PID:", os.getpid())

def call_back(ch, method, prop, body):
    print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
    ch.basic_ack(delivery_tag=method.delivery_tag)

    # Get previous message
    prev_method, prev_props, prev_body = ch.basic_get(queue_name)
    if prev_method:
        print("Previous message:", prev_body)
        ch.basic_ack(delivery_tag=prev_method.delivery_tag)

    
credentials = pika.PlainCredentials('root', 'Xxxnuxer')
parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

try:
    channel.exchange_delete(exchange='syslog')
except pika.exceptions.ChannelClose as e:
    print(f"Error deleting exchange: {e}")

channel.exchange_declare(exchange='syslog', exchange_type='topic', durable=True)
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='syslog', queue=queue_name, routing_key='rsyslog')

channel.basic_consume(queue_name, call_back, consumer_tag='all', auto_ack=False)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("exit ...")

connection.close()
