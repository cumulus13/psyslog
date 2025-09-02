#!/usr/bin/env python

import sys
from ctraceback import CTraceback
sys.exepthook = CTraceback()
import os
from pydebugger.debug import debug
import re
from datetime import datetime
import time
import traceback
from configset import configset
from pathlib import Path
from rich.console import Console
console = Console()
import json5
from rich import print_json
import importlib

try:
    from . import syslog
except Exception:
    spec_syslog = importlib.util.spec_from_file_location("syslog", str(Path(__file__).parent / 'syslogx.py'))
    syslog = importlib.util.module_from_spec(spec_syslog)
    spec_syslog.loader.exec_module(syslog)

lineNumber = 0

class Dict(dict):
    
    def __init__(self, config, _dict = {}, **kwargs):
        super().__init__(**kwargs)  # Initialize the dict with the key-value pairs
        self.config = config
        self.update(_dict)
        
    def __getitem__(self, key):
        if key in self.config.sections():
            for i in self.config.options(key):
                console.print(f"[bold #FFAA00]{i}[/] = [bold #00FFFF]{self.config.get_config(key, i)}[/]")
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key in self.config.sections():
            for i in self.config.options(key):
                console.print(f"[bold #FFAA00]{i}[/] = [bold #00FFFF]{self.config.get_config(key, i)}[/]")
        return super().get(key, default)

