#!/usr/bin/python
##############################################################################
# Project: 	SBProbe
# Module: 	sbprobe.py
# Purpose: 	Server for interactive Modbus/TCP web client.
# Language:	Python 2.5
# Date:		06-May-2010.
# Ver:		24-Jul-2010.
# Author:	M. Griffin.
# Copyright:	2008 - 2010 - Michael Griffin       <m.os.griffin@gmail.com>
#
# This file is part of SBProbe.
# SBProbe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# SBProbe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with SBProbe. If not, see <http://www.gnu.org/licenses/>.
#
# Important:	WHEN EDITING THIS FILE, USE TABS TO INDENT - NOT SPACES!
##############################################################################

_HelpStr = """
SBProbe Ver. 24-Jul-2010

This program allows for interactive reading and writing of the data table
addresses in a SAIA Ether SBus field device. It provides a simple combination 
http (web) server and field device client (master). The field device must 
use SBus. Requests from a web browser are translated into the field
device protocol commands and passed through to the field device. Replies 
from the field device are in turn translated and passed back to the web 
browser.

This program can be started with a variety of command line parameters. 
Any parameters which are not specified will use their default values. 
The parameters can also be set through the web based user interface
after the system has started. These include:

-p Port number of web server (this program). The default is 8680.
-h Name or address of field device. The default is localhost.
-r Port number of field device. The default is 5050.
-u Station address of field device. The default is 1. (This is device specific).
-t Timeout for communications. The default is 5.0 seconds.
-c Auto connect ('y' for yes). The default is no.
-a Auto reconnect ('y' for yes). The default is yes.
-e hElp. (this screen).

Example: (Linux)

./sbprobe.py -p 8680 -h localhost -r 5050 -u 1 -t 30.0 -c y -a y

Example: (MS Windows)

c:\python25\python sbprobe.py -p 8680 -h localhost -r 5050 -u 1 -t 30.0 -c y -a y

To access the user interface, enter the URL of a web page into the address
bar of a web browser. E.g.

http://localhost:8680/help.html

Replace the address and port number as required.


Author: Michael Griffin
Copyright 2008 - 2010 Michael Griffin. This is free software. You may 
redistribute copies of it under the terms of the GNU General Public License
<http://www.gnu.org/licenses/gpl.html>. There is NO WARRANTY, to the
extent permitted by law.

"""

############################################################

import http.server
import socketserver
import os
import posixpath
import shutil
import time
import getopt, sys
import signal
import mimetypes
import urllib.parse

import MBWebPage

import RequestHandler
import SBusClient

############################################################

# Name of the directory where the web pages are stored.
AppPageDir = "C:\\Users\\Thomas Grob\\PycharmProjects\\tahu\\sbusserver\\mbprotocols\\clientpages\\"

tf=open(AppPageDir+"help.html","r")
print (tf)
# Names of the reports.
HelpPage = 'help.html'
ReadDataPage = 'readdata.html'
WriteDataPage = 'writedata.html'
SetParamsPage = 'setparams.html'

ReportPages = [ReadDataPage, WriteDataPage, SetParamsPage]


# Name of this program.
_SOFTNAME = 'SBProbe-SBC'

# Version of this server.
_VERSION = _SOFTNAME + ' 24-Jul-2010'


