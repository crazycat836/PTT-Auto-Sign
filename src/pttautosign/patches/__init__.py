"""
Patches for compatibility with different Python versions and libraries.
"""

# Import patches
from pttautosign.patches.pyptt_patch import apply_pyptt_patch

# Export patches
__all__ = ['apply_pyptt_patch', 'pyptt_patch']

# Make modules available
import pttautosign.patches.pyptt_patch as pyptt_patch

# Apply patches automatically when the module is imported
apply_pyptt_patch()
