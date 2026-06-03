"""
Patch for PyPtt compatibility issues with websockets and newer Python versions.
This module should be imported before importing PyPtt.
"""

import os
import re
import sys
import logging
import warnings
import importlib.util

logger = logging.getLogger(__name__)


class PyPttPatcher:
    """Apply targeted, import-time compatibility patches for PyPtt."""

    def apply_all(self) -> bool:
        logger.debug("Applying PyPtt compatibility patches...")

        results = {
            "websockets": self.patch_websockets(),
            "warnings": self.suppress_pyptt_warnings(),
            "pyptt_module_tweaks": self.direct_patch_pyptt(),
        }

        success_count = sum(1 for v in results.values() if v)

        if success_count == len(results):
            logger.info("All PyPtt compatibility patches applied successfully")
            return True

        # Partial application is a degraded state, not a success: surface the
        # failed patches and return False so callers can react (H2).
        failed = [k for k, v in results.items() if not v]
        applied = [k for k, v in results.items() if v]
        if success_count > 0:
            logger.warning(f"Some PyPtt patches failed: {failed} (applied: {applied})")
        else:
            logger.error("Failed to apply any PyPtt compatibility patches")
        return False

    def patch_websockets(self) -> bool:
        """Backfill USER_AGENT attribute on websockets.http when missing."""
        try:
            import websockets
            import websockets.http
            if not hasattr(websockets.http, "USER_AGENT"):
                py_version = sys.version.split()[0]
                ws_version = getattr(websockets, "__version__", "unknown")
                websockets.http.USER_AGENT = f"Python/{py_version} websockets/{ws_version}"
                logger.debug("Added USER_AGENT to websockets.http")
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.error(f"Failed to patch websockets: {type(e).__name__}: {e}")
            logger.debug("websockets patch traceback", exc_info=True)
            return False

    def suppress_pyptt_warnings(self) -> bool:
        """Silence noisy SyntaxWarning / FutureWarning / DeprecationWarning from PyPtt."""
        try:
            for category in (SyntaxWarning, FutureWarning, DeprecationWarning):
                warnings.filterwarnings("ignore", category=category, module="PyPtt.*")
                warnings.filterwarnings("ignore", category=category, module=".*pyptt_patch.*")
            return True
        except Exception as e:
            logger.error(f"Failed to suppress warnings: {type(e).__name__}: {e}")
            logger.debug("warning-suppression traceback", exc_info=True)
            return False

    def direct_patch_pyptt(self) -> bool:
        """Apply targeted runtime tweaks to PyPtt (logging, ANSI stripping)."""
        try:
            if importlib.util.find_spec("PyPtt") is None:
                return False

            self._patch_pyptt_logging()
            self._apply_special_patches()
            return True
        except Exception as e:
            logger.error(f"Failed to apply direct patches: {type(e).__name__}: {e}")
            logger.debug("direct-patch traceback", exc_info=True)
            return False

    def _patch_pyptt_logging(self) -> None:
        """Force PyPtt API into SILENT log level when requested via env."""
        if os.environ.get("PYPTT_DISABLE_LOGS", "0").lower() not in ("1", "true", "yes"):
            return
        try:
            from PyPtt import PTT
            import PyPtt.log as ptt_log

            original_init = PTT.API.__init__

            def patched_init(self, *args, **kwargs):
                if hasattr(ptt_log, "SILENT"):
                    kwargs["log_level"] = ptt_log.SILENT
                original_init(self, *args, **kwargs)

            PTT.API.__init__ = patched_init
            logger.info("Forced PyPtt API to SILENT log level")
        except Exception as e:
            logger.warning(f"Could not patch PyPtt logging: {type(e).__name__}: {e}")
            logger.debug("PyPtt logging-patch traceback", exc_info=True)

    def _apply_special_patches(self) -> None:
        """Strip ANSI escape codes from screens.get_data output when present."""
        try:
            import PyPtt.screens as screens
        except ImportError:
            return

        if not hasattr(screens, "get_data"):
            return

        original_get_data = screens.get_data
        ansi_re = re.compile(r"\x1B\[\d+;*\d*m")

        def patched_get_data(*args, **kwargs):
            result = original_get_data(*args, **kwargs)
            if isinstance(result, str) and "\x1B[" in result:
                return ansi_re.sub("", result)
            return result

        screens.get_data = patched_get_data


def apply_patches() -> bool:
    """Apply all PyPtt compatibility patches.

    Call this explicitly once, before PyPtt is used, instead of relying on
    import-time side effects. Returns True only when every patch succeeds.
    """
    return PyPttPatcher().apply_all()


__all__ = ["PyPttPatcher", "apply_patches"]
