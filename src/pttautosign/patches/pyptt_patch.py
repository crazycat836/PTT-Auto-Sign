"""
Patch for PyPtt compatibility issues with websockets and Python 3.13.
This module should be imported before importing PyPtt.
"""

import sys
import logging
import importlib.util
import re
import warnings
import os
from typing import Any, Pattern

logger = logging.getLogger(__name__)

def patch_websockets():
    """Patch websockets.http module to add USER_AGENT attribute if missing."""
    try:
        import websockets.http
        if not hasattr(websockets.http, 'USER_AGENT'):
            logger.info("Adding USER_AGENT attribute to websockets.http")
            websockets.http.USER_AGENT = "Python/3.13 websockets/12.0"
            return True
        return True
    except ImportError:
        logger.error("Failed to import websockets.http")
        return False

# Store the original re.compile function
original_compile = re.compile

# Keep track of whether we're in PyPtt module
in_pyptt_module = False

# Helper function to fix regex patterns
def fix_pattern(pattern_str):
    """Fix invalid escape sequences in regex patterns."""
    if not isinstance(pattern_str, str):
        return pattern_str
        
    # Fix common escape sequences
    escape_sequences = {
        '\\d': '\\\\d',  # Digit
        '\\w': '\\\\w',  # Word character
        '\\s': '\\\\s',  # Whitespace
        '\\S': '\\\\S',  # Non-whitespace
        '\\[': '\\\\[',  # Opening bracket
        '\\]': '\\\\]',  # Closing bracket
        '\\(': '\\\\(',  # Opening parenthesis
        '\\)': '\\\\)',  # Closing parenthesis
        '\\{': '\\\\{',  # Opening brace
        '\\}': '\\\\}',  # Closing brace
        '\\+': '\\\\+',  # Plus sign
        '\\-': '\\\\-',  # Minus sign
        '\\|': '\\\\|',  # Pipe
        '\\.': '\\\\.',  # Dot
    }
    
    # Only replace if not already properly escaped
    for seq, replacement in escape_sequences.items():
        if seq in pattern_str and not '\\\\' + seq[1] in pattern_str:
            pattern_str = pattern_str.replace(seq, replacement[1:])
    
    return pattern_str

def patched_compile(pattern, flags=0):
    """Patched version of re.compile that fixes invalid escape sequences only for PyPtt modules."""
    global in_pyptt_module
    
    # Get the caller's module
    import inspect
    frame = inspect.currentframe().f_back
    module_name = frame.f_globals.get('__name__', '')
    
    # Only patch patterns from PyPtt modules
    if isinstance(pattern, str) and module_name.startswith('PyPtt'):
        # Use the fix_pattern function to fix the pattern
        pattern = fix_pattern(pattern)
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