class CONFIG:
    
    def __init__(self, message = None):        
        self.CONFIG = configset(str(Path(__file__).parent / 'psyslog.ini'))
        if message: self.handle(message)
        
    def get_date(self):
        return datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f')

    def __call__(self, *args, **kwds):
        return self.handle(*args, **kwds)

    def __getattr__(self, name):
        if name in ['config', '__config__', 'Config', 'show', 'show_config', 'all_config']:
            data1 = {}
            data2 = {}
            # console.print(f"[bold #FFFF00]\[GENERAL][/]")
            for i in self.CONFIG.options('GENERAL'):
                # console.print(f"[bold #FFAA00]{i}[/] = [bold #00FFFF]{self.CONFIG.get_config('GENERAL', i)}[/]")
                data1.update({i: self.CONFIG.get_config('GENERAL', i)})
            
            # console.print("\n")    
            # console.print(f"[bold #FFFF00]\[LOGS][/]")
            for i in self.CONFIG.options('LOGS'):
                # console.print(f"[bold #FFAA00]{i}[/] = [bold #00FFFF]{self.CONFIG.get_config('GENERAL', i)}[/]")
                data2.update({i: self.CONFIG.get_config('GENERAL', i)})
            
            return Dict(self.CONFIG, {'GENERAL': data1, 'LOGS': data2})
        
        elif name in ['config_file', '__config_file__', 'configname', '__configname__', 'configfile', '__configfile__']:
            return self.CONFIG.filename()
        elif name in self.CONFIG.options('GENERAL'):
            return self.CONFIG.get_config('GENERAL', name)
        elif name in self.CONFIG.options('LOGS'):
            return self.CONFIG.get_config('LOGS', name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        debug(name = name)
        debug(value = value)
        # if name == "CONFIG":  # Directly set CONFIG without recursion
        #     super().__setattr__(name, value)
        #     return
        
        if name and name not in ['config', 'CONFIG', 'Config'] and hasattr(self, "CONFIG") and name in self.CONFIG.options('GENERAL') and str(value).strip() not in ["None", '']:
            # print(f"write config {name} = {value}")
            self.CONFIG.write_config('GENERAL', name, str(value))
        else:
            super().__setattr__(name, value)

class RFC(CONFIG):
    
    def priority_to_severity_facility(self, priority):
        facility = priority // 8
        severity = priority % 8
        
        facilities = [
            "kern", "user", "mail", "daemon", "auth", "syslog", "lpr", "news",
            "uucp", "clock", "authpriv", "ftp", "ntp", "logaudit", "logalert", "cron",
            "local0", "local1", "local2", "local3", "local4", "local5", "local6", "local7"
        ]
        severities = [
            "emergency", "alert", "critical", "error", "warning", "notice", "informational", "debug"
        ]
        
        return {
            "facility": facilities[facility] if facility < len(facilities) else "unknown",
            "severity": severities[severity] if severity < len(severities) else "unknown"
        }
    
    def handle(self, message):
        """
        The function `handle` processes incoming data, extracts relevant information, formats it, and
        saves it to a file or sends it to a broker.
        
        :param data: The `handle` method in the provided code snippet seems to be processing log data
        received from a client. The `data` parameter in this method represents the log data that is
        being processed. The method performs various operations on the `data` such as decoding, parsing,
        and formatting before returning a new
        :param client_address: The `client_address` parameter in the `handle` method of the code snippet
        you provided is used to store the client's IP address extracted from the incoming data. It is
        initially set to an empty string (`''`) and then updated based on the data received. The IP
        address is extracted using a
        :return: The `handle` method returns two values: `newLogString` and `lineNumber`.
        """
        
        global lineNumber
        data = ""
        
        show_priority = self.CONFIG.get_config('GENERAL', 'show_priority')
        send_queue = self.CONFIG.get_config('GENERAL', 'send_queue')
        save_to_database = self.CONFIG.get_config('GENERAL', 'save_to_database')
        save_to_file = self.CONFIG.get_config('GENERAL', 'save_to_file')
        database_type = self.CONFIG.get_config('DATABASE', 'database_type')
        log_file_name = self.CONFIG.get_config('LOGS', 'log_file_name')
        max_line = self.CONFIG.get_config('LOGS', 'max_line')
        rotate = self.CONFIG.get_config('LOGS', 'rotate')
        show_priority_number = self.CONFIG.get_config('GENERAL', 'show_priority_number')

        debug(show_priority = show_priority)
        debug(send_queue = send_queue)
        debug(save_to_file = save_to_file)
        debug(save_to_database = save_to_database)
        debug(database_type = database_type)
        debug(log_file_name = log_file_name)
        debug(max_line = max_line)
        debug(rotate = rotate)
        debug(show_priority_number = show_priority_number)

        dtime = None
        facility_string = ''
        message = message.decode() if hasattr(message, 'decode') else message
        debug(data = data)
        
        try:
            # Extract "Original Address" as hostname if present
            address_match = re.search(r'Original Address=(?P<host>\S+)\s+', message)
            if address_match:
                host = address_match.group('host')
                message = re.sub(r'Original Address=\S+\s+', '', message, 1)
            else:
                host = None
            
            # Attempt to remove unexpected prefixes before the priority field
            message = re.sub(r'^[^<]*<', '<', message, 1)
            
            # Define regex patterns for RFC 3164 and RFC 5424
            rfc3164_pattern = re.compile(r'^<(?P<priority>\d+)>\s*(?P<timestamp>[A-Za-z]+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(?P<syslog_host>\S+)\s+(?P<appname>[^:]+):\s*(?P<message>.*)$')
            rfc5424_pattern = re.compile(r'^<(?P<priority>\d+)>\d\s+(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2})\s+(?P<syslog_host>\S+)\s+(?P<appname>\S+)\s+\d+\s+-\s+-\s+(?P<message>.*)$')
            
            match = rfc3164_pattern.match(message) or rfc5424_pattern.match(message)
            
            if match:
                data = match.groupdict()
                
                # Use extracted host if available
                data['host'] = host if host else data.pop('syslog_host', None)
                
                # Convert timestamp
                if 'T' in data['timestamp']:  # RFC 5424
                    data['timestamp'] = datetime.strptime(data['timestamp'], "%Y-%m-%dT%H:%M:%S.%f%z")
                else:  # RFC 3164
                    data['timestamp'] = datetime.strptime(data['timestamp'], "%b %d %H:%M:%S")
                    data['timestamp'] = data['timestamp'].replace(year=datetime.now().year)  # Assume current year

            debug(data=data)
            if not data: return f"{message} [error]\[FAILED TO PARSE !][/]"
            debug(GENERAL_show_priority = self.CONFIG.get_config('GENERAL', 'show_priority'))
            debug(facility_string = facility_string)
            if self.CONFIG.get_config('GENERAL', 'show_priority_number'):
                pass
            
            # if save_to_file: self.save_to_file(message, times, facility_string, log_file_name, rotate)
            
            if lineNumber and lineNumber > (self.CONFIG.get_config('LOGS', 'max_line') or 100000):
                debug(lineNumber=lineNumber)
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                lineNumber = 1
            elif not lineNumber:
                lineNumber = 1
            else:
                lineNumber += 1

            return data, lineNumber

        except KeyboardInterrupt:
            print ("Closing .. by user")
            sys.exit(0)
        except:
            print(traceback.format_exc())
            print ("Closing .. by system")
            #sys.exit(0)
    
class JSON(CONFIG):

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

    def priority_to_severity_facility(self, priority):
        facility = priority // 8
        severity = priority % 8
        
        facilities = [
            "kern", "user", "mail", "daemon", "auth", "syslog", "lpr", "news",
            "uucp", "clock", "authpriv", "ftp", "ntp", "logaudit", "logalert", "cron",
            "local0", "local1", "local2", "local3", "local4", "local5", "local6", "local7"
        ]
        severities = [
            "emergency", "alert", "critical", "error", "warning", "notice", "informational", "debug"
        ]
        
        return {
            "facility": facilities[facility] if facility < len(facilities) else "unknown",
            "severity": severities[severity] if severity < len(severities) else "unknown"
        }
        
    def handle(self, data, N = None):
        global lineNumber
        data_raw = data
        # Example raw data from rsyslog with json format
        # {
        #     'tag': 'rsyslog_server',
        #     'msg': ' -- MARK --',
        #     'rawmsg': '<46>Jan 27 04:47:29 rsyslogd: -- MARK --',
        #     'hostname': 'd812c8fc19b3',
        #     'fromhost': 'd812c8fc19b3',
        #     'fromhost-ip': '127.0.0.1',
        #     'syslogtag': 'rsyslogd:',
        #     'pri': '46',
        #     'syslogfacility': '5',
        #     'syslogfacility-text': 'syslog',
        #     'syslogseverity': '6',
        #     'syslogseverity-text': 'info',
        #     'timereported': '2025-01-27T11:47:29.155219+07:00',
        #     'timegenerated': '2025-01-27T11:47:29.155219+07:00',
        #     'programname': 'rsyslogd',
        #     'protocol-version': '0',
        #     'inputname': 'imuxsock'
        # }
        
        try:
            data = json5.loads(data)
            
            lineNumber = int(lineNumber) if lineNumber and str(lineNumber).isdigit() else 1
            
            timereported = self.convert_time4(data.get('timereported'))
            debug(timereported = timereported)
            timereported_color = f"[bold #FFFFFF]{timereported}[/]" if timereported else ''
            
            hostname = data.get('fromhost') or data.get('hostname')
            debug(hostname = hostname)
            hostname_color = f"[white on #005500]{hostname}[/]" if hostname else ''
            
            tag = data.get('tag')
            debug(tag = tag)
            tag_color = f"[white on #00007F]{tag}[/]" if tag else '' 
            
            ip = data.get('fromhost-ip')
            debug(ip = ip)
            ip_color = f"[white on #55007F]\[{ip}][/]" if ip else ''
            
            app = data.get('programname') or data.get('syslogtag')
            debug(app = app)
            app_color = f"[white on #0055FF]{app}[/]" if app else ''
            
            facility = data.get('syslogfacility-text') or syslog.FACILITY_REVERSED.get(data.get('syslogfacility')) if data.get('syslogfacility') else ''
            debug(facility = facility)
            facility_colors = f"[black on #AAFF00]\[{facility}][/]" if facility else ''
            
            message = data.get('msg') or data.get('message')
            debug(message = message)
            message_color = f"[{data.get('syslogseverity-text') or syslog.LEVEL_REVERSED.get(data.get('syslogseverity')) or self.convert_priority_to_severity.get('pri')}]{message}[/]"
            
            data_color = f"[#FFFF00 on #000000]{str(self.format_number(lineNumber))}[/]" + '@' + timereported_color + " " + tag_color + " " + hostname_color + ip_color + " " + app_color + " " + facility_colors + " " + message_color
            debug(data_color = data_color)
            console.print(data_color)
            debug(lineNumber = lineNumber)
            
            if lineNumber and lineNumber > (self.CONFIG.get_config('LOGS', 'max_line') or 100000):
                debug(lineNumber=lineNumber)
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                lineNumber = 1
            elif not lineNumber:
                lineNumber = 1
            else:
                lineNumber += 1
            
            # return self.format_number(lineNumber) + '@' + timereported + " " + tag + "/" + hostname + ip + " " + app + " " + facility + " " + message, N
            return f"{self.format_number(lineNumber)}@{timereported} {tag}/{hostname}{ip} {app} {facility} {message}", lineNumber
            
        except Exception as e:
            CTraceback(*sys.exc_info(), print_it = True if os.getenv('VERBOSE') in ["1", "True", "true"] else False)
            console.log(f"e0 = [error]{e}[/]")
            try:
                print_json(data) if os.getenv('VERBOSE') in ["1", "True", "true"] else None
            except Exception as e1:
                CTraceback(*sys.exc_info(), print_it = True if os.getenv('VERBOSE') in ["1", "True", "true"] else False)
                console.log(f"e1 = [error]{e1}[/]")
                
                try:
                    print_json(data = data) if os.getenv('VERBOSE') in ["1", "True", "true"] else None
                except Exception as e2:
                    CTraceback(*sys.exc_info(), print_it = True if os.getenv('VERBOSE') in ["1", "True", "true"] else False)
                    console.log(f"e2 = [error]{e2}[/]")
                    console.print(data) if os.getenv('VERBOSE') in ["1", "True", "true"] else None
    
            return f"{self.format_number(lineNumber)}@{self.get_date()} [white on red blink]ERROR parse date:[/] [white on blue]{e1}[/] : [white on magenta]{e2}[/] : [bold #00FFFF]{data_raw}[/]", lineNumber
    