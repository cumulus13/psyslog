#!/usr/bin/python
#Author: cumulus13
#Email: cumulus13@gmail.com
#Syslog Server (Receive Only) processing will be on Client with Server Mode/Monitor Mode

from __future__ import print_function
import click
import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback
import os
import traceback
import socket
if sys.version_info.major == 2:
    import SocketServer
else:
    import socketserver
import time
from make_colors import make_colors
import re
from datetime import datetime
import syslogx as syslog
import time
from configset import configset
from pydebugger.debug import debug
import bitmath
import signal
from rich.theme import Theme
from rich.console import Console

import json
import shutil

severity_theme1 = Theme({
    "emergency": "#FFFFFF on #ff00ff",
    "emerg": "#FFFFFF on #ff00ff",
    "alert": "white on #005500",
    "ale": "white on #005500",
    "aler": "white on #005500",
    'critical': "white on #0000FF",
    'criti': "white on #0000FF",
    'crit': "white on #0000FF",
    "error": "white on red",
    "err": "white on red",
    "warning": "black on #FFFF00",
    "warni": "black on #FFFF00",
    "warn": "black on #FFFF00",
    'notice': "black on #55FFFF",
    'notic': "black on #55FFFF",
    'noti': "black on #55FFFF",
    "info": "bold #AAFF00",
    "debug": "black on #FFAA00",
    "deb": "black on #FFAA00",
    "unknown": "white on #FF00FF"
})

console = Console(theme=severity_theme1)

PID = os.getpid()
lineNumber = 1