def suppress_pyptt_warnings():
    """Suppress SyntaxWarning warnings from PyPtt modules."""
    try:
        # Filter out SyntaxWarnings from PyPtt modules
        warnings.filterwarnings("ignore", category=SyntaxWarning, module="PyPtt.*")
        warnings.filterwarnings("ignore", category=FutureWarning, module="PyPtt.*")
        warnings.filterwarnings("ignore", category=SyntaxWarning, module=".*pyptt_patch.*")
        warnings.filterwarnings("ignore", category=FutureWarning, module=".*pyptt_patch.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="PyPtt.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*pyptt_patch.*")
        logger.info("Suppressed SyntaxWarning and FutureWarning warnings from PyPtt modules")
        return True
    except Exception as e:
        logger.error(f"Failed to suppress PyPtt warnings: {str(e)}")
        return False

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
        
        # Check if we should disable PyPtt logs
        disable_logs = os.environ.get('PYPTT_DISABLE_LOGS', '0').lower() in ('1', 'true', 'yes')
        
        # Patch PyPtt logging to use our logger
        try:
            import PyPtt.log as ptt_log
            from PyPtt import PTT
            
            # Only patch the PyPtt API to use SILENT log level
            if disable_logs:
                # Store the original __init__ method
                original_init = PTT.API.__init__
                
                # Create a patched __init__ method that always sets log_level to SILENT
                def patched_init(self, *args, **kwargs):
                    # Force log_level to SILENT
                    if hasattr(ptt_log, 'SILENT'):
                        kwargs['log_level'] = ptt_log.SILENT
                    original_init(self, *args, **kwargs)
                
                # Apply the patch
                PTT.API.__init__ = patched_init
                logger.info("Patched PyPtt API to use SILENT log level")
            
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to patch PyPtt logging: {str(e)}")
        
        # Patch _api_util.py patterns
        if hasattr(api_util, 'line_from_pattern'):
            api_util.line_from_pattern = original_compile(fix_pattern(r'[\d]+~[\d]+'))
        
        if hasattr(api_util, 'pattern_result'):
            # Will be recompiled when needed, but we'll fix it anyway
            api_util.pattern_result = None
        
        # Fix all patterns in api_util
        for attr_name in dir(api_util):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(api_util, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(api_util, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in api_util.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in api_util.{attr_name}: {str(e)}")
        
        # Patch screens.py patterns
        if hasattr(screens, 'xy_pattern_h'):
            screens.xy_pattern_h = original_compile(fix_pattern(r'^=ESC=\[\d+;\d+H'))
            
        if hasattr(screens, 'xy_pattern_s'):
            screens.xy_pattern_s = original_compile(fix_pattern(r'^=ESC=\[\d+;\d+s'))
        
        # Fix all patterns in screens
        for attr_name in dir(screens):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(screens, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(screens, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in screens.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in screens.{attr_name}: {str(e)}")
        
        # Patch lib_util.py patterns
        if hasattr(lib_util, 'pattern'):
            lib_util.pattern = original_compile(fix_pattern(r'https://www.ptt.cc/bbs/[-.\w]+/M.[\d]+.A[.\w]*.html'))
        
        # Fix all patterns in lib_util
        for attr_name in dir(lib_util):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(lib_util, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(lib_util, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in lib_util.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in lib_util.{attr_name}: {str(e)}")
        
        # Patch _api_get_post.py patterns
        if hasattr(get_post, 'push_author_pattern'):
            get_post.push_author_pattern = original_compile(fix_pattern(r'[推|噓|→] [\w| ]+:'))
            
        if hasattr(get_post, 'push_date_pattern'):
            get_post.push_date_pattern = original_compile(fix_pattern(r'[\d]+/[\d]+ [\d]+:[\d]+'))
            
        if hasattr(get_post, 'push_ip_pattern'):
            get_post.push_ip_pattern = original_compile(fix_pattern(r'[\d]+\.[\d]+\.[\d]+\.[\d]+'))
        
        # Fix all patterns in get_post
        for attr_name in dir(get_post):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(get_post, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(get_post, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in get_post.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in get_post.{attr_name}: {str(e)}")
        
        # Fix all patterns in get_board_info
        for attr_name in dir(get_board_info):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(get_board_info, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(get_board_info, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in get_board_info.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in get_board_info.{attr_name}: {str(e)}")
        
        # Fix all patterns in get_newest_index
        for attr_name in dir(get_newest_index):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(get_newest_index, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(get_newest_index, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in get_newest_index.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in get_newest_index.{attr_name}: {str(e)}")
        
        # Fix all patterns in get_time
        for attr_name in dir(get_time):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(get_time, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(get_time, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in get_time.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in get_time.{attr_name}: {str(e)}")
        
        # Fix all patterns in loginout
        for attr_name in dir(loginout):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(loginout, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(loginout, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in loginout.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in loginout.{attr_name}: {str(e)}")
        
        # Fix all patterns in mail
        for attr_name in dir(mail):
            if attr_name.startswith('__'):
                continue
            
            attr = getattr(mail, attr_name)
            if isinstance(attr, re.Pattern):
                try:
                    pattern_str = attr.pattern
                    fixed_pattern = fix_pattern(pattern_str)
                    setattr(mail, attr_name, original_compile(fixed_pattern))
                    logger.debug(f"Fixed pattern in mail.{attr_name}: {pattern_str} -> {fixed_pattern}")
                except Exception as e:
                    logger.warning(f"Failed to fix pattern in mail.{attr_name}: {str(e)}")
        
        # Fix re.sub calls in screens.py
        if hasattr(screens, 'get_data') and callable(screens.get_data):
            original_get_data = screens.get_data
            
            def patched_get_data(self, *args, **kwargs):
                result = original_get_data(self, *args, **kwargs)
                if isinstance(result, str) and '\x1B[' in result:
                    # Fix the problematic re.sub call
                    return re.sub(r'\x1B\[\d+;*\d*m', '', result)
                return result
            
            screens.get_data = patched_get_data
        
        logger.info("Applied direct patches to PyPtt regex patterns")
        return True
    except Exception as e:
        logger.error(f"Failed to apply direct patches to PyPtt: {str(e)}")
        return False

def apply_pyptt_patch():
    """Apply all PyPtt compatibility patches."""
    # Log a single message at the start
    logger.info("Applying PyPtt compatibility patches...")
    
    # Apply patches
    websockets_patched = patch_websockets()
    regex_patched = patch_pyptt_regex()
    direct_patched = direct_patch_pyptt()
    warnings_suppressed = suppress_pyptt_warnings()
    
    # Log a summary of applied patches
    patches_applied = []
    if websockets_patched:
        patches_applied.append("websockets")
    if regex_patched:
        patches_applied.append("regex")
    if direct_patched:
        patches_applied.append("direct patterns")
    if warnings_suppressed:
        patches_applied.append("warnings")
    
    if len(patches_applied) == 4:
        logger.info("All PyPtt compatibility patches applied successfully")
        return True
    elif len(patches_applied) > 0:
        logger.warning(f"Some PyPtt patches applied: {', '.join(patches_applied)}")
        return True
    else:
        logger.error("Failed to apply any PyPtt compatibility patches")
        return False

# Apply patches when the module is imported
apply_pyptt_patch()

# Restore original sys.path if needed
# sys.path = original_path 