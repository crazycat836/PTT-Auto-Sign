"""
Monkey patch for telnetlib module which was removed in Python 3.13.
This module creates a fake telnetlib module in sys.modules.
"""

import sys
import socket
import time
import logging
from typing import Optional, Union, Any, List, Tuple

# Setup logger
logger = logging.getLogger(__name__)

# Define telnet constants as bytes
BINARY = bytes([0])
ECHO = bytes([1])
RCP = bytes([2])
SGA = bytes([3])
NAMS = bytes([4])
STATUS = bytes([5])
TM = bytes([6])
RCTE = bytes([7])
NAOL = bytes([8])
NAOP = bytes([9])
NAOCRD = bytes([10])
NAOHTS = bytes([11])
NAOHTD = bytes([12])
NAOFFD = bytes([13])
NAOVTS = bytes([14])
NAOVTD = bytes([15])
NAOLFD = bytes([16])
XASCII = bytes([17])
LOGOUT = bytes([18])
BM = bytes([19])
DET = bytes([20])
SUPDUP = bytes([21])
SUPDUPOUTPUT = bytes([22])
SNDLOC = bytes([23])
TTYPE = bytes([24])
EOR = bytes([25])
TUID = bytes([26])
OUTMRK = bytes([27])
TTYLOC = bytes([28])
VT3270REGIME = bytes([29])
X3PAD = bytes([30])
NAWS = bytes([31])
TSPEED = bytes([32])
LFLOW = bytes([33])
LINEMODE = bytes([34])
XDISPLOC = bytes([35])
OLD_ENVIRON = bytes([36])
AUTHENTICATION = bytes([37])
ENCRYPT = bytes([38])
NEW_ENVIRON = bytes([39])
TN3270E = bytes([40])
XAUTH = bytes([41])
CHARSET = bytes([42])
RSP = bytes([43])
COM_PORT_OPTION = bytes([44])
SUPPRESS_LOCAL_ECHO = bytes([45])
TLS = bytes([46])
KERMIT = bytes([47])
SEND_URL = bytes([48])
FORWARD_X = bytes([49])
PRAGMA_LOGON = bytes([138])
SSPI_LOGON = bytes([139])
PRAGMA_HEARTBEAT = bytes([140])
EXOPL = bytes([255])
NOOPT = bytes([0])

SE = bytes([240])
NOP = bytes([241])
DM = bytes([242])
BRK = bytes([243])
IP = bytes([244])
AO = bytes([245])
AYT = bytes([246])
EC = bytes([247])
EL = bytes([248])
GA = bytes([249])
SB = bytes([250])
WILL = bytes([251])
WONT = bytes([252])
DO = bytes([253])
DONT = bytes([254])
IAC = bytes([255])

theNULL = bytes([0])

