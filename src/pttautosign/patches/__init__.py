"""
Patches module for compatibility with various libraries.
"""

# Import patches to make them available when importing the patches package
from pttautosign.patches.monkey_patch import apply_monkey_patch
from pttautosign.patches.pyptt_patch import apply_pyptt_patch

# Apply patches automatically when the module is imported
apply_monkey_patch()
apply_pyptt_patch()
