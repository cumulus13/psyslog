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
import traceback
import os
# I'm a python novice, so I don't know of better ways to define enums

FACILITY = {
	'kern': 0,     0:'kern',          'note 1': 4,
	'user': 1,     1:'user',		  'note 2': 9,
	'mail': 2,     2:'mail',          'user-level': 1,
	'daemon': 3,   3:'daemon',        'system daemon': 3,       
	'auth': 4,     4:'auth',          'security': 4,
	'syslog': 5,   5:'syslog',        'internal': 5,
	'lpr': 6,      6:'lpr',           'line printer':6,
	'news': 7,     7:'news',          'network news': 7,
	'uucp': 8,     8:'uucp',           'UUCP': 8,
	'cron': 9,     9:'cron',          
	'authpriv':10, 10:'authpriv', 
	'ftp': 11,     11:'ftp',
	'ntp': 12,     12:'ntp',
	'audit': 13,   13:'audit',
	'alert': 14,   14:'alert',
	'clock': 15,   15:'clock',
	'local0': 16,  16:'local0',
	'local1': 17,  17:'local1',
	'local2': 18,  18:'local2',
	'local3': 19,  19:'local3',
	'local4': 20,  20:'local4',
	'local5': 21,  21:'local5',
	'local6': 22,  22:'local6',
	'local7': 23,  23:'local7',
}

LEVEL = {
	'emerg': 0,  0:'emergency', 'emergency': 0,
	'alert':1,   1:'alert', 
	'crit': 2,   2:'critical', 'critical': 2,
	'err': 3,    3:'error', 'error': 3,
	'warning': 4,4:'warning', 
	'notice': 5, 5:'notice',
	'info': 6,   6:'info',
	'debug': 7,   7:'debug'
}

SEVERITY = LEVEL

def syslog(message, level=LEVEL['notice'], facility=FACILITY['daemon'],
	host='localhost', port=514):

	"""
	Send syslog UDP packet to given host and port.
	"""

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	data = '<%d>%s' % (level + facility*8, message)
	try:
		sock.sendto(data, (host, port))
	except:
		if os.getenv('DEBUG'):
			print "ERROR:"
			traceback.format_exc(syslog = False)
	sock.close()

