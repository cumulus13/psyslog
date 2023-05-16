import pika
from datetime import datetime
import os
import logging
import sys

print("PID:", os.getpid())

if len(sys.argv) == 1:
	sys.argv += ['', '']
elif len(sys.argv) == 2:
	sys.argv += ['']

#def call_back(ch, met, prop, body):
    #print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
    #ch.basic_ack(delivery_tag = met.delivery_tag)
    
#def callback(ch, method, properties, body):
    #msg = body.decode('utf-8')
    #logging.debug('Received message: %s', msg)
    
#logging.basicConfig(level=logging.INFO)

##connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

#credentials = pika.PlainCredentials('root', 'Xxxnuxer')
#parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
#connection = pika.BlockingConnection(parameters)
#channel = connection.channel()
#try:
    #channel.queue_declare('nginx', auto_delete = True)#, durable = True)
#except pika.exceptions.ChannelClosedByBroker:
    #channel = connection.channel()
    #channel.queue_delete('nginx')
    #channel.queue_declare('nginx', auto_delete = True)#, durable = True)

##channel.exchange_declare(exchange='nginx', exchange_type='direct', durable = True)

##result = channel.queue_declare('', exclusive=True, durable = True)
##queue_name = result.method.queue

##channel.queue_bind(exchange='nginx', queue=queue_name, routing_key='')

##channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True, consumer_tag = 'licx')
#channel.basic_consume('nginx', callback, True)#, consumer_tag = 'licx')

#logging.info('Waiting for messages. To exit press CTRL+C')
##channel.start_consuming()


#try:
    #channel.start_consuming()
#except KeyboardInterrupt:
    #print("Terminate ....")

#connection.close()

# RabbitMQ connection parameters
RABBITMQ_HOST = '127.0.0.1'
RABBITMQ_PORT = 5672
RABBITMQ_VHOST = '/'
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'

# Queue name and exchange name
QUEUE_NAME = 'nginx'
EXCHANGE_NAME = (sys.argv[1] or 'nginx')

print("QUEUE_NAME    =", QUEUE_NAME)
print("EXCHANGE_NAME =", EXCHANGE_NAME)

# Establishing connection to RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, virtual_host=RABBITMQ_VHOST, credentials=credentials)
connection = pika.BlockingConnection(parameters)

# Creating channel
channel = connection.channel()

try:
    # Declare exchange and queue
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable = True)
except pika.exceptions.ChannelClosedByBroker as e:
    if 'PRECONDITION_FAILED' in str(e):
        channel = connection.channel()
        channel.exchange_delete(EXCHANGE_NAME)
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable = True)
try:
    channel.queue_declare(queue=QUEUE_NAME, durable = True)
except pika.exceptions.ChannelClosedByBroker as e:
    if 'PRECONDITION_FAILED' in str(e):
        channel = connection.channel()
        channel.queue_delete(QUEUE_NAME)
        channel.queue_declare(queue=QUEUE_NAME, durable = True)

# Bind queue to exchange
routing_key=(sys.argv[2] or 'nginx')
print("ROUTING_KEY =", routing_key)
channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key='nginx')

# Consumer
def receive_messages():
    while True:
        try:
            method, properties, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=True)
            if method is not None:
                print("Received message:", body.decode())
        except pika.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
            break
try:
	receive_messages()
except KeyboardInterrupt:
	print("connection terminated !")
	sys.exit(0)
	
channel.close()
connection.close()