class Psyslog(object):
    
    CONFIG = configset()
    HOST = CONFIG.get_config('SERVER', 'host') or '127.0.0.1'
    PORT = CONFIG.get_config('SERVER', 'port') or 1514
    CLIENT_HOST = None
    CLIENT_PORT = None
    facility_string = None
    lineNumber = 0
    
    def __init__(self):
        #super(Psyslog, self).__init__()
        debug(HOST = self.HOST)
        debug(PORT = self.PORT)
        self.handler = 'socket'
        
    def import_handle(self, handle_name, file_path = None):
        file_path = file_path or os.path.join(os.path.dirname(os.path.realpath(__file__)), handle_name + ".py")
        if sys.version_info.major == 3 and sys.version_info.minor > 4:
            import importlib.util
            if os.path.splitext(os.path.basename(file_path))[-1] == ".py": handle_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(handle_name, file_path)
            module_name = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module_name
            spec.loader.exec_module(module_name)
            return module_name
        
        elif sys.version_info.major == 3 and sys.version_info.minor < 5:
            from importlib.machinery import SourceFileLoader
            module_name = SourceFileLoader(handle_name, file_path).load_module()
            return module_name
        else:
            import imp
            module_name = imp.load_source(handle_name, file_path)
            return module_name
            
            
    def format_number(self, number, length = 10000):
        length = self.CONFIG.get('LOGS', 'max_line') or length
        number = str(number).strip()
        if not str(number).isdigit():
            return number
        zeros = len(str(length)) - len(number)
        r = ("0" * zeros) + str(number)
        if len(r) == 1:
            return "0" + r
        return r    

    def sent_to_broker(self, newLogString, host="localhost", port=6379, db=1):
        '''function sent_to_broker
        
        sent message/text string to broker (rabbitmq, etc)
        
        Keyword Arguments:
            newLogString {str} -- [description] (default: {"localhost"})
            host {str} -- [description] (default: {"localhost"})
            port {number} -- [description] (default: {6379})
            db {number} -- [description] (default: {1})
        '''
        if self.CONFIG.get_config('QUEUE', 'host'):
            host = self.CONFIG.get_config('QUEUE', 'host')
        if self.CONFIG.get_config('QUEUE', 'port'):
            port = int(self.CONFIG.get_config('QUEUE', 'port'))
        if host and port:
            from hotqueue import HotQueue
            queue = HotQueue("logqueue", host=host, port=port, db=db)
            queue.put(newLogString)

    # def convert_priority_to_severity(self, number):
    #     try:
    #         facility = int(number) / 8
    #         total_faciliy = facility*8
    #         severity = int(number) - total_faciliy
    #         debug(severity = severity)
    #         return severity
    #     except:
    #         return 8
        
    def convert_priority_to_severity(self, number):
        facility = int(number) // 8
        level = int(number) % 8
        return facility, level

    def get_level_color_config(self, level):
        if str(level) == '0':
            return self.CONFIG.get_config('LEVEL_EMERGENCY', 'fore', value='white'), self.CONFIG.get_config('LEVEL_EMERGENCY', 'back', value='magenta')
        elif str(level) == '1':
            return self.CONFIG.get_config('LEVEL_ALERT', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ALERT', 'back', value='blue')
        elif str(level) == '2':
            return self.CONFIG.get_config('LEVEL_CRITICAL', 'fore', value='black'), self.CONFIG.get_config('LEVEL_CRITICAL', 'back', value='green')
        elif str(level) == '3':
            return self.CONFIG.get_config('LEVEL_ERROR', 'fore', value='white'), self.CONFIG.get_config('LEVEL_ERROR', 'back', value='red')
        elif str(level) == '4':
            return self.CONFIG.get_config('LEVEL_WARNING', 'fore', value='black'), self.CONFIG.get_config('LEVEL_WARNING', 'back', value='yellow')
        elif str(level) == '5':
            return self.CONFIG.get_config('LEVEL_NOTICE', 'fore', value='white'), self.CONFIG.get_config('LEVEL_NOTICE', 'back', value='cyan')
        elif str(level) == '6':
            return self.CONFIG.get_config('LEVEL_INFO', 'fore', value='green'), self.CONFIG.get_config('LEVEL_INFO', 'back', value='black')
        elif str(level) == '7':
            return self.CONFIG.get_config('LEVEL_DEBUG', 'fore', value='yellow'), self.CONFIG.get_config('LEVEL_DEBUG', 'back', value='black')
        else:
            return self.CONFIG.get_config('LEVEL_UNKNOWN', 'fore', value='red'), self.CONFIG.get_config('LEVEL_UNKNOWN', 'back', value='white')
        
    def _coloring(self, level, facility, text, dtime):
        severity_theme1 = Theme({
            "emergency": "white on #ff00ff",
            "emerg": "white on #ff00ff",
            "alert": "white on #005500",
            'critical': "white on #0000FF",
            "error": "white on red",
            "warning": "black on #FFFF00",
            'notice': "black on #55FFFF",
            "info": "bold #AAFF00",
            "debug": "black on #FFAA00" 
        })

        severity_theme2 = Theme({
            "0": "white on #ff00ff",
            "1": "white on #005500",
            '2': "white on #0000FF",
            "3": "white on red",
            "4": "black on #FFFF00",
            '5': "black on #55FFFF",
            "6": "bold #AAFF00",
            "7": "black on #FFAA00" 
        })

        valid_severity = ['emergency', 'emerg', 'emer', 'alert', 'aler', 'critical', 'critic', 'criti', 'error', 'err', 'warning', 'warn', 'notice', 'noti', 'info', 'debug', 'deb']

        # SEVERITY_STRING = f"\[[{severity_theme2.get(level) if str(level).isdigit() else severity_theme1.get(level)}]{syslog.LEVEL_REVERSED.get(level) if str(level).isdigit() else level.lower() if level.lower() in valid_severity else 'unknown'}][/]" if self.CONFIG.get_config('GENERAL', 'show_severity_string') else ''
        SEVERITY_STRING = f"\[[{syslog.FACILITY_REVERSED.get(level) if str(level).isdigit() else syslog.LEVEL.get(level) if level.lower() in valid_severity else 'unknown'}]{syslog.LEVEL_REVERSED.get(level) if str(level).isdigit() else level.lower() if level.lower() in valid_severity else 'unknown'}][/]" if self.CONFIG.get_config('GENERAL', 'show_severity_string') else ''

        debug(SEVERITY_STRING = SEVERITY_STRING)

        FACILITY_STRING = f"\[[{self.CONFIG.get_config('FACILITY', 'color') if self.CONFIG.get_config('FACILITY', 'color') else 'bold white on green'}]{syslog.FACILITY_REVERSED.get(facility) if str(facility).isdigit() and syslog.FACILITY_REVERSED.get(facility) else facility}[/]]" if self.CONFIG.get_config('GENERAL', 'show_priority') in [1, True] else ''

        debug(text = text)
        debug(level = level)
        debug(level_reversed_get_level = syslog.LEVEL_REVERSED.get(level) if str(level).isdigit() else syslog.LEVEL.get(level))
        # debug(check_valid_level = str(level).lower() if str(level).lower() in valid_severity else 'white on #FF00FF')
        debug(check_color_text = syslog.LEVEL_REVERSED.get(level) if str(level).isdigit() else syslog.LEVEL.get(level) if str(level).lower() in valid_severity else 'unknown')

        TEXT = f"[{syslog.LEVEL_REVERSED.get(level) if str(level).isdigit() else syslog.LEVEL_REVERSED.get(syslog.LEVEL.get(level)) if level.lower() in valid_severity else 'unknown'}]{text}[/]"

        # return f"[bold #55FFFF]{dtime}[/] {SEVERITY_STRING} {FACILITY_STRING} {TEXT}"
        return f"{SEVERITY_STRING} {FACILITY_STRING} {TEXT}"

    def get_facility_color_config(self):
        return self.CONFIG.get_config('FACILITY', 'fore', 'white'), self.CONFIG.get_config('FACILITY', 'back', 'green')
    
    def coloring_severity_string(self, text, fore = None, back = None):
        if text and fore and back:
            return "[" + make_colors(text, fore, back) + "]"
        elif text and not fore and not back:
            return "[" + text + "]"
        return ''

    def coloring(self, level, text, facility='', dtime = ''):
        '''function coloring
        
        Convert priority number and message then colored
        
        Arguments:
            level {str/int} -- number include from syslog receive
            text {str} -- text string syslog receiver per line/time
        
        Returns:
             str -- message/text with colored
        '''
        if not dtime: dtime = ''
        # if facility_string:
        #     facility_fore, facility_back = self.get_facility_color_config()
        #     if facility_fore and facility_back:
        #         facility_string = make_colors("[", 'white', 'black') + make_colors(facility_string, facility_fore, facility_back) + make_colors("]", 'white', 'black') + " "
        #     else:   
        #         facility_string = make_colors("[", 'white', 'black') + make_colors(facility_string, 'white', 'magenta') + make_colors("]", 'white', 'black') + " "
        debug(level = level)
        if int(level) <= 7:
            severity = int(level)
        else:
            _, severity = self.convert_priority_to_severity(level)
        debug(severity = severity)
        # print(f"Severity: {severity}")
        # if not facility_string: facility_string = ''
        if not facility: facility = ''
        # print "severity =", severity
        SEVERITY_STRING = ''
        debug(severity = severity)
        debug(severity_is_digit = str(severity).isdigit())
        debug(severity_config_show_string = self.CONFIG.get_config('GENERAL', 'show_severity_string'))
        debug(severity_config_show_string_check = self.CONFIG.get_config('GENERAL', 'show_severity_string') == 1 or self.CONFIG.get_config('GENERAL', 'show_severity_string') == True)

        # if str(severity).isdigit() and (self.CONFIG.get_config('GENERAL', 'show_severity_string') == 1 or self.CONFIG.get_config('GENERAL', 'show_severity_string') == True):
        #     SEVERITY_STRING = syslog.LEVEL_REVERSED.get(int(severity))
        #     debug(SEVERITY_STRING = SEVERITY_STRING)
        debug(SEVERITY_STRING = SEVERITY_STRING)
        return self._coloring(severity, facility, text, dtime)
        # if int(severity) == 0:
        #     fore_0, back_0 = self.get_level_color_config(0)
        #     if fore_0 and back_0:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_0, back_0) + " " + facility_string + make_colors(text, fore_0, back_0)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_0, back_0) + " " + facility_string + make_colors(text, 'white', 'magenta')
        # elif int(severity) == 1:
        #     fore_1, back_1 = self.get_level_color_config(1)
        #     if fore_1 and back_1:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_1, back_1) + " " + facility_string + make_colors(text, fore_1, back_1)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_1, back_1) + " " + facility_string + make_colors(text, 'white', 'blue')
        # elif int(severity) == 2:
        #     fore_2, back_2 = self.get_level_color_config(2)
        #     if fore_2 and back_2:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_2, back_2) + " " + facility_string + make_colors(text, fore_2, back_2)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_2, back_2) + " " + facility_string + make_colors(text, 'white', 'green')
        # elif int(severity) == 3:
        #     fore_3, back_3 = self.get_level_color_config(3)
        #     if fore_3 and back_3:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_3, back_3) + " " + facility_string + make_colors(text, fore_3, back_3)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_3, back_3) + " " + facility_string + make_colors(text, 'white', 'red')
        # elif int(severity) == 4:
        #     fore_4, back_4 = self.get_level_color_config(4)
        #     if fore_4 and back_4:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_4, back_4) + " " + facility_string + make_colors(text, fore_4, back_4)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_4, back_4) + " " + facility_string + make_colors(text, 'black', 'yellow')
        # elif int(severity) == 5:
        #     fore_5, back_5 = self.get_level_color_config(5)
        #     if fore_5 and back_5:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_5, back_5) + " " + facility_string + make_colors(text, fore_5, back_5)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_5, back_5) + " " + facility_string + make_colors(text, 'white', 'cyan')
        # elif int(severity) == 6:
        #     fore_6, back_6 = self.get_level_color_config(6)
        #     if fore_6 and back_6:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_6, back_6) + " " + facility_string + make_colors(text, fore_6, back_6)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_6, back_6) + " " + facility_string + make_colors(text, 'green')
        # elif int(severity) == 7:
        #     fore_7, back_7 = self.get_level_color_config(7)
        #     if fore_7 and back_7:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_7, back_7) + " " + facility_string + make_colors(text, fore_7, back_7)
        #     else:
        #         return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING, fore_7, back_7) + " " + facility_string + make_colors(text, 'yellow')
        # else:
        #     return make_colors(dtime, 'lm') + " " + self.coloring_severity_string(SEVERITY_STRING) + " " + facility_string + make_colors(text, 'red', 'white')

    def set_config(self, file_config_path='psyslog.ini'):
        if file_config_path:
            file_config_path = os.path.join(os.path.dirname(__file__), os.path.basename(file_config_path))
        else:
            file_config_path = os.path.join(os.path.dirname(__file__), 'psyslog.ini')
        try:
            import ConfigParser
        except:
            import configparser as ConfigParser
        cfg = ConfigParser.RawConfigParser(allow_no_value=True)
        cfg.optionxform = str
        if not os.path.isfile(file_config_path):
            f = open(file_config_path, 'w')
            f.close()
        return cfg, file_config_path

    def read_config(self, section, option, value=''):
        """
            option: section, option, filename='', value=None
        """
        cfg, config_file = self.set_config()
        cfg.read(config_file)
        
        try:
            data = cfg.get(section, option)
        except:
            try:
                self.write_config(section, option, value)
            except:
                # pass
                traceback.format_exc()
            try:
                data = cfg.get(section, option)
            except:
                return ''
        return data

    def write_config(self, section, option, value):
        cfg, config_file = self.set_config()
        if cfg:
            cfg.read(config_file)
        
        try:
            cfg.set(section, option, value)
        except:
            cfg.add_section(section)
            cfg.set(section, option, value)
        cfg_data = open(config_file,'wb')
        cfg.write(cfg_data) 
        cfg_data.close()  

        # import configset
        # configset.write_config(section, option, config_file, value)
        # # try:
        # #     cfg.set(section, option, value)
        # # except ConfigParser.NoSectionError:
        # #     cfg.add_section(section)
        # #     cfg.set(section, option, value)
        # # cfg_data = open(config_file,'wb')
        # # cfg.write(cfg_data) 
        # # cfg_data.close()

    def convert_time(self, time):
        '''function convert time
        
        Convert Integer to strftime {string} time
        based on format
        
        Arguments:
            time {int} -- integer timstamps
        
        Returns:
            string -- format: 'YEAR:MONT:DAY HOUR:MINUTE:SECOND:MILISECOND'
        '''
        x = datetime.fromtimestamp(time)
        # ct = make_colors(datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f'), 'magenta')
        #return datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f')
        return datetime.strftime(x, '%Y:%m:%d %H:%M:%S')
    
    def convert_time2(self, time):
        '''function convert time
        
        Convert Integer to strftime {string} time
        based on format
        
        Arguments:
            datetime {str} -- string datetime, format example: 'Jan 16 09:53:48' 
        
        Returns:
            string -- format: 'YEAR:MONT:DAY HOUR:MINUTE:SECOND:MILISECOND'
        '''
        debug(time = time)
        #c = re.findall(" \d{1} ", time)
        #if c:
            #c1 = c[0].strip()
            #c1 = " 0" + c1 + " "
            #time = time.replace(c[0], c1)
        x = datetime.strptime(time, '%Y %b %d %H:%M:%S')
        # ct = make_colors(datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f'), 'magenta')
        #return datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f')
        return datetime.strftime(x, '%Y:%m:%d %H:%M:%S')
    
    def convert_time3(self, time):
        '''function convert time
        
        Convert Integer to strftime {string} time
        based on format
        
        Arguments:
            datetime {str} -- string datetime, format example: 'Jan 16 09:53:48' 
        
        Returns:
            string -- format: 'YEAR:MONT:DAY HOUR:MINUTE:SECOND:MILISECOND'
        '''
        debug(time = time)
        c = re.findall(" \d{1} ", time)
        if c:
            c1 = c[0].strip()
            c1 = " 0" + c1 + " "
            time = time.replace(c[0], c1)
        x = datetime.strptime(time, '%Y %m %H:%M:%S')
        # ct = make_colors(datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f'), 'magenta')
        #return datetime.strftime(x, '%Y:%m:%d %H:%M:%S.%f')
        return datetime.strftime(x, '%Y:%m:%d %H:%M:%S')    

    def time_to_integer(self, timestamps):
        return time.mktime(timestamps.timetuple())

    def save_to_file(self, message, timestamps, facility_string='', logfile_name='psyslog.log', rotate='100M'):
        rotate = self.CONFIG.get_config('LOGS', 'rotate') or rotate
        if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs')):
            os.makedirs(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs'))
        rotate = rotate or self.CONFIG.get_config('LOGS', 'rotate')
        if facility_string: facility_string = " [" + facility_string + "] "
        message = timestamps + facility_string + message + "\n"
        if os.path.isfile(logfile_name):
            with open(logfile_name, 'a') as logfile:
                logfile.write(message)
        else:
            with open(logfile_name, 'w') as logfile:
                logfile.write(message)
        
        if bitmath.getsize(logfile_name).MB.value > bitmath.parse_string_unsafe(rotate).value:
            with open(logfile_name, 'w') as logfile:
                logfile.write("")
                    
    def rabbit_call_back(self, ch, met, prop, body):
        debug(body = body)
        data = body.decode() if hasattr(body, 'decode') else body
        debug(data = data)
        #print(make_colors(datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), 'lc') + " ", end = '')
        console.print(data)
        ch.basic_ack(delivery_tag = met.delivery_tag)
        
    def set_data(self, data):
        debug(data = data)
        if not data:
            console.print(f"[error]No Data ![/]")
            return            
        yield console.print(data.decode())
        
    def socket_handler(self, host = None, port = None):
        debug(host = host)
        debug(port = port)
        port = port or 1514
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = host or self.CONFIG.get_config('SERVER', 'host', '0.0.0.0')
        port = port or self.CONFIG.get_config('SERVER', 'port', '1514')
        debug(port = port)
        if isinstance(port, str): port = int(port)
        try:
            sock.bind((host, int(port[0])))
            # sock.listen(5)
            print("Syslog Bind: %s:%s [pid:%s]" %(make_colors(host, 'green'), make_colors(str(port), 'cyan'), make_colors(PID, 'white', 'blue')))
            while 1:
                data = sock.recv(65565)
                if data:
                    if data == 'EXIT':
                        sys.exit('server shutdown ....')
                    for i in self.set_data(data = data):
                        pass
                    # print "data =", data
                    # print "client_address =", client_address
                    # print self.handle(data, client_address)
        except KeyboardInterrupt:
            os.kill(os.getpid(), signal.SIGTERM)
        except SystemExit:
            sys.exit('SYSTEM EXIT !')
        except:
            CTraceback(*sys.exc_info())
            traceback.format_exc()
        
    def server(self, host='0.0.0.0', port=None, handler = 'socket'):
        debug(handler = handler)
        if handler == 'socket' or self.CONFIG.get_config('SERVER', 'handle') == 'socket':
            print("run with socket handler ...")
            self.socket_handler(host, port)
        elif handler in ['rabbit', 'rabbitmq'] or self.CONFIG.get_config('SERVER', 'handle') in ['rabbit', 'rabbitmq']:
            console.print(f"[notice]Run with[/] [error]RabbitMQ[/] [notice]handler ![/]")
            if self.CONFIG.get_config('rabbitmq', 'exchange_type') == 'fanout':
                try:
                    from . import fanout
                except:
                    import fanout

                self.username = self.CONFIG.get_config('rabbitmq', 'username') or 'guest'
                debug(self_username =  self.username)
                self.password = self.CONFIG.get_config('rabbitmq', 'password') or 'guest'
                debug(self_password = self.password)
                self.host = self.CONFIG.get_config('rabbitmq', 'host') or host or '127.0.0.1'
                debug(self_host = self.host)
                self.port = self.CONFIG.get_config('rabbitmq', 'port') or port or 5672
                debug(self_port = self.port)
                
                fanout.Fanout.main(self.CONFIG.get_config('rabbitmq', 'exchange_name') or 'syslog', self.rabbit_call_back, self.host, self.port, self.username, self.password)
            else:
                debug(exchange_type_config = self.CONFIG.get_config('rabbitmq', 'exchange_type'))
                if self.CONFIG.get_config('rabbitmq', 'exchange_type'):
                    console.print(f"[error]{self.CONFIG.get_config('rabbitmq', 'exchange_type')} not yet support/created ![/]")
                    sys.exit()
                else:
                    console.print(f"[error]Please set Exchange Type before in config file [/][notice]{self.CONFIG.filename()}[/] [error]![/]")

    def handle(self, data, client_address):
        # os.environ.update({'DEBUG':'1'})
        pid = os.getpid()
        hostname = ''
        app = ''
        global lineNumber
        show_priority = self.CONFIG.get_config('GENERAL', 'show_priority')
        send_queue = self.CONFIG.get_config('GENERAL', 'send_queue')
        save_to_database = self.CONFIG.get_config('GENERAL', 'save_to_database')
        save_to_file = self.CONFIG.get_config('GENERAL', 'save_to_file')
        database_type = self.CONFIG.get_config('DATABASE', 'database_type')
        log_file_name = self.CONFIG.get_config('LOGS', 'log_file_name')
        max_line = self.CONFIG.get_config('LOGS', 'max_line')
        rotate = self.CONFIG.get_config('LOGS', 'rotate')
        show_priority_number = self.CONFIG.get_config('GENERAL', 'show_priority_number')

        debug(show_priority = show_priority, debug = 1)
        debug(send_queue = send_queue, debug = 1)
        debug(save_to_file = save_to_file, debug = 1)
        debug(save_to_database = save_to_database, debug = 1)
        debug(database_type = database_type, debug = 1)
        debug(log_file_name = log_file_name, debug = 1)
        debug(max_line = max_line, debug = 1)
        debug(rotate = rotate, debug = 1)
        debug(show_priority_number = show_priority_number, debug = 1)

        dtime = None
        facility_string = ''
        data = data.decode() if hasattr(data, 'decode') else data
        debug(data = data, debug = 1)
        try:
            data_client_ip = re.findall('Original Address=(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', data)
            debug(data_client_ip = data_client_ip, debug = 1)
            if data_client_ip:
                client_address = data_client_ip[0]
                data = re.sub('Original Address=\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3}', '', data)
                debug(data = data, debug = 1)
                # client_address = make_colors(client_address, 'lc')
                client_address = f"[bold #55FFFF]{client_address}[/]"
            else:
                # client_address = make_colors(client_address[0], 'lc')
                client_address = f"[bold #55FFFF]{client_address[0]}[/]"
            debug(data = data, debug = 1)
            data = re.sub("\S{0,3} \d{0,2} \d{0,2}:\d{0,2}:\d{0,2} \d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3} Kiwi_Syslog_Server  ", "", data)
            debug(data = data, debug = 1)
            
            #client_address = make_colors(client_address[0], 'cyan')
            times = re.findall("\S{0,3} \d{0,2} \d{0,2}:\d{0,2}:\d{0,2} .*? ", data)
            debug(times = times)
            if times:
                data = re.sub("\S{0,3} \d{0,2} \d{0,2}:\d{0,2}:\d{0,2} .*? ", '', data)
                times, hostname = re.findall("(\S{0,3} \d{0,2} \d{0,2}:\d{0,2}:\d{0,2}) (.*?) ", times[0])[0]
                try:
                    times = f"[white on black]{self.convert_time(str(datetime.now().year) + ' ' + times)}[/]"
                except:
                    try:
                        times = f"[white on black]{self.convert_time2(str(datetime.now().year) + ' ' + times)}[/]"
                    except:
                        times = f"[white on black]{self.convert_time3(str(datetime.now().year) + ' ' + times)}[/]"
            else:
                # times = make_colors(self.convert_time(int(time.time())), 'white', 'black')
                times = f"[white on black]{self.convert_time(int(time.time()))}[/]"
            debug(times = times, debug = 1)
            
            debug(data = data, debug = 1)
            data_split = re.split('<|>', data, 2)
            debug(data_split=data_split, debug = 1)
            if data_split[0] == u'':
                number = data_split[1]
                message = " ".join(data_split[2:]).strip()
                debug(number=number, debug = 1)
                debug(message=message, debug = 1)
            else:
                number = data_split[0]
                message = " ".join(data_split[1:]).strip()
                debug(number=number, debug = 1)
                debug(message=message, debug = 1)
            app = re.findall("^.*?: ", message)
            debug(app = app, debug = 1)
            if app:
                message = re.sub("^.*?: ", "", message).strip()
                debug(data = data, debug = 1)
                app = app[0].strip()
            else:
                app = ''
            debug(message = message, debug = 1)
            
            if re.findall("\S{0,3}  \d{0,1} \d{0,2}:\d{0,2}:\d{0,2} ", message):
                dtime = re.findall("\S{0,3}  \d{0,1} \d{0,2}:\d{0,2}:\d{0,2} ", message)
                if dtime:
                    message = re.sub("\S{0,3}  \d{0,1} \d{0,2}:\d{0,2}:\d{0,2} ", '', message).strip()
                    dtime = datetime.strptime(dtime[0] + str(datetime.now().year), '%b  %d %H:%M:%S %Y')
                    dtime = datetime.strftime(dtime, '%Y/%m/%d %H:%M:%S')
                    message = re.sub(dtime + " ", '', message)
                    #message = dtime + " " + message
            debug(GENERAL_show_priority = self.CONFIG.get_config('GENERAL', 'show_priority'), debug = 1)
            # if self.CONFIG.get_config('GENERAL', 'show_priority') == 1 or self.CONFIG.get_config('GENERAL', 'show_priority') == True:
            #     facility_string = syslog.FACILITY_REVERSED.get(int(self.convert_priority_to_severity(number)[0])) or ''
            debug(facility_string = facility_string, debug = 1)
            debug(number = number, debug = 1)
            if self.CONFIG.get_config('GENERAL', 'show_priority_number'):
                data = self.coloring(number, data, int(self.convert_priority_to_severity(number)[0]), dtime)
            else:
                data = self.coloring(number, message, int(self.convert_priority_to_severity(number)[0]), dtime)
            
            #data = self.coloring(number, data)
            #data = self.coloring(number, message)
            debug(data=data, debug = 1)
            laengde = len(data)
            debug(laengde=laengde, debug = 1)
            # newLogString = "%s%s%s %s %s%s [%s]" % (make_colors(self.format_number(lineNumber), 'yellow'), make_colors('@', 'red'), times, client_address, make_colors(app, 'lb'), data, str(pid))
            # newLogString = f"[#FFFF00]self.format_number(lineNumber)[/][bold #FF007F]@[/]{times} {client_address} [bold #0055FF]{app}[/] {data} [bold #FFCBB3]{str(pid)}[/]"
            if laengde > 4:
                # newLogString = "%s%s%s %s %s%s [%s]" % (make_colors(self.format_number(lineNumber), 'yellow'), make_colors('@', 'red'), times, client_address, make_colors(app, 'lb'), data, str(pid))
                newLogString = f"[#FFFF00]{self.format_number(lineNumber)}[/][bold #FF007F]@[/]{times} {client_address} [bold #0055FF]{app}[/]{data} \[[bold #FFCBB3]{str(pid)}[/]]"
                if send_queue:
                    newLogString = "%s@%s %s %s%s [%s]" % (self.format_number(lineNumber), times, client_address, app, data, str(pid))
                    self.sent_to_broker(newLogString)
                if lineNumber > (self.CONFIG.get_config('LOGS', 'max_line') or 100000):
                    debug(lineNumber=lineNumber, debug = 1)
                    if sys.platform == 'win32':
                        os.system('cls')
                    else:
                        os.system('clear')
                    lineNumber = 1

                if save_to_file: self.save_to_file(message, times, facility_string, log_file_name, rotate)
            lineNumber += 1

            # if lineNumber > 10000000:
            # return newLogString
            # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if not newLogString: newLogString = data
            debug(newLogString = newLogString, debug = 1)
            debug(lineNumber = lineNumber, debug = 1)
            return newLogString, lineNumber

        except KeyboardInterrupt:
            print ("Closing .. by user")
            sys.exit(0)
        except:
            print(traceback.format_exc())
            print ("Closing .. by system")
            #sys.exit(0)

    def _client(self, host='0.0.0.0', port=514, server_port=1514):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.CONFIG.get_config('CLIENT', 'host', value= '0.0.0.0'):
            host = self.CONFIG.get_config('CLIENT', 'host', value= '0.0.0.0')
        if self.CONFIG.get_config('CLIENT', 'port', value= '1514'):
            port = int(self.CONFIG.get_config('CLIENT', 'port', value= '1514'))
        try:
            sock.bind((host, port))
            print ("Syslog Client Bind: %s:%s [%s]" %(make_colors(host, 'green'), make_colors(str(port), 'cyan'), PID))
            while 1:
                data, client_address = sock.recvfrom(65565)
                if data:
                    if data == 'EXIT':
                        sys.exit('server shutdown ....')
                    data, lineNumber = self.handle(data, client_address)
                    sock.sendto(data, ('127.0.0.1', server_port))
        except:
            traceback.format_exc()
            #print "Closing .. by system"
            #print make_colors('SYSTEM EXIT !', 'white', 'lightred', attrs= ['blink'])
            #sock.close()
            #sys.exit('SYSTEM EXIT !')
    def client(self, host = None, port = None, server_host = None, server_port = None, foreground = False, handler = None):
            
        import client
        host = host or self.CONFIG.get_config('CLIENT', 'host') or '0.0.0.0'
        port = port or self.CONFIG.get_config('CLIENT', 'port') or 514
        server_host = server_host or self.CONFIG.get_config('SERVER', 'host') or '0.0.0.0'
        server_port = server_port or self.CONFIG.get_config('SERVER', 'port') or 1514        
        debug(host = host)
        debug(port = port)
        debug(server_host = server_host)
        debug(server_port = server_port)
        handler = handler or self.CONFIG.get_config('SERVER', 'handle') or 'socket'
        debug(handler = handler, debug = 1)
        client.monitor(host, port, server_port, foreground, handler)
        
    def shutdown(self, host='127.0.0.1', port=514):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto("EXIT", (host, port))
        s.close()
        os.kill(os.getpid(), signal.SIGTERM)

    def tester(self):
        syslog.syslog('TEST MESSAGE EMERGENCY', 0, 5)
        syslog.syslog('TEST MESSAGE ALERT', 1, 5)
        syslog.syslog('TEST MESSAGE CRITICAL', 2, 5)
        syslog.syslog('TEST MESSAGE ERROR', 3, 5)
        syslog.syslog('TEST MESSAGE WARNING', 4, 5)
        syslog.syslog('TEST MESSAGE NOTICE', 5, 5)
        syslog.syslog('TEST MESSAGE INFO', 6, 5)
        syslog.syslog('TEST MESSAGE DEBUG', 7, 5)

    def usage(self):
        import argparse
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-s', '--server', action='store_true', help='run server')
        parser.add_argument('-c', '--client', action='store_true', help='run client server')
        parser.add_argument('-H', '--host', action='store', help='Host binding (SERVER/CLIENT) default:0.0.0.0 -- all network interface', default='0.0.0.0')
        parser.add_argument('-P', '--client-port', action='store', help='Port binding default: 514', default=514)
        parser.add_argument('-R', '--server-host', action='store', help='Host of Server default: 127.0.0.1', default= '127.0.0.1')
        parser.add_argument('-S', '--server-port', action='store', help='Port binding default: 1514', type = int, nargs = '*')
        parser.add_argument('-x', '--exit', action='store_true', help='shutdown/terminate server')
        parser.add_argument('-T', '--test', action='store_true', help='Test Send Message to port 514 (Client)')
        parser.add_argument('-f', '--foreground', action = 'store_true', help = 'Print data to foreground (CLIENT)')
        parser.add_argument('-t', '--type', help = 'Type of log, use --support to get list of support log type', action = 'store')
        parser.add_argument('--support', help = 'Get list of log type support', action = 'store_true')
        parser.add_argument('-ha', '--handler', help = "Server handler, valid argument: 'socket|rabbit[mq]|zero[mq]|kafka|redis', default = socket", default = 'socket')
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            args = parser.parse_args()
            if args.test:
                self.tester()
                sys.exit(0)
            if args.server:
                self.handler = args.handler
                self.server((args.server_host or args.host), args.server_port, args.handler)
                self.HOST = args.host or self.HOST
                self.PORT = args.server_port or self.PORT
            if args.client:
                print ("PID:", PID)
                debug(server_port = args.server_port)
                self.client(args.host, args.client_port, args.server_host, args.server_port, foreground = args.foreground, handler = args.handler)
                self.HOST = args.server_host or self.HOST
                self.PORT = args.server_port or self.PORT
                self.CLIENT_HOST = args.host
                self.CLIENT_PORT = args.port
            if args.exit:
                host = (args.host or args.server_host)
                if host == '0.0.0.0': host = '127.0.0.1'                
                if args.server:
                    self.shutdown(host, args.server_port)
                elif args.client:
                    self.shutdown(host, args.client_port)
                else:
                    self.shutdown(host, args.server_port)                
                    self.shutdown(host, args.client_port)


if __name__ == "__main__":
    c = Psyslog()
    c.usage()
