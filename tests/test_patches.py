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


# Main menu as PTT1 draws it since the 2026-10-04 footer redesign: the footer
# no longer carries 「我是」 or 「呼叫器」 (PttCurrent M.1789902495.A.1C6).
NEW_MAIN_MENU_SCREEN = """【主功能表】                     批踢踢實業坊
                      (A)nnounce     【 精華公佈欄 】
                    > (C)lass        【 分組討論區 】
                      (G)oodbye         離開，再見…
 主選單  [ 處女時 ]    10/6 週二 11:41 | crazycat836 | 線上27863人     (h)說明"""

# Main menu before the redesign, in the short footer format.
OLD_MAIN_MENU_SCREEN = """【主功能表】                     批踢踢實業坊
                      (A)nnounce     【 精華公佈欄 】
                    > (C)lass        【 分組討論區 】
                      (G)oodbye         離開，再見…
8/19週三22:35   [ 七夕 ]   線上30721人,我是DeepLearning 呼叫器關閉  (h)說明"""


def _is_main_menu(screen, markers):
    # Same check PyPtt's login() uses to decide whether it reached the menu.
    return all(m in screen for m in markers)


def test_mainmenu_detection_matches_new_and_old_footer():
    # Regression: after PTT's 2026-10-04 footer redesign, PyPtt's 「我是」
    # marker never matched, login kept pressing ← to "go back to the main
    # menu" and PTT dropped the connection on every attempt.
    import PyPtt.screens as screens

    apply_patches()

    markers = screens.Target.MainMenu
    assert _is_main_menu(NEW_MAIN_MENU_SCREEN, markers), markers
    assert _is_main_menu(OLD_MAIN_MENU_SCREEN, markers), markers


def test_mainmenu_detection_drops_footer_markers():
    # Footer text is not stable: 「呼叫器」 is a per-account display setting and
    # PTT removed both 「呼叫器」 and 「我是」 on 2026-10-04. Detection must rely
    # on the (G)oodbye item and the 【主功能表】 title that PTT keeps fixed.
    #
    # Assert on substrings, not on exact strings: PyPtt spells these markers
    # differently across versions ('[呼叫器]' / '人, 我是' in 1.3.3, '呼叫器' /
    # '我是' in 2.3.7). Pinning one exact spelling lets the assertion pass
    # vacuously on another version.
    import PyPtt.screens as screens

    apply_patches()

    assert not [m for m in screens.Target.MainMenu if "呼叫器" in m]
    assert not [m for m in screens.Target.MainMenu if "我是" in m]
    assert any("離開，再見" in m for m in screens.Target.MainMenu)
    assert "【主功能表】" in screens.Target.MainMenu


def test_mainmenu_patch_handles_pyptt_spellings():
    # Guard the substring matching directly, so the patch keeps working when a
    # future PyPtt renames the markers again. Drive it with a stand-in screens
    # module rather than whichever PyPtt version happens to be installed.
    from types import SimpleNamespace

    for caller, me in (("[呼叫器]", "人, 我是"), ("呼叫器", "我是"), ("(呼叫器)", "我是")):
        menu = ["離開，再見", me, caller]
        screens = SimpleNamespace(Target=SimpleNamespace(MainMenu=menu))

        PyPttPatcher()._patch_mainmenu_detection(screens)

        assert menu == ["離開，再見", "【主功能表】"], f"{caller!r}/{me!r} 沒有被換掉"
        # Must mutate in place: PyPtt keeps its own reference to this list.
        assert screens.Target.MainMenu is menu


def test_mainmenu_patch_is_idempotent():
    from types import SimpleNamespace

    menu = ["離開，再見", "我是", "呼叫器"]
    screens = SimpleNamespace(Target=SimpleNamespace(MainMenu=menu))

    PyPttPatcher()._patch_mainmenu_detection(screens)
    PyPttPatcher()._patch_mainmenu_detection(screens)

    assert menu == ["離開，再見", "【主功能表】"]
