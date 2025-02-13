import pika

credentials = pika.PlainCredentials('root', 'root')
parameters = pika.ConnectionParameters(host='192.168.100.2', port=5672, credentials=credentials, virtual_host='psyslog')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.exchange_declare(exchange='syslog', exchange_type='fanout', durable=True)

channel.queue_declare(queue="q_psyslog", durable=True)

channel.queue_bind(exchange='syslog', queue="q_psyslog", routing_key='syslog.all')

# Publish messages with different routing keys
channel.basic_publish(
        exchange='syslog_raw',
        routing_key="syslog.all",
        body="TEST 001",
        properties=pika.BasicProperties(delivery_mode=2)  # Message persistence
    )
print(f" [x] Sent 'syslog_raw':'TEST 001'")
# channel.queue_delete(queue='last_5_queue')
connection.close()
