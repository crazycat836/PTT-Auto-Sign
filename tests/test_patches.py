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
    # default 呼叫器 marker (e.g. to a date/時辰 display), which makes
    # every login falsely raise LoginError even though it actually
    # succeeded. apply_patches() must strip that marker so detection relies
    # only on the two markers every main menu always has.
    #
    # Assert on substrings, not on exact strings: PyPtt spells these markers
    # differently across versions ('[呼叫器]' / '人, 我是' in 1.3.3, '呼叫器' /
    # '我是' in 2.3.7). Pinning the exact 1.3.3 spelling made the first
    # assertion pass vacuously on 2.3.7 -- the marker really was still in the
    # list, just without its brackets -- which is exactly the case this test
    # exists to catch.
    import PyPtt.screens as screens

    apply_patches()

    assert not [m for m in screens.Target.MainMenu if "呼叫器" in m]
    assert any("離開，再見" in m for m in screens.Target.MainMenu)
    assert any("我是" in m for m in screens.Target.MainMenu)


def test_mainmenu_patch_handles_both_pyptt_spellings():
    # Guard the substring matching directly, so the patch keeps working when a
    # future PyPtt renames the marker again. Drive it with a stand-in screens
    # module rather than whichever PyPtt version happens to be installed.
    from types import SimpleNamespace

    for spelling in ("[呼叫器]", "呼叫器", "(呼叫器)"):
        menu = ["離開，再見", "我是", spelling]
        screens = SimpleNamespace(Target=SimpleNamespace(MainMenu=menu))

        PyPttPatcher()._patch_mainmenu_detection(screens)

        assert menu == ["離開，再見", "我是"], f"{spelling!r} 沒有被移除"
        # Must mutate in place: PyPtt keeps its own reference to this list.
        assert screens.Target.MainMenu is menu
