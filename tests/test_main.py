"""Tests for the CLI entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from pttautosign.main import main, parse_args, _run_test_login
from pttautosign.utils.config import ConfigValidationError


class TestParseArgs:
    def test_default_has_no_test_login(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign"])
        assert parse_args().test_login is False

    def test_test_login_flag(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign", "--test-login"])
        assert parse_args().test_login is True


class TestRunTestLogin:
    def _ctx(self, accounts, results):
        ctx = MagicMock()
        ctx.get_accounts.return_value = accounts
        ctx.get_login_service.return_value.batch_login.return_value = results
        return ctx

    def test_all_success_does_not_exit(self):
        _run_test_login(self._ctx([("a", "1")], {"a": True}))

    def test_partial_success_does_not_exit(self):
        _run_test_login(
            self._ctx([("a", "1"), ("b", "2")], {"a": True, "b": False})
        )

    def test_all_failure_exits_one(self):
        with pytest.raises(SystemExit) as exc:
            _run_test_login(self._ctx([("a", "1")], {"a": False}))
        assert exc.value.code == 1


# Patch targets: main() imports these lazily from their source modules, so we
# patch them where they are defined.
_PATCH_PATCHES = "pttautosign.patches.pyptt_patch.apply_patches"
_PATCH_DOTENV = "dotenv.load_dotenv"
_PATCH_CTX = "pttautosign.utils.app_context.AppContext"


class TestMain:
    @patch(_PATCH_PATCHES, return_value=True)
    @patch(_PATCH_DOTENV)
    @patch(_PATCH_CTX)
    def test_normal_run(self, mock_ctx_cls, _dotenv, _patches, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign"])
        main()
        ctx = mock_ctx_cls.return_value
        ctx.initialize.assert_called_once()
        ctx.run.assert_called_once()

    @patch(_PATCH_PATCHES, return_value=True)
    @patch(_PATCH_DOTENV)
    @patch(_PATCH_CTX)
    def test_test_login_path(self, mock_ctx_cls, _dotenv, _patches, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign", "--test-login"])
        ctx = mock_ctx_cls.return_value
        ctx.get_accounts.return_value = [("a", "1")]
        ctx.get_login_service.return_value.batch_login.return_value = {"a": True}
        main()
        ctx.run.assert_not_called()

    @patch(_PATCH_PATCHES, return_value=True)
    @patch(_PATCH_DOTENV)
    @patch(_PATCH_CTX)
    def test_config_error_exits_one(self, mock_ctx_cls, _dotenv, _patches, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign"])
        mock_ctx_cls.return_value.initialize.side_effect = ConfigValidationError("bad")
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    @patch(_PATCH_PATCHES, return_value=True)
    @patch(_PATCH_DOTENV)
    @patch(_PATCH_CTX)
    def test_unexpected_error_exits_one(self, mock_ctx_cls, _dotenv, _patches, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pttautosign"])
        mock_ctx_cls.return_value.run.side_effect = RuntimeError("boom")
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    @patch(_PATCH_PATCHES, return_value=False)
    @patch(_PATCH_DOTENV)
    @patch(_PATCH_CTX)
    def test_warns_when_patches_partially_fail(
        self, mock_ctx_cls, _dotenv, _patches, monkeypatch, caplog
    ):
        monkeypatch.setattr(sys, "argv", ["pttautosign"])
        with caplog.at_level("WARNING"):
            main()
        assert any("修補" in r.getMessage() for r in caplog.records)
