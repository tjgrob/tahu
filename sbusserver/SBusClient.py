##############################################################################
# Project: 	MBProbe
# Module: 	SBusClient.py
# Purpose: 	Handle requests to client for data.
# Language:	Python 2.5
# Date:		06-May-2010.
# Ver.:		07-May-2010.
# Copyright:	2010 - Michael Griffin       <m.os.griffin@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# Important:	WHEN EDITING THIS FILE, USE TABS TO INDENT - NOT SPACES!
##############################################################################

"""
This handles the client interface to the field device for all requests.
"""


from mbprotocols import SBusMsg
import SBusSimpleClient
from mbprotocols import ModbusDataStrLib

############################################################

# Error messages.
_ErrorMsgs = {'invalidaddress' : 'Invalid address.',
	'invalidcmdcode' : 'Invalid command code.',
	'invaliddataformat' : 'Invalid data format.',
	'invalidparam' : 'Invalid parameter.',
	'responselength' : 'Invalid response length.',
	'crcerr' : 'CRC error.',
	'deviceerror' : 'Device error.',
	'badmessage' : 'Bad response message.',

	'connnecterror' : 'Error - Could not establish contact with remote host.',
	'dataerr' : 'Invalid data.',

	'badcmdcode' : 'Unsupported command code.',
	
}

############################################################
class ReadParamValidator:
	"""Validate the read parameters for SAIA SBus.
	"""

	def __init__(self):
		# Command code translation for reading.
		self._ReadCmdCodes = {'Flag' : 2,
				'Input' : 3,
				'Output' : 5,
				'Register' : 6
				}

	########################################################
	def Validate(self, addrtype, addr):
		"""Validate the parameters entered by the user for a read operation.
		This checks for format only. It does not check to see if the values
		are within range.
		Parameters: addrtype (string) = The type of address (flag, etc.).
		addr (string) = The address to read from.
		Returns: (tuple) = (SBus command code, SBus address, Error string). 
			Command code and address are integers if OK, or are None if either 
			an error occurred, or if no address type was selected.
			Error string will return an error message if an error was detected,
			or an empty string if not.
		"""


		cmdcode = None
		addrval = None

		# If no function is selected, skip the further checks.
		if (addrtype == 'None'):
			return cmdcode, addrval, ''


		# See if the address type is OK.
		try:
			cmdcode = self._ReadCmdCodes[addrtype]
		except:
			cmdcode = None
			return cmdcode, addr, _ErrorMsgs['invalidcmdcode']
		
		# Check the address to see if it is a number.
		try:
			# Convert to integer.
			addrval = int(addr)
		except:
			addrval = None
			return cmdcode, addr, _ErrorMsgs['invalidaddress']
			

		return cmdcode, addrval, ''



############################################################


############################################################
class WriteParamValidator:
	"""Validate the write parameters for SAIA SBus.
	"""

	def __init__(self):
		# Command code translation for writing.
		self._WriteCmdCodes = {'Flag' : 11,
				'Output' : 13,
				'Register' : 14,
				}


	########################################################
	def Validate(self, addrtype, addr, writedata):
		"""Validate the parameters entered by the user for a write operation.
		This checks for format only. It does not check to see if the values
		are within range.
		Parameters: addrtype (string) = The type of address (coil, etc.).
		addr (string) = The address to read from.
		writedata (string) = Register value to be checked.
		Returns: (tuple) = (SBus command code, SBus address, 
			Validated data value, Error string). Command code, address, and
			data value are integers if OK, or all are None if either an error 
			occurred, or if no address type was selected.
			Error string will return an error message if an error was detected,
			or an empty string if not.
		"""


		cmdcode = None
		addrval = None
		wval = None

		# If no function is selected, skip the further checks.
		if (addrtype == 'None'):
			return cmdcode, addrval, wval, ''

		# See if the address type is OK.
		try:
			cmdcode = self._WriteCmdCodes[addrtype]
		except:
			cmdcode = None
			return cmdcode, addrval, wval, _ErrorMsgs['invalidcmdcode']
		
		# Check the address to see if it is a number.
		try:
			# Convert to integer.
			addrval = int(addr)
		except:
			addr = None
			return cmdcode, addrval, wval, _ErrorMsgs['invalidaddress']

		# Check the value to see if it is a number.
		try:
			# Convert to integer.
			wval = int(writedata)
		except:
			wval = None
			return cmdcode, addrval, wval, _ErrorMsgs['invaliddataformat']

		return cmdcode, addrval, wval, ''

############################################################



