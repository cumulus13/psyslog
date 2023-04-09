import pika
import sys
from datetime import datetime

#establish connection to RabbitMQ
credentials = pika.PlainCredentials('root', 'Xxxnuxer')
# parameters = pika.ConnectionParameters(host='192.168.0.9', port = 5672, credentials=credentials)
parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

#create a queue to send messages
#channel.queue_declare(queue='syslog', durable=True)
channel.exchange_declare(exchange = 'logs', exchange_type='fanout', durable=True)


#send message to queue
message = (" ".join(sys.argv[1:]) or datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f') + "_TEST")
#channel.basic_publish(exchange='', routing_key='TEST-003', body=message, properties=pika.BasicProperties(delivery_mode=2))
channel.basic_publish(exchange = 'logs', body = message, routing_key = '')

print("%s Message sent to RabbitMQ" % datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'))

connection.close()
