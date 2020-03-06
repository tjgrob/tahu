##############################################################################
# Project: 	SBProbe
# Module: 	RequestHandler.py
# Purpose: 	Handle web page requests for data. Adapted from Modbus version.
# Language:	Python 2.5
# Date:		21-Jun-2009.
# Ver.:		24-Jul-2010.
# Copyright:	2009 - 2010 - Michael Griffin       <m.os.griffin@gmail.com>
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

"""Handle all web page requests for data. 
"""

import time
# import cgi		# This will eventually be changed to urlparse.
import urllib

############################################################

# Error messages.
_ErrorMsgs = {'connectionerror': 'Connection error.',
              'connnecterror': 'Error - Could not establish contact with remote host.'
              }

# Message to indicate when automatically reconnecting.
_AutoReconnectMsg = 'Auto reconnecting ...'


############################################################

def _ParseQueryString(postdata):
    """Reformat the post data query string and return it as a dictionary.
    E.g. 'addrtype02=Discrete+Input&addr02=1&addrtype03=Holding+Register&addr03=55555'
    becomes: {'addr03': '55555', 'addr02': '1', 'addrtype02': 'Discrete Input',
    'addrtype03': 'Holding Register'}
    Parameters: postdata (string) = The post data query string.
    Returns: (dict) = A dictionary with the post data query names as keys, and the
    individual data items as values.
    Note: This uses parse_qs from cgi instead of from urlparse for compatibility
    with Debian Stable 5.0, which still uses Python 2.5.
    """

    # This will parse out the content data and turn it into a dictionary.
    # Any fields that were blank will be missing.
    postvalues = urllib.parse.parse_qs(postdata)

    # Next, reformat the new data. The parse_qs routine uses lists as the
    # data elements. We need to change those to individual values.
    return dict(list(zip(list(postvalues.keys()), [postvalues[i][0] for i in list(postvalues.keys())])))


############################################################

