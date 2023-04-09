import pika
from datetime import datetime

## Connect to RabbitMQ
#credentials = pika.PlainCredentials('root', 'Xxxnuxer')
#parameters = pika.URLParameters('amqp://root:Xxxnuxer13@192.168.0.9:5672/%2F')
#connection = pika.BlockingConnection(parameters)
#channel = connection.channel()

#try:
    #channel.queue_declare('nginx', auto_delete = True)#, durable = True)
#except pika.exceptions.ChannelClosedByBroker:
    #channel.queue_delete('nginx')
    #channel.queue_declare('nginx', auto_delete = True)#, durable = True)
#channel.basic_publish('', 'nginx', 'Message ' + datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'))

## Declare the queue with a TTL
##queue_name = 'my_queue'
##queue_arguments = {'x-message-ttl': 5000}  # TTL in milliseconds
##channel.queue_declare(queue=queue_name, durable=True)#, arguments=queue_arguments)

##channel.exchange_declare(exchange='nginx', exchange_type='direct', durable = True)
##result = channel.queue_declare('', exclusive=True, durable = True)
##queue_name = result.method.queue
##channel.queue_bind(exchange='nginx', queue=queue_name, routing_key='')


## Publish a message with a TTL
##message = 'Hello, World!'
##channel.basic_publish(exchange='nginx', routing_key=queue_name, body=message)#, properties=pika.BasicProperties(delivery_mode=2))#, expiration=str(5000)))

## Close the connection
#connection.close()


# RabbitMQ connection parameters
RABBITMQ_HOST = '192.168.0.9'
RABBITMQ_PORT = 5672
RABBITMQ_VHOST = '/'
RABBITMQ_USER = 'root'
RABBITMQ_PASSWORD = 'Xxxnuxer13'

# Queue name and exchange name
QUEUE_NAME = 'logs'
EXCHANGE_NAME = 'nginx'

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
    print("ERROR [1]:", str(e))
    if 'PRECONDITION_FAILED' in str(e):
        channel = connection.channel()
        channel.exchange_delete(EXCHANGE_NAME)
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable = True)
try:
    channel.queue_declare(queue=QUEUE_NAME, durable = True)
except pika.exceptions.ChannelClosedByBroker as e:
    print("ERROR [2]:", str(e))
    if 'PRECONDITION_FAILED' in str(e):
        channel = connection.channel()
        channel.queue_delete(QUEUE_NAME)
        channel.queue_declare(queue=QUEUE_NAME, durable = True)

# Bind queue to exchange
channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key='')

# Producer
def send_message():
    while True:
        try:
            message = input("Enter message: ")
            if message == 'exit':
                break
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=message, properties = pika.BasicProperties(delivery_mode = 2))
            print("Message sent")
        except pika.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
            break

send_message()

channel.close()
connection.close()