"""
Patch for PyPtt compatibility issues with websockets and Python 3.13.
This module should be imported before importing PyPtt.
"""

import sys
import logging
import importlib.util
import re

logger = logging.getLogger(__name__)

def patch_websockets():
    """Patch websockets.http module to add USER_AGENT attribute if missing."""
    try:
        import websockets.http
        if not hasattr(websockets.http, 'USER_AGENT'):
            logger.info("Adding USER_AGENT attribute to websockets.http")
            websockets.http.USER_AGENT = "Python/websockets"
            return True
        return True
    except ImportError:
        logger.error("Failed to import websockets.http")
        return False

# Store the original re.compile function
original_compile = re.compile

# Keep track of whether we're in PyPtt module
in_pyptt_module = False

def patched_compile(pattern, flags=0):
    """Patched version of re.compile that fixes invalid escape sequences only for PyPtt modules."""
    global in_pyptt_module
    
    # Get the caller's module
    import inspect
    frame = inspect.currentframe().f_back
    module_name = frame.f_globals.get('__name__', '')
    
    # Only patch patterns from PyPtt modules
    if isinstance(pattern, str) and module_name.startswith('PyPtt'):
        # Create a list of escape sequences to fix
        escape_sequences = ['\\d', '\\w', '\\S', '\\[', '\\]', '\\-', '\\+', '\\|', '\\(', '\\)', '\\{', '\\}', '\\s']
        
        # Fix each escape sequence
        for seq in escape_sequences:
            if seq in pattern and not '\\\\' + seq[1] in pattern:
                pattern = pattern.replace(seq, '\\' + seq)
        
        # Fix nested character classes
        if '[' in pattern and ']' in pattern:
            # This is a more complex fix that would require parsing the regex
            # For now, we'll just log a warning
            if '[' in pattern[pattern.find('[') + 1:pattern.find(']')]:
                logger.debug(f"Possible nested character class in pattern: {pattern}")
        
        logger.debug(f"Patched regex pattern in {module_name}: {pattern}")
    
    # Call the original compile function with the fixed pattern
    try:
        return original_compile(pattern, flags)
    except re.error as e:
        logger.warning(f"Failed to compile regex pattern: {pattern}, error: {e}")
        # Try to escape the pattern as a literal string as a fallback
        try:
            return original_compile(re.escape(pattern), flags)
        except re.error:
            # If all else fails, return a pattern that matches nothing
            logger.error(f"Could not fix regex pattern: {pattern}")
            return original_compile(r'(?!)', flags)

def patch_pyptt_regex():
    """Patch PyPtt regex patterns to fix invalid escape sequences."""
    try:
        # Only attempt to patch if PyPtt is installed
        if importlib.util.find_spec("PyPtt") is None:
            logger.warning("PyPtt not found, skipping regex patch")
            return False
        
        # Apply the patch
        re.compile = patched_compile
        logger.info("Patched re.compile to fix invalid escape sequences in PyPtt modules")
        return True
    except Exception as e:
        logger.error(f"Failed to patch PyPtt regex: {str(e)}")
        return False

def direct_patch_pyptt():
    """Directly patch known problematic regex patterns in PyPtt."""
    try:
        # Only attempt to patch if PyPtt is installed
        if importlib.util.find_spec("PyPtt") is None:
            logger.warning("PyPtt not found, skipping direct patch")
            return False
        
        # Import PyPtt modules that need patching
        import PyPtt._api_util as api_util
        import PyPtt._api_get_board_info as get_board_info
        import PyPtt.screens as screens
        import PyPtt.lib_util as lib_util
        import PyPtt._api_get_newest_index as get_newest_index
        import PyPtt._api_get_post as get_post
        import PyPtt._api_get_time as get_time
        import PyPtt._api_loginout as loginout
        import PyPtt._api_mail as mail
        
        # Patch specific patterns in _api_util.py
        if hasattr(api_util, 'line_from_pattern'):
            api_util.line_from_pattern = original_compile(r'[\d]+~[\d]+'.replace('\\d', '\\d'))
        
        if hasattr(api_util, 'pattern_result'):
            api_util.pattern_result = None  # Will be recompiled when needed
            
        # Patch screens.py patterns
        if hasattr(screens, 'xy_pattern_h'):
            screens.xy_pattern_h = original_compile(r'^=ESC=\[\d+;\d+H'.replace('\\d', '\\d'))
            
        if hasattr(screens, 'xy_pattern_s'):
            screens.xy_pattern_s = original_compile(r'^=ESC=\[\d+;\d+s'.replace('\\d', '\\d'))
        
        # Patch lib_util.py patterns
        if hasattr(lib_util, 'pattern'):
            lib_util.pattern = original_compile(r'https://www.ptt.cc/bbs/[-.\w]+/M.[\d]+.A[.\w]*.html'.replace('\\w', '\\w').replace('\\d', '\\d'))
        
        # Patch _api_get_post.py patterns
        if hasattr(get_post, 'push_author_pattern'):
            get_post.push_author_pattern = original_compile(r'[推|噓|→] [\w| ]+:'.replace('\\w', '\\w'))
            
        if hasattr(get_post, 'push_date_pattern'):
            get_post.push_date_pattern = original_compile(r'[\d]+/[\d]+ [\d]+:[\d]+'.replace('\\d', '\\d'))
            
        if hasattr(get_post, 'push_ip_pattern'):
            get_post.push_ip_pattern = original_compile(r'[\d]+\.[\d]+\.[\d]+\.[\d]+'.replace('\\d', '\\d'))
        
        # Add more direct patches as needed
        
        logger.info("Applied direct patches to PyPtt regex patterns")
        return True
    except Exception as e:
        logger.error(f"Failed to apply direct patches to PyPtt: {str(e)}")
        return False

def apply_pyptt_patch():
    """Apply all PyPtt compatibility patches."""
    websockets_patched = patch_websockets()
    regex_patched = patch_pyptt_regex()
    direct_patched = direct_patch_pyptt()
    
    if websockets_patched and (regex_patched or direct_patched):
        logger.info("PyPtt compatibility patches applied successfully")
        return True
    else:
        logger.warning("Some PyPtt compatibility patches failed to apply")
        return False

# Apply patches when the module is imported
apply_pyptt_patch()

# Restore original sys.path if needed
# sys.path = original_path 