############################################################
class GetOptions:
	"""Get the command line options.
	If the user does not set any options, then default values are returned.
	"""

	########################################################
	def __init__(self):
		self._port = 8680
		self._rhost = 'localhost'
		self._rport = '5050'
		self._runitid = 1
		self._timeout = 5.0
		self._autoconnect = False
		self._autoreconnect = True

		# Read the command line options.
		try:
			opts, args = getopt.getopt(sys.argv[1:], 'p: h: r: u: t: e: c: a:', 
				['port', 'remotehost', 'remoteport', 'unitid', 
					'timeout', 'help', 'connect' 'autoconnect'])
		except:
			print('Unrecognised options.')
			sys.exit()

		# Parse out the options.
		for o, a in opts:

			# Port for web server.
			if o == '-p':
				try:
					self._port = int(a)
				except:
					print('Invalid local port number.')
					sys.exit()

			# Remote host name or IP address.
			elif o == '-h':
				if (len(a) > 0):
					self._rhost = a
				else:
					print('Invalid remote host name.')
					sys.exit()

			# Remote port number.
			elif o == '-r':
				try:
					self._rport = int(a)
				except:
					print('Invalid remote port number.')
					sys.exit()


			# Remote unit id.
			elif o == '-u':
				try:
					self._runitid = int(a)
				except:
					print('Invalid remote station address number.')
					sys.exit()
				if ((self._runitid > 255) or (self._runitid < 0)):
					print('Invalid remote station address number.')
					sys.exit()


			# Time out for field device communications.
			elif o == '-t':
				try:
					self._timeout = float(a)
				except:
					print('Invalid time out.')
					sys.exit()
				if (self._timeout < 0.0):
					print('Invalid Invalid time out.')
					sys.exit()

			# Auto connect on start up.
			elif o == '-c':
				self._autoconnect = (a in ['y', 'Y'])

			# Auto re-connect on error.
			elif o == '-a':
				self._autoreconnect = (a in ['y', 'Y'])

			# Help.
			elif o == '-e':
				print(_HelpStr)
				sys.exit()

			else:
				print(('Unrecognised option %s %s' % (o, a)))
				sys.exit()

	########################################################
	def GetPort(self):
		"""Return the port setting.
		"""
		return self._port

	########################################################
	def GetRemoteParams(self):
		"""Return the remote server parameters.
		Return: hostname, portnumber, timeout, unitid, autoreconnect
		"""
		return self._rhost, self._rport, self._timeout, self._runitid, self._autoreconnect


	########################################################
	def GetAutoConnect(self):
		"""Returns True if autoconnect is selected.
		"""
		return self._autoconnect


############################################################



############################################################

class HMIWebRequestHandler(http.server.BaseHTTPRequestHandler):


	########################################################
	# Set server version number.
	server_version = _VERSION
	# Set HTTP version.
	protocol_version = 'HTTP/1.0'
	print ("t HTTP version")


	########################################################
	# This is just used to enable silencing the routine connection logging.
	def _request_report(self, result):
		pass


	# Turn off routine display of connections.
	log_request = _request_report


	########################################################
	def do_GET(self):
		"""Serve a GET request."""
		print ("t do Get")
		# Check if the request is the right length. The first element
		# should be a blank ''.
		fpath = self.path.split('/')
		if (len(fpath) == 2):
			filepath = fpath[1]
		else:
			# If it wasn't found, return an error
			self.send_error(404, 'File not found: %s - bad path length.' % self.path)
			return


		# Handle the report request.
		self._HandleReportFile(filepath)


	########################################################
	def do_HEAD(self):
		print ("t du Head")
		"""Serve a HEAD request."""
		f = self.send_head()
		if f:
			f.close()

	########################################################
	def _HandleReportFile(self, filepath):
		"""Handle a page request.
		Parameters: filepath (string) = file name.
		Returns: Nothing. It writes the file out to the browser.
		"""
		print ("t HandelreportFile")
		# Check in the application report directory.
		f, ctype, flength, ftime, ErrorStr = MBWebPage.GetWebPage(AppPageDir, filepath)
		# Send the reply.
		if f:
			# Is is a recognised report?
			if (filepath in ReportPages):
				reportfile = f.read(-1)
				f.close()

				# Substitute in the data.
				# Read the field device.
				if (filepath == ReadDataPage):
					reportdata = reportfile % ReadRequestHandler.GetPagedata()
				# Write to the field device.
				elif (filepath == WriteDataPage):
					reportdata = reportfile % WriteRequestHandler.GetPagedata()
				# Change the communications parameters.
				elif (filepath == SetParamsPage):
					reportdata = reportfile
					reportdata = reportfile % ConnectionHandler.GetPagedata()
				else:
					reportdata = ''

				# Send the headers.
				self.send_head(ctype, len(reportdata), ftime)
				# Send the page.
				self.wfile.write(reportdata)
			else:
				# We don't recognise the file name, so just send it.
				# Send the headers.
				self.send_head(ctype, flength, ftime)
				# Send the page.
				shutil.copyfileobj(f, self.wfile)
				f.close()

		else:
			# Still didn't find it? Return an error.
			self.send_error(404, ErrorStr)


	########################################################
	def _GetHeaderData(self, recvheaders):
		"""Extract the content length and referer file from
		the headers.
		"""
		print ("t Get Headeer Data")
		headerlist = str(recvheaders).splitlines()
		contentlengthstr = ''
		postreferer = ''
		for headline in headerlist:
			if headline.startswith('Content-Length:'):
				contentlengthstr = headline.split('Content-Length:')[1]
			elif headline.startswith('Referer:'):
				postreferer = headline.split('Referer:')[1]

		contentlength = int(contentlengthstr)

		filepath = urllib.parse.urlparse(postreferer).path

		return contentlength, filepath


	########################################################
	def do_POST(self):
		"""Serve a POST request."""
		print ("t Post")

		# Split the headers into separate lines.
		recvheaders = self.headers
		contentlength, filepath = self._GetHeaderData(recvheaders)

		content = self.rfile.read(contentlength)

		# Get the file name from the path. This should be in the form
		# [' http:', '', 'localhost:8680', 'readdata.html']
		fpath = filepath.split('/')[-1]

		# Substitute in the data.
		if (fpath == ReadDataPage):
			ReadRequestHandler.ReadData(content)
		elif (fpath == WriteDataPage):
			WriteRequestHandler.WriteData(content)
		elif (fpath == SetParamsPage):
			ConnectionHandler.ConnectData(content)
			

		# Process the report file.
		self._HandleReportFile(fpath)




	########################################################
	def send_head(self, ctype, flength, lastmod):
		""" Send the headers."""
		print ("t send head")
		# The file was found and opened, now send the response.
		self.send_response(200)
		self.send_header('Content-type', ctype)  
		self.send_header('Content-Length', flength)
		self.send_header('Last-Modified', self.date_time_string(lastmod))
		self.end_headers()