class ReadData:
    """Format web page for reading from field device.
    """

    ########################################################
    def __init__(self, paramvalidator, connectionhandler):
        """Parameters:
        paramvalidator (object) = An initialised object for
        validating the parameters.
        connectionhandler (object) = An initialised object for handling
        communications with the field device.
        """
        self._ParamValidator = paramvalidator
        self._ConnectionHandler = connectionhandler

        # This is the default data used to populate an empty page.
        self._PageDefaultData = {
            'addrtype01': 'None', 'data01': '', 'addr01': '', 'errors01': '',
            'addrtype02': 'None', 'data02': '', 'addr02': '', 'errors02': '',
            'addrtype03': 'None', 'data03': '', 'addr03': '', 'errors03': '',
            'addrtype04': 'None', 'data04': '', 'addr04': '', 'errors04': '',
            'addrtype05': 'None', 'data05': '', 'addr05': '', 'errors05': '',
            'addrtype06': 'None', 'data06': '', 'addr06': '', 'errors06': '',
            'addrtype07': 'None', 'data07': '', 'addr07': '', 'errors07': '',
            'addrtype08': 'None', 'data08': '', 'addr08': '', 'errors08': '',
            'addrtype09': 'None', 'data09': '', 'addr09': '', 'errors09': '',
            'addrtype10': 'None', 'data10': '', 'addr10': '', 'errors10': '',
            'addrtype11': 'None', 'data11': '', 'addr11': '', 'errors11': '',
            'addrtype12': 'None', 'data12': '', 'addr12': '', 'errors12': '',
            'addrtype13': 'None', 'data13': '', 'addr13': '', 'errors13': '',
            'addrtype14': 'None', 'data14': '', 'addr14': '', 'errors14': '',
            'addrtype15': 'None', 'data15': '', 'addr15': '', 'errors15': '',
            'addrtype16': 'None', 'data16': '', 'addr16': '', 'errors16': '',
            'addrtype17': 'None', 'data17': '', 'addr17': '', 'errors17': '',
            'addrtype18': 'None', 'data18': '', 'addr18': '', 'errors18': '',
            'addrtype19': 'None', 'data19': '', 'addr19': '', 'errors19': '',
            'addrtype20': 'None', 'data20': '', 'addr20': '', 'errors20': ''
        }

        self._PageData = {}
        # This is the current page data.
        self._PageData.update(self._PageDefaultData)

        # List of keys for address type, address, and data. We need this as a list
        # of tuples so we know which ones are associated with each other.
        self._DataKeys = [('addrtype01', 'addr01', 'data01', 'errors01'),
                          ('addrtype02', 'addr02', 'data02', 'errors02'),
                          ('addrtype03', 'addr03', 'data03', 'errors03'),
                          ('addrtype04', 'addr04', 'data04', 'errors04'),
                          ('addrtype05', 'addr05', 'data05', 'errors05'),
                          ('addrtype06', 'addr06', 'data06', 'errors06'),
                          ('addrtype07', 'addr07', 'data07', 'errors07'),
                          ('addrtype08', 'addr08', 'data08', 'errors08'),
                          ('addrtype09', 'addr09', 'data09', 'errors09'),
                          ('addrtype10', 'addr10', 'data10', 'errors10'),
                          ('addrtype11', 'addr11', 'data11', 'errors11'),
                          ('addrtype12', 'addr12', 'data12', 'errors12'),
                          ('addrtype13', 'addr13', 'data13', 'errors13'),
                          ('addrtype14', 'addr14', 'data14', 'errors14'),
                          ('addrtype15', 'addr15', 'data15', 'errors15'),
                          ('addrtype16', 'addr16', 'data16', 'errors16'),
                          ('addrtype17', 'addr17', 'data17', 'errors17'),
                          ('addrtype18', 'addr18', 'data18', 'errors18'),
                          ('addrtype19', 'addr19', 'data19', 'errors19'),
                          ('addrtype20', 'addr20', 'data20', 'errors20')
                          ]

        # Function code translation for reading.
        self._ReadFuncCodes = {'Flag': 2,
                               'Input': 3,
                               'Output': 5,
                               'Register': 6
                               }

    ########################################################
    def GetPagedata(self):
        """ Return a dictionary with the page data for a read request.
		"""
        return self._PageData

    ########################################################
    def _PreparePageData(self, postdata):
        """Clear the old page data, and insert the new values from
        the page POST data.
        Parameters: postdata (string) - This is the parameter string from
        the HTML POST headers.
        Returns: Nothing. This updates the page data dictionary directly.
        """

        # Update the current page data.
        # First, discard the old data.
        self._PageData = {}
        # Next populate it with defaults.
        self._PageData.update(self._PageDefaultData)

        # Parse out the content data and turn it into a dictionary.
        postvalues = _ParseQueryString(postdata)

        # Finally, add the new results.
        self._PageData.update(postvalues)

    ########################################################
    def _ClearPage(self):
        """Clear the page of existing data.
        """
        # First, discard the old data.
        self._PageData = {}
        # Next populate it with defaults.
        self._PageData.update(self._PageDefaultData)

    ########################################################
    def ReadData(self, postdata):
        """Analyse the POST data content string, contact the field device
        and read the data, and insert the new data into the page dictionary.
        Parameters: postdata (string) - This is the parameter string from
        the HTML POST headers.
        Returns: Nothing. This updates the page data dictionary directly.
        """

        # Populate the page dictionary with the POST data.
        self._PreparePageData(postdata)

        # Check if the user has selected to just clear the page.

        if self._PageData[b'read'] == 'reset':
            self._ClearPage()
        else:
            for addrtype, addr, data, errors in self._DataKeys:

                try:
                    func, addrval, errmsg = self._ParamValidator.Validate(self._PageData[addrtype.encode()].decode(),
                                                                          self._PageData[addr.encode()].decode())
                except:
                    func = None
                    addrval = None
                    errmsg = 'No red values'

                if (func is not None) and (addrval is not None):
                    try:
                        result, msgdata = self._ConnectionHandler.Request(func, addrval)

                        if result:
                            self._PageData[data.encode()] = msgdata
                        else:
                            self._PageData[errors.encode()] = msgdata

                    except:
                        self._PageData[errors.encode()] = _ErrorMsgs['connectionerror ']

                elif (len(errmsg) > 0):
                    self._PageData[errors.encode()] = errmsg


############################################################


############################################################

