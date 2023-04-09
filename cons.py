import pika
from datetime import datetime
import os

print("PID:", os.getpid())

def call_back(ch, met, prop, body):
    print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
    ch.basic_ack(delivery_tag = met.delivery_tag)
    
#establish connection to RabbitMQ
credentials = pika.PlainCredentials('root', 'Xxxnuxer')
#parameters = pika.ConnectionParameters(host='192.168.0.9', credentials=credentials)
parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
parameters.socket_timeout = 5
parameters.connection_attempts =  3
parameters.retry_delay =  5
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

#delete exchange before
try:
    channel.exchange_delete(exchange = 'syslog')
except pika.exceptions.ChannelClose as e:
    print(f"Error deleting exchange: {e}")
    
#channel.exchange_declare(exchange = 'logs', exchange_type = 'fanout', durable = True)
channel.exchange_declare(exchange = 'syslog', exchange_type = 'fanout', durable = True)
result = channel.queue_declare(queue = '', exclusive = True)
queue_name = result.method.queue
#channel.queue_bind(exchange = 'logs', queue = queue_name)
#channel.queue_bind(exchange = 'syslog', queue = queue_name)
channel.queue_bind(exchange = 'syslog', queue = queue_name, routing_key = '')

# Declare the queue to retrieve messages from
#queue = channel.queue_declare(queue='TEST-003', durable=True)

# Retrieve the last message from the queue
#method_frame, header_frame, body = channel.basic_get(queue='TEST-003')#, no_ack=True)
#channel.basic_qos(prefetch_count=1)
#channel.basic_consume('TEST-003', call_back, auto_ack=True, consumer_tag='all')
#channel.basic_consume('TEST-003', call_back, consumer_tag='all', auto_ack = True)
channel.basic_consume(queue_name, call_back, consumer_tag='all', auto_ack = False)
#channel.basic_recover(requeue = True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("exit ...")

#if method_frame:
    # # Print the message
    #print("%s [x] Received message: %s" % (datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), body))
#else:
    # # No message was retrieved
    #print("No message retrieved")

# Close the connection to RabbitMQ
connection.close()
