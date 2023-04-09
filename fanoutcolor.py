import threading
import queue
import datetime
import json
import time
import pika
import urwid
from urwid import ListBox, SimpleListWalker

class ColoredText(urwid.Text):
    def __init__(self, text, color=None):
        if color:
            text = ('{0}{1}{2}'.format(color, text, urwid.NORMAL))
        urwid.Text.__init__(self, text)

class MyWidget(ListBox):
    def __init__(self):
        self.messages = SimpleListWalker([])
        ListBox.__init__(self, self.messages)

    def append_message(self, message):
        message = json.loads(message)
        log_message = "{0} - {1} - {2}".format(
            datetime.datetime.fromisoformat(message['timestamp']).strftime("%Y-%m-%d %H:%M:%S"),
            message['hostname'],
            message['message'])
        if message['severity'] == 'info':
            self.messages.append(ColoredText(log_message, 'black'))
        elif message['severity'] == 'warning':
            self.messages.append(ColoredText(log_message, 'yellow'))
        elif message['severity'] == 'error':
            self.messages.append(ColoredText(log_message, 'light red'))
        self.set_focus(len(self.messages) - 1)

class MyApplication:
    palette = [
            ('header', 'white', 'dark blue'),
            ('footer', 'black', 'dark cyan'),
            ('normal', 'white', 'black'),
            ('line', 'black', 'light gray'),
        ]    
    def __init__(self):
        self.input_panel = urwid.Edit(caption="Type message: ")
        self.output_panel = MyWidget()
        self.main_widget = urwid.Pile([self.output_panel, self.input_panel])
        self._shutdown_event = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self.consume)
        self.thread.start()
        self.loop = urwid.MainLoop(self.main_widget, self.palette,
                                   unhandled_input=self.handle_input)
        self.loop.set_alarm_in(1, self.update)
        self.loop.run()

    def handle_input(self, input_):
        if input_ in ('q', 'Q'):
            self.loop.stop()
            self._shutdown_event.set()
        else:
            self.publish(input_)

    def publish(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.basic_publish(exchange='syslog', routing_key='', body=message)
        connection.close()

    def consume(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='syslog', exchange_type='fanout', durable = True)
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='syslog', queue=queue_name)
        channel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True)
        channel.start_consuming()

    def callback(self, ch, method, properties, body):
        self.output_panel.append_message(body)

    def update(self, loop, user_data):
        self.loop.set_alarm_in(1, self.update)
        while not self._shutdown_event.is_set():
            time.sleep(0.5)

if __name__ == "__main__":
    my_app = MyApplication()
    my_app.start()
