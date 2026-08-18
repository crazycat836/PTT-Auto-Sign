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


def test_mainmenu_detection_drops_unreliable_caller_marker():
    # Some accounts customize the main-menu corner display away from PTT's
    # default '[呼叫器]' marker (e.g. to a date/時辰 display), which makes
    # every login falsely raise LoginError even though it actually
    # succeeded. apply_patches() must strip that marker so detection relies
    # only on the two markers every main menu always has.
    import PyPtt.screens as screens

    apply_patches()

    assert "[呼叫器]" not in screens.Target.MainMenu
    assert "離開，再見" in screens.Target.MainMenu
    assert "人, 我是" in screens.Target.MainMenu