############################################################
class SBus:
	"""Create a SAIA SBus client to communcate with the source of the HMI data.
	"""

	########################################################
	def __init__(self, host, port, timeout, stnaddr=1):
		"""
		host (string) = IP address of server.
		port (integer) = Port for server.
		timeout (float) = Time out in seconds.
		stnaddr (integer) = The desired SBus station address.
		"""
		self._host = host
		self._port = port
		self._timeout = timeout
		self._stnaddr = stnaddr
		self._msgsequence = 1

		# Define the boolean values for 0 and 1.
		self._bitoff = ModbusDataStrLib.boollist2bin([False, False, False, False, False, False, False, False])
		self._biton = ModbusDataStrLib.boollist2bin([True, False, False, False, False, False, False, False])

		# Initialise the client connection.
		try:
			self._msg = SBusSimpleClient.SBusSimpleClient(self._host,
								 self._port, self._timeout)
		except:
			self._msg = None
			print((_ErrorMsgs['connnecterror']))
			# Raise the exception again so the next layer can deal with it.
			raise


	########################################################
	def _IncMsgSeq(self):
		"""Increment the message sequence.
		"""
		self._msgsequence +=1
		if self._msgsequence > 32767:
			self._msgsequence = 1

	########################################################
	def Request(self, cmdcode, dataaddr, data=None):
		"""Read data from an address.
		Parameters: cmdcode (integer) = SBus command code.
			dataaddr (integer) = SBus address.
			data (integer) = Data to be written (optional).
		Returns: (tuple) = If OK, returns True plus the received data.
			If error, returns False plus an error message.
		"""

		# Increment the transaction id.
		self._IncMsgSeq()

		# Only request one at a time.
		datacount = 1
		sendata = None

		# Only the following command codes are supported.
		if (cmdcode not in [2, 3, 5, 6, 11, 13, 14]):
			return False, _ErrorMsgs['badcmdcode']

		# Check if the SBus address is legal. This does not guaranty though
		# that it will be supported in the field device.
		if (dataaddr < 0) or (dataaddr > 65535):
			return False, _ErrorMsgs['invalidaddress']


		# If we are writing data, make sure it is valid.
		if cmdcode in [11, 13, 14]:
			try:
				dataint = int(data)
			except:
				return False, _ErrorMsgs['dataerr']


		# For writing data, convert the data to a binary string, 
		# and check if it is within range for that function.
		if (cmdcode in (11, 13)):
			if (dataint == 0):
				sendata = self._bitoff
			elif (dataint == 1):
				sendata = self._biton
			else:
				return False, _ErrorMsgs['dataerr']
		elif (cmdcode == 14):
			if ((dataint >= -2147483648) and (dataint <= 2147483647)):
				sendata = SBusMsg.signedint32list2bin([data])
			else:
				return False, _ErrorMsgs['dataerr']

		# Send the request.
		try:	
			self._msg.SendRequest(self._msgsequence, self._stnaddr, cmdcode, datacount, dataaddr, sendata)
		# Something was wrong with the parameters we gave it to send. 
		# This should have been caught earlier.
		except SBusMsg.ParamError:
			return False, _ErrorMsgs['invalidparam']
		# Some other error occured while sending.
		except:
			return False, _ErrorMsgs['connnecterror']

		# Receive the response.
		try:
			telegramattr, recv_msgsequence, recv_msgdata = self._msg.ReceiveResponse()
		# The message length did not match any valid message type.
		except SBusMsg.MessageLengthError:
			return False, _ErrorMsgs['responselength']
		# The message CRC was bad.
		except SBusMsg.CRCError:
			return False, _ErrorMsgs['crcerr']
		# Some other error occured while receiving.
		except:
			return False, _ErrorMsgs['connnecterror']

		# Look at the telegrapm attribute to see what sort of response 
		# it was, and compare that to the command code.

		# If it was a 1, we expect some data from a read operation.
		if (telegramattr == 1):
			# Decode the data by command code.
			if (cmdcode in (2, 3, 5)):
				rdata = int(ModbusDataStrLib.bin2boollist(recv_msgdata)[0])
			elif (cmdcode == 6):
				rdata = SBusMsg.signedbin2int32list(recv_msgdata)[0]
		# This was an ack from a write operation, or it was a NAK.
		elif (telegramattr == 2): 
			acknak = ModbusDataStrLib.signedbin2intlist(recv_msgdata)[0]
			# This is an ACK from a write operation
			if (acknak == 0) and (cmdcode in (11, 13, 14)):
				return True, ''
			else :
				return False, _ErrorMsgs['deviceerror']
		# We have an invalid telegram.
		else:
			return False, _ErrorMsgs['badmessage']


		return True, rdata


############################################################


