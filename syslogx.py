#!/usr/bin/python
# -*- encoding: iso-8859-1 -*-

"""
Python syslog client.

This code is placed in the public domain by the author.
Written by Christian Stigen Larsen.

This is especially neat for Windows users, who (I think) don't
get any syslog module in the default python installation.

See RFC3164 for more info -- http://tools.ietf.org/html/rfc3164

Note that if you intend to send messages to remote servers, their
syslogd must be started with -r to allow to receive UDP from
the network.
"""

import socket
import sys
# I'm a python novice, so I don't know of better ways to define enums

FACILITY = {
	'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
	'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
	'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
	'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
	'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
}

FACILITY_REVERSED = {
    0: 'kern', 1: 'user', 2: 'mail', 3: 'daemon',
    4: 'auth', 5: 'syslog', 6: 'lpr', 7: 'news',
    8: 'uucp', 9: 'cron', 10: 'authpriv', 11: 'ftp',
    16: 'local0', 17: 'local1', 18: 'local2', 19: 'local3',
    20: 'local4', 21: 'local5', 22: 'local6', 23: 'local7',
}


LEVEL = {
	'emerg': 0, 'emergency': 0, 'alert':1, 'crit': 2, 'critical': 2, 'err': 3, 'error': 3,
	'warning': 4, 'warn': 4, 'notice': 5, 'info': 6, 'debug': 7
}

LEVEL_REVERSED = {
    0: 'emerg',
    1: 'alert',
    2: 'criti',
    3: 'error',
    4: 'warni',
    5: 'notic',
    6: 'info ',
    7: 'debug',
}


def syslog(message, level=LEVEL['notice'], facility=FACILITY['daemon'], host='localhost', port=514):

	"""
	Send syslog UDP packet to given host and port.
	"""

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	data = '<%d>%s' % (level + facility*8, message)
	if sys.version_info.major == 3:
		data = data.encode('utf-8', errors = 'replace')
	sock.sendto(data, (host, port))
	sock.close()

if __name__ == '__main__':
	syslog(*sys.argv[1:])
