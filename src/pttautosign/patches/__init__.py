"""
Patches for compatibility with different Python versions and libraries.
"""

# Import patches module (which applies patches on import)
from pttautosign.patches import pyptt_patch

# Export patches
__all__ = ['pyptt_patch']

