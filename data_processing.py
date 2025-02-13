
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

lineNumber = 0

class RFC:
    
    def __init__(self, message = None):
        
        self.CONFIG = configset(str(Path(__file__).parent / 'psyslog.ini'))
        if message: self.handle(message)

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
            
            lineNumber += 1

            return data, lineNumber

        except KeyboardInterrupt:
            print ("Closing .. by user")
            sys.exit(0)
        except:
            print(traceback.format_exc())
            print ("Closing .. by system")
            #sys.exit(0)
    
    def __call__(self, *args, **kwds):
        return self.handle(*args, **kwds)

    def __getattr__(self, name):
        if name in ['config', '__config__', 'Config', 'show', 'show_config', 'all_config']:
            data = {}
            console.print(f"[bold #FFFF00]\[GENERAL][/]")
            for i in self.CONFIG.options('GENERAL'):
                console.print(f"[bold #FFAA00]{i}[/] = [bold #00FFFF]{self.CONFIG.get_config('GENERAL', i)}[/]")
                data.update({i: self.CONFIG.get_config('GENERAL', i)})
            return {'GENERAL': data}
        elif name in ['config_file', '__config_file__', 'configname', '__configname__', 'configfile', '__configfile__']:
            return self.CONFIG.filename()
        elif name in self.CONFIG.options('GENERAL'):
            return self.CONFIG.get_config('GENERAL', name)
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