#############################################################################

############################################################
##########TTTTTTTTTTTTT
class MyTCPRequestHandler(socketserver.StreamRequestHandler):

# handle() method will be called once per connection
    def handle(self):
        # Receive and print the data received from client
        print("Recieved one request from {}".format(self.client_address[0]))
        msg = self.rfile.readline().strip()
        print("Data Recieved from client is:".format(msg))
        print(msg)

        # Send some data to client
        self.wfile.write("Hello Client....Got your message".encode())
        print("Data to client is sent")
##########TTTTTTTTTTTTT

# Signal handler.
def SigHandler(signum, frame):
	print(('Operator terminated server at %s' % time.ctime()))
	sys.exit()


# Initialise the signal handler.
signal.signal(signal.SIGINT, SigHandler)


# Get the command line parameter options.
CmdOpts = GetOptions()

# Initialise the read parameter validator.
ReadParams = SBusClient.ReadParamValidator()
# Initialise the write parameter validator.
WriteParams = SBusClient.WriteParamValidator()

# Handles setting communications parameters.
ConnectionHandler = RequestHandler.ConnectionStat(5050, SBusClient.SBus)
# Set the current version number for display on the web pages.
ConnectionHandler.SetVersionInfo(_VERSION)

# Handles reading data.
ReadRequestHandler = RequestHandler.ReadData(ReadParams, ConnectionHandler)
# Handles writing data.
WriteRequestHandler = RequestHandler.WriteData(WriteParams, ConnectionHandler)

############################################################


# Initialise the client. First get the remote host parameters.
rhost, rport, rtimeout, runitid, autoreconnect = CmdOpts.GetRemoteParams()

# Set the parameters. 
ConnectionHandler.SetConnectionParams(rhost, rport, rtimeout, runitid, autoreconnect)

if CmdOpts.GetAutoConnect():
	ConnectionHandler.Connect()


# If we exit and then try to restart the server again immediately,
# sometimes we cannot bind to the port until a short period of time
# has passed. In this case, we will sleep, and try again later. If
# we still don't succeed after several attempts, we will give up.
		
bindcount = 10
while True:
	try:
#		allow_reuse_address = True
#		httpd = socketserver.TCPServer(("127.0.0.1", CmdOpts.GetPort()), MyTCPRequestHandler)
		httpd = socketserver.TCPServer(("127.0.0.1", CmdOpts.GetPort()), HMIWebRequestHandler)
		print ("t socketserver up")
		break	# Succeeded, so we can exit this loop.
	except:
		if (bindcount > 0):
			print(('Failed to bind to socket for port: %d. Will retry in 30 seconds...' % CmdOpts.GetPort()))
			bindcount -= 1
			time.sleep(30)
		else:
			print(('Failed to bind to socket for port: %d. Exiting...' % CmdOpts.GetPort()))
			sys.exit()
		
# Print a welcome message.
print(('\nStarted %s on %s at port %s.' % 
	(_VERSION, time.ctime(), CmdOpts.GetPort())))


# Start up the server.
httpd.serve_forever()

#############################################################################

