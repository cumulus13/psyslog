import pika
import shutil

N=1
def callback(ch, method, properties, body):
    global N
    print(f" [Consumer 1 [RSYSLOG]] Received {method.routing_key}: {body.decode()}")
    print(N, "-"*(shutil.get_terminal_size()[0] - 5))
    N+=1
    ch.basic_ack(delivery_tag=method.delivery_tag)

credentials = pika.PlainCredentials('root', 'root')
parameters = pika.ConnectionParameters(host='192.168.100.2', port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='rsyslog', exchange_type='topic', durable=True)
queue = channel.queue_declare(queue='rsyslog_queue', durable=True)  # Named durable queue
queue_name = queue.method.queue
channel.queue_bind(exchange='rsyslog', queue=queue_name, routing_key='syslog.*')

# Consume messages
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
print(" [Consumer 1 [RSYSLOG]] Waiting for messages. To exit press CTRL+C")
channel.start_consuming()
