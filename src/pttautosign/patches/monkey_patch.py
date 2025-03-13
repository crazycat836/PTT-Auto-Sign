"""
Monkey patch for telnetlib module which was removed in Python 3.13.
This module creates a fake telnetlib module in sys.modules.
"""

import sys
import asyncio
import threading
import time
import logging
from typing import Optional, Union, Any

# Use our fake telnetlib3 module
from pttautosign.patches.fake_telnetlib3 import open_connection

# Setup logger
logger = logging.getLogger(__name__)

class Telnet:
    """
    Telnet interface class that mimics the API of the original telnetlib.Telnet class
    but uses telnetlib3 under the hood.
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
        self._reader = None
        self._writer = None
        self._loop = None
        self._thread = None
        self._buffer = b""
        self._connected = False
        self._connection_event = threading.Event()
        self._connection_error = None
        
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
        
        # Reset connection state
        self._connection_event.clear()
        self._connection_error = None
        
        # Keep track of whether we're in PyPtt module
        in_pyptt_module = False
        
        # Create a new event loop for this connection
        self._loop = asyncio.new_event_loop()
        
        # Connect in a separate thread
        self._thread = threading.Thread(target=self._connect_thread, name=f"Telnet-{host}:{port}")
        self._thread.daemon = True
        self._thread.start()
        
        # Wait for connection to be established or timeout
        timeout_value = timeout if timeout is not None else 30  # Default timeout
        if not self._connection_event.wait(timeout=timeout_value):
            logger.error(f"Connection to {host}:{port} timed out after {timeout_value} seconds")
            raise TimeoutError(f"Connection to {host}:{port} timed out after {timeout_value} seconds")
        
        # Check if there was an error during connection
        if self._connection_error:
            logger.error(f"Connection to {host}:{port} failed: {self._connection_error}")
            raise self._connection_error
        
        logger.info(f"Successfully connected to {host}:{port}")
    
    def _connect_thread(self) -> None:
        """Thread function to run the event loop and connect."""
        try:
            asyncio.set_event_loop(self._loop)
            
            async def connect():
                try:
                    logger.debug(f"Attempting to connect to {self.host}:{self.port}")
                    self._reader, self._writer = await open_connection(
                        self.host, self.port, connect_minwait=0.05
                    )
                    self._connected = True
                    logger.debug(f"Connection established to {self.host}:{self.port}")
                    self._connection_event.set()
                    
                    # Keep the connection alive
                    while self._connected:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error connecting to {self.host}:{self.port}: {e}")
                    self._connection_error = ConnectionError(f"Telnet connection error: {e}")
                    self._connection_event.set()
                    self._connected = False
            
            self._loop.run_until_complete(connect())
        except Exception as e:
            logger.error(f"Error in connect thread: {e}")
            self._connection_error = ConnectionError(f"Thread error: {e}")
            self._connection_event.set()
    
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
        if not self._connected:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug(f"Reading until {expected!r} with timeout {timeout}")
        start_time = time.time()
        timeout_value = timeout if timeout is not None else self.timeout
        
        while True:
            if expected in self._buffer:
                index = self._buffer.find(expected) + len(expected)
                result = self._buffer[:index]
                self._buffer = self._buffer[index:]
                logger.debug(f"Found expected pattern, returning {len(result)} bytes")
                return result
            
            # Check for timeout
            if timeout_value and time.time() - start_time > timeout_value:
                logger.debug(f"Timeout reached after {time.time() - start_time:.2f} seconds")
                result = self._buffer
                self._buffer = b""
                return result
            
            # Get more data
            self._read_more()
            time.sleep(0.05)
    
    def read_all(self) -> bytes:
        """Read all data until EOF.
        
        Returns:
            bytes: All data in the buffer
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug("Reading all data")
        result = self._buffer
        self._buffer = b""
        return result
    
    def read_some(self) -> bytes:
        """Read at least one byte of data.
        
        Returns:
            bytes: Data read from the connection
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            logger.error("Attempted to read from closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug("Reading some data")
        if not self._buffer:
            self._read_more()
        
        result = self._buffer
        self._buffer = b""
        return result
    
    def _read_more(self) -> None:
        """Read more data from the connection."""
        if not self._connected:
            return
            
        async def read_data():
            try:
                logger.debug("Reading more data from connection")
                data = await asyncio.wait_for(
                    self._reader.read(1024),
                    timeout=self.timeout if self.timeout is not None else 30
                )
                if data:
                    encoded_data = data.encode('utf-8')
                    self._buffer += encoded_data
                    logger.debug(f"Read {len(encoded_data)} bytes")
                else:
                    logger.debug("No data read from connection")
            except asyncio.TimeoutError:
                logger.debug("Timeout while reading data")
            except Exception as e:
                logger.error(f"Error reading data: {e}")
                self._connected = False
                raise ConnectionError(f"Error reading data: {e}")
        
        try:
            future = asyncio.run_coroutine_threadsafe(read_data(), self._loop)
            future.result(timeout=self.timeout if self.timeout is not None else 30)
        except Exception as e:
            logger.debug(f"Exception during read: {e}")
            # Ignore timeout errors during read
            pass
    
    def write(self, buffer: bytes) -> None:
        """Write a string to the socket.
        
        Args:
            buffer: Data to send
            
        Raises:
            ConnectionError: If not connected or write fails
        """
        if not self._connected:
            logger.error("Attempted to write to closed connection")
            raise ConnectionError("Not connected")
        
        logger.debug(f"Writing {len(buffer)} bytes to connection")
        
        async def write_data():
            try:
                decoded_data = buffer.decode('utf-8', errors='replace')
                self._writer.write(decoded_data)
                await self._writer.drain()
                logger.debug(f"Successfully wrote {len(buffer)} bytes")
            except Exception as e:
                logger.error(f"Error writing data: {e}")
                self._connected = False
                raise ConnectionError(f"Error writing data: {e}")
        
        try:
            future = asyncio.run_coroutine_threadsafe(write_data(), self._loop)
            future.result(timeout=self.timeout if self.timeout is not None else 30)
        except Exception as e:
            logger.error(f"Failed to write data: {e}")
            raise ConnectionError(f"Failed to write data: {e}")
    
    def close(self) -> None:
        """Close the connection."""
        if self._connected:
            logger.debug(f"Closing connection to {self.host}:{self.port}")
            
            async def close_connection():
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                    logger.debug("Connection closed successfully")
                except Exception as e:
                    logger.debug(f"Error during close: {e}")
                    pass  # Ignore errors during close
            
            try:
                future = asyncio.run_coroutine_threadsafe(close_connection(), self._loop)
                future.result(timeout=self.timeout if self.timeout is not None else 5)
            except Exception as e:
                logger.debug(f"Exception during close: {e}")
                pass  # Ignore timeout errors during close
            
            self._connected = False
            
            # Stop the event loop
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception as e:
                logger.debug(f"Error stopping event loop: {e}")
            
            # Wait for the thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1)
                if self._thread.is_alive():
                    logger.warning(f"Thread for {self.host}:{self.port} did not terminate")
            
            # Close the event loop
            if self._loop and not self._loop.is_closed():
                try:
                    self._loop.close()
                except Exception as e:
                    logger.debug(f"Error closing event loop: {e}")
            
            # Reset attributes
            self._reader = None
            self._writer = None
            self._loop = None
            self._thread = None
            self._buffer = b""
            self._connection_event.clear()
            
            logger.info(f"Connection to {self.host}:{self.port} closed")

# Create a fake telnetlib module
class TelnetlibModule:
    def __init__(self):
        self.Telnet = Telnet
        logger.debug("Telnetlib compatibility layer initialized")

def apply_monkey_patch():
    """Apply the monkey patch for telnetlib."""
    # Install the fake telnetlib module in sys.modules
    sys.modules['telnetlib'] = TelnetlibModule()
    logger.debug("Installed telnetlib compatibility layer in sys.modules")

# Apply the patch when the module is imported
apply_monkey_patch() 