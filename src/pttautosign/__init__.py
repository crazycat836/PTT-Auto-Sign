"""
PTT Auto Sign - A tool for automatic PTT login with Telegram notifications.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import TYPE_CHECKING, Any

try:
    __version__ = _pkg_version("pttautosign")
except PackageNotFoundError:  # not installed (e.g. running from a source tree)
    __version__ = "0.0.0"

__author__ = "crazycat836"
__email__ = "crazycat836@gmail.com"

__all__ = [
    "AppConfig",
    "ConfigValidationError",
    "AppContext",
    "main",
]

if TYPE_CHECKING:  # for type checkers / IDEs only — no runtime import
    from pttautosign.utils.config import AppConfig, ConfigValidationError
    from pttautosign.utils.app_context import AppContext
    from pttautosign.main import main


def __getattr__(name: str) -> Any:
    """Lazily resolve public symbols (PEP 562).

    Importing ``pttautosign`` stays side-effect free: PyPtt is not imported and
    no compatibility patches are applied until a symbol is actually used. This
    keeps modules such as ``pttautosign.utils.config`` importable in isolation
    (e.g. for unit tests) without triggering global state mutation.
    """
    if name in ("AppConfig", "ConfigValidationError"):
        from pttautosign.utils import config

        return getattr(config, name)
    if name == "AppContext":
        from pttautosign.utils.app_context import AppContext

        return AppContext
    if name == "main":
        from pttautosign.main import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
