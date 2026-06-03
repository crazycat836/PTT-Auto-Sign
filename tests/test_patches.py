"""Tests for the PyPtt compatibility patch loader."""

from pttautosign.patches.pyptt_patch import PyPttPatcher, apply_patches


def test_apply_patches_succeeds_in_dev_env():
    # websockets and PyPtt are installed in the dev environment, so every
    # patch should apply successfully.
    assert apply_patches() is True


def test_partial_failure_returns_false(monkeypatch):
    # H2 regression: a single failed patch must not report overall success.
    patcher = PyPttPatcher()
    monkeypatch.setattr(patcher, "patch_websockets", lambda: True)
    monkeypatch.setattr(patcher, "suppress_pyptt_warnings", lambda: True)
    monkeypatch.setattr(patcher, "direct_patch_pyptt", lambda: False)
    assert patcher.apply_all() is False


def test_total_failure_returns_false(monkeypatch):
    patcher = PyPttPatcher()
    monkeypatch.setattr(patcher, "patch_websockets", lambda: False)
    monkeypatch.setattr(patcher, "suppress_pyptt_warnings", lambda: False)
    monkeypatch.setattr(patcher, "direct_patch_pyptt", lambda: False)
    assert patcher.apply_all() is False
