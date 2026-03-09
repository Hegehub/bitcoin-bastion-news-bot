import importlib


def _load_keyboards_with_url(monkeypatch, url: str):
    import config
    monkeypatch.setattr(config, "WEBAPP_URL", url)
    import keyboards
    return importlib.reload(keyboards)


def test_main_menu_hides_webapp_button_for_non_https(monkeypatch):
    keyboards = _load_keyboards_with_url(monkeypatch, "http://localhost:8000/webapp")

    markup = keyboards.main_menu_keyboard("en")

    web_app_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "web_app", None)
    ]
    assert web_app_buttons == []


def test_main_menu_shows_webapp_button_for_https(monkeypatch):
    keyboards = _load_keyboards_with_url(monkeypatch, "https://example.com/webapp")

    markup = keyboards.main_menu_keyboard("en")

    web_app_buttons = [
        btn for row in markup.inline_keyboard for btn in row if getattr(btn, "web_app", None)
    ]
    assert len(web_app_buttons) == 1
    assert web_app_buttons[0].web_app.url == "https://example.com/webapp"