class WriteData:
    """Format page for writing to field device.
    """

    ########################################################
    def __init__(self, paramvalidator, connectionhandler):
        """Parameters:
        paramvalidator (object) = An initialised object for
        validating the parameters.
        connectionhandler (object) = An initialised object for handling
        communications with the field device.
        """
        self._ParamValidator = paramvalidator
        self._ConnectionHandler = connectionhandler

        # This is the default data used to populate an empty page.
        self._PageDefaultData = {
            'addrtype01': 'None', 'data01': '', 'addr01': '', 'errors01': '',
            'addrtype02': 'None', 'data02': '', 'addr02': '', 'errors02': '',
            'addrtype03': 'None', 'data03': '', 'addr03': '', 'errors03': '',
            'addrtype04': 'None', 'data04': '', 'addr04': '', 'errors04': '',
            'addrtype05': 'None', 'data05': '', 'addr05': '', 'errors05': '',
            'addrtype06': 'None', 'data06': '', 'addr06': '', 'errors06': '',
            'addrtype07': 'None', 'data07': '', 'addr07': '', 'errors07': '',
            'addrtype08': 'None', 'data08': '', 'addr08': '', 'errors08': '',
            'addrtype09': 'None', 'data09': '', 'addr09': '', 'errors09': '',
            'addrtype10': 'None', 'data10': '', 'addr10': '', 'errors10': '',
            'addrtype11': 'None', 'data11': '', 'addr11': '', 'errors11': '',
            'addrtype12': 'None', 'data12': '', 'addr12': '', 'errors12': '',
            'addrtype13': 'None', 'data13': '', 'addr13': '', 'errors13': '',
            'addrtype14': 'None', 'data14': '', 'addr14': '', 'errors14': '',
            'addrtype15': 'None', 'data15': '', 'addr15': '', 'errors15': '',
            'addrtype16': 'None', 'data16': '', 'addr16': '', 'errors16': '',
            'addrtype17': 'None', 'data17': '', 'addr17': '', 'errors17': '',
            'addrtype18': 'None', 'data18': '', 'addr18': '', 'errors18': '',
            'addrtype19': 'None', 'data19': '', 'addr19': '', 'errors19': '',
            'addrtype20': 'None', 'data20': '', 'addr20': '', 'errors20': ''
        }

        self._PageData = {}
        # This is the current page data.
        self._PageData.update(self._PageDefaultData)

        # List of keys for address type, address, and data. We need this as a list
        # of tuples so we know which ones are associated with each other.
        self._DataKeys = [('addrtype01', 'addr01', 'data01', 'errors01'),
                          ('addrtype02', 'addr02', 'data02', 'errors02'),
                          ('addrtype03', 'addr03', 'data03', 'errors03'),
                          ('addrtype04', 'addr04', 'data04', 'errors04'),
                          ('addrtype05', 'addr05', 'data05', 'errors05'),
                          ('addrtype06', 'addr06', 'data06', 'errors06'),
                          ('addrtype07', 'addr07', 'data07', 'errors07'),
                          ('addrtype08', 'addr08', 'data08', 'errors08'),
                          ('addrtype09', 'addr09', 'data09', 'errors09'),
                          ('addrtype10', 'addr10', 'data10', 'errors10'),
                          ('addrtype11', 'addr11', 'data11', 'errors11'),
                          ('addrtype12', 'addr12', 'data12', 'errors12'),
                          ('addrtype13', 'addr13', 'data13', 'errors13'),
                          ('addrtype14', 'addr14', 'data14', 'errors14'),
                          ('addrtype15', 'addr15', 'data15', 'errors15'),
                          ('addrtype16', 'addr16', 'data16', 'errors16'),
                          ('addrtype17', 'addr17', 'data17', 'errors17'),
                          ('addrtype18', 'addr18', 'data18', 'errors18'),
                          ('addrtype19', 'addr19', 'data19', 'errors19'),
                          ('addrtype20', 'addr20', 'data20', 'errors20')
                          ]

    ########################################################
    def GetPagedata(self):
        """ Return a dictionary with the page data for a read request.
        """
        return self._PageData

    ########################################################
    def _PreparePageData(self, postdata):
        """Clear the old page data, and insert the new values from
        the page POST data.
        Parameters: postdata (string) - This is the parameter string from
        the HTML POST headers.
        Returns: Nothing. This updates the page data dictionary directly.
        """

        # Update the current page data.
        # First, discard the old data.
        self._PageData = {}
        # Next populate it with defaults.
        self._PageData.update(self._PageDefaultData)

        # Parse out the content data and turn it into a dictionary.
        postvalues = _ParseQueryString(postdata)

        # Finally, add the new results.
        self._PageData.update(postvalues)

    ########################################################
    def _ClearPage(self):
        """Clear the page of existing data.
        """
        # First, discard the old data.
        self._PageData = {}
        # Next populate it with defaults.
        self._PageData.update(self._PageDefaultData)

    ########################################################
    def WriteData(self, postdata):
        """Analyse the POST data content string, contact the field device
        and write the data, and insert any errors into the page dictionary.
        Parameters: postdata (string) - This is the parameter string from
        the HTML POST headers.
        Returns: Nothing. This updates the page data dictionary directly.
        """

        # Populate the page dictionary with the POST data.
        self._PreparePageData(postdata)

        # Check if the user has selected to just clear the page.
        if (self._PageData[b'write'] == b'reset'):
            self._ClearPage()
            return

        # Read the data from the field device.
        for addrtype, addr, data, errors in self._DataKeys:

            func, addrval, writevalue, errmsg = self._ParamValidator.Validate(
                self._PageData[addrtype.encode()].decode(),

                self._PageData[addr.encode()].decode(), self._PageData[data.encode()].decode())
            if ((func != None) and (addrval != None) and (writevalue != None)):
                try:
                    result, msgdata = self._ConnectionHandler.Request(func, addrval, writevalue)
                    if not result:
                        self._PageData[errors.encode()] = msgdata
                except:
                    self._PageData[errors.encode()] = _ErrorMsgs['connectionerror']

            elif (len(errmsg) > 0):
                self._PageData[errors.encode()] = errmsg