class Telnet:
    """
    Basic Telnet interface class compatible with the original telnetlib.Telnet API.
    Simplified version for PTT connection.
    """
    
    def __init__(self, host: Optional[str] = None, port: int = 23, 
                 timeout: Optional[Union[int, float]] = None):
        """Initialize Telnet object.
        
        Args:
            host: Host name or IP address of remote host
            port: Port number
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.rawq = b""
        self.irawq = 0
        self.cookedq = b""
        self.eof = False
        self.option_callback = None
        
        logger.debug(f"Telnet object initialized with host={host}, port={port}, timeout={timeout}")
        
        if host is not None:
            self.open(host, port, timeout)
    
    def open(self, host: str, port: int = 23, 
             timeout: Optional[Union[int, float]] = None) -> None:
        """Connect to a host.
        
        Args:
            host: Host name or IP address of remote host
            port: Port number
            timeout: Connection timeout in seconds
            
        Raises:
            TimeoutError: If connection times out
            ConnectionError: If connection fails
        """
        logger.debug(f"Connecting to {host}:{port} with timeout {timeout}")
        self.host = host
        self.port = port
        self.timeout = timeout
        
        try:
            self.sock = socket.create_connection((host, port), timeout)
            self.sock.settimeout(timeout)
            logger.info(f"Successfully connected to {host}:{port}")
        except socket.timeout:
            logger.error(f"Connection to {host}:{port} timed out")
            raise TimeoutError(f"Connection to {host}:{port} timed out")
        except socket.error as e:
            logger.error(f"Connection to {host}:{port} failed: {e}")
            raise ConnectionError(f"Connection to {host}:{port} failed: {e}")
    
    def read_until(self, expected: bytes, timeout: Optional[Union[int, float]] = None) -> bytes:
        """Read until a given byte string is encountered or until timeout.
        
        Args:
            expected: Expected byte string
            timeout: Timeout in seconds
            
        Returns:
            bytes: Data read from the connection
            
        Raises:
            ConnectionError: If not connected
        """
        if self.sock is None:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug(f"Reading until {expected!r} with timeout {timeout}")
        start_time = time.time()
        timeout_value = timeout if timeout is not None else self.timeout
        
        while True:
            # Check for expected pattern in cookedq
            index = self.cookedq.find(expected)
            if index >= 0:
                index = index + len(expected)
                result = self.cookedq[:index]
                self.cookedq = self.cookedq[index:]
                logger.debug(f"Found expected pattern, returning {len(result)} bytes")
                return result
            
            # Check for timeout
            if timeout_value is not None and time.time() - start_time > timeout_value:
                logger.debug(f"Timeout reached after {time.time() - start_time:.2f} seconds")
                result = self.cookedq
                self.cookedq = b""
                return result
            
            # Read more data
            self._read_from_socket()
            
            # Check for EOF
            if self.eof:
                result = self.cookedq
                self.cookedq = b""
                return result
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.01)
    
    def read_all(self) -> bytes:
        """Read all data until EOF.
        
        Returns:
            bytes: All data in the buffer
            
        Raises:
            ConnectionError: If not connected
        """
        if self.sock is None:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug("Reading all data")
        
        # Read until EOF
        while not self.eof:
            self._read_from_socket()
        
        result = self.cookedq
        self.cookedq = b""
        return result
    
    def read_some(self) -> bytes:
        """Read at least one byte of data.
        
        Returns:
            bytes: Data read from the connection
            
        Raises:
            ConnectionError: If not connected
        """
        if self.sock is None:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug("Reading some data")
        
        if not self.cookedq and not self.eof:
            self._read_from_socket()
        
        result = self.cookedq
        self.cookedq = b""
        return result
    
    def _read_from_socket(self) -> None:
        """Read more data from the socket."""
        if self.sock is None:
            return
        
        try:
            data = self.sock.recv(2048)
            logger.debug(f"Read {len(data)} bytes from socket")
            
            if not data:
                self.eof = True
                logger.debug("EOF received from socket")
            else:
                self.cookedq += data
                
        except socket.timeout:
            logger.debug("Timeout reading from socket")
        except socket.error as e:
            logger.error(f"Error reading from socket: {e}")
            self.eof = True
            raise ConnectionError(f"Error reading from socket: {e}")
    
    def write(self, buffer: bytes) -> None:
        """Write a string to the socket.
        
        Args:
            buffer: Data to send
            
        Raises:
            ConnectionError: If not connected or write fails
        """
        if self.sock is None:
            logger.error("Attempted to write to closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug(f"Writing {len(buffer)} bytes to socket")
        
        try:
            self.sock.sendall(buffer)
            logger.debug(f"Successfully wrote {len(buffer)} bytes")
        except socket.error as e:
            logger.error(f"Error writing to socket: {e}")
            raise ConnectionError(f"Error writing to socket: {e}")
    
    def close(self) -> None:
        """Close the connection."""
        if self.sock:
            logger.debug(f"Closing connection to {self.host}:{self.port}")
            
            try:
                self.sock.close()
            except Exception as e:
                logger.debug(f"Error during close: {e}")
            
            self.sock = None
            self.eof = True
            logger.info(f"Connection to {self.host}:{self.port} closed")
    
    def interact(self) -> None:
        """Interaction function - not implemented."""
        raise NotImplementedError("The interact method is not implemented.")
    
    def mt_interact(self) -> None:
        """Multithreaded interaction function - not implemented."""
        raise NotImplementedError("The mt_interact method is not implemented.")

# Create a fake telnetlib module
class TelnetlibModule:
    def __init__(self):
        self.Telnet = Telnet
        
        # Add all telnet constants to the module
        self.BINARY = BINARY
        self.ECHO = ECHO
        self.RCP = RCP
        self.SGA = SGA
        self.NAMS = NAMS
        self.STATUS = STATUS
        self.TM = TM
        self.RCTE = RCTE
        self.NAOL = NAOL
        self.NAOP = NAOP
        self.NAOCRD = NAOCRD
        self.NAOHTS = NAOHTS
        self.NAOHTD = NAOHTD
        self.NAOFFD = NAOFFD
        self.NAOVTS = NAOVTS
        self.NAOVTD = NAOVTD
        self.NAOLFD = NAOLFD
        self.XASCII = XASCII
        self.LOGOUT = LOGOUT
        self.BM = BM
        self.DET = DET
        self.SUPDUP = SUPDUP
        self.SUPDUPOUTPUT = SUPDUPOUTPUT
        self.SNDLOC = SNDLOC
        self.TTYPE = TTYPE
        self.EOR = EOR
        self.TUID = TUID
        self.OUTMRK = OUTMRK
        self.TTYLOC = TTYLOC
        self.VT3270REGIME = VT3270REGIME
        self.X3PAD = X3PAD
        self.NAWS = NAWS
        self.TSPEED = TSPEED
        self.LFLOW = LFLOW
        self.LINEMODE = LINEMODE
        self.XDISPLOC = XDISPLOC
        self.OLD_ENVIRON = OLD_ENVIRON
        self.AUTHENTICATION = AUTHENTICATION
        self.ENCRYPT = ENCRYPT
        self.NEW_ENVIRON = NEW_ENVIRON
        self.TN3270E = TN3270E
        self.XAUTH = XAUTH
        self.CHARSET = CHARSET
        self.RSP = RSP
        self.COM_PORT_OPTION = COM_PORT_OPTION
        self.SUPPRESS_LOCAL_ECHO = SUPPRESS_LOCAL_ECHO
        self.TLS = TLS
        self.KERMIT = KERMIT
        self.SEND_URL = SEND_URL
        self.FORWARD_X = FORWARD_X
        self.PRAGMA_LOGON = PRAGMA_LOGON
        self.SSPI_LOGON = SSPI_LOGON
        self.PRAGMA_HEARTBEAT = PRAGMA_HEARTBEAT
        self.EXOPL = EXOPL
        self.NOOPT = NOOPT
        
        self.SE = SE
        self.NOP = NOP
        self.DM = DM
        self.BRK = BRK
        self.IP = IP
        self.AO = AO
        self.AYT = AYT
        self.EC = EC
        self.EL = EL
        self.GA = GA
        self.SB = SB
        self.WILL = WILL
        self.WONT = WONT
        self.DO = DO
        self.DONT = DONT
        self.IAC = IAC
        
        self.theNULL = theNULL
        
        logger.debug("Telnetlib compatibility layer initialized with all constants")

def apply_monkey_patch():
    """Apply the monkey patch for telnetlib."""
    # Install the fake telnetlib module in sys.modules
    sys.modules['telnetlib'] = TelnetlibModule()
    logger.debug("Installed telnetlib compatibility layer in sys.modules")

# Apply the patch when the module is imported
apply_monkey_patch() 