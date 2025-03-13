"""
Fake telnetlib3 module for compatibility.
This module provides minimal functionality to allow the monkey_patch module to work.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

async def open_connection(host, port, connect_minwait=0.05):
    """
    Fake open_connection function that returns dummy reader and writer objects.
    """
    logger.debug(f"Fake telnetlib3.open_connection called for {host}:{port}")
    
    class DummyReader:
        async def read(self, n):
            await asyncio.sleep(0.1)
            return ""
    
    class DummyWriter:
        def write(self, data):
            pass
            
        async def drain(self):
            await asyncio.sleep(0.1)
            
        def close(self):
            pass
            
        async def wait_closed(self):
            await asyncio.sleep(0.1)
    
    return DummyReader(), DummyWriter() 