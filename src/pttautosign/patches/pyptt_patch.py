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
from typing import Any, Pattern, Optional, Dict

logger = logging.getLogger(__name__)

class PyPttPatcher:
    """Class to handle all PyPtt compatibility patches."""
    
    def __init__(self):
        self._original_compile = re.compile
        self._patched_modules = []
    
    def apply_all(self) -> bool:
        """Apply all patches."""
        logger.debug("Applying PyPtt compatibility patches...")
        
        results = {
            "websockets": self.patch_websockets(),
            "regex": self.patch_pyptt_regex(),
            "direct_patterns": self.direct_patch_pyptt(),
            "warnings": self.suppress_pyptt_warnings()
        }
        
        success_count = sum(1 for v in results.values() if v)
        
        if success_count == len(results):
            logger.info("All PyPtt compatibility patches applied successfully")
            return True
        elif success_count > 0:
            logger.warning(f"Some PyPtt patches applied: {[k for k, v in results.items() if v]}")
            return True
        else:
            logger.error("Failed to apply any PyPtt compatibility patches")
            return False

    def patch_websockets(self) -> bool:
        """Patch websockets.http module to add USER_AGENT attribute if missing."""
        try:
            import websockets.http
            if not hasattr(websockets.http, 'USER_AGENT'):
                logger.debug("Adding USER_AGENT attribute to websockets.http")
                websockets.http.USER_AGENT = "Python/3.13 websockets/12.0"
            return True
        except ImportError:
            # websockets might not be installed or version differs
            return False
        except Exception as e:
            logger.error(f"Failed to patch websockets: {e}")
            return False

    def _fix_pattern(self, pattern_str: str) -> str:
        """Fix invalid escape sequences in regex patterns."""
        if not isinstance(pattern_str, str):
            return pattern_str
            
        # Common escape sequences that need double escaping in strings but are valid in regex
        # map: escape_sequence -> replacement (escaped version)
        escape_sequences = {
            '\\d': '\\\\d', '\\w': '\\\\w', '\\s': '\\\\s', '\\S': '\\\\S',
            '\\[': '\\\\[', '\\]': '\\\\]', '\\(': '\\\\(', '\\)': '\\\\)',
            '\\{': '\\\\{', '\\}': '\\\\}', '\\+': '\\\\+', '\\-': '\\\\-',
            '\\|': '\\\\|', '\\.': '\\\\.'
        }
        
        for seq, replacement in escape_sequences.items():
            # Check if seq is in pattern and NOT preceded by a backslash (already escaped)
            # This is a naive check but works for most PyPtt cases
            if seq in pattern_str and not ('\\\\' + seq[1]) in pattern_str:
                pattern_str = pattern_str.replace(seq, replacement[1:])
        
        return pattern_str

    def _patched_compile(self, pattern, flags=0):
        """Patched version of re.compile."""
        # Get the caller's module name to only apply patch to PyPtt
        try:
            import inspect
            frame = inspect.currentframe().f_back
            module_name = frame.f_globals.get('__name__', '')
        except Exception:
            module_name = ''
        
        if isinstance(pattern, str) and module_name.startswith('PyPtt'):
            pattern = self._fix_pattern(pattern)
            # logger.debug(f"Patched regex pattern in {module_name}")
        
        try:
            return self._original_compile(pattern, flags)
        except re.error as e:
            logger.warning(f"Regex compilation error: {e}. Pattern: {pattern}")
            # Fallback attempts
            try:
                return self._original_compile(re.escape(pattern), flags)
            except re.error:
                return self._original_compile(r'(?!)', flags)

    def patch_pyptt_regex(self) -> bool:
        """Patch PyPtt regex patterns globally by hooking re.compile."""
        try:
            if importlib.util.find_spec("PyPtt") is None:
                return False
            
            re.compile = self._patched_compile
            logger.debug("Patched re.compile for PyPtt modules")
            return True
        except Exception as e:
            logger.error(f"Failed to patch PyPtt regex: {e}")
            return False

    def suppress_pyptt_warnings(self) -> bool:
        """Suppress SyntaxWarning and FutureWarning from PyPtt."""
        try:
            for category in [SyntaxWarning, FutureWarning, DeprecationWarning]:
                warnings.filterwarnings("ignore", category=category, module="PyPtt.*")
                warnings.filterwarnings("ignore", category=category, module=".*pyptt_patch.*")
            return True
        except Exception as e:
            logger.error(f"Failed to suppress warnings: {e}")
            return False

    def direct_patch_pyptt(self) -> bool:
        """Directly patch known problematic modules/attributes in PyPtt."""
        try:
            if importlib.util.find_spec("PyPtt") is None:
                return False

            # 1. Disable PyPtt Logs if requested
            self._patch_pyptt_logging()

            # 2. Patch specific modules
            modules_to_patch = [
                'PyPtt._api_util',
                'PyPtt.screens',
                'PyPtt.lib_util',
                'PyPtt._api_get_post',
                'PyPtt._api_get_board_info',
                'PyPtt._api_get_newest_index',
                'PyPtt._api_get_time',
                'PyPtt._api_loginout',
                'PyPtt._api_mail'
            ]
            
            for mod_name in modules_to_patch:
                self._patch_module_regex(mod_name)

            # 3. Special case patches
            self._apply_special_patches()
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply direct patches: {e}")
            return False

    def _patch_pyptt_logging(self):
        """Patch PyPtt logging to be silent if configured."""
        if os.environ.get('PYPTT_DISABLE_LOGS', '0').lower() in ('1', 'true', 'yes'):
            try:
                from PyPtt import PTT
                import PyPtt.log as ptt_log
                
                original_init = PTT.API.__init__
                def patched_init(self, *args, **kwargs):
                    if hasattr(ptt_log, 'SILENT'):
                        kwargs['log_level'] = ptt_log.SILENT
                    original_init(self, *args, **kwargs)
                
                PTT.API.__init__ = patched_init
                logger.info("forced PyPtt API to SILENT log level")
            except Exception as e:
                logger.warning(f"Could not patch PyPtt logging: {e}")

    def _patch_module_regex(self, module_name: str):
        """Fix regex patterns in a specific module."""
        try:
            # Dynamically import the module
            if module_name not in sys.modules:
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    return

            module = sys.modules[module_name]
            
            for attr_name in dir(module):
                if attr_name.startswith('__'):
                    continue
                
                attr = getattr(module, attr_name)
                if isinstance(attr, re.Pattern):
                    try:
                        fixed_pattern = self._fix_pattern(attr.pattern)
                        if fixed_pattern != attr.pattern:
                            setattr(module, attr_name, self._original_compile(fixed_pattern))
                            # logger.debug(f"Fixed {module_name}.{attr_name}")
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error patching module {module_name}: {e}")

    def _apply_special_patches(self):
        """Apply specific Logic patches."""
        # Patch screens.get_data to remove ANSI codes if it fails regex
        try:
            import PyPtt.screens as screens
            if hasattr(screens, 'get_data'):
                original_get_data = screens.get_data
                def patched_get_data(self, *args, **kwargs):
                    result = original_get_data(self, *args, **kwargs)
                    if isinstance(result, str) and '\x1B[' in result:
                        return re.sub(r'\x1B\[\d+;*\d*m', '', result)
                    return result
                screens.get_data = patched_get_data
        except ImportError:
            pass

# Create and apply patches on import
_patcher = PyPttPatcher()
_patcher.apply_all()