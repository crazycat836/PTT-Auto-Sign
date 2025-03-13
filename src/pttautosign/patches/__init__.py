"""
Patches for compatibility with different Python versions and libraries.
"""

# Import patches
from pttautosign.patches.monkey_patch import apply_monkey_patch
from pttautosign.patches.pyptt_patch import apply_pyptt_patch

# Export patches
__all__ = ['apply_monkey_patch', 'apply_pyptt_patch', 'monkey_patch', 'pyptt_patch']

# Make modules available
import pttautosign.patches.monkey_patch as monkey_patch
import pttautosign.patches.pyptt_patch as pyptt_patch

# Apply patches automatically when the module is imported
apply_monkey_patch()
apply_pyptt_patch()