############################################################


############################################################

class ConnectionStat:
    """Control the field device connection status.
    """

    ########################################################
    def __init__(self, defaultrport, clienthandler):
        """Parameters:
        defaultrport (integer) = The default port for the remote device.
        clienthandler (class) = A class which handles the actual client
        communications functions.
        """
        self._rhost = 'localhost'
        self._rport = defaultrport
        self._rtimeout = 5.0
        self._runitid = 1
        self._Connected = False
        self._AutoReconnect = True
        self._ConnectionError = False

        # This should handle the actual communications.
        self._ClientHandler = clienthandler

        # This is the default data used to populate an empty page.
        self._PageDefaultData = {'host': self._rhost,
                                 'port': self._rport,
                                 'timeout': self._rtimeout,
                                 'unitid': self._runitid,
                                 'connectedstat': 'checked',
                                 'disconnectedstat': '',
                                 'autoconnectstat': 'checked',
                                 'connectionstat': '',
                                 'currenthost': '',
                                 'currentport': '',
                                 'currenttimeout': '',
                                 'currentunitid': '',
                                 'connectionstyle': 'statusdisconnected',
                                 'softversion': ''
                                 }

        self._PageData = {}
        self._PageData.update(self._PageDefaultData)

    ########################################################
    def SetVersionInfo(self, versioninfo):
        """Set the package version name and number for display.
        Parameters: versioninfo (string) = The package name and version.
        """
        self._PageDefaultData[b'softversion'] = versioninfo

    ########################################################
    def _SetPageData(self):
        """Set the page data dictionary with the updated data.
        """

        self._PageDefaultData['host'] = self._rhost
        self._PageDefaultData['port'] = self._rport
        self._PageDefaultData['timeout'] = self._rtimeout
        self._PageDefaultData['unitid'] = self._runitid

        if self._Connected:
            self._PageDefaultData['connectionstat'] = 'Connected'
            self._PageDefaultData['currenthost'] = self._rhost
            self._PageDefaultData['currentport'] = self._rport
            self._PageDefaultData['currenttimeout'] = ''
            self._PageDefaultData['currentunitid'] = ''
            self._PageDefaultData['connectionstyle'] = 'statusconnected'
        else:
            self._PageDefaultData['connectionstat'] = 'Disconnected'
            self._PageDefaultData['currenthost'] = ''
            self._PageDefaultData['currentport'] = ''
            self._PageDefaultData['currenttimeout'] = ''
            self._PageDefaultData['currentunitid'] = ''
            self._PageDefaultData['connectionstyle'] = 'statusdisconnected'
        # This sets the correct status for the "radio button" input
        # for connected or disconnected.
        if self._Connected:
            self._PageDefaultData['connectedstat'] = 'checked="checked"'
            self._PageDefaultData['disconnectedstat'] = ''
        else:
            self._PageDefaultData['connectedstat'] = ''
            self._PageDefaultData['disconnectedstat'] = 'checked="checked"'

        # This sets the correct status for the "radio button" input
        # for auto-connect.
        if self._AutoReconnect:
            self._PageDefaultData['autoconnectstat'] = 'checked="checked"'
        else:
            self._PageDefaultData['autoconnectstat'] = ''

        # Check if there was a connection error.
        if self._ConnectionError:
            self._PageDefaultData['connecterror'] = _ErrorMsgs['connnecterror']
        else:
            self._PageDefaultData['connecterror'] = ''

        self._PageData = {}
        # This is the current page data.
        self._PageData.update(self._PageDefaultData)

    ########################################################
    def SetConnectionParams(self, rhost, rport, rtimeout, runitid, autoreconnect):
        """Set the remote field device server connection parameters.
        """
        self._rhost = rhost
        self._rport = rport
        self._rtimeout = rtimeout
        self._runitid = runitid
        self._AutoReconnect = autoreconnect

        self._SetPageData()

    ########################################################
    def GetPagedata(self):
        """ Return a dictionary with the page data for a read request.
        """
        return self._PageData

    ########################################################
    def _PreparePageData(self, postdata):
        """Clear the old page data, and insert the new values from
        the page POST data.
        """

        # Update the current page data.
        # First, discard the old data.
        self._PageData = {}
        # Next populate it with defaults.
        self._PageData.update(self._PageDefaultData)

        # Parse out the content data and turn it into a dictionary.
        postvalues = _ParseQueryString(postdata)

        # Finally, add the new results.
        self._PageData.update(postvalues)

    ########################################################
    def ConnectData(self, postdata):
        """Analyse the POST data content string.
        """

        # Populate the page dictionary with the POST data.
        self._PreparePageData(postdata)

        try:
            rhost = self._PageData[b'host'].decode()
            if (len(rhost) <= 0):
                rhost = None
        except:
            rhost = None

        try:
            rport = int(self._PageData[b'port'])
        except:
            rport = None

        try:
            rtimeout = float(self._PageData[b'timeout'])
        except:
            rtimeout = None

        try:
            # Station address must be a number.
            runitid = int(self._PageData[b'unitid'])
            # and it must be between 0 and 255.
            if (runitid < 0) or (runitid > 255):
                runitid = None
        except:
            runitid = None

        try:
            connectreq = self._PageData[b'connect'] == b'connect'
        except:
            connectreq = None

        try:
            autoconnectreq = self._PageData[b'autoconnect'] == b'autoconnect'
        except:
            autoconnectreq = False

        # Check if the parameters were OK. We don't check for 'autoconnect',
        # because as a check box if it is off it will not be present.
        print(str("host "+rhost)+"port "+str(rport)+"t "+str(rtimeout)+"id "+str(runitid)+"con "+str(connectreq))

        if (rhost != None) and (rport != None) and (rtimeout != None) and (runitid != None) and connectreq:
            # Save the new parameters.
            self._rhost = rhost
            self._rport = rport
            self._rtimeout = rtimeout
            self._runitid = runitid

            # If already connected, then disconnect and reconnect.

            self.Reconnect()

        # Disconnect.
        elif not connectreq:
            self._ClientConnect = None
            self._Connected = False
            self._SetPageData()

        # Auto reconnect doesn't depend on the current connection status.
        self._AutoReconnect = autoconnectreq

        # Update the page data.
        self._SetPageData()

    ########################################################
    def Request(self, func, addr, data=None):
        """ Make a client request to the field device. The parameters
        and data are the same as for the corresponding client object method.
        """
        try:
            result, recvdata = self._ClientConnect.Request(func, addr, data)
        except:
            result = False
            recvdata = _ErrorMsgs['connnecterror']

        # If an error occured and autoconnect is set, then automatically
        # re-connect and try again.
        if not result and self._AutoReconnect:
            self.Reconnect()
            result, recvdata = self._ClientConnect.Request(func, addr, data)

        return result, recvdata

    ########################################################
    def Connect(self):
        """ Connect to the remote field device server.
        """
        try:
            self._ClientConnect = self._ClientHandler(self._rhost, self._rport,
                                                      self._rtimeout, self._runitid)
            self._Connected = True
            self._ConnectionError = False
        except:
            self._Connected = False
            self._ClientConnect = None
            self._ConnectionError = True

        # Update the page data.
        self._SetPageData()

    ########################################################
    def Reconnect(self):
        """ Disconnect from the remote field device and then
        reconnect.
        """
        # If already connected, then disconnect.
        self._ClientConnect = None
        # Delay slightly before attempting a new connection.
        time.sleep(1.0)
        # Make the new connection.
        self.Connect()

############################################################